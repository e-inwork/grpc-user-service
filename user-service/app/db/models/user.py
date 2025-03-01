# 2024 amicroservice author.

from datetime import datetime

import bcrypt


class UserModel:
    def __init__(self, group_id: str,  email: str, first_name: str, last_name: str, password=None):
        # Initialize a new User instance with provided details
        self.id = None  # Unique identifier for the user (can be set later)
        self.created_at = None  # Timestamp of when the user was created
        self.updated_at = None  # Timestamp of the last update to the user

        # User's basic information
        self.group_id = group_id
        self.email = email
        self.first_name = first_name
        self.last_name = last_name

        # Store the hashed password if provided, otherwise set to None
        self.password_hash = self._hash_password(password) if password else None

    def _hash_password(self, password):
        """Securely hash the password using bcrypt."""
        if password:
            # Generate a salt and hash the password
            salt = bcrypt.gensalt()
            return bcrypt.hashpw(password.encode("utf-8"), salt)
        return None  # Return None if no password provided

    def valid_password(self, password: str):
        """Check if the provided password matches the stored password hash."""
        # Verify the password by comparing with the stored password hash
        if bcrypt.checkpw(password.encode("utf-8"), bytes(self.password_hash)):
            return True  # Password matches

        # Password does not match
        return False

    def update(self, email=None, first_name=None, last_name=None, password=None):
        """Update User fields with new information."""
        # Update the email if a new value is provided
        if email:
            self.email = email

        # Update the first name if a new value is provided
        if first_name:
            self.first_name = first_name

        # Update the last name if a new value is provided
        if last_name:
            self.last_name = last_name

        # Hash and update the password if a new password is provided
        if password:
            self.password_hash = self._hash_password(password)

        # Update the 'updated_at' field to the current time
        self.updated_at = datetime.now()
