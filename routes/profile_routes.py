import os
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from database import db, User, Service, Review, Order
from utils.helpers import save_uploaded_file

profile_bp = Blueprint('profile', __name__)

@profile_bp.route('/profile')
@login_required
def view_profile():
    # Fetch own services
    my_services = Service.query.filter_by(seller_id=current_user.id).order_by(Service.created_at.desc()).all()
    
    # Fetch orders where the current user is the buyer
    orders_bought = Order.query.filter_by(buyer_id=current_user.id).order_by(Order.created_at.desc()).all()
    
    # Fetch orders where the current user is the seller
    orders_sold = Order.query.filter_by(seller_id=current_user.id).order_by(Order.created_at.desc()).all()
    
    # Fetch all reviews received across all the seller's services
    my_service_ids = [s.id for s in my_services]
    reviews_received = Review.query.filter(Review.service_id.in_(my_service_ids)).order_by(Review.created_at.desc()).all() if my_service_ids else []

    # Dynamic Achievement Badges
    badges = []
    badges.append({
        'name': 'Broke Genius',
        'desc': 'Default member of the campus side-hustle guild.',
        'icon': 'bi-lightbulb-fill',
        'color': 'text-warning'
    })
    if len(orders_bought) > 0:
        badges.append({
            'name': 'Campus Scholar',
            'desc': 'Booked at least one tutoring session or study service.',
            'icon': 'bi-mortarboard-fill',
            'color': 'text-primary'
        })
    if len(my_services) > 0:
        badges.append({
            'name': 'Side Hustler',
            'desc': 'Created a service listing to make a campus income.',
            'icon': 'bi-briefcase-fill',
            'color': 'text-success'
        })
    completed_gigs = [o for o in orders_sold if o.status == 'Completed']
    if len(completed_gigs) > 0:
        badges.append({
            'name': 'Master Tutor',
            'desc': 'Delivered and completed a tutoring gig or service.',
            'icon': 'bi-patch-check-fill',
            'color': 'text-info'
        })
    unlocked_packages = any(not order.session.is_locked for order in orders_bought if order.session)
    if unlocked_packages:
        badges.append({
            'name': 'Study Guru',
            'desc': 'Unlocked an AI Revision package to boost grades.',
            'icon': 'bi-trophy-fill',
            'color': 'text-warning'
        })

    return render_template(
        'users/profile.html',
        my_services=my_services,
        orders_bought=orders_bought,
        orders_sold=orders_sold,
        reviews_received=reviews_received,
        badges=badges
    )

@profile_bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        university = request.form.get('university', '').strip()
        profile_pic_file = request.files.get('profile_pic')
        
        if not name or not email or not university:
            flash("Name, email, and university are required fields.", "danger")
            return render_template('users/edit_profile.html')
            
        # Check unique email (excluding self)
        existing_email = User.query.filter(User.email == email, User.id != current_user.id).first()
        if existing_email:
            flash("Email is already in use by another account.", "danger")
            return render_template('users/edit_profile.html')
            
        selected_avatar = request.form.get('selected_avatar', '').strip()
        
        # Handle file upload
        if profile_pic_file and profile_pic_file.filename != '':
            saved_filename = save_uploaded_file(profile_pic_file, current_app.config['PROFILE_PICS_DIR'])
            if saved_filename:
                # Delete old pic if it wasn't default
                if current_user.profile_pic and current_user.profile_pic != 'default_profile.png':
                    old_path = os.path.join(current_app.config['PROFILE_PICS_DIR'], current_user.profile_pic)
                    if os.path.exists(old_path):
                        try:
                            os.remove(old_path)
                        except Exception as e:
                            print(f"Error removing old profile picture: {e}")
                
                current_user.profile_pic = saved_filename
            else:
                flash("Invalid file type. Allowed formats: PNG, JPG, JPEG, WEBP.", "danger")
                return render_template('users/edit_profile.html')
        elif selected_avatar:
            # User chose a predefined avatar
            import shutil
            import uuid
            src_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'avatars', selected_avatar)
            if os.path.exists(src_path):
                # Generate unique filename for profile_pics
                ext = selected_avatar.rsplit('.', 1)[1].lower() if '.' in selected_avatar else 'png'
                unique_filename = f"avatar_{uuid.uuid4().hex}.{ext}"
                dest_path = os.path.join(current_app.config['PROFILE_PICS_DIR'], unique_filename)
                
                try:
                    shutil.copy(src_path, dest_path)
                    
                    # Delete old pic if it wasn't default
                    if current_user.profile_pic and current_user.profile_pic != 'default_profile.png':
                        old_path = os.path.join(current_app.config['PROFILE_PICS_DIR'], current_user.profile_pic)
                        if os.path.exists(old_path):
                            os.remove(old_path)
                            
                    current_user.profile_pic = unique_filename
                except Exception as e:
                    print(f"Error copying predefined avatar: {e}")
                
        # Update user fields
        current_user.name = name
        current_user.email = email
        current_user.university = university
        db.session.commit()
        
        flash("Profile updated successfully!", "success")
        return redirect(url_for('profile.view_profile'))
        
    return render_template('users/edit_profile.html')

# Order Action Routes
@profile_bp.route('/orders/<int:order_id>/accept', methods=['POST'])
@login_required
def accept_order(order_id):
    order = Order.query.get_or_404(order_id)
    # Check authorization (only the seller can accept)
    if order.seller_id != current_user.id:
        flash("Unauthorized action.", "danger")
        return redirect(url_for('profile.view_profile'))
        
    if order.status == 'Pending':
        order.status = 'Accepted'
        db.session.commit()
        flash("Order accepted! Get in touch with the buyer.", "success")
    else:
        flash("Order cannot be accepted in its current state.", "warning")
        
    return redirect(url_for('profile.view_profile'))

@profile_bp.route('/orders/<int:order_id>/reject', methods=['POST'])
@login_required
def reject_order(order_id):
    order = Order.query.get_or_404(order_id)
    # Check authorization (only the seller can reject, or buyer can cancel if pending)
    if order.seller_id != current_user.id and order.buyer_id != current_user.id:
        flash("Unauthorized action.", "danger")
        return redirect(url_for('profile.view_profile'))
        
    if order.status == 'Pending':
        order.status = 'Cancelled'
        db.session.commit()
        flash("Order has been cancelled.", "info")
    else:
        flash("Order cannot be cancelled in its current state.", "warning")
        
    return redirect(url_for('profile.view_profile'))

@profile_bp.route('/orders/<int:order_id>/complete', methods=['POST'])
@login_required
def complete_order(order_id):
    order = Order.query.get_or_404(order_id)
    # Check authorization (only the seller can mark completed, or buyer can confirm)
    if order.seller_id != current_user.id and order.buyer_id != current_user.id:
        flash("Unauthorized action.", "danger")
        return redirect(url_for('profile.view_profile'))
        
    if order.status in ['Accepted', 'Pending']:
        order.status = 'Completed'
        db.session.commit()
        flash("Order marked as Completed. Feel free to leave a review!", "success")
    else:
        flash("Order cannot be marked completed.", "warning")
        
    return redirect(url_for('profile.view_profile'))
