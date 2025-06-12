# app/adapters/llm_groq.py
import requests
import os
import logging # Import logging to use Flask's app.logger

# Get the logger for this module (Flask will configure it via extensions.py)
logger = logging.getLogger(__name__)

def generate_gpt_reply(message: str) -> str:
    """
    Makes an API call to Groq to generate a chat reply based on the user's message.
    Assumes GROQ_API_KEY is set in your environment variables (.env file).

    Args:
        message (str): The user's input message to send to the LLM.

    Returns:
        str: The generated reply from the LLM, or an error message if the call fails.
    """
    try:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            logger.error("GROQ_API_KEY environment variable not found. Cannot make API call.")
            return "Error: API key not configured. Please contact support."

        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            # Ensure this model name is correct and available for Groq.
            # 'llama-4-scout-17b-16e-instruct' might be an internal or custom model.
            # Common Groq models are like 'llama3-8b-8192', 'llama3-70b-8192', etc.
            "model": "meta-llama/llama-4-scout-17b-16e-instruct",
            "messages": [
                {
                    "role": "system",
                    "content": "You are a helpful insurance quote assistant. Ask for missing information if needed."
                },
                {
                    "role": "user",
                    "content": message.strip()
                }
            ],
            "temperature": 0.7
        }

        logger.info(f"Sending request to Groq API for message: '{message[:50]}...'")
        response = requests.post(url, headers=headers, json=payload, timeout=30) # Added a timeout

        if not response.ok:
            # Log the full response text for debugging non-2xx status codes
            logger.error(f"Groq API error: {response.status_code} - {response.text}")
            # Raise an HTTPError so the next except block can catch it
            response.raise_for_status()

        # Extract and return the content
        reply_content = response.json()['choices'][0]['message']['content'].strip()
        logger.info("Successfully received reply from Groq API.")
        return reply_content

    except requests.exceptions.Timeout:
        logger.error("Groq API request timed out.")
        return "Error: The AI did not respond in time. Please try again later."
    except requests.exceptions.ConnectionError as conn_e:
        logger.error(f"Groq API connection error: {conn_e}")
        return "Error: Could not connect to the AI service. Please check your internet connection."
    except requests.exceptions.RequestException as req_e:
        # Catches other requests-related errors (e.g., HTTPError from raise_for_status)
        logger.error(f"Groq API request failed: {req_e}. Response: {response.text if 'response' in locals() else 'N/A'}")
        return f"Error communicating with the AI: {str(req_e)}"
    except KeyError as key_e:
        # Catches if the expected JSON structure (choices[0].message.content) is missing
        logger.error(f"Error parsing Groq response (missing key: {key_e}). Full response: {response.json() if 'response' in locals() else 'No valid JSON response.'}")
        return "Error: Received an unexpected response format from the AI."
    except Exception as e:
        # Catch any other unexpected errors
        logger.exception("An unexpected error occurred during Groq API call.") # logs full traceback
        return f"An unexpected error occurred: {str(e)}"