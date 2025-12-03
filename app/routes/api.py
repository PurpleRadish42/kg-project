"""
API routes for the Knowledge Graph application
"""

from flask import Blueprint, request, jsonify, current_app as app
from flask_login import current_user, login_required
from app.services.kg_service import KnowledgeGraphService

bp = Blueprint("api", __name__)


@bp.route("/add", methods=["POST"])
def add_knowledge():
    """Add knowledge from natural language text (API endpoint)"""
    from app.services.db_service import get_db_service
    
    data = request.get_json()
    text = data.get("text", "").strip() if data else ""
    kb_id = data.get("kb_id") if data else None
    
    if not text:
        return jsonify({"error": "Text is required"}), 400
    
    try:
        # Use current_user.username if logged in, otherwise demo_user
        if hasattr(current_user, 'is_authenticated') and current_user.is_authenticated:
            user_id = current_user.username
        else:
            user_id = "demo_user"
        
        # If no kb_id provided, try to get the first KB for the user
        # If no KBs exist, create a default one
        if kb_id is None:
            db_service = get_db_service()
            user_kbs = db_service.get_user_knowledge_bases(user_id)
            if user_kbs:
                kb_id = user_kbs[0]["id"]
            else:
                # Create default KB
                kb_id = db_service.create_knowledge_base(user_id, "My Knowledge Base", "Default knowledge base")
                if kb_id is None:
                    return jsonify({"error": "Failed to create default knowledge base"}), 500
        
        print(f"Storing knowledge for user_id: {user_id}, kb_id: {kb_id}")
        
        kg_service = KnowledgeGraphService()
        knowledge = kg_service.extract_knowledge(text)
        print(f"Extracted {len(knowledge.get('entities', []))} entities")
        
        kg_service.store_knowledge(knowledge, text, user_id=user_id, kb_id=kb_id)
        print(f"Successfully stored knowledge for {user_id} in KB {kb_id}")
        
        return jsonify({
            "success": True,
            "kb_id": kb_id,
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
    """Query the knowledge graph across all KBs (API endpoint)"""
    import time
    from app.services.mongo_service import get_mongo_service
    import json
    
    data = request.get_json()
    question = data.get("question", "").strip() if data else ""
    conversation_id = data.get("conversation_id") if data else None
    
    if not question:
        return jsonify({"error": "Question is required"}), 400
    
    try:
        # Use current_user.username if logged in, otherwise demo_user
        if hasattr(current_user, 'is_authenticated') and current_user.is_authenticated:
            user_id = current_user.username
        else:
            user_id = "demo_user"
        
        # Get or create conversation
        mongo_service = get_mongo_service()
        if not conversation_id:
            conversation_id = mongo_service.create_conversation(user_id)
        
        # Store user message
        mongo_service.add_message(
            conversation_id=conversation_id,
            user_id=user_id,
            role="user",
            content=question
        )
        
        # Get AI response (now returns list of results per KB)
        start_time = time.time()
        kg_service = KnowledgeGraphService()
        results = kg_service.query_knowledge(question, user_id=user_id)
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        # Store AI response (serialize the results as JSON for storage)
        answer_text = json.dumps(results)
        mongo_service.add_message(
            conversation_id=conversation_id,
            user_id=user_id,
            role="assistant",
            content=answer_text,
            metadata={
                "model": app.config.get("OPENAI_MODEL", "gpt-4o-mini"),
                "processing_time_ms": processing_time_ms,
                "multi_kb": True
            }
        )
        
        return jsonify({
            "results": results,
            "conversation_id": conversation_id
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


@bp.route("/conversations", methods=["GET"])
@login_required
def get_conversations():
    """Get all conversations for the current user"""
    try:
        from app.services.mongo_service import get_mongo_service
        
        mongo_service = get_mongo_service()
        conversations = mongo_service.get_user_conversations(current_user.username)
        
        return jsonify({
            "success": True,
            "conversations": conversations
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


@bp.route("/conversations/<conversation_id>", methods=["GET"])
@login_required
def get_conversation(conversation_id):
    """Get all messages in a specific conversation"""
    try:
        from app.services.mongo_service import get_mongo_service
        
        mongo_service = get_mongo_service()
        messages = mongo_service.get_conversation_messages(conversation_id, current_user.username)
        
        if not messages and messages != []:
            return jsonify({"error": "Conversation not found or access denied"}), 404
        
        return jsonify({
            "success": True,
            "messages": messages
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


@bp.route("/conversations/<conversation_id>", methods=["DELETE"])
@login_required
def delete_conversation(conversation_id):
    """Delete a conversation and all its messages"""
    try:
        from app.services.mongo_service import get_mongo_service
        
        mongo_service = get_mongo_service()
        success = mongo_service.delete_conversation(conversation_id, current_user.username)
        
        if not success:
            return jsonify({"error": "Conversation not found or access denied"}), 404
        
        return jsonify({
            "success": True,
            "message": "Conversation deleted"
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
@bp.route("/kb/create", methods=["POST"])
@login_required
def create_kb():
    """Create a new knowledge base"""
    from app.services.db_service import get_db_service
    
    data = request.get_json()
    name = data.get("name", "").strip() if data else ""
    description = data.get("description", "").strip() if data else ""
    
    if not name:
        return jsonify({"error": "Name is required"}), 400
    
    try:
        db_service = get_db_service()
        kb_id = db_service.create_knowledge_base(current_user.username, name, description)
        
        if kb_id is None:
            return jsonify({"error": "A knowledge base with this name already exists"}), 400
        
        return jsonify({
            "success": True,
            "kb_id": kb_id,
            "name": name,
            "description": description
        }), 200
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        error_msg = str(e)
        print(f"\n{'='*60}")
        print(f"ERROR in create_kb:")
        print(f"Message: {error_msg}")
        print(f"Traceback:\n{error_trace}")
        print(f"{'='*60}\n")
        return jsonify({
            "error": error_msg,
            "details": error_trace if app.config.get("DEBUG") else "Enable DEBUG mode for details"
        }), 500


@bp.route("/kb/list", methods=["GET"])
@login_required
def list_kbs():
    """List all knowledge bases for the current user"""
    from app.services.db_service import get_db_service
    
    try:
        db_service = get_db_service()
        kbs = db_service.get_user_knowledge_bases(current_user.username)
        
        return jsonify({
            "success": True,
            "knowledge_bases": kbs
        }), 200
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        error_msg = str(e)
        print(f"\n{'='*60}")
        print(f"ERROR in list_kbs:")
        print(f"Message: {error_msg}")
        print(f"Traceback:\n{error_trace}")
        print(f"{'='*60}\n")
        return jsonify({
            "error": error_msg,
            "details": error_trace if app.config.get("DEBUG") else "Enable DEBUG mode for details"
        }), 500


@bp.route("/kb/<int:kb_id>", methods=["DELETE"])
@login_required
def delete_kb(kb_id):
    """Delete a knowledge base and all its data"""
    from app.services.db_service import get_db_service
    
    try:
        db_service = get_db_service()
        kg_service = KnowledgeGraphService()
        
        # Delete from Neo4j first
        kg_service.clear_database(user_id=current_user.username, kb_id=kb_id)
        
        # Then delete from PostgreSQL
        success = db_service.delete_knowledge_base(kb_id, current_user.username)
        
        if not success:
            return jsonify({"error": "Knowledge base not found or access denied"}), 404
        
        return jsonify({
            "success": True,
            "message": "Knowledge base deleted"
        }), 200
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        error_msg = str(e)
        print(f"\n{'='*60}")
        print(f"ERROR in delete_kb:")
        print(f"Message: {error_msg}")
        print(f"Traceback:\n{error_trace}")
        print(f"{'='*60}\n")
        return jsonify({
            "error": error_msg,
            "details": error_trace if app.config.get("DEBUG") else "Enable DEBUG mode for details"
        }), 500
