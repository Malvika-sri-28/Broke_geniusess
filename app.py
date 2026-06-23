import os
from flask import Flask, render_template
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from config import Config
from database import db, User, Service, Review, Order

csrf = CSRFProtect()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Ensure instances directory exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['PROFILE_PICS_DIR'], exist_ok=True)
    os.makedirs(app.config['SERVICE_IMAGES_DIR'], exist_ok=True)
    os.makedirs(app.config['REVIEW_IMAGES_DIR'], exist_ok=True)
    os.makedirs(app.config['SESSION_FILES_DIR'], exist_ok=True)
    os.makedirs(os.path.join(app.config['BASE_DIR'], 'instance'), exist_ok=True)

    # Initialize extensions
    db.init_app(app)
    csrf.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'

    # Initialize Web Application Firewall (WAF)
    from utils.firewall import init_waf
    init_waf(app)

    # User loader
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register custom template filters
    @app.template_filter('star_rating')
    def star_rating_filter(rating):
        """Generates HTML stars based on a rating value."""
        if rating is None:
            return "No ratings"
        full_stars = int(rating)
        half_star = 1 if (rating - full_stars) >= 0.5 else 0
        empty_stars = 5 - full_stars - half_star
        
        stars_html = ""
        for _ in range(full_stars):
            stars_html += '<i class="bi bi-star-fill text-warning"></i>'
        for _ in range(half_star):
            stars_html += '<i class="bi bi-star-half text-warning"></i>'
        for _ in range(empty_stars):
            stars_html += '<i class="bi bi-star text-warning"></i>'
        return stars_html

    # Register Blueprints
    from routes.auth_routes import auth_bp
    from routes.profile_routes import profile_bp
    from routes.service_routes import service_bp
    from routes.review_routes import review_bp
    from routes.admin_routes import admin_bp
    from routes.chat_routes import chat_bp
    from routes.ai_routes import ai_bp
    from routes.session_routes import session_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(profile_bp)
    app.register_blueprint(service_bp)
    app.register_blueprint(review_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(chat_bp)
    app.register_blueprint(ai_bp)
    app.register_blueprint(session_bp)

    # Home/Index route
    @app.route('/')
    def index():
        # Get a few featured services to show on homepage
        featured_services = Service.query.order_by(Service.total_rating.desc()).limit(6).all()
        return render_template('index.html', featured_services=featured_services)

    # Initialize database & seed mock data
    with app.app_context():
        db.create_all()
        seed_database()

    return app

def seed_database():
    """Seeds the database with mock records if there are no users present."""
    if User.query.first() is not None:
        return # Database already seeded
    
    print("Database is empty. Seeding mock data for 'Broke Geniuses'...")
    
    # 1. Create Admin
    admin = User(
        name="System Admin",
        username="admin",
        email="admin@broke-geniuses.in",
        university="IIT Bombay",
        is_admin=True
    )
    admin.set_password("AdminPassword123!")
    db.session.add(admin)

    # 2. Create Sellers
    seller1 = User(
        name="Rajesh Kumar",
        username="coder_raj",
        email="rajesh.kumar@iitb.ac.in",
        university="IIT Bombay",
        is_top_rated=True,
        is_demo=True
    )
    seller1.set_password("Password123!")
    
    seller2 = User(
        name="Priya Sharma",
        username="graphic_girl",
        email="priya.sharma@bits-pilani.ac.in",
        university="BITS Pilani",
        is_demo=True
    )
    seller2.set_password("Password123!")
    
    # 3. Create Buyer
    buyer1 = User(
        name="Samarth Mehta",
        username="student_sam",
        email="sam.mehta@du.ac.in",
        university="Delhi University"
    )
    buyer1.set_password("Password123!")
    
    db.session.add_all([seller1, seller2, buyer1])
    db.session.commit() # Commit to get IDs

    # 4. Create Services
    s1 = Service(
        title="Python & Django Tutoring",
        description="Struggling with Python or your web development assignments? I am a final-year CSE student at IIT Bombay with 3 years of programming experience. I will help you understand OOP concepts, data structures, and Django framework backend development. Classes conducted over Zoom/Meet with live coding.",
        price=499.0,
        image="default_service.png",
        seller_id=seller1.id,
        university="IIT Bombay",
        keywords="python, django, tutoring, programming, homework, assignment",
        total_rating=4.8,
        review_count=2
    )

    s2 = Service(
        title="Resume & LinkedIn Review",
        description="Get your resume reviewed by someone who bagged offers at top tech firms! I will review your resume structure, descriptions, and projects, and optimize your LinkedIn profile to get noticed by recruiters. Includes one 30-min call.",
        price=299.0,
        image="default_service.png",
        seller_id=seller1.id,
        university="IIT Bombay",
        keywords="resume, review, career, job, interview",
        total_rating=5.0,
        review_count=1
    )

    s3 = Service(
        title="Minimalist Logo & Banner Design",
        description="Need a sleek, modern identity for your student startup, club, or YouTube channel? I offer customized logo and vector banner illustrations. Delivered within 48 hours. Source file (.ai/.psd) included!",
        price=799.0,
        image="default_service.png",
        seller_id=seller2.id,
        university="BITS Pilani",
        keywords="logo, graphics, banner, design, startup, branding",
        total_rating=4.5,
        review_count=2
    )

    s4 = Service(
        title="Data Structures & Algorithms Notes",
        description="Comprehensive hand-written and digital notes covering arrays, trees, graphs, dynamic programming, and recursion. Clean diagrams and code snippets in C++ and Java. Perfect for exam prep and coding interviews.",
        price=150.0,
        image="default_service.png",
        seller_id=seller1.id,
        university="IIT Bombay",
        keywords="notes, dsa, algorithms, exams, coding",
        total_rating=0.0,
        review_count=0
    )

    db.session.add_all([s1, s2, s3, s4])
    db.session.commit()

    # 5. Create Reviews
    # Review 1 for Python tutoring
    r1 = Review(
        rating=5,
        text="Rajesh was amazing! He explained recursive functions so easily. My grades improved after just two sessions.",
        reviewer_id=buyer1.id,
        service_id=s1.id,
        sentiment="Positive"
    )
    # Review 2 for Python tutoring
    r2 = Review(
        rating=4,
        text="Very detailed classes, although we had to reschedule once. Highly recommended for beginners.",
        reviewer_id=seller2.id,
        service_id=s1.id,
        sentiment="Positive"
    )
    # Review 3 for Resume Review
    r3 = Review(
        rating=5,
        text="Outstanding tips. Re-wrote my bullet points and got two callbacks within a week!",
        reviewer_id=buyer1.id,
        service_id=s2.id,
        sentiment="Positive"
    )
    # Review 4 for Logo Design
    r4 = Review(
        rating=4,
        text="Great designer, loved the logo concept. Minor delays in communication but quality is premium.",
        reviewer_id=buyer1.id,
        service_id=s3.id,
        sentiment="Positive"
    )
    # Review 5 for Logo Design
    r5 = Review(
        rating=5,
        text="She designed a fabulous banner for my college coding club. Quick revisions!",
        reviewer_id=seller1.id,
        service_id=s3.id,
        sentiment="Positive"
    )

    db.session.add_all([r1, r2, r3, r4, r5])
    db.session.commit()

    # 6. Create Orders
    # Order 1: Sam purchased Python Tutoring (Completed)
    o1 = Order(
        buyer_id=buyer1.id,
        seller_id=seller1.id,
        service_id=s1.id,
        status="Completed"
    )
    # Order 2: Sam purchased Resume Review (Accepted)
    o2 = Order(
        buyer_id=buyer1.id,
        seller_id=seller1.id,
        service_id=s2.id,
        status="Accepted"
    )
    # Order 3: Sam purchased Logo Design (Completed)
    o3 = Order(
        buyer_id=buyer1.id,
        seller_id=seller2.id,
        service_id=s3.id,
        status="Completed"
    )
    # Order 4: Priya purchased Python Tutoring (Completed)
    o4 = Order(
        buyer_id=seller2.id,
        seller_id=seller1.id,
        service_id=s1.id,
        status="Completed"
    )
    # Order 5: Rajesh purchased Logo Design (Completed)
    o5 = Order(
        buyer_id=seller1.id,
        seller_id=seller2.id,
        service_id=s3.id,
        status="Completed"
    )
    # Order 6: Sam purchased DSA notes (Pending)
    o6 = Order(
        buyer_id=buyer1.id,
        seller_id=seller1.id,
        service_id=s4.id,
        status="Pending"
    )

    db.session.add_all([o1, o2, o3, o4, o5, o6])
    db.session.commit()
    print("Database seeding completed.")

app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
