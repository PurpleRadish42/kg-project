"""
Web routes for the Knowledge Graph application
"""

from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import current_user, login_required
from app.services.kg_service import KnowledgeGraphService

bp = Blueprint("web", __name__)


@bp.route("/")
def index():
    """Welcome page - redirect to query if logged in"""
    if current_user.is_authenticated:
        return redirect(url_for("web.query"))
    return render_template("welcome.html")


@bp.route("/knowledge-base")
@login_required
def knowledge_base():
    """Knowledge base page showing all stored knowledge"""
    kg_service = KnowledgeGraphService()
    try:
        knowledge_items = kg_service.get_knowledge_base(user_id=current_user.username)
    except Exception as e:
        flash(f"Error fetching knowledge base: {str(e)}", "error")
        knowledge_items = []
    
    return render_template("knowledge_base.html", knowledge_items=knowledge_items)


@bp.route("/add", methods=["GET", "POST"])
@login_required
def add_knowledge():
    """Add knowledge page"""
    kg_service = KnowledgeGraphService()
    text = None
    if request.method == "POST":
        text = request.form.get("text")
        if text:
            try:
                # Extract and store knowledge
                knowledge = kg_service.extract_knowledge(text)
                kg_service.store_knowledge(knowledge, text, user_id=current_user.username)
                flash("Knowledge extracted and stored successfully!", "success")
            except Exception as e:
                flash(f"Error processing text: {str(e)}", "error")
    
    return render_template("add.html", text=text)


@bp.route("/query", methods=["GET", "POST"])
@login_required
def query():
    """Query interface"""
    kg_service = KnowledgeGraphService()
    question = None
    answer = None
    
    if request.method == "POST":
        question = request.form.get("question")
        if question:
            try:
                answer = kg_service.query_knowledge(question, user_id=current_user.username)
            except Exception as e:
                answer = f"Error: {str(e)}"
                
    return render_template("query.html", question=question, answer=answer)


@bp.route("/graph")
@login_required
def view_graph():
    """View knowledge graph"""
    kg_service = KnowledgeGraphService()
    try:
        entities = kg_service.get_all_entities(user_id=current_user.username)
        relationships = kg_service.get_all_relationships(user_id=current_user.username)
    except Exception as e:
        flash(f"Error fetching graph data: {str(e)}", "error")
        entities = []
        relationships = []
        
    return render_template("graph.html", entities=entities, relationships=relationships)


@bp.route("/clear", methods=["POST"])
@login_required
def clear_database():
    """Clear all data for the current user"""
    kg_service = KnowledgeGraphService()
    try:
        kg_service.clear_database(user_id=current_user.username)
        flash("Knowledge graph cleared successfully!", "success")
    except Exception as e:
        flash(f"Error clearing database: {str(e)}", "error")
        
    return redirect(url_for("web.view_graph"))


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
