import os
from google import genai
from dotenv import load_dotenv
import json
import time

load_dotenv()

key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=key)


import json

import time

def genResponse(context: str) -> dict:
    """
    Sends a prompt to Gemini and expects structured JSON output.
    Returns a Python dictionary.
    """

    for attempt in range(3):

        try:
            response = client.models.generate_content(
                model="gemini-3-flash-preview",
                contents=context,
                config={
                    "response_mime_type": "application/json"
                }
            )

            if not response.text:
                raise ValueError("Empty response from model")

            parsed = json.loads(response.text)

            return parsed

        except json.JSONDecodeError:
            return {
                "error": "Model did not return valid JSON",
                "raw_output": response.text if "response" in locals() else None
            }

        except Exception as e:
            if attempt < 2:
                time.sleep(2)  
            else:
                return {
                    "error": "LLM call failed: " + str(e)
                }
            

def summerize(context):
    try:
        response = client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=context,
        )

        if not response.text:
            return "Error: Empty response from model" # Return a string since the success is a string

        return response.text

    except Exception as e:
        return f"Error: LLM call failed: {str(e)}"