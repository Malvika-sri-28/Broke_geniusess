import os
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from database import db, User, Service, Order, Review
from utils.helpers import save_uploaded_file, UNIVERSITIES
from utils.recommender import get_recommended_services

service_bp = Blueprint('service', __name__)

@service_bp.route('/services')
def browse_services():
    query = request.args.get('q', '').strip()
    university_filter = request.args.get('university', '').strip()
    min_price = request.args.get('min_price', '').strip()
    max_price = request.args.get('max_price', '').strip()
    sort_by = request.args.get('sort', 'newest')

    # Base query
    services_query = Service.query

    # Apply keyword search (title, description, keywords)
    if query:
        search_pattern = f"%{query}%"
        services_query = services_query.filter(
            (Service.title.ilike(search_pattern)) |
            (Service.description.ilike(search_pattern)) |
            (Service.keywords.ilike(search_pattern))
        )

    # Apply university filtering (case-insensitive partial match)
    if university_filter:
        services_query = services_query.filter(Service.university.ilike(f"%{university_filter}%"))

    # Apply price constraints
    if min_price:
        try:
            services_query = services_query.filter(Service.price >= float(min_price))
        except ValueError:
            pass
    if max_price:
        try:
            services_query = services_query.filter(Service.price <= float(max_price))
        except ValueError:
            pass

    # Sorting
    if sort_by == 'price_asc':
        services_query = services_query.order_by(Service.price.asc())
    elif sort_by == 'price_desc':
        services_query = services_query.order_by(Service.price.desc())
    elif sort_by == 'rating':
        services_query = services_query.order_by(Service.total_rating.desc())
    else: # newest first
        services_query = services_query.order_by(Service.created_at.desc())

    services = services_query.all()

    # Get list of unique universities that have active services for filter dropdown
    db_unis = db.session.query(Service.university).distinct().all()
    db_unis = [u[0] for u in db_unis if u[0]]
    
    # Merge predefined universities with active database universities, sorted alphabetically
    universities = sorted(list(set(UNIVERSITIES + db_unis)))

    return render_template(
        'services/browse_services.html',
        services=services,
        universities=universities,
        search_query=query,
        selected_university=university_filter,
        min_price=min_price,
        max_price=max_price,
        sort_by=sort_by
    )

@service_bp.route('/services/new', methods=['GET', 'POST'])
@login_required
def post_service():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        price = request.form.get('price', '').strip()
        keywords = request.form.get('keywords', '').strip()
        service_image = request.files.get('service_image')
        
        if not title or not description or not price:
            flash("Title, description, and price are required.", "danger")
            return render_template('services/post_service.html')
            
        try:
            price_val = float(price)
            if price_val <= 0:
                flash("Price must be a positive number.", "danger")
                return render_template('services/post_service.html')
        except ValueError:
            flash("Invalid price format.", "danger")
            return render_template('services/post_service.html')
            
        # Handle file upload
        image_filename = 'default_service.png'
        if service_image and service_image.filename != '':
            saved_filename = save_uploaded_file(service_image, current_app.config['SERVICE_IMAGES_DIR'])
            if saved_filename:
                image_filename = saved_filename
            else:
                flash("Invalid image format. Allowed formats: PNG, JPG, JPEG, WEBP.", "danger")
                return render_template('services/post_service.html')
                
        # Create service
        new_service = Service(
            title=title,
            description=description,
            price=price_val,
            image=image_filename,
            seller_id=current_user.id,
            university=current_user.university, # service is anchored to seller's uni
            keywords=keywords
        )
        
        db.session.add(new_service)
        db.session.commit()
        
        flash("Service listing posted successfully!", "success")
        return redirect(url_for('profile.view_profile'))
        
    return render_template('services/post_service.html')

@service_bp.route('/services/<int:service_id>')
def service_detail(service_id):
    service = Service.query.get_or_404(service_id)
    reviews = Review.query.filter_by(service_id=service.id).order_by(Review.created_at.desc()).all()
    keywords_list = [k.strip() for k in service.keywords.split(',')] if service.keywords else []
    
    # Check if the current user has already purchased this service
    has_purchased = False
    if current_user.is_authenticated:
        completed_order = Order.query.filter_by(
            buyer_id=current_user.id,
            service_id=service.id,
            status='Completed'
        ).first()
        if completed_order:
            has_purchased = True

    # Get related services recommendations using text analysis
    recommended_services = get_recommended_services(service, limit=3)

    return render_template(
        'services/service_detail.html',
        service=service,
        reviews=reviews,
        keywords_list=keywords_list,
        has_purchased=has_purchased,
        recommended_services=recommended_services
    )

