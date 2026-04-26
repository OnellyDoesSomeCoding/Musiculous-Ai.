import time
import requests
from django.conf import settings

from domain.music_generation import GenerationRequest, GenerationResult, MusicGenerationStrategy


class SunoStrategy(MusicGenerationStrategy):
    """
    Calls the sunoapi.org API to generate music from a text prompt.

    Required settings (settings.py):
        SUNO_API_KEY  - your Suno API key
        SUNO_API_URL  - base URL, defaults to https://api.sunoapi.org/api/v1
        SUNO_MODEL    - optional model name, defaults to V4_5ALL
        SUNO_CALLBACK_URL - optional callback URL, defaults to https://example.com/callback
    """

    BASE_URL = getattr(settings, "SUNO_API_URL", "https://api.sunoapi.org/api/v1")
    POLL_INTERVAL_SECONDS = 10
    MAX_POLL_ATTEMPTS = 60  # 10 minutes / 10s

    def _build_headers(self) -> dict:
        api_key = getattr(settings, "SUNO_API_KEY", None)
        if not api_key:
            raise RuntimeError("SUNO_API_KEY is not configured.")
        return {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

    def create_task(self, request: GenerationRequest) -> str:
        """Submit a generation job to Suno and return its taskId."""
        model = getattr(settings, "SUNO_MODEL", "V4_5ALL")
        callback_url = getattr(
            settings,
            "SUNO_CALLBACK_URL",
            "https://example.com/callback",
        )

        payload = {
            "prompt": request.prompt,
            "customMode": False,
            "instrumental": False,
            "model": model,
            "callBackUrl": callback_url,
        }

        response = requests.post(
            f"{self.BASE_URL}/generate",
            json=payload,
            headers=self._build_headers(),
            timeout=30,
        )
        response.raise_for_status()
        job_data = response.json()
        if job_data.get("code") != 200:
            raise RuntimeError(f"Suno generation failed: {job_data.get('msg', 'Unknown error')}")

        task_id = job_data.get("data", {}).get("taskId")
        if not task_id:
            raise RuntimeError("Suno did not return a taskId.")
        return task_id

    def get_task_details(self, task_id: str) -> dict:
        """Fetch Suno record details for a previously created taskId."""
        response = requests.get(
            f"{self.BASE_URL}/generate/record-info",
            params={"taskId": task_id},
            headers=self._build_headers(),
            timeout=30,
        )
        response.raise_for_status()
        payload = response.json()
        if payload.get("code") != 200:
            raise RuntimeError(
                f"Suno status check failed: {payload.get('msg', 'Unknown error')}"
            )
        return payload.get("data") or {}

    def get_task_status(self, task_id: str) -> str:
        """Return current task status (e.g. PENDING/RUNNING/FAILED/SUCCESS)."""
        details = self.get_task_details(task_id)
        return (details.get("status") or "").upper()

    def generate(self, request: GenerationRequest) -> GenerationResult:
        task_id = self.create_task(request)
        audio_url = self._poll_for_audio(task_id)

        audio_response = requests.get(audio_url, timeout=60)
        audio_response.raise_for_status()

        return GenerationResult(
            audio_bytes=audio_response.content,
            mime_type="audio/mpeg",
            source="suno",
        )

    def _poll_for_audio(self, task_id: str) -> str:
        for _ in range(self.MAX_POLL_ATTEMPTS):
            time.sleep(self.POLL_INTERVAL_SECONDS)
            record = self.get_task_details(task_id)
            status = (record.get("status") or "").upper()

            if status == "FAILED":
                err = record.get("errorMessage") or "unknown failure"
                raise RuntimeError(f"Suno generation failed: {err}")

            response_data = record.get("response") or {}
            tracks = response_data.get("sunoData") or []

            for track in tracks:
                track = track or {}
                audio_url = track.get("audioUrl") or track.get("sourceAudioUrl")
                if audio_url:
                    return audio_url

        raise TimeoutError("Suno generation timed out before any audio URL became available.")
