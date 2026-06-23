import re
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from database import db, User

auth_bp = Blueprint('auth', __name__)

from utils.helpers import UNIVERSITIES as BASE_UNIVERSITIES
UNIVERSITIES = BASE_UNIVERSITIES + ["Other"]

def is_password_strong(password):
    """
    Checks if a password is strong:
    - At least 8 characters long
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special character
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter."
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter."
    if not re.search(r"\d", password):
        return False, "Password must contain at least one number."
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False, "Password must contain at least one special character (!@#$%^&* etc.)."
    return True, ""

@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        university_select = request.form.get('university_select', '').strip()
        university_other = request.form.get('university_other', '').strip()
        
        # Decide university name
        university = university_other if university_select == 'Other' else university_select
        
        # Validation checks
        if not name or not username or not email or not password or not university:
            flash("All fields are required.", "danger")
            return render_template('auth/signup.html', universities=UNIVERSITIES, form_data=request.form)
            
        # Email format validation
        email_regex = r"^[\w\.-]+@[\w\.-]+\.\w+$"
        if not re.match(email_regex, email):
            flash("Invalid email format.", "danger")
            return render_template('auth/signup.html', universities=UNIVERSITIES, form_data=request.form)
            
        # Check unique username
        existing_username = User.query.filter_by(username=username).first()
        if existing_username:
            flash("Username is already taken.", "danger")
            return render_template('auth/signup.html', universities=UNIVERSITIES, form_data=request.form)
            
        # Check unique email
        existing_email = User.query.filter_by(email=email).first()
        if existing_email:
            flash("Email is already registered.", "danger")
            return render_template('auth/signup.html', universities=UNIVERSITIES, form_data=request.form)
            
        # Check password strength
        is_strong, error_msg = is_password_strong(password)
        if not is_strong:
            flash(error_msg, "danger")
            return render_template('auth/signup.html', universities=UNIVERSITIES, form_data=request.form)
            
        # Create user
        new_user = User(
            name=name,
            username=username,
            email=email,
            university=university
        )
        new_user.set_password(password)
        
        # Automatically make the first registered user an admin (helps with testing!)
        if User.query.count() == 0:
            new_user.is_admin = True
            
        db.session.add(new_user)
        db.session.commit()
        
        flash("Registration successful! You can now log in.", "success")
        return redirect(url_for('auth.login'))
        
    return render_template('auth/signup.html', universities=UNIVERSITIES)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        login_id = request.form.get('login_id', '').strip() # Can be username or email
        password = request.form.get('password', '')
        remember = True if request.form.get('remember') else False
        
        if not login_id or not password:
            flash("Please enter both credentials.", "danger")
            return render_template('auth/login.html')
            
        # Fetch user by email or username
        user = User.query.filter((User.email == login_id) | (User.username == login_id)).first()
        
        if not user or not user.check_password(password):
            flash("Invalid username/email or password.", "danger")
            return render_template('auth/login.html')
            
        login_user(user, remember=remember)
        flash(f"Welcome back, {user.name}!", "success")
        
        # If admin, redirect to admin dashboard; else homepage
        if user.is_admin:
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('index'))
        
    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "success")
    return redirect(url_for('index'))
