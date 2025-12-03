"""
Authentication routes
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from app.services.db_service import get_db_service

bp = Blueprint("auth", __name__)


@bp.route("/register", methods=["GET", "POST"])
def register():
    """User registration"""
    if current_user.is_authenticated:
        return redirect(url_for("web.index"))
    
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        
        # Validation
        if not username or not email or not password:
            flash("All fields are required.", "error")
            return render_template("auth/register.html")
        
        if password != confirm_password:
            flash("Passwords do not match.", "error")
            return render_template("auth/register.html")
        
        if len(password) < 6:
            flash("Password must be at least 6 characters long.", "error")
            return render_template("auth/register.html")
        
        # Create user
        db_service = get_db_service()
        user = db_service.create_user(username, email, password)
        
        if user:
            # Automatically log in the user after successful registration
            login_user(user)
            flash("Welcome! Your account has been created successfully.", "success")
            return redirect(url_for("web.index"))
        else:
            flash("Username or email already exists.", "error")
            return render_template("auth/register.html")
    
    return render_template("auth/register.html")


@bp.route("/login", methods=["GET", "POST"])
def login():
    """User login"""
    if current_user.is_authenticated:
        return redirect(url_for("web.index"))
    
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        remember = request.form.get("remember", False) == "on"
        
        if not username or not password:
            flash("Please provide username and password.", "error")
            return render_template("auth/login.html")
        
        # Authenticate user
        db_service = get_db_service()
        user = db_service.get_user_by_username(username)
        
        if user and user.check_password(password):
            login_user(user, remember=remember)
            flash("You've successfully logged in!", "success")
            next_page = request.args.get("next")
            return redirect(next_page) if next_page else redirect(url_for("web.index"))
        else:
            flash("Invalid username or password.", "error")
            return render_template("auth/login.html")
    
    return render_template("auth/login.html")


@bp.route("/logout")
@login_required
def logout():
    """User logout"""
    logout_user()
    flash("You have been logged out.", "success")
    return redirect(url_for("web.index"))



@bp.route("/google")
def google_login():
    """Initiate Google OAuth flow"""
    from app.services.oauth import get_google_oauth
    from flask import url_for
    
    google = get_google_oauth()
    redirect_uri = url_for('auth.google_callback', _external=True)
    return google.authorize_redirect(redirect_uri)


@bp.route("/google/callback")
def google_callback():
    """Handle Google OAuth callback"""
    from app.services.oauth import get_google_oauth
    
    google = get_google_oauth()
    
    try:
        # Get OAuth token
        token = google.authorize_access_token()
        
        # Get user info from Google
        user_info = token.get('userinfo')
        if not user_info:
            # Fallback: parse ID token
            user_info = google.parse_id_token(token)
        
        google_id = user_info.get('sub')
        email = user_info.get('email')
        name = user_info.get('name', '')
        picture = user_info.get('picture', '')
        
        if not google_id or not email:
            flash("Failed to get user information from Google.", "error")
            return redirect(url_for('auth.login'))
        
        db_service = get_db_service()
        
        # Check if user already exists with this Google ID
        user = db_service.get_user_by_google_id(google_id)
        
        if user:
            # User exists, log them in
            login_user(user, remember=True)
            flash(f"Welcome back, {user.username}!", "success")
            return redirect(url_for('web.index'))
        
        # Check if user exists with this email
        existing_user = db_service.get_user_by_email_oauth(email)
        
        if existing_user:
            # Auto-link Google account to existing user
            user = db_service.link_google_account(existing_user.id, google_id, picture)
            if user:
                login_user(user, remember=True)
                flash(f"Welcome back, {user.username}! Your Google account has been linked.", "success")
                return redirect(url_for('web.index'))
            else:
                flash("Failed to link Google account. Please try again.", "error")
                return redirect(url_for('auth.login'))
        
        # Create new user with Google credentials
        user = db_service.create_google_user(google_id, email, name, picture)
        
        if user:
            login_user(user, remember=True)
            flash(f"Welcome to Knowledge Graph AI, {user.username}!", "success")
            return redirect(url_for('web.index'))
        else:
            flash("Failed to create account. Please try again.", "error")
            return redirect(url_for('auth.register'))
    
    except Exception as e:
        print(f"Error during Google OAuth: {e}")
        import traceback
        traceback.print_exc()
        flash("An error occurred during Google sign-in. Please try again.", "error")
        return redirect(url_for('auth.login'))

