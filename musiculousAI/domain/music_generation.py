from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class GenerationRequest:
    prompt: str
    genres: str = ""
    duration_in_seconds: int = 30


@dataclass
class GenerationResult:
    audio_bytes: bytes
    mime_type: str  # e.g. "audio/mpeg"
    source: str     # which strategy produced this, e.g. "suno", "lyria"


class MusicGenerationStrategy(ABC):
    """Domain interface for any music generation backend."""

    @abstractmethod
    def generate(self, request: GenerationRequest) -> GenerationResult:
        """
        Generate audio from the given request.
        Raises an exception on failure so the MusicGenerator can try the next strategy.
        """
        ...
