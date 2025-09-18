"""
Voice Conversation Tracking System
Handles logging and persistence of voice conversations for the A2A Voice Agent.
"""

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

class VoiceConversationTracker:
    """
    Tracks and persists voice conversations to voice_chat.json
    Manages session-based conversation history and metadata.
    """
    
    def __init__(self, log_file: str = "voice_chat.json", max_history: int = 50):
        self.log_file = Path(log_file)
        self.max_history = max_history
        self.current_session_id = None
        self.logger = logging.getLogger(__name__)
        
        # Ensure log file exists
        self._initialize_log_file()
    
    def _initialize_log_file(self):
        """Initialize the conversation log file if it doesn't exist"""
        if not self.log_file.exists():
            initial_data = {
                "metadata": {
                    "created": datetime.now(timezone.utc).isoformat(),
                    "agent_type": "A2A Voice Agent",
                    "version": "1.0.0"
                },
                "sessions": {}
            }
            self._write_to_file(initial_data)
            self.logger.info(f"📝 Initialized conversation log: {self.log_file}")
    
    def start_session(self, session_metadata: Optional[Dict] = None) -> str:
        """
        Start a new conversation session
        
        Args:
            session_metadata: Optional metadata for the session
            
        Returns:
            Session ID
        """
        self.current_session_id = str(uuid.uuid4())
        
        session_data = {
            "session_id": self.current_session_id,
            "start_time": datetime.now(timezone.utc).isoformat(),
            "end_time": None,
            "metadata": session_metadata or {},
            "messages": [],
            "stats": {
                "total_messages": 0,
                "user_messages": 0,
                "assistant_messages": 0,
                "system_messages": 0,
                "voice_interactions": 0,
                "duration_seconds": 0
            }
        }
        
        # Load existing data and add new session
        data = self._load_from_file()
        data["sessions"][self.current_session_id] = session_data
        
        # Cleanup old sessions if needed
        self._cleanup_old_sessions(data)
        
        self._write_to_file(data)
        
        self.logger.info(f"🎤 Started new voice session: {self.current_session_id}")
        return self.current_session_id
    
    def end_session(self):
        """End the current conversation session"""
        if not self.current_session_id:
            return
        
        data = self._load_from_file()
        if self.current_session_id in data["sessions"]:
            session = data["sessions"][self.current_session_id]
            session["end_time"] = datetime.now(timezone.utc).isoformat()
            
            # Calculate duration
            if session["start_time"]:
                start_time = datetime.fromisoformat(session["start_time"].replace('Z', '+00:00'))
                end_time = datetime.fromisoformat(session["end_time"].replace('Z', '+00:00'))
                session["stats"]["duration_seconds"] = (end_time - start_time).total_seconds()
            
            self._write_to_file(data)
            
            self.logger.info(f"🏁 Ended voice session: {self.current_session_id}")
            self.logger.info(f"📊 Session stats: {session['stats']}")
        
        self.current_session_id = None
    
    def log_message(self, 
                   sender: str, 
                   content: str, 
                   message_type: str = "text",
                   metadata: Optional[Dict] = None):
        """
        Log a message to the current session
        
        Args:
            sender: "user", "assistant", or "system"
            content: Message content
            message_type: "text", "audio", "transcript", "system"
            metadata: Additional metadata for the message
        """
        if not self.current_session_id:
            self.logger.warning("⚠️ No active session - starting new session")
            self.start_session()
        
        message = {
            "id": str(uuid.uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "sender": sender,
            "content": content,
            "type": message_type,
            "metadata": metadata or {}
        }
        
        # Load data and add message
        data = self._load_from_file()
        if self.current_session_id in data["sessions"]:
            session = data["sessions"][self.current_session_id]
            session["messages"].append(message)
            
            # Update statistics
            session["stats"]["total_messages"] += 1
            if sender == "user":
                session["stats"]["user_messages"] += 1
            elif sender == "assistant":
                session["stats"]["assistant_messages"] += 1
            elif sender == "system":
                session["stats"]["system_messages"] += 1
            
            if message_type in ["audio", "transcript"]:
                session["stats"]["voice_interactions"] += 1
            
            self._write_to_file(data)
            
            self.logger.debug(f"📝 Logged message: {sender} -> {content[:50]}...")
    
    def log_voice_interaction(self, 
                            transcript: str,
                            audio_metadata: Optional[Dict] = None):
        """
        Log a voice interaction (transcript + audio metadata)
        
        Args:
            transcript: Transcribed text from voice
            audio_metadata: Audio format, duration, etc.
        """
        self.log_message(
            sender="user",
            content=transcript,
            message_type="transcript",
            metadata={
                "audio": audio_metadata or {},
                "interaction_type": "voice_input"
            }
        )
    
    def log_agent_response(self, 
                          response: str,
                          response_metadata: Optional[Dict] = None):
        """
        Log an agent response
        
        Args:
            response: Agent response text
            response_metadata: Azure AI Foundry metadata, processing time, etc.
        """
        self.log_message(
            sender="assistant",
            content=response,
            message_type="text",
            metadata={
                "agent": response_metadata or {},
                "interaction_type": "agent_response"
            }
        )
    
    def log_system_event(self, 
                        event: str,
                        event_metadata: Optional[Dict] = None):
        """
        Log system events (connections, errors, etc.)
        
        Args:
            event: System event description
            event_metadata: Additional event data
        """
        self.log_message(
            sender="system",
            content=event,
            message_type="system",
            metadata=event_metadata or {}
        )
    
    def get_session_history(self, session_id: Optional[str] = None) -> Optional[Dict]:
        """
        Get conversation history for a session
        
        Args:
            session_id: Session ID (uses current session if None)
            
        Returns:
            Session data or None if not found
        """
        session_id = session_id or self.current_session_id
        if not session_id:
            return None
        
        data = self._load_from_file()
        return data["sessions"].get(session_id)
    
    def get_recent_sessions(self, limit: int = 10) -> List[Dict]:
        """
        Get recent conversation sessions
        
        Args:
            limit: Maximum number of sessions to return
            
        Returns:
            List of session data sorted by start time (newest first)
        """
        data = self._load_from_file()
        sessions = list(data["sessions"].values())
        
        # Sort by start time (newest first)
        sessions.sort(key=lambda x: x["start_time"], reverse=True)
        
        return sessions[:limit]
    
    def search_conversations(self, query: str, limit: int = 20) -> List[Dict]:
        """
        Search conversation history for specific content
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of matching messages with session context
        """
        results = []
        data = self._load_from_file()
        
        query_lower = query.lower()
        
        for session_id, session in data["sessions"].items():
            for message in session["messages"]:
                if query_lower in message["content"].lower():
                    results.append({
                        "session_id": session_id,
                        "session_start": session["start_time"],
                        "message": message
                    })
        
        # Sort by timestamp (newest first)
        results.sort(key=lambda x: x["message"]["timestamp"], reverse=True)
        
        return results[:limit]
    
    def get_conversation_stats(self) -> Dict:
        """
        Get overall conversation statistics
        
        Returns:
            Dictionary with conversation statistics
        """
        data = self._load_from_file()
        
        total_sessions = len(data["sessions"])
        total_messages = 0
        total_voice_interactions = 0
        total_duration = 0
        
        for session in data["sessions"].values():
            stats = session["stats"]
            total_messages += stats["total_messages"]
            total_voice_interactions += stats["voice_interactions"]
            total_duration += stats.get("duration_seconds", 0)
        
        return {
            "total_sessions": total_sessions,
            "total_messages": total_messages,
            "total_voice_interactions": total_voice_interactions,
            "total_duration_seconds": total_duration,
            "average_session_duration": total_duration / max(total_sessions, 1),
            "average_messages_per_session": total_messages / max(total_sessions, 1)
        }
    
    def _load_from_file(self) -> Dict:
        """Load conversation data from file"""
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            self.logger.error(f"❌ Error loading conversation log: {e}")
            # Return empty structure
            return {
                "metadata": {
                    "created": datetime.now(timezone.utc).isoformat(),
                    "agent_type": "A2A Voice Agent",
                    "version": "1.0.0"
                },
                "sessions": {}
            }
    
    def _write_to_file(self, data: Dict):
        """Write conversation data to file"""
        try:
            # Update metadata
            data["metadata"]["last_updated"] = datetime.now(timezone.utc).isoformat()
            
            with open(self.log_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"❌ Error writing conversation log: {e}")
    
    def _cleanup_old_sessions(self, data: Dict):
        """Remove old sessions if we exceed max_history"""
        sessions = list(data["sessions"].items())
        if len(sessions) <= self.max_history:
            return
        
        # Sort by start time and keep only the most recent
        sessions.sort(key=lambda x: x[1]["start_time"], reverse=True)
        sessions_to_keep = sessions[:self.max_history]
        
        # Create new sessions dict with only recent sessions
        data["sessions"] = dict(sessions_to_keep)
        
        removed_count = len(sessions) - len(sessions_to_keep)
        self.logger.info(f"🧹 Cleaned up {removed_count} old conversation sessions")

# Global tracker instance
conversation_tracker = VoiceConversationTracker()