from collections import defaultdict

class SessionManager:
    _instance = None

    def __new__(cls):
        if not cls._instance:
            cls._instance = super(SessionManager, cls).__new__(cls)
            cls._instance.user_sessions = defaultdict(lambda: {"current_menu": None})
        return cls._instance

    def reset_user_session(self, user_id):
        """Reset a specific user's session."""
        if user_id in self.user_sessions:
            self.user_sessions[user_id] = {"current_menu": None}

# ایجاد نمونه Singleton
session_manager = SessionManager()

