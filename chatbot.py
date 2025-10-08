import os
from PIL import Image
from io import BytesIO
import google.generativeai as genai
import base64

class Chatbot:
    """
    Manages the connection to the Gemini API for AI-powered image generation.
    Handles API configuration, safety checks, and processes image requests.
    """
    def __init__(self):
        """
        Initializes the Chatbot and configures the Gemini API.
        """
        self.image_gen_model = None
        try:
            # This will use the environment variable you set up previously.
            GEMINI_API_KEY = os.environ.get('GOOGLE_API_KEY')
            if not GEMINI_API_KEY:
                raise ValueError("GOOGLE_API_KEY environment variable not found.")
            
            genai.configure(api_key=GEMINI_API_KEY)
            
            # Initialize the model for image generation
            self.image_gen_model = genai.GenerativeModel(model_name='gemini-1.5-flash')
            print("Chatbot initialized: Gemini API configured successfully.")

        except Exception as e:
            print(f"FATAL ERROR: Could not configure Gemini API: {e}")

    def _prepare_content(self, pil_image, prompt_text):
        """
        Prepares the content for the Gemini model. The API itself has built-in safety features.
        """
        if self.image_gen_model is None:
            return {"success": False, "error": "Gemini model is not initialized."}
            
        return {
            "success": True, 
            "content": [prompt_text, pil_image]
        }

    def generate_image_api(self, image_file_storage, prompt_text):
        """
        Main API method to handle image generation for the web server.
        Takes a FileStorage object and a prompt, returns a dictionary with base64 image or an error.
        """
        if not hasattr(image_file_storage, 'read'):
            error_msg = f"Developer Error: Expected a file object, but received a {type(image_file_storage).__name__}."
            print(error_msg)
            return {"success": False, "error": error_msg}

        if self.image_gen_model is None:
            return {"success": False, "error": "Cannot generate image, Gemini model not configured."}

        try:
            image_bytes = image_file_storage.read()
            image = Image.open(BytesIO(image_bytes))
        except Exception as e:
            return {"success": False, "error": f"Invalid image file: {e}"}

        # 1. Prepare content
        content_result = self._prepare_content(image, prompt_text)
        if not content_result["success"]:
            return content_result 

        # 2. Generate the image
        try:
            print("Generating image with Gemini...")
            response = self.image_gen_model.generate_content(
                contents=content_result["content"],
            )
            
            # --- NEW, MORE DETAILED SAFETY CHECK ---
            # Check if the API itself blocked the prompt without throwing an error.
            if response.prompt_feedback.block_reason:
                reason = response.prompt_feedback.block_reason.name
                print(f"Request blocked by API for safety reasons: {reason}")
                return {"success": False, "error": f"Image generation blocked due to: {reason}. Please modify your prompt or image."}

            if not response.candidates or not response.candidates[0].content.parts:
                 raise ValueError("Invalid response structure from Gemini API.")

            generated_image_bytes = response.candidates[0].content.parts[0].inline_data.data
            generated_image_base64 = base64.b64encode(generated_image_bytes).decode('utf-8')
            
            print("Image generation successful.")
            return {"success": True, "image_base64": generated_image_base64}

        except Exception as e:
            # --- NEW, MORE DETAILED ERROR LOGGING ---
            # This will now print the specific error from Google to your terminal.
            print(f"!!! An error occurred during Gemini API call: {e}")
            
            error_message = str(e).upper()
            user_friendly_error = "Could not generate image due to an API error."

            # Provide a more specific user-facing message if it's clearly a safety issue.
            if "SAFETY" in error_message:
                user_friendly_error = "Image generation failed because the prompt or image was blocked by safety filters. Try being more specific or using a different image."
            
            return {"success": False, "error": user_friendly_error}