@service_bp.route('/services/<int:service_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_service(service_id):
    service = Service.query.get_or_404(service_id)
    
    # Check authorization
    if service.seller_id != current_user.id and not current_user.is_admin:
        flash("Unauthorized action.", "danger")
        return redirect(url_for('service.service_detail', service_id=service.id))
        
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        price = request.form.get('price', '').strip()
        keywords = request.form.get('keywords', '').strip()
        service_image = request.files.get('service_image')
        
        if not title or not description or not price:
            flash("Title, description, and price are required.", "danger")
            return render_template('services/edit_service.html', service=service)
            
        try:
            price_val = float(price)
            if price_val <= 0:
                flash("Price must be a positive number.", "danger")
                return render_template('services/edit_service.html', service=service)
        except ValueError:
            flash("Invalid price format.", "danger")
            return render_template('services/edit_service.html', service=service)
            
        # Handle file upload
        if service_image and service_image.filename != '':
            saved_filename = save_uploaded_file(service_image, current_app.config['SERVICE_IMAGES_DIR'])
            if saved_filename:
                # Delete old service image if it wasn't default
                if service.image and service.image != 'default_service.png':
                    old_path = os.path.join(current_app.config['SERVICE_IMAGES_DIR'], service.image)
                    if os.path.exists(old_path):
                        try:
                            os.remove(old_path)
                        except Exception as e:
                            print(f"Error removing old service image: {e}")
                service.image = saved_filename
            else:
                flash("Invalid image format. Allowed formats: PNG, JPG, JPEG, WEBP.", "danger")
                return render_template('services/edit_service.html', service=service)
                
        service.title = title
        service.description = description
        service.price = price_val
        service.keywords = keywords
        
        db.session.commit()
        flash("Service listing updated successfully!", "success")
        return redirect(url_for('service.service_detail', service_id=service.id))
        
    return render_template('services/edit_service.html', service=service)

@service_bp.route('/services/<int:service_id>/delete', methods=['POST'])
@login_required
def delete_service(service_id):
    service = Service.query.get_or_404(service_id)
    
    # Check authorization
    if service.seller_id != current_user.id and not current_user.is_admin:
        flash("Unauthorized action.", "danger")
        return redirect(url_for('service.service_detail', service_id=service.id))
        
    # Delete image if not default
    if service.image and service.image != 'default_service.png':
        img_path = os.path.join(current_app.config['SERVICE_IMAGES_DIR'], service.image)
        if os.path.exists(img_path):
            try:
                os.remove(img_path)
            except Exception as e:
                print(f"Error deleting service image: {e}")
                
    db.session.delete(service)
    db.session.commit()
    flash("Service has been deleted.", "info")
    
    if current_user.is_admin:
        return redirect(url_for('admin.services_list'))
    return redirect(url_for('profile.view_profile'))

# Order Creation / Booking Route
@service_bp.route('/services/<int:service_id>/book', methods=['POST'])
@login_required
def book_service(service_id):
    service = Service.query.get_or_404(service_id)
    
    # Prevent booking demo services
    if service.seller.is_demo:
        flash("This is a demo listing. Booking is disabled for example services.", "warning")
        return redirect(url_for('service.service_detail', service_id=service.id))
        
    # Prevent self-booking
    if service.seller_id == current_user.id:
        flash("You cannot book your own service!", "warning")
        return redirect(url_for('service.service_detail', service_id=service.id))
        
    # Create new order
    order = Order(
        buyer_id=current_user.id,
        seller_id=service.seller_id,
        service_id=service.id,
        status='Pending'
    )
    
    db.session.add(order)
    db.session.commit()
    
    flash("Service booked successfully! The seller has been notified to accept your request.", "success")
    return redirect(url_for('profile.view_profile'))
