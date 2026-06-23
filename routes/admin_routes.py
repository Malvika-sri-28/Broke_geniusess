import os
import json
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from database import db, User, Service, Review, Order, SecurityAlert
from utils.decorators import admin_required
from utils.analytics import (
    get_admin_metrics,
    get_registrations_per_month,
    get_services_per_month,
    get_reviews_per_month,
    get_order_status_distribution,
    get_most_popular_services,
    get_top_rated_sellers
)
from routes.review_routes import update_service_stats

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    metrics = get_admin_metrics()
    
    # Fetch chart data
    reg_data = get_registrations_per_month()
    serv_data = get_services_per_month()
    rev_data = get_reviews_per_month()
    status_data = get_order_status_distribution()
    pop_services = get_most_popular_services()
    top_sellers = get_top_rated_sellers()
    
    # Fetch recent security alerts blocked by WAF
    recent_alerts = SecurityAlert.query.order_by(SecurityAlert.created_at.desc()).limit(10).all()
    
    # Prepare JSON serializable structures for Chart.js
    charts_json = {
        'registrations': {
            'labels': list(reg_data.keys()),
            'data': list(reg_data.values())
        },
        'services': {
            'labels': list(serv_data.keys()),
            'data': list(serv_data.values())
        },
        'reviews': {
            'labels': list(rev_data.keys()),
            'data': list(rev_data.values())
        },
        'order_status': {
            'labels': list(status_data.keys()),
            'data': list(status_data.values())
        },
        'popular_services': {
            'labels': list(pop_services.keys()),
            'data': list(pop_services.values())
        },
        'top_sellers': {
            'labels': list(top_sellers.keys()),
            'data': list(top_sellers.values())
        }
    }
    
    return render_template(
        'admin/dashboard.html',
        metrics=metrics,
        charts_data=json.dumps(charts_json),
        recent_alerts=recent_alerts
    )

@admin_bp.route('/users')
@login_required
@admin_required
def users_list():
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin/users.html', users=users)

@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    
    if user.id == current_user.id:
        flash("You cannot delete your own administrative account.", "danger")
        return redirect(url_for('admin.users_list'))
        
    # Delete profile picture if not default
    if user.profile_pic and user.profile_pic != 'default_profile.png':
        img_path = os.path.join(current_app.config['PROFILE_PICS_DIR'], user.profile_pic)
        if os.path.exists(img_path):
            try:
                os.remove(img_path)
            except Exception as e:
                print(f"Error deleting profile pic: {e}")
                
    db.session.delete(user)
    db.session.commit()
    flash(f"User '{user.username}' and all associated records have been deleted.", "success")
    return redirect(url_for('admin.users_list'))

@admin_bp.route('/services')
@login_required
@admin_required
def services_list():
    services = Service.query.order_by(Service.created_at.desc()).all()
    return render_template('admin/services.html', services=services)

@admin_bp.route('/reviews')
@login_required
@admin_required
def reviews_list():
    reviews = Review.query.order_by(Review.created_at.desc()).all()
    return render_template('admin/reviews.html', reviews=reviews)

@admin_bp.route('/reviews/<int:review_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_review(review_id):
    review = Review.query.get_or_404(review_id)
    service_id = review.service_id
    
    # Delete review image if exists
    if review.image:
        img_path = os.path.join(current_app.config['REVIEW_IMAGES_DIR'], review.image)
        if os.path.exists(img_path):
            try:
                os.remove(img_path)
            except Exception as e:
                print(f"Error deleting review image: {e}")
                
    db.session.delete(review)
    db.session.commit()
    
    # Re-calculate service ratings
    update_service_stats(service_id)
    
    flash("Review has been deleted and service rating updated.", "success")
    return redirect(url_for('admin.reviews_list'))
