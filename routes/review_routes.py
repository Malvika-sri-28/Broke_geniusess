import os
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from database import db, User, Service, Review, Order
from utils.helpers import save_uploaded_file

review_bp = Blueprint('review', __name__)

def update_service_stats(service_id):
    """Recalculates average rating and review count for a service, and updates top-rated status for the seller."""
    service = Service.query.get(service_id)
    if not service:
        return
        
    reviews = Review.query.filter_by(service_id=service_id).all()
    count = len(reviews)
    
    if count > 0:
        total = sum(r.rating for r in reviews)
        service.total_rating = round(total / count, 2)
        service.review_count = count
    else:
        service.total_rating = 0.0
        service.review_count = 0
        
    db.session.commit()
    
    # Recalculate top-rated status for the seller
    # Rule: A seller is top-rated if they have at least 3 total reviews and an average rating of >= 4.5 across all services.
    seller = User.query.get(service.seller_id)
    if seller:
        seller_services = Service.query.filter_by(seller_id=seller.id).all()
        seller_service_ids = [s.id for s in seller_services]
        
        all_seller_reviews = Review.query.filter(Review.service_id.in_(seller_service_ids)).all()
        total_reviews_count = len(all_seller_reviews)
        
        if total_reviews_count >= 3:
            avg_seller_rating = sum(r.rating for r in all_seller_reviews) / total_reviews_count
            if avg_seller_rating >= 4.5:
                seller.is_top_rated = True
            else:
                seller.is_top_rated = False
        else:
            seller.is_top_rated = False
            
        db.session.commit()

@review_bp.route('/orders/<int:order_id>/review', methods=['GET', 'POST'])
@login_required
def add_review(order_id):
    order = Order.query.get_or_404(order_id)
    
    # Validation: Only the buyer can write the review
    if order.buyer_id != current_user.id:
        flash("Unauthorized action.", "danger")
        return redirect(url_for('profile.view_profile'))
        
    # Validation: Order must be Completed to allow reviewing
    if order.status != 'Completed':
        flash("You can only review services for completed orders.", "warning")
        return redirect(url_for('profile.view_profile'))
        
    # Validation: Single review per user per service
    existing_review = Review.query.filter_by(
        reviewer_id=current_user.id,
        service_id=order.service_id
    ).first()
    
    if existing_review:
        flash("You have already reviewed this service.", "warning")
        return redirect(url_for('profile.view_profile'))
        
    if request.method == 'POST':
        rating = request.form.get('rating', '').strip()
        text = request.form.get('text', '').strip()
        review_image = request.files.get('review_image')
        
        if not rating or not text:
            flash("Rating and review text are required.", "danger")
            return render_template('reviews/add_review.html', order=order)
            
        try:
            rating_val = int(rating)
            if rating_val < 1 or rating_val > 5:
                flash("Rating must be between 1 and 5 stars.", "danger")
                return render_template('reviews/add_review.html', order=order)
        except ValueError:
            flash("Invalid rating selected.", "danger")
            return render_template('reviews/add_review.html', order=order)
            
        # Handle optional review image or meme
        image_filename = None
        if review_image and review_image.filename != '':
            saved_filename = save_uploaded_file(review_image, current_app.config['REVIEW_IMAGES_DIR'])
            if saved_filename:
                image_filename = saved_filename
            else:
                flash("Invalid image format. Allowed formats: PNG, JPG, JPEG, WEBP.", "danger")
                return render_template('reviews/add_review.html', order=order)
                
        # Calculate basic sentiment
        if rating_val >= 4:
            sentiment = "Positive"
        elif rating_val == 3:
            sentiment = "Neutral"
        else:
            sentiment = "Negative"
            
        # Create review
        review = Review(
            rating=rating_val,
            text=text,
            image=image_filename,
            reviewer_id=current_user.id,
            service_id=order.service_id,
            sentiment=sentiment
        )
        
        db.session.add(review)
        db.session.commit()
        
        # Update service statistics
        update_service_stats(order.service_id)
        
        flash("Thank you for your feedback!", "success")
        return redirect(url_for('profile.view_profile'))
        
    return render_template('reviews/add_review.html', order=order)
