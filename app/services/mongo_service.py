"""
MongoDB Service for Chat History Management
Handles conversation and message storage/retrieval
"""

from pymongo import MongoClient, ASCENDING, DESCENDING
from bson import ObjectId
from datetime import datetime
from typing import List, Dict, Optional
from flask import current_app


class MongoService:
    """Singleton service for MongoDB operations"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MongoService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        # Build connection URI
        username = current_app.config.get("MONGODB_USERNAME", "")
        password = current_app.config.get("MONGODB_PASSWORD", "")
        base_uri = current_app.config.get("MONGODB_URI", "mongodb://localhost:27017/")
        
        # Handle authentication for both mongodb:// and mongodb+srv:// URIs
        if username and password:
            # Check if URI already contains credentials
            if "@" not in base_uri:
                # Handle mongodb+srv:// (DigitalOcean)
                if "mongodb+srv://" in base_uri:
                    uri = base_uri.replace("mongodb+srv://", f"mongodb+srv://{username}:{password}@")
                # Handle mongodb:// (local)
                else:
                    uri = base_uri.replace("mongodb://", f"mongodb://{username}:{password}@")
            else:
                # URI already has credentials embedded
                uri = base_uri
        else:
            uri = base_uri
        
        self.client = MongoClient(uri)
        self.db = self.client[current_app.config.get("MONGODB_DATABASE", "kg_chat_history")]
        
        # Initialize database (create collections and indexes)
        self._initialize_database()
        self._initialized = True
    
    def _initialize_database(self):
        """Create collections and indexes if they don't exist"""
        try:
            # Create collections if they don't exist
            existing_collections = self.db.list_collection_names()
            
            if "conversations" not in existing_collections:
                self.db.create_collection("conversations")
                print("✅ Created 'conversations' collection")
            
            if "messages" not in existing_collections:
                self.db.create_collection("messages")
                print("✅ Created 'messages' collection")
            
            # Create indexes for conversations
            self.db.conversations.create_index([("user_id", ASCENDING)])
            self.db.conversations.create_index([("updated_at", DESCENDING)])
            
            # Create indexes for messages
            self.db.messages.create_index([("conversation_id", ASCENDING)])
            self.db.messages.create_index([("user_id", ASCENDING)])
            self.db.messages.create_index([("timestamp", ASCENDING)])
            
            print("✅ MongoDB initialized successfully")
        except Exception as e:
            print(f"⚠️  MongoDB initialization warning: {e}")
    
    def create_conversation(self, user_id: str, title: str = "New Conversation") -> str:
        """Create a new conversation and return its ID"""
        now = datetime.utcnow()
        conversation = {
            "user_id": user_id,
            "title": title,
            "created_at": now,
            "updated_at": now,
            "message_count": 0,
            "last_message_preview": ""
        }
        
        result = self.db.conversations.insert_one(conversation)
        return str(result.inserted_id)
    
    def add_message(
        self, 
        conversation_id: str, 
        user_id: str, 
        role: str, 
        content: str,
        metadata: Optional[Dict] = None
    ) -> str:
        """Add a message to a conversation"""
        now = datetime.utcnow()
        
        message = {
            "conversation_id": ObjectId(conversation_id),
            "user_id": user_id,
            "role": role,  # "user" or "assistant"
            "content": content,
            "timestamp": now,
            "metadata": metadata or {}
        }
        
        # Insert message
        result = self.db.messages.insert_one(message)
        
        # Update conversation metadata
        self.db.conversations.update_one(
            {"_id": ObjectId(conversation_id)},
            {
                "$set": {
                    "updated_at": now,
                    "last_message_preview": content[:100]  # First 100 chars
                },
                "$inc": {"message_count": 1}
            }
        )
        
        # If this is the first user message, update title
        if role == "user":
            conv = self.db.conversations.find_one({"_id": ObjectId(conversation_id)})
            if conv and conv.get("message_count", 0) == 1:
                title = self._generate_title(content)
                self.db.conversations.update_one(
                    {"_id": ObjectId(conversation_id)},
                    {"$set": {"title": title}}
                )
        
        return str(result.inserted_id)
    
    def get_user_conversations(self, user_id: str, limit: int = 50) -> List[Dict]:
        """Get all conversations for a user, sorted by most recent"""
        conversations = self.db.conversations.find(
            {"user_id": user_id}
        ).sort("updated_at", DESCENDING).limit(limit)
        
        result = []
        for conv in conversations:
            result.append({
                "id": str(conv["_id"]),
                "title": conv.get("title", "New Conversation"),
                "created_at": conv.get("created_at").isoformat() if conv.get("created_at") else None,
                "updated_at": conv.get("updated_at").isoformat() if conv.get("updated_at") else None,
                "message_count": conv.get("message_count", 0),
                "last_message_preview": conv.get("last_message_preview", "")
            })
        
        return result
    
    def get_conversation_messages(self, conversation_id: str, user_id: str) -> List[Dict]:
        """Get all messages in a conversation (with user verification)"""
        # Verify user owns this conversation
        conversation = self.db.conversations.find_one({
            "_id": ObjectId(conversation_id),
            "user_id": user_id
        })
        
        if not conversation:
            return []
        
        messages = self.db.messages.find(
            {"conversation_id": ObjectId(conversation_id)}
        ).sort("timestamp", ASCENDING)
        
        result = []
        for msg in messages:
            result.append({
                "id": str(msg["_id"]),
                "role": msg.get("role"),
                "content": msg.get("content"),
                "timestamp": msg.get("timestamp").isoformat() if msg.get("timestamp") else None,
                "metadata": msg.get("metadata", {})
            })
        
        return result
    
    def delete_conversation(self, conversation_id: str, user_id: str) -> bool:
        """Delete a conversation and all its messages"""
        # Verify user owns this conversation
        conversation = self.db.conversations.find_one({
            "_id": ObjectId(conversation_id),
            "user_id": user_id
        })
        
        if not conversation:
            return False
        
        # Delete all messages in this conversation
        self.db.messages.delete_many({"conversation_id": ObjectId(conversation_id)})
        
        # Delete the conversation
        self.db.conversations.delete_one({"_id": ObjectId(conversation_id)})
        
        return True
    
    def _generate_title(self, first_message: str) -> str:
        """Generate a conversation title from the first message"""
        # Simple implementation: truncate to 50 chars
        title = first_message.strip()
        if len(title) > 50:
            title = title[:47] + "..."
        return title or "New Conversation"


# Singleton instance getter
def get_mongo_service() -> MongoService:
    """Get the singleton MongoService instance"""
    return MongoService()
