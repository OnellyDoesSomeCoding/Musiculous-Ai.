from dataclasses import dataclass


@dataclass
class GenerationResult:
    audio_bytes: bytes
    mime_type: str  # e.g. "audio/mpeg"
    source: str     # which strategy produced this, e.g. "suno", "lyria"
