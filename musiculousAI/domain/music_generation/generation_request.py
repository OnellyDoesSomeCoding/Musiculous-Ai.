from dataclasses import dataclass


@dataclass
class GenerationRequest:
    prompt: str
    genres: str = ""
    duration_in_seconds: int = 30
