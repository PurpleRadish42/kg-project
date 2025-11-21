"""
API routes for the Knowledge Graph application
"""

from flask import Blueprint, request, jsonify, current_app as app
from flask_login import current_user
from app.services.kg_service import KnowledgeGraphService

bp = Blueprint("api", __name__)


@bp.route("/add", methods=["POST"])
def add_knowledge():
    """Add knowledge from natural language text (API endpoint)"""
    data = request.get_json()
    text = data.get("text", "").strip() if data else ""
    
    if not text:
        return jsonify({"error": "Text is required"}), 400
    
    try:
        # Use current_user.username if logged in, otherwise demo_user
        # Safely check if user is authenticated (works even if AnonymousUser)
        if hasattr(current_user, 'is_authenticated') and current_user.is_authenticated:
            user_id = current_user.username
        else:
            user_id = "demo_user"
        
        print(f"Storing knowledge for user_id: {user_id}")
        
        kg_service = KnowledgeGraphService()
        knowledge = kg_service.extract_knowledge(text)
        print(f"Extracted {len(knowledge.get('entities', []))} entities")
        
        kg_service.store_knowledge(knowledge, text, user_id=user_id)
        print(f"Successfully stored knowledge for {user_id}")
        
        return jsonify({
            "success": True,
            "entities_count": len(knowledge.get("entities", [])),
            "relationships_count": len(knowledge.get("relationships", [])),
            "knowledge": knowledge
        }), 200
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        error_msg = str(e)
        endpoint_name = request.endpoint or "unknown"
        print(f"\n{'='*60}")
        print(f"ERROR in {endpoint_name}:")
        print(f"Message: {error_msg}")
        print(f"Traceback:\n{error_trace}")
        print(f"{'='*60}\n")
        return jsonify({
            "error": error_msg,
            "details": error_trace if app.config.get("DEBUG") else "Enable DEBUG mode for details"
        }), 500


@bp.route("/query", methods=["POST"])
def query():
    """Query the knowledge graph (API endpoint)"""
    data = request.get_json()
    question = data.get("question", "").strip() if data else ""
    
    if not question:
        return jsonify({"error": "Question is required"}), 400
    
    try:
        # Use current_user.username if logged in, otherwise demo_user
        # Safely check if user is authenticated (works even if AnonymousUser)
        if hasattr(current_user, 'is_authenticated') and current_user.is_authenticated:
            user_id = current_user.username
        else:
            user_id = "demo_user"
        
        kg_service = KnowledgeGraphService()
        answer = kg_service.query_knowledge(question, user_id=user_id)
        
        return jsonify({
            "success": True,
            "question": question,
            "answer": answer
        }), 200
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        error_msg = str(e)
        endpoint_name = request.endpoint or "unknown"
        print(f"\n{'='*60}")
        print(f"ERROR in {endpoint_name}:")
        print(f"Message: {error_msg}")
        print(f"Traceback:\n{error_trace}")
        print(f"{'='*60}\n")
        return jsonify({
            "error": error_msg,
            "details": error_trace if app.config.get("DEBUG") else "Enable DEBUG mode for details"
        }), 500


@bp.route("/entities", methods=["GET"])
def get_entities():
    """Get all entities (API endpoint)"""
    try:
        # Use current_user.username if logged in, otherwise demo_user
        # Safely check if user is authenticated (works even if AnonymousUser)
        if hasattr(current_user, 'is_authenticated') and current_user.is_authenticated:
            user_id = current_user.username
        else:
            user_id = "demo_user"
        
        kg_service = KnowledgeGraphService()
        entities = kg_service.get_all_entities(user_id=user_id)
        return jsonify({"success": True, "entities": entities}), 200
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        error_msg = str(e)
        endpoint_name = request.endpoint or "unknown"
        print(f"\n{'='*60}")
        print(f"ERROR in {endpoint_name}:")
        print(f"Message: {error_msg}")
        print(f"Traceback:\n{error_trace}")
        print(f"{'='*60}\n")
        return jsonify({
            "error": error_msg,
            "details": error_trace if app.config.get("DEBUG") else "Enable DEBUG mode for details"
        }), 500


@bp.route("/relationships", methods=["GET"])
def get_relationships():
    """Get all relationships (API endpoint)"""
    try:
        # Use current_user.username if logged in, otherwise demo_user
        # Safely check if user is authenticated (works even if AnonymousUser)
        if hasattr(current_user, 'is_authenticated') and current_user.is_authenticated:
            user_id = current_user.username
        else:
            user_id = "demo_user"
        
        kg_service = KnowledgeGraphService()
        relationships = kg_service.get_all_relationships(user_id=user_id)
        return jsonify({"success": True, "relationships": relationships}), 200
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        error_msg = str(e)
        endpoint_name = request.endpoint or "unknown"
        print(f"\n{'='*60}")
        print(f"ERROR in {endpoint_name}:")
        print(f"Message: {error_msg}")
        print(f"Traceback:\n{error_trace}")
        print(f"{'='*60}\n")
        return jsonify({
            "error": error_msg,
            "details": error_trace if app.config.get("DEBUG") else "Enable DEBUG mode for details"
        }), 500


@bp.route("/clear-demo", methods=["POST"])
def clear_demo():
    """Clear demo user's knowledge graph data"""
    try:
        kg_service = KnowledgeGraphService()
        kg_service.clear_database(user_id="demo_user")
        return jsonify({"success": True, "message": "Demo data cleared"}), 200
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        error_msg = str(e)
        print(f"\n{'='*60}")
        print(f"ERROR in clear_demo:")
        print(f"Message: {error_msg}")
        print(f"Traceback:\n{error_trace}")
        print(f"{'='*60}\n")
        return jsonify({
            "error": error_msg,
            "details": error_trace if app.config.get("DEBUG") else "Enable DEBUG mode for details"
        }), 500

