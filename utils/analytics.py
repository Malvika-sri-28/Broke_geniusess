from sqlalchemy import func, desc
from database import db, User, Service, Review, Order

def get_registrations_per_month():
    """Returns user registrations grouped by year-month."""
    results = db.session.query(
        func.strftime('%Y-%m', User.created_at).label('month'),
        func.count(User.id).label('count')
    ).group_by('month').order_by('month').all()
    
    return {r.month: r.count for r in results if r.month}

def get_services_per_month():
    """Returns services created grouped by year-month."""
    results = db.session.query(
        func.strftime('%Y-%m', Service.created_at).label('month'),
        func.count(Service.id).label('count')
    ).group_by('month').order_by('month').all()
    
    return {r.month: r.count for r in results if r.month}

def get_reviews_per_month():
    """Returns reviews posted grouped by year-month."""
    results = db.session.query(
        func.strftime('%Y-%m', Review.created_at).label('month'),
        func.count(Review.id).label('count')
    ).group_by('month').order_by('month').all()
    
    return {r.month: r.count for r in results if r.month}

def get_order_status_distribution():
    """Returns the count of orders grouped by status."""
    results = db.session.query(
        Order.status,
        func.count(Order.id).label('count')
    ).group_by(Order.status).all()
    
    return {r.status: r.count for r in results}

def get_most_popular_services(limit=5):
    """Returns the most popular services by number of orders completed/booked."""
    results = db.session.query(
        Service.title,
        func.count(Order.id).label('order_count')
    ).join(Order, Order.service_id == Service.id)\
     .group_by(Service.id)\
     .order_by(desc('order_count'))\
     .limit(limit).all()
     
    return {r.title: r.order_count for r in results}

def get_top_rated_sellers(limit=5):
    """Returns top rated sellers based on their average service rating."""
    # A seller is a User. We average the rating of all services owned by this seller
    results = db.session.query(
        User.username,
        func.avg(Service.total_rating).label('avg_rating')
    ).join(Service, Service.seller_id == User.id)\
     .filter(Service.review_count > 0)\
     .group_by(User.id)\
     .order_by(desc('avg_rating'))\
     .limit(limit).all()
     
    return {r.username: round(r.avg_rating, 2) for r in results}

def get_admin_metrics():
    """Returns count metrics for the dashboard summary cards."""
    return {
        'total_users': User.query.count(),
        'total_services': Service.query.count(),
        'total_reviews': Review.query.count(),
        'total_orders': Order.query.count()
    }
