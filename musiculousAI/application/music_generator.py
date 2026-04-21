import logging
from domain.music_generation import GenerationRequest, GenerationResult, MusicGenerationStrategy

logger = logging.getLogger(__name__)


class MusicGenerator:
    """
    Application-layer context that executes music generation strategies in order.
    Tries each strategy in sequence; moves to the next if one raises an exception.
    Raises RuntimeError if all strategies fail.
    """

    def __init__(self, strategies: list[MusicGenerationStrategy]):
        if not strategies:
            raise ValueError("At least one strategy must be provided.")
        self.strategies = strategies

    def generate(self, request: GenerationRequest) -> GenerationResult:
        last_error = None
        for strategy in self.strategies:
            strategy_name = type(strategy).__name__
            try:
                logger.info("Attempting music generation with %s", strategy_name)
                result = strategy.generate(request)
                logger.info("Music generation succeeded with %s", strategy_name)
                return result
            except Exception as exc:
                logger.warning(
                    "Strategy %s failed: %s — trying next strategy.",
                    strategy_name,
                    exc,
                )
                last_error = exc

        raise RuntimeError(
            f"All music generation strategies failed. Last error: {last_error}"
        )


def build_default_generator() -> MusicGenerator:
    """
    Factory that wires the strategy chain.

    Controlled by the MUSIC_STRATEGY environment variable (set in .env):
      - "suno"      → SunoStrategy → ReplicateStrategy fallback (default)
      - "replicate" → ReplicateStrategy only
      - "mock"      → MockStrategy (no API key required, for testing)
    """
    import os
    from infrastructure.suno_strategy import SunoStrategy
    from infrastructure.replicate_strategy import ReplicateStrategy
    from infrastructure.mock_strategy import MockStrategy

    strategy = os.getenv("MUSIC_STRATEGY", "suno").lower().strip()

    if strategy == "mock":
        return MusicGenerator([MockStrategy()])
    if strategy == "replicate":
        return MusicGenerator([ReplicateStrategy()])
    # default: suno with replicate fallback
    return MusicGenerator([SunoStrategy(), ReplicateStrategy()])
