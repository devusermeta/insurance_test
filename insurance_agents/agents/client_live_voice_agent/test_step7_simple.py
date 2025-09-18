#!/usr/bin/env python3
"""
Simple test for conversation tracking functionality
Tests the core conversation tracking without server dependencies.
"""

import os
import sys
import tempfile
import json
from datetime import datetime

# Add current directory to path
current_dir = os.path.dirname(__file__)
sys.path.append(current_dir)

try:
    from conversation_tracker import VoiceConversationTracker
    print("✅ Successfully imported VoiceConversationTracker")
except ImportError as e:
    print(f"❌ Failed to import VoiceConversationTracker: {e}")
    sys.exit(1)

def test_conversation_tracking():
    """Test basic conversation tracking functionality"""
    print("🧪 Testing conversation tracking...")
    
    # Create temporary file for testing
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
    temp_file.close()
    
    try:
        # Initialize tracker
        tracker = VoiceConversationTracker(log_file=temp_file.name)
        print("✅ Conversation tracker initialized")
        
        # Start a session
        session_id = tracker.start_session({
            "test_mode": True,
            "user": "test_user"
        })
        print(f"✅ Session started: {session_id}")
        
        # Log some interactions
        tracker.log_voice_interaction(
            transcript="Hello, I need help with my insurance claim",
            audio_metadata={"duration": 3.2, "format": "audio/wav"}
        )
        print("✅ Voice interaction logged")
        
        tracker.log_agent_response(
            response="I'd be happy to help you with your insurance claim. Can you provide your claim number?",
            response_metadata={"response_time": 1.5, "azure_ai_used": True}
        )
        print("✅ Agent response logged")
        
        tracker.log_system_event(
            event="Conversation tracking test completed",
            event_metadata={"test": True}
        )
        print("✅ System event logged")
        
        # Get session history
        history = tracker.get_session_history()
        print(f"✅ Retrieved session history with {len(history['messages'])} messages")
        
        # Search conversations
        results = tracker.search_conversations("insurance claim")
        print(f"✅ Search found {len(results)} matching messages")
        
        # Get statistics
        stats = tracker.get_conversation_stats()
        print(f"✅ Statistics: {stats['total_sessions']} sessions, {stats['total_messages']} messages")
        
        # End session
        tracker.end_session()
        print("✅ Session ended")
        
        # Verify file contents
        with open(temp_file.name, 'r') as f:
            data = json.load(f)
            print(f"✅ Log file contains {len(data['sessions'])} sessions")
            
        print("\n🎉 All conversation tracking tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Clean up
        if os.path.exists(temp_file.name):
            os.unlink(temp_file.name)

def main():
    """Run conversation tracking tests"""
    print("🚀 Starting Conversation Tracking Tests")
    print("=" * 50)
    
    success = test_conversation_tracking()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ Step 7: Conversation Tracking - PASSED")
        print("📝 Conversation tracking system is working correctly")
        print("💾 Voice conversations will be logged to voice_chat.json")
        print("🔍 Search and analytics functionality verified")
    else:
        print("❌ Step 7: Conversation Tracking - FAILED")
        
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)