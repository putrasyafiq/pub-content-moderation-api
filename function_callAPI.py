import requests
import subprocess
import json

def get_gcloud_token():
    """Executes the gcloud command to get an identity token."""
    try:
        # Run the gcloud command and capture its output
        # The command is split into a list for security and compatibility
        token = subprocess.check_output(
            ['gcloud', 'auth', 'print-identity-token'], 
            text=True
        ).strip()
        print("✅ Successfully fetched gcloud token.")
        return token
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print("❌ Error: Failed to get gcloud token.")
        print("   Make sure you have the gcloud CLI installed and are authenticated (`gcloud auth login`).")
        print(f"   Details: {e}")
        return None

def analyze_image(api_url: str, image_url: str):
    """
    Calls the image moderation API with the provided image URL.
    
    Args:
        api_url: The full URL of the Cloud Function endpoint.
        image_url: The public URL of the image to analyze.
    """
    # 1. Get the authentication token
    token = get_gcloud_token()
    if not token:
        return

    # 2. Set up the request headers
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

    # 3. Set up the JSON data payload
    data = {
        'image_url': image_url
    }

    print(f"▶️  Sending request to API for image: {image_url}")

    # 4. Make the POST request
    try:
        response = requests.post(api_url, headers=headers, json=data)
        
        # Raise an exception for bad status codes (4xx or 5xx)
        response.raise_for_status() 

        print("✅ Request successful!")
        # Print the JSON response prettily
        print(json.dumps(response.json(), indent=4))

    except requests.exceptions.HTTPError as e:
        print(f"❌ HTTP Error: {e.response.status_code} {e.response.reason}")
        print(f"   Response Body: {e.response.text}")
    except requests.exceptions.RequestException as e:
        print(f"❌ An unexpected error occurred: {e}")

# --- Main execution block ---
if __name__ == "__main__":
    # Your Cloud Function URL
    API_ENDPOINT_URL = "https://image-content-moderation-api-605626490127.asia-southeast1.run.app"
    
    # The image you want to analyze
    image_to_analyze = "https://media.cnn.com/api/v1/images/stellar/prod/gettyimages-2235891756.jpg"

    analyze_image(API_ENDPOINT_URL, image_to_analyze)