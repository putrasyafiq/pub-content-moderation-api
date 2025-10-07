# Image Content Moderation API with Gemini & Google Cloud

This project provides a serverless, scalable API endpoint built on Google Cloud Functions that analyzes and moderates image content using Google's Gemini multimodal model.

You can provide an image URL, and the API will return a structured JSON object containing a description of the image, a content category, and safety flags for violence, pornography, and profanity. It also provides a score and explanation for the likelihood of the image being AI-generated.

## Table of Contents

  - [How It Works](https://www.google.com/search?q=%23how-it-works)
  - [API Endpoint](https://www.google.com/search?q=%23api-endpoint)
      - [Request Format](https://www.google.com/search?q=%23request-format)
      - [Success Response](https://www.google.com/search?q=%23success-response)
      - [Error Responses](https://www.google.com/search?q=%23error-responses)
  - [Usage Example](https://www.google.com/search?q=%23usage-example)
  - [Code Breakdown](https://www.google.com/search?q=%23code-breakdown)
      - [Initialization](https://www.google.com/search?q=%23-initialization)
      - [Core Logic: `analyze_image_from_url`](https://www.google.com/search?q=%23%EF%B8%8F-core-logic-analyze_image_from_url)
      - [Entry Point: `content_moderation_entry`](https://www.google.com/search?q=%23-entry-point-content_moderation_entry)
  - [Setup and Deployment](https://www.google.com/search?q=%23setup-and-deployment)
      - [Prerequisites](https://www.google.com/search?q=%23prerequisites)
      - [Configuration](https://www.google.com/search?q=%23configuration)
      - [Deployment](https://www.google.com/search?q=%23deployment)

-----

## How It Works

The architecture is straightforward and leverages Google Cloud's serverless capabilities.

1.  **HTTP Trigger**: The function is triggered by an HTTP POST request sent to its unique Cloud Run URL.
2.  **Authentication**: The endpoint is secured using Google Cloud's Identity and Access Management (IAM). Callers must provide a valid GCP identity token in the `Authorization` header.
3.  **Image Fetching**: The function receives a JSON payload containing an `image_url`. It then sends a GET request to this URL to fetch the raw image data in bytes.
4.  **Gemini API Call**: The image bytes, along with a detailed text prompt, are sent to the Gemini API. The prompt instructs the model to analyze the image and return a JSON object with specific fields. This is a multimodal request, combining both image and text inputs.
5.  **Response Processing**: The function receives the raw text response from the Gemini model. It cleans up any potential markdown formatting (like ` json ...  `) that the model might add.
6.  **JSON Output**: The cleaned text is parsed into a JSON object and returned to the client with a `200 OK` status. The function includes robust error handling to manage issues like invalid URLs, model errors, or malformed responses.

-----

## API Endpoint

**URL**: `https://image-content-moderation-api-605626490127.asia-southeast1.run.app`

**Method**: `POST`

### Request Format

The request must be a JSON object with a single key, `image_url`.

**Headers:**

  * `Content-Type: application/json`
  * `Authorization: Bearer <GCP_IDENTITY_TOKEN>`

**Body:**

```json
{
  "image_url": "https://path.to/your/image.jpg"
}
```

### Success Response

A successful request returns a `200 OK` status code with the analysis in a JSON object.

**Example Response Body:**

```json
{
    "details": "A dramatic photograph of a large, dark smoke cloud rising into the sky from what appears to be a fire on a hillside or in a valley. The smoke is thick and billows upwards, obscuring the horizon. In the foreground, there are trees and some buildings partially visible. The lighting suggests it is daytime, but the scene is somber due to the smoke.",
    "category": "Disaster",
    "isViolence": false,
    "isPornographic": false,
    "isProfanity": false,
    "isLikelyAI_Score": 0.1,
    "isLikelyAI_Explanation": "The image has the characteristics of a real photograph, including natural lighting, complex textures in the smoke and foliage, and slight imperfections that are typical of camera captures. There are no tell-tale signs of AI generation like unnatural shapes or repetitive patterns."
}
```

### Error Responses

The API returns appropriate HTTP status codes and error messages for failed requests.

  * **400 Bad Request**: If the `image_url` is missing or the image cannot be fetched.
    ```json
    {
        "error": "Missing 'image_url' in request body"
    }
    ```
  * **405 Method Not Allowed**: If a method other than `POST` is used.
    ```json
    {
        "error": "Only POST method is accepted"
    }
    ```
  * **500 Internal Server Error**: If the model returns an invalid response or an unexpected error occurs.
    ```json
    {
        "error": "Failed to decode JSON from model response.",
        "raw_response": "This is not valid JSON."
    }
    ```
  * **503 Service Unavailable**: If the GenAI client fails to initialize.
    ```json
    {
       "error": "GenAI client is not initialized. Check environment variables."
    }
    ```

-----

## Usage Example

This example uses `curl` and the `gcloud` CLI to call the deployed function. The `gcloud auth print-identity-token` command generates the required authentication token.

```bash
curl -X POST \
  -H "Authorization: Bearer $(gcloud auth print-identity-token)" \
  -H "Content-Type: application/json" \
  -d '{
      "image_url": "https://media.cnn.com/api/v1/images/stellar/prod/gettyimages-2235891756.jpg"
  }' \
  "https://image-content-moderation-api-605626490127.asia-southeast1.run.app"
```

-----

## Code Breakdown

The function is contained within a single `main.py` file.

### Initialization

```python
# This code runs once when a new function instance is started.
google_cloud_project = 'project-id'
google_cloud_location = 'project-location'
model_name = 'gemini-1.5-flash-latest'

# The GenAI client is initialized globally.
# This makes subsequent invocations on the same instance faster (a "warm" start).
try:
    genai_client = genai.Client(...)
    MODEL_NAME = model_name
except Exception as e:
    print(f"Error initializing GenAI Client: {e}")
```

The script begins by initializing the Gemini client. This is done in the global scope so that it can be reused across multiple invocations of the function without needing to be re-initialized, improving performance.

### ⚙️ Core Logic: `analyze_image_from_url`

This is the helper function that contains the main business logic.

1.  **Fetch Image**: It takes a URL, uses the `requests` library to download the image, and stores it in memory as `image_bytes`.
2.  **Define Instructions**: A detailed prompt string (`instructions`) is created. This is crucial as it tells the Gemini model exactly what to look for and precisely how to format its output as a JSON object.
3.  **Generate Content**: It calls `genai_client.models.generate_content`, passing a list of `contents` that includes both the image bytes and the text instructions. This is the core multi-modal API call.
4.  **Clean and Return**: The function gets the text part of the model's response, cleans any surrounding markdown backticks, and returns the clean string.

### ➡️ Entry Point: `content_moderation_entry`

This function is decorated with `@functions_framework.http`, marking it as the entry point for HTTP triggers.

1.  **Validate Request**: It first checks that the request method is `POST` and that the JSON body contains the `image_url` field.
2.  **Call Logic**: It calls the `analyze_image_from_url` function to perform the analysis.
3.  **Handle Errors**: It uses a `try...except` block to gracefully handle various potential errors during the process, such as `JSONDecodeError` if the model's output is not valid JSON, `ValueError` for bad URLs, or `ConnectionError`.
4.  **Return Response**: On success, it parses the string from the model into a dictionary and returns it as a JSON response with a `200` status code.

-----

## Setup and Deployment

To deploy this function to your own Google Cloud project, follow these steps.

### Prerequisites

1.  A Google Cloud Project with billing enabled.
2.  The `gcloud` CLI installed and authenticated.
3.  The following Google Cloud APIs enabled:
      * Cloud Functions API
      * Cloud Run API
      * Cloud Build API
      * Artifact Registry API
      * Vertex AI API

### Configuration

1.  **`main.py`**: Save the provided Python code as `main.py`.

      * **Best Practice**: Instead of hardcoding credentials like `project-id`, it is recommended to use environment variables during deployment.

2.  **`requirements.txt`**: Create a file named `requirements.txt` in the same directory with the following content:

    ```
    functions-framework==3.*
    requests==2.*
    google-generativeai==0.7.*
    ```

### Deployment

Run the following command from your terminal in the directory containing the files. Replace `<YOUR_PROJECT_ID>` and `<YOUR_REGION>` with your specific GCP project ID and desired region (e.g., `asia-southeast1`).

```bash
gcloud functions deploy image-content-moderation-api \
  --project=<YOUR_PROJECT_ID> \
  --region=<YOUR_REGION> \
  --gen2 \
  --runtime=python312 \
  --source=. \
  --entry-point=content_moderation_entry \
  --trigger-http \
  --allow-unauthenticated
```

**Note**: The `--allow-unauthenticated` flag makes the function publicly accessible, but it's still protected by IAM. For production, you may want to configure stricter invocation policies. After deployment, the command will output the public URL for your function.