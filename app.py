from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from user_manager import UserManager
from marketplace import MarketplaceManager
from chatbot import Chatbot
import os

# --- Initialization ---
app = Flask(__name__)
# --- FIX ---
# The secret key is now a static string. This ensures that the user's session
# remains valid even when the server auto-restarts during development.
app.secret_key = "a_very_secret_and_static_key_for_development" 

# Create instances of our managers
user_manager = UserManager()
marketplace_manager = MarketplaceManager()
chatbot = Chatbot()

# --- Page Routes (for users to visit) ---

@app.route('/')
def route_index():
    """Serves the login/registration page."""
    if 'username' in session:
        return redirect(url_for('route_marketplace'))
    return render_template('index.html')

@app.route('/marketplace')
def route_marketplace():
    """Serves the main marketplace page."""
    if 'username' not in session:
        return redirect(url_for('route_index'))
    return render_template('marketplace.html')

@app.route('/logout')
def route_logout():
    """Logs the user out and clears the session."""
    session.pop('username', None)
    return redirect(url_for('route_index'))

# --- API Endpoints (for JavaScript to talk to) ---

@app.route('/api/register', methods=['POST'])
def api_register():
    data = request.get_json()
    result = user_manager.register_api(data.get('username'), data.get('password'))
    return jsonify(result)

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json()
    username = user_manager.login_api(data.get('username'), data.get('password'))
    if username:
        session['username'] = username # Create the session here
        return jsonify({"success": True, "message": "Login successful!"})
    else:
        return jsonify({"success": False, "message": "Invalid credentials."})

@app.route('/api/marketplace-data')
def api_get_marketplace_data():
    """A single endpoint to get all necessary data for the marketplace page."""
    if 'username' not in session:
        return jsonify({"success": False, "error": "Unauthorized"}), 401
    
    current_user = session['username']
    all_items = marketplace_manager.get_all_items_api()
    inbox_summary = marketplace_manager.get_inbox_api(current_user)
    
    return jsonify({
        "success": True,
        "username": current_user,
        "listings": all_items,
        "inbox": inbox_summary
    })

@app.route('/api/listings', methods=['POST'])
def api_create_listing():
    if 'username' not in session:
        return jsonify({"success": False, "error": "Unauthorized"}), 401
        
    data = request.get_json()
    owner = session['username']
    result = marketplace_manager.create_listing_api(data, owner)
    return jsonify(result)

# --- AI Image Generation API Endpoint ---
@app.route('/api/generate-image', methods=['POST'])
def api_generate_image():
    if 'username' not in session:
        return jsonify({"success": False, "error": "Unauthorized"}), 401

    if 'image' not in request.files:
        return jsonify({"success": False, "error": "No image file provided."})

    image_file = request.files['image']
    prompt_text = request.form.get('prompt')
    
    result = chatbot.generate_image_api(image_file, prompt_text)
    
    return jsonify(result)


# --- Main Execution ---
if __name__ == '__main__':
    app.run(debug=True)

