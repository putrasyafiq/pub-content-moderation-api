from google import genai
from dotenv import load_dotenv
from google.genai import types as genai_types
import os
import requests

load_dotenv()

google_cloud_project = os.getenv("GOOGLE_CLOUD_PROJECT")
google_cloud_location = os.getenv("GOOGLE_CLOUD_LOCATION")
google_genai_use_vertexai = os.getenv("GOOGLE_GENAI_USE_VERTEXAI")
model_name = os.getenv("MODEL_NAME")

def ContentModerationAnalysis():
    
    genai_client = genai.Client(project=google_cloud_project, location=google_cloud_location, vertexai=google_genai_use_vertexai)

    age_limit = 18

    image_url = "https://storage.googleapis.com/putra_image_content_moderation_1/protests.jpg"
    image_bytes = None

    try:
        # Send an HTTP GET request to the URL
        response = requests.get(image_url)
        
        # Raise an exception if the request was unsuccessful (e.g., 404 Not Found)
        response.raise_for_status() 
        
        # Get the raw binary content of the image
        image_bytes = response.content

    except requests.exceptions.RequestException as e:
        print(f"Error fetching the image from URL: {e}")

    instructions = f"""

        Return a JSON object with the following fields:
        1. details = A description of the image.
        2. category = A common one word category that would label the image.
        3. isViolence = True if the image contains violence that is inappropriate for persons below {age_limit} years old. Else False.
        4. isPornographic = True if the image contains pornographic material. Else False.
        5. isProfanity = True if the image contains any use of profanity language. Else False.
        6. isLikelyAI_Score = A probability score that the image is likely AI generated (0 to 1).
        7. isLikelyAI_Explanation = Explanation for the probability score given.

    """

    # try:
    #     with open(image_path, "rb") as image_file:
    #         image_bytes = image_file.read()
    # except FileNotFoundError:
    #     print(f"Error: The file was not found at {image_path}")
    #     image_bytes = None

    if image_bytes:
        response = genai_client.models.generate_content(
            model = model_name,
            contents = [
                genai_types.Part.from_bytes(
                    data=image_bytes,
                    mime_type='image/jpeg'
                ),
                instructions
            ]
        )
        print(response.text)
        return response.text
    else:
        print("The image data is empty.")
        return None

ContentModerationAnalysis()