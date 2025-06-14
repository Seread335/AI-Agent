from typing import Dict, Optional, List
import time
from utils.logger import get_logger

logger = get_logger(__name__)

class ContextManager:
    def __init__(self, max_history: int = 10):
        self.max_history = max_history
        self.contexts: Dict[str, Dict] = {}
        self.default_context_ttl = 3600  # 1 hour

    def get_context(self, user_id: Optional[str] = None) -> Dict:
        """
        Get conversation context for a user
        """
        if not user_id:
            return {}

        context = self.contexts.get(user_id, {})
        
        # Check if context has expired
        if context and self._is_context_expired(context):
            self.clear_context(user_id)
            return {}

        return context.get("data", {})

    def update_context(self, 
                      user_id: str, 
                      query: str, 
                      response: Dict,
                      ttl: Optional[int] = None) -> None:
        """
        Update conversation context with new interaction
        """
        if not user_id:
            return

        current_context = self.contexts.get(user_id, {
            "data": {
                "history": [],
                "preferences": {},
                "state": {}
            },
            "timestamp": time.time()
        })

        # Update history
        history = current_context["data"].get("history", [])
        history.append({
            "timestamp": time.time(),
            "query": query,
            "response": response
        })

        # Trim history if needed
        if len(history) > self.max_history:
            history = history[-self.max_history:]

        # Update context
        current_context["data"]["history"] = history
        current_context["timestamp"] = time.time()
        current_context["ttl"] = ttl or self.default_context_ttl

        self.contexts[user_id] = current_context

    def update_user_preferences(self, 
                              user_id: str, 
                              preferences: Dict) -> None:
        """
        Update user preferences in context
        """
        if not user_id:
            return

        current_context = self.contexts.get(user_id, {
            "data": {
                "history": [],
                "preferences": {},
                "state": {}
            },
            "timestamp": time.time()
        })

        # Update preferences
        current_prefs = current_context["data"].get("preferences", {})
        current_prefs.update(preferences)
        current_context["data"]["preferences"] = current_prefs

        self.contexts[user_id] = current_context

    def update_state(self, 
                    user_id: str, 
                    state_updates: Dict) -> None:
        """
        Update conversation state
        """
        if not user_id:
            return

        current_context = self.contexts.get(user_id, {
            "data": {
                "history": [],
                "preferences": {},
                "state": {}
            },
            "timestamp": time.time()
        })

        # Update state
        current_state = current_context["data"].get("state", {})
        current_state.update(state_updates)
        current_context["data"]["state"] = current_state

        self.contexts[user_id] = current_context

    def clear_context(self, user_id: str) -> None:
        """
        Clear context for a user
        """
        if user_id in self.contexts:
            del self.contexts[user_id]

    def get_recent_interactions(self, 
                              user_id: str, 
                              limit: int = 5) -> List[Dict]:
        """
        Get recent interactions for a user
        """
        context = self.contexts.get(user_id, {})
        history = context.get("data", {}).get("history", [])
        
        return history[-limit:]

    def _is_context_expired(self, context: Dict) -> bool:
        """
        Check if context has expired
        """
        timestamp = context.get("timestamp", 0)
        ttl = context.get("ttl", self.default_context_ttl)
        
        return (time.time() - timestamp) > ttl
