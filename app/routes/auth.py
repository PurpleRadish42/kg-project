"""
Authentication routes
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from flask_login import login_user, logout_user, login_required, current_user
from app.services.db_service import get_db_service
from app.services.email_service import generate_otp, hash_otp, verify_otp_hash, get_otp_expiry, send_otp_email
from datetime import datetime

bp = Blueprint("auth", __name__)


def send_verification_otp(user, db_service):
    """Generate and send OTP to user's email"""
    otp = generate_otp()
    otp_hash = hash_otp(otp)
    expires_at = get_otp_expiry()
    
    # Save OTP to database
    db_service.save_otp(user.id, otp_hash, expires_at)
    
    # Send OTP email
    user_name = user.full_name.split()[0] if user.full_name else user.username
    success = send_otp_email(user.email, otp, user_name)
    
    return success


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
        
        # Create user with email_verified=False
        db_service = get_db_service()
        user = db_service.create_user(username, email, password, email_verified=False)
        
        if user:
            # Send OTP for email verification
            if send_verification_otp(user, db_service):
                # Store user_id in session for OTP verification
                session['pending_verification_user_id'] = user.id
                session['pending_verification_email'] = user.email
                flash("We've sent a verification code to your email.", "success")
                return redirect(url_for("auth.verify_otp"))
            else:
                flash("Failed to send verification email. Please try again.", "error")
                return render_template("auth/register.html")
        else:
            flash("Username or email already exists.", "error")
            return render_template("auth/register.html")
    
    return render_template("auth/register.html")


@bp.route("/verify-otp", methods=["GET", "POST"])
def verify_otp():
    """Verify OTP for email verification"""
    # Check if there's a pending verification
    user_id = session.get('pending_verification_user_id')
    email = session.get('pending_verification_email')
    
    if not user_id:
        flash("No pending verification. Please register first.", "error")
        return redirect(url_for("auth.register"))
    
    db_service = get_db_service()
    user = db_service.get_user_by_id(user_id)
    
    if not user:
        session.pop('pending_verification_user_id', None)
        session.pop('pending_verification_email', None)
        flash("User not found. Please register again.", "error")
        return redirect(url_for("auth.register"))
    
    # If already verified, redirect to login
    if user.email_verified:
        session.pop('pending_verification_user_id', None)
        session.pop('pending_verification_email', None)
        flash("Email already verified. Please login.", "success")
        return redirect(url_for("auth.login"))
    
    # Get OTP config
    max_attempts = current_app.config.get("OTP_MAX_ATTEMPTS", 3)
    
    if request.method == "POST":
        otp_input = request.form.get("otp", "").strip()
        
        if not otp_input or len(otp_input) != 6:
            flash("Please enter a valid 6-digit code.", "error")
            return render_template("auth/verify_otp.html", email=email)
        
        # Get stored OTP data
        otp_data = db_service.get_otp_data(user_id)
        
        if not otp_data or not otp_data['otp_hash']:
            flash("No verification code found. Please request a new one.", "error")
            return render_template("auth/verify_otp.html", email=email, can_resend=True)
        
        # Check if OTP expired
        if otp_data['expires_at'] and datetime.utcnow() > otp_data['expires_at']:
            db_service.clear_otp(user_id)
            flash("Verification code expired. Please request a new one.", "error")
            return render_template("auth/verify_otp.html", email=email, can_resend=True, expired=True)
        
        # Check attempts
        if otp_data['attempts'] >= max_attempts:
            db_service.clear_otp(user_id)
            flash("Too many failed attempts. Please request a new code.", "error")
            return render_template("auth/verify_otp.html", email=email, can_resend=True, max_attempts_reached=True)
        
        # Verify OTP
        if verify_otp_hash(otp_input, otp_data['otp_hash']):
            # Success! Mark email as verified
            verified_user = db_service.mark_email_verified(user_id)
            
            if verified_user:
                # Clear session
                session.pop('pending_verification_user_id', None)
                session.pop('pending_verification_email', None)
                
                # Log in the user
                login_user(verified_user)
                flash("Email verified successfully! Welcome to Knowledge Graph AI.", "success")
                return redirect(url_for("web.index"))
            else:
                flash("Verification failed. Please try again.", "error")
        else:
            # Wrong OTP - increment attempts
            attempts = db_service.increment_otp_attempts(user_id)
            remaining = max_attempts - attempts
            
            if remaining > 0:
                flash(f"Incorrect code. {remaining} attempt{'s' if remaining > 1 else ''} remaining.", "error")
            else:
                db_service.clear_otp(user_id)
                flash("Too many failed attempts. Please request a new code.", "error")
                return render_template("auth/verify_otp.html", email=email, can_resend=True, max_attempts_reached=True)
    
    # Get remaining time for display
    otp_data = db_service.get_otp_data(user_id)
    remaining_seconds = 0
    if otp_data and otp_data['expires_at']:
        remaining = (otp_data['expires_at'] - datetime.utcnow()).total_seconds()
        remaining_seconds = max(0, int(remaining))
    
    return render_template("auth/verify_otp.html", 
                         email=email, 
                         remaining_seconds=remaining_seconds,
                         max_attempts=max_attempts)


@bp.route("/resend-otp", methods=["POST"])
def resend_otp():
    """Resend OTP for email verification"""
    user_id = session.get('pending_verification_user_id')
    
    if not user_id:
        flash("No pending verification.", "error")
        return redirect(url_for("auth.register"))
    
    db_service = get_db_service()
    user = db_service.get_user_by_id(user_id)
    
    if not user:
        flash("User not found.", "error")
        return redirect(url_for("auth.register"))
    
    # Check cooldown
    cooldown = current_app.config.get("OTP_RESEND_COOLDOWN_SECONDS", 30)
    can_resend, remaining = db_service.can_resend_otp(user_id, cooldown)
    
    if not can_resend:
        flash(f"Please wait {remaining} seconds before requesting a new code.", "error")
        return redirect(url_for("auth.verify_otp"))
    
    # Send new OTP
    if send_verification_otp(user, db_service):
        flash("A new verification code has been sent to your email.", "success")
    else:
        flash("Failed to send verification email. Please try again.", "error")
    
    return redirect(url_for("auth.verify_otp"))


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
            # Check if email is verified (only for local auth, not Google)
            if not user.email_verified and user.password_hash:
                # Email not verified - redirect to OTP verification
                session['pending_verification_user_id'] = user.id
                session['pending_verification_email'] = user.email
                
                # Send new OTP
                if send_verification_otp(user, db_service):
                    flash("Please verify your email first. We've sent a new code.", "info")
                else:
                    flash("Please verify your email. Check your inbox for the verification code.", "info")
                
                return redirect(url_for("auth.verify_otp"))
            
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

