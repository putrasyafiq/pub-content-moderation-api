import os
import requests
import json
import functions_framework
from google import genai
from google.genai import types as genai_types

# --- Initialization ---
# This code runs once when a new function instance is started.
# Initializing the client here is more efficient.
google_cloud_project = 'project-id'
google_cloud_location = 'project-location'
google_genai_use_vertexai = 'False'
# It's good practice to use a specific version or 'latest'
model_name = 'gemini-2.5-flash-lite' 

try:
    genai_client = genai.Client(
        project=google_cloud_project,
        location=google_cloud_location,
        vertexai=google_genai_use_vertexai
    )
    MODEL_NAME = model_name
except Exception as e:
    print(f"Error initializing GenAI Client: {e}")
    genai_client = None
    model_name = None

def analyze_image_from_url(image_url: str):
    """Helper function with the core analysis logic."""
    if not genai_client or not model_name:
        raise ConnectionError("GenAI client is not initialized. Check environment variables.")

    # 1. Fetch the image from the provided URL
    try:
        response = requests.get(image_url)
        response.raise_for_status()
        image_bytes = response.content
    except requests.exceptions.RequestException as e:
        raise ValueError(f"Could not fetch the image from the URL. Details: {e}")

    # 2. Prepare instructions for the model
    instructions = f"""
        Return a JSON object with the following fields:
        1. details = A description of the image.
        2. category = A common one word category that would label the image.
        3. isViolence = True if the image contains violence. Else False.
        4. isPornographic = True if the image contains pornographic material. Else False.
        5. isProfanity = True if the image contains any use of profanity language. Else False.
        6. isLikelyAI_Score = A probability score that the image is likely AI generated (0 to 1).
        7. isLikelyAI_Explanation = Explanation for the probability score given.
    """

    # 3. Call the model and return the response text
    if image_bytes:
        
        model_response = genai_client.models.generate_content(
            model=MODEL_NAME, # Use the constant
            contents=[
                genai_types.Part.from_bytes(data=image_bytes, mime_type='image/jpeg'),
                instructions
            ]
        )
        
        # Best Practice: Check if the response was blocked anyway and handle it
        if not model_response.candidates:
             # This can happen if there's a severe policy violation even with BLOCK_NONE
             raise ValueError(f"Response was blocked by API. Feedback: {model_response.prompt_feedback}")
        
        # Best Practice: Clean the output before parsing
        # Models sometimes wrap JSON in markdown backticks
        response_text = model_response.text
        if response_text.startswith("```json"):
            response_text = response_text[7:-3].strip()
        elif response_text.startswith("`"):
             response_text = response_text[1:-1].strip()

        return response_text
    else:
        raise ValueError("Image data could not be processed.")

@functions_framework.http
def content_moderation_entry(request):
    """
    This is the Cloud Function entry point. It's triggered by HTTP requests.
    Args:
        request (flask.Request): The HTTP request object.
    Returns:
        The response text or a JSON-serializable object.
    """
    # 1. Check for the correct request method
    if request.method != "POST":
        return {"error": "Only POST method is accepted"}, 405

    # 2. Get the JSON data from the request
    request_json = request.get_json(silent=True)
    if not request_json or "image_url" not in request_json:
        return {"error": "Missing 'image_url' in request body"}, 400

    image_url = request_json["image_url"]

    # 3. Call the analysis logic and handle potential errors
    try:
        analysis_result_str = analyze_image_from_url(image_url)
        
        # Add a check for an empty string before parsing
        if not analysis_result_str:
            return {"error": "Model returned an empty response, likely due to a severe safety policy violation."}, 500

        analysis_result_json = json.loads(analysis_result_str)
        return analysis_result_json, 200

    except json.JSONDecodeError:
        # Handle cases where the model output isn't valid JSON
        return {"error": "Failed to decode JSON from model response.", "raw_response": analysis_result_str}, 500
    except ValueError as e:
        return {"error": str(e)}, 400
    except ConnectionError as e:
        return {"error": str(e)}, 503  # Service Unavailable
    except Exception as e:
        return {"error": f"An unexpected error occurred: {e}"}, 500