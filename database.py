from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import UniqueConstraint, CheckConstraint

db = SQLAlchemy()

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    profile_pic = db.Column(db.String(255), nullable=True, default='default_profile.png')
    university = db.Column(db.String(150), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    is_top_rated = db.Column(db.Boolean, default=False)
    is_demo = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    services = db.relationship('Service', backref='seller', lazy=True, cascade='all, delete-orphan')
    reviews_given = db.relationship('Review', backref='reviewer', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
        
    def __repr__(self):
        return f"<User {self.username}>"


class Service(db.Model):
    __tablename__ = 'services'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    image = db.Column(db.String(255), nullable=True, default='default_service.png')
    seller_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    university = db.Column(db.String(150), nullable=False)
    keywords = db.Column(db.String(255), nullable=True) # comma-separated keywords
    total_rating = db.Column(db.Float, default=0.0)
    review_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    reviews = db.relationship('Review', backref='service', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f"<Service {self.title}>"


class Review(db.Model):
    __tablename__ = 'reviews'
    
    id = db.Column(db.Integer, primary_key=True)
    rating = db.Column(db.Integer, nullable=False)
    text = db.Column(db.Text, nullable=False)
    image = db.Column(db.String(255), nullable=True) # review meme or product image
    reviewer_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey('services.id', ondelete='CASCADE'), nullable=False)
    sentiment = db.Column(db.String(20), nullable=True) # Positive, Neutral, Negative
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('reviewer_id', 'service_id', name='unique_user_review_per_service'),
        CheckConstraint('rating >= 1 AND rating <= 5', name='rating_range'),
    )
    
    def __repr__(self):
        return f"<Review {self.rating} stars for Service {self.service_id}>"


class Order(db.Model):
    __tablename__ = 'orders'
    
    id = db.Column(db.Integer, primary_key=True)
    buyer_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    seller_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey('services.id', ondelete='CASCADE'), nullable=False)
    status = db.Column(db.String(50), nullable=False, default='Pending') # Pending, Accepted, Completed, Cancelled
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships to access buyer, seller and service directly
    buyer = db.relationship('User', foreign_keys=[buyer_id], backref=db.backref('orders_bought', cascade='all, delete-orphan'))
    seller_user = db.relationship('User', foreign_keys=[seller_id], backref=db.backref('orders_sold', cascade='all, delete-orphan'))
    service = db.relationship('Service', backref=db.backref('orders', cascade='all, delete-orphan'))
    messages = db.relationship('Message', backref='order', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f"<Order {self.id} Status: {self.status}>"


class Message(db.Model):
    __tablename__ = 'messages'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id', ondelete='CASCADE'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    sender = db.relationship('User', backref='messages_sent')
    
    def __repr__(self):
        return f"<Message {self.id} on Order {self.order_id}>"


class SessionRoom(db.Model):
    __tablename__ = 'session_rooms'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id', ondelete='CASCADE'), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    consent_given = db.Column(db.Boolean, default=False)
    transcript = db.Column(db.Text, nullable=True, default='')
    summary = db.Column(db.Text, nullable=True, default='')
    quiz = db.Column(db.Text, nullable=True, default='') # stores JSON string of quiz questions
    notes = db.Column(db.Text, nullable=True, default='')
    is_locked = db.Column(db.Boolean, default=True)
    price = db.Column(db.Float, default=100.0)
    is_paid = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship to Order
    order = db.relationship('Order', backref=db.backref('session', uselist=False, cascade='all, delete-orphan'))
    
    def __repr__(self):
        return f"<SessionRoom {self.id} for Order {self.order_id} Active: {self.is_active}>"


class SecurityAlert(db.Model):
    __tablename__ = 'security_alerts'
    
    id = db.Column(db.Integer, primary_key=True)
    ip_address = db.Column(db.String(45), nullable=False)
    path = db.Column(db.String(255), nullable=False)
    method = db.Column(db.String(10), nullable=False)
    threat_type = db.Column(db.String(50), nullable=False) # e.g. SQL Injection, XSS, Path Traversal
    payload = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<SecurityAlert {self.threat_type} from {self.ip_address} on {self.path}>"
