import json
import os
from uuid import uuid4
import time

class MarketplaceManager:
    """
    Manages item listings and a full messaging/reply system for the API.
    Data is saved to and loaded from a JSON file for persistence.
    """
    def __init__(self, filename='marketplace_data.json'):
        self.filename = filename
        # The data structure now holds listings and conversations
        self.data = self._load_data()
        print("MarketplaceManager initialized with messaging capabilities.")

    def _load_data(self):
        """Loads data from the JSON file."""
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                pass # Fallback to default if file is corrupted
        # Default structure if no file exists
        return {"listings": {}, "conversations": {}}

    def _save_data(self):
        """Saves the current data to the JSON file."""
        with open(self.filename, 'w') as f:
            json.dump(self.data, f, indent=4)

    # --- Item Listing API Methods ---

    def get_all_items_api(self):
        """Returns a list of all listings."""
        return list(self.data.get("listings", {}).values())

    def create_listing_api(self, item_data, owner):
        """Creates a new listing from API data."""
        name = item_data.get('name')
        description = item_data.get('description')
        price = item_data.get('price')
        category = item_data.get('category')

        if not all([name, description, price, category]):
            return {"success": False, "message": "All fields are required."}

        listing_id = str(uuid4())
        
        if "listings" not in self.data:
            self.data["listings"] = {}
            
        self.data["listings"][listing_id] = {
            'id': listing_id,
            'name': name,
            'description': description,
            'price': price,
            'category': category,
            'owner': owner
        }
        self._save_data()
        return {"success": True, "message": "Listing created successfully!", "listing": self.data["listings"][listing_id]}

    # --- Messaging and Inbox API Methods ---

    def send_message_api(self, item_id, sender, content):
        """Starts a new conversation or adds a message to an existing one."""
        if not item_id in self.data["listings"]:
            return {"success": False, "message": "Item not found."}

        item = self.data["listings"][item_id]
        recipient = item['owner']

        if sender == recipient:
            return {"success": False, "message": "You cannot message yourself."}

        # Check if a conversation between these users about this item already exists
        # This logic ensures one conversation per item/user pair
        convo_id = None
        for cid, convo in self.data["conversations"].items():
            if convo["item_id"] == item_id and sender in convo["participants"] and recipient in convo["participants"]:
                convo_id = cid
                break

        message = {
            "sender": sender,
            "content": content,
            "timestamp": time.time(),
            "read": False
        }

        if convo_id:
            # Add to existing conversation
            self.data["conversations"][convo_id]["messages"].append(message)
        else:
            # Create a new conversation
            new_convo_id = str(uuid4())
            self.data["conversations"][new_convo_id] = {
                "id": new_convo_id,
                "item_id": item_id,
                "participants": [sender, recipient],
                "messages": [message]
            }
        
        self._save_data()
        return {"success": True, "message": "Message sent successfully."}

    def get_inbox_api(self, username):
        """Gets all conversations for a specific user."""
        user_inbox = []
        for convo_id, convo in self.data["conversations"].items():
            if username in convo["participants"]:
                # Add extra info to make it easier for the frontend
                item = self.data["listings"].get(convo["item_id"])
                other_participant = next(p for p in convo["participants"] if p != username)
                
                unread_count = 0
                for msg in convo["messages"]:
                    if not msg["read"] and msg["sender"] != username:
                        unread_count += 1

                summary = {
                    "convo_id": convo_id,
                    "item_name": item["name"] if item else "Deleted Item",
                    "other_participant": other_participant,
                    "last_message": convo["messages"][-1],
                    "unread_count": unread_count
                }
                user_inbox.append(summary)
        
        # Sort by the most recent message
        user_inbox.sort(key=lambda x: x['last_message']['timestamp'], reverse=True)
        return user_inbox

    def get_conversation_api(self, convo_id, username):
        """Gets a single conversation and marks messages as read."""
        if convo_id not in self.data["conversations"]:
            return {"success": False, "message": "Conversation not found."}

        convo = self.data["conversations"][convo_id]
        if username not in convo["participants"]:
            return {"success": False, "message": "Unauthorized access."}

        # Mark messages as read by the current user
        for message in convo["messages"]:
            if message["sender"] != username:
                message["read"] = True
        
        self._save_data()

        # Add item info for context on the frontend
        item = self.data["listings"].get(convo["item_id"])
        convo["item_info"] = item
        
        return {"success": True, "conversation": convo}

