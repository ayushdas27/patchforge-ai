from typing import Optional, Dict, Any
from openai import OpenAI
from app.config import settings
from app.security.redaction import redact_secrets, mask_api_key

class NebiusClient:
    """Wrapper around OpenAI SDK targeting Nebius Token Factory with safety controls."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
    ):
        self.base_url = base_url if base_url is not None else settings.nebius_base_url
        self.api_key = api_key if api_key is not None else settings.nebius_api_key
        self.model = model if model is not None else settings.nebius_model

    def get_client(self) -> OpenAI:
        if not self.api_key or not self.api_key.strip():
            raise ValueError(
                "NEBIUS_API_KEY is not configured. Please add NEBIUS_API_KEY to your local .env file."
            )
        return OpenAI(
            base_url=self.base_url,
            api_key=self.api_key
        )

    def test_connection(self) -> Dict[str, Any]:
        """Performs a minimal health check / test call against Nebius Token Factory."""
        if not self.api_key or not self.api_key.strip():
            return {
                "success": False,
                "error": "Missing NEBIUS_API_KEY in local .env file.",
                "hint": "Set NEBIUS_API_KEY in your local .env file. Never commit it to Git.",
                "model": self.model,
                "base_url": self.base_url,
                "key_status": "Missing"
            }

        try:
            client = self.get_client()
            # Send minimal test request to verify authentication and model availability
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a test ping agent."},
                    {"role": "user", "content": "ping"}
                ],
                max_tokens=5,
                temperature=0.0
            )
            content = response.choices[0].message.content or ""
            return {
                "success": True,
                "message": "Successfully connected to Nebius Token Factory.",
                "model": self.model,
                "base_url": self.base_url,
                "key_status": f"Configured ({mask_api_key(self.api_key)})",
                "response_sample": content.strip()
            }
        except Exception as e:
            raw_err = str(e)
            safe_err = redact_secrets(raw_err)
            hint = "Check your NEBIUS_API_KEY and verify if your account has access to the model."
            if "model_not_found" in safe_err.lower() or "404" in safe_err:
                hint = f"Model '{self.model}' is not available or not permitted. Try configuring an alternative Nemotron model ID."
            elif "authentication" in safe_err.lower() or "401" in safe_err:
                hint = "Authentication failed. Check if NEBIUS_API_KEY in .env is valid."
            elif "rate_limit" in safe_err.lower() or "429" in safe_err:
                hint = "Rate limit or credit quota reached on Nebius Token Factory."

            return {
                "success": False,
                "error": safe_err,
                "hint": hint,
                "model": self.model,
                "base_url": self.base_url,
                "key_status": f"Configured ({mask_api_key(self.api_key)})"
            }

nebius_client = NebiusClient()
