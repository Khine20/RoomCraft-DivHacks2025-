import json
import os
import hashlib

class UserManager:
    """Manages user registration and login for the web application."""
    def __init__(self, filename="users.json"):
        self.filename = filename
        self.users = self._load_users()
        print("UserManager initialized.")

    def _load_users(self):
        """Loads users from the specified JSON file."""
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                # If the file is corrupted or empty, start fresh
                return {}
        return {}

    def _save_users(self):
        """Saves the current user dictionary to the JSON file."""
        with open(self.filename, 'w') as f:
            json.dump(self.users, f, indent=4)

    def _hash_password(self, password):
        """Hashes a password using SHA256 for secure storage."""
        return hashlib.sha256(password.encode()).hexdigest()

    def register_api(self, username, password):
        """API method for user registration. Returns a dictionary."""
        if not username or not password:
            return {"success": False, "message": "Username and password cannot be empty."}
        
        # Store username in lowercase for case-insensitive login
        username_lower = username.lower()
        if username_lower in self.users:
            return {"success": False, "message": "Username already exists. Please choose another."}

        self.users[username_lower] = self._hash_password(password)
        self._save_users()
        return {"success": True, "message": "Registration successful! You can now log in."}

    def login_api(self, username, password):
        """API method for user login. Returns the username on success or None on failure."""
        if not username or not password:
            return None
            
        hashed_password = self._hash_password(password)
        username_lower = username.lower()
        
        # Check if the user exists and the hashed password matches
        if self.users.get(username_lower) == hashed_password:
            return username_lower
        else:
            return None

