"""
Web routes for the Knowledge Graph application
"""

from flask import Blueprint, render_template, redirect, url_for
from flask_login import current_user, login_required

bp = Blueprint("web", __name__)


@bp.route("/")
def index():
    """Welcome page - redirect to chat if logged in"""
    if current_user.is_authenticated:
        return redirect(url_for("web.chat"))
    return render_template("welcome.html")


@bp.route("/chat")
@login_required
def chat():
    """Chat interface for logged-in users"""
    return render_template("chat.html")


@bp.route("/demo")
def demo():
    """Demo page with pre-filled paragraph and questions"""
    # Test paragraph
    paragraph = """On Monday morning, I placed my car keys on the kitchen counter next to the coffee maker. Later that afternoon, my roommate moved them to the key hook by the front door because he needed to use the car. The coffee maker is a Breville model that I bought in January 2024, and it's usually kept plugged in on the left side of the counter. My car is a blue Honda Civic parked in the garage, and I typically drive it to work every weekday. The front door key hook was installed by my roommate last month specifically for keeping keys organized. On Tuesday evening, the keys were missing from the hook, and I found them in my roommate's jacket pocket in the bedroom closet."""
    
    # Test questions
    questions = [
        "Where are my car keys?",
        "Where is the coffee maker?",
        "What's in the bedroom closet?",
        "What items are on the kitchen counter?"
    ]
    
    return render_template("demo.html", paragraph=paragraph, questions=questions)
