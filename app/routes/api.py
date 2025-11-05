"""
API routes for the Knowledge Graph application
"""

from flask import Blueprint, request, jsonify
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
        kg_service = KnowledgeGraphService()
        knowledge = kg_service.extract_knowledge(text)
        kg_service.store_knowledge(knowledge, text)
        
        return jsonify({
            "success": True,
            "entities_count": len(knowledge.get("entities", [])),
            "relationships_count": len(knowledge.get("relationships", [])),
            "knowledge": knowledge
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/query", methods=["POST"])
def query():
    """Query the knowledge graph (API endpoint)"""
    data = request.get_json()
    question = data.get("question", "").strip() if data else ""
    
    if not question:
        return jsonify({"error": "Question is required"}), 400
    
    try:
        kg_service = KnowledgeGraphService()
        answer = kg_service.query_knowledge(question)
        
        return jsonify({
            "success": True,
            "question": question,
            "answer": answer
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/entities", methods=["GET"])
def get_entities():
    """Get all entities (API endpoint)"""
    try:
        kg_service = KnowledgeGraphService()
        entities = kg_service.get_all_entities()
        return jsonify({"success": True, "entities": entities}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/relationships", methods=["GET"])
def get_relationships():
    """Get all relationships (API endpoint)"""
    try:
        kg_service = KnowledgeGraphService()
        relationships = kg_service.get_all_relationships()
        return jsonify({"success": True, "relationships": relationships}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


