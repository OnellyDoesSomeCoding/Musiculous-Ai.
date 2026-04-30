from abc import ABC, abstractmethod

from .generation_request import GenerationRequest
from .generation_result import GenerationResult


class MusicGenerationStrategy(ABC):
    """Domain interface for any music generation backend."""

    @abstractmethod
    def generate(self, request: GenerationRequest) -> GenerationResult:
        """
        Generate audio from the given request.
        Raises an exception on failure so the MusicGenerator can try the next strategy.
        """
        ...
