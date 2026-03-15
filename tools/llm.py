import os
import json
import time
from dotenv import load_dotenv

load_dotenv()

# ─────────────────────────────────────────────────────────────────────────────
# LLM PROVIDER SELECTION
# Set LLM_PROVIDER in your .env to switch between backends:
#   LLM_PROVIDER=openai   (default) → uses the free GPT-OSS 120B server
#   LLM_PROVIDER=gemini             → uses your Gemini API key
# ─────────────────────────────────────────────────────────────────────────────
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai").lower()


# ── OpenAI (GPT-OSS free server) ─────────────────────────────────────────────
from openai import OpenAI

openai_client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY", "test"),
    base_url="https://vjioo4r1vyvcozuj.us-east-2.aws.endpoints.huggingface.cloud/v1",
)
OPENAI_MODEL = "openai/gpt-oss-120b"


# ── Gemini (kept available, unused by default) ────────────────────────────────
# from google import genai as _genai
# _gemini_client = _genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
# GEMINI_MODEL = "gemini-2.0-flash"


# ─────────────────────────────────────────────────────────────────────────────
# Internal helpers
# ─────────────────────────────────────────────────────────────────────────────

def _call_openai_json(prompt: str) -> dict:
    """Ask OpenAI GPT-OSS to respond with a JSON object."""
    for attempt in range(3):
        try:
            resp = openai_client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a helpful AI agent. "
                            "Always respond with valid JSON only — no markdown, no extra text."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=2048,
                response_format={"type": "json_object"},   # structured output
            )
            raw = resp.choices[0].message.content or ""
            return json.loads(raw)
        except json.JSONDecodeError:
            return {"error": "Model did not return valid JSON", "raw_output": raw}
        except Exception as e:
            if attempt < 2:
                time.sleep(2)
            else:
                return {"error": f"LLM call failed: {str(e)}"}


def _call_openai_text(prompt: str) -> str:
    """Ask OpenAI GPT-OSS for a plain-text response."""
    try:
        resp = openai_client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "You are a helpful assistant. Respond in clear, concise plain text."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=1024,
        )
        return resp.choices[0].message.content or ""
    except Exception as e:
        return f"Error: LLM call failed: {str(e)}"


# ─── Gemini equivalents (kept for reference, unused) ──────────────────────────
# def _call_gemini_json(prompt):
#     for attempt in range(3):
#         try:
#             response = _gemini_client.models.generate_content(
#                 model=GEMINI_MODEL, contents=prompt,
#                 config={"response_mime_type": "application/json"})
#             if not response.text:
#                 raise ValueError("Empty response")
#             return json.loads(response.text)
#         except json.JSONDecodeError:
#             return {"error": "Model did not return valid JSON"}
#         except Exception as e:
#             if attempt < 2: time.sleep(2)
#             else: return {"error": "LLM call failed: " + str(e)}
#
# def _call_gemini_text(prompt):
#     try:
#         response = _gemini_client.models.generate_content(model=GEMINI_MODEL, contents=prompt)
#         return response.text or "Error: Empty response"
#     except Exception as e:
#         return f"Error: LLM call failed: {str(e)}"


# ─────────────────────────────────────────────────────────────────────────────
# Public API  (same function signatures as before — nothing else needs to change)
# ─────────────────────────────────────────────────────────────────────────────

def genResponse(context: str) -> dict:
    """
    Sends a prompt to the configured LLM and expects structured JSON output.
    Returns a Python dictionary.
    Provider is selected via LLM_PROVIDER env variable ('openai' or 'gemini').
    """
    if LLM_PROVIDER == "gemini":
        # Uncomment the Gemini helpers above and swap this call if desired:
        # return _call_gemini_json(context)
        return {"error": "Gemini provider selected but not enabled. Set LLM_PROVIDER=openai or uncomment the Gemini code in llm.py."}
    return _call_openai_json(context)


def summerize(context) -> str:
    """
    Summarises the given text (list of chunks or a single string).
    Returns a plain-text summary string.
    """
    if isinstance(context, list):
        text = "\n\n".join(str(c) for c in context)
    else:
        text = str(context)

    prompt = f"Please summarise the following content clearly and concisely:\n\n{text}"

    if LLM_PROVIDER == "gemini":
        # return _call_gemini_text(prompt)
        return "Error: Gemini provider selected but not enabled. Set LLM_PROVIDER=openai."
    return _call_openai_text(prompt)