import time
import requests
from django.conf import settings

from domain.music_generation import GenerationRequest, GenerationResult, MusicGenerationStrategy


class ReplicateStrategy(MusicGenerationStrategy):
    """
    Calls Replicate's MusicGen model (meta/musicgen) to generate music from a text prompt.

    Required settings:
        REPLICATE_API_KEY            - your Replicate API token
        REPLICATE_MUSICGEN_VERSION   - optional model version hash; uses the deployment
                                       endpoint (always latest) when omitted
    """

    POLL_INTERVAL_SECONDS = 5
    MAX_POLL_ATTEMPTS = 120  # 10 minutes / 5s

    def generate(self, request: GenerationRequest) -> GenerationResult:
        api_key = getattr(settings, "REPLICATE_API_KEY", None)
        if not api_key:
            raise RuntimeError("REPLICATE_API_KEY is not configured.")

        headers = {
            "Authorization": f"Token {api_key}",
            "Content-Type": "application/json",
        }

        prompt_text = request.prompt
        if request.genres:
            prompt_text = f"{request.genres} music. {prompt_text}"

        try:
            duration = int(request.duration_in_seconds)
        except (TypeError, ValueError):
            duration = 30
        duration = max(5, min(duration, 180))

        payload = {
            "input": {
                "prompt": prompt_text,
                "duration": duration,
                "output_format": "mp3",
            }
        }

        version = getattr(settings, "REPLICATE_MUSICGEN_VERSION", None)
        if version:
            url = "https://api.replicate.com/v1/predictions"
            payload["version"] = version
        else:
            url = "https://api.replicate.com/v1/models/meta/musicgen/predictions"

        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        prediction = response.json()

        prediction_id = prediction.get("id")
        if not prediction_id:
            raise RuntimeError("Replicate did not return a prediction ID.")

        audio_url = self._poll_for_result(prediction_id, headers)

        audio_response = requests.get(audio_url, timeout=120)
        audio_response.raise_for_status()

        return GenerationResult(
            audio_bytes=audio_response.content,
            mime_type="audio/mpeg",
            source="replicate",
        )

    def _poll_for_result(self, prediction_id: str, headers: dict) -> str:
        poll_url = f"https://api.replicate.com/v1/predictions/{prediction_id}"
        for _ in range(self.MAX_POLL_ATTEMPTS):
            time.sleep(self.POLL_INTERVAL_SECONDS)
            response = requests.get(poll_url, headers=headers, timeout=30)
            response.raise_for_status()
            data = response.json()

            status = data.get("status", "")

            if status == "failed":
                error = data.get("error") or "unknown failure"
                raise RuntimeError(f"Replicate generation failed: {error}")

            if status == "succeeded":
                output = data.get("output")
                if isinstance(output, list) and output:
                    return output[0]
                if isinstance(output, str):
                    return output
                raise RuntimeError("Replicate succeeded but returned no audio URL.")

        raise TimeoutError("Replicate generation timed out after 10 minutes.")
