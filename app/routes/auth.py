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
            flash("Registration successful! Please log in.", "success")
            return redirect(url_for("auth.login"))
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

