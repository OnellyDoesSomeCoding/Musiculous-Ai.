from domain.music_generation import GenerationRequest, GenerationResult, MusicGenerationStrategy


class MockStrategy(MusicGenerationStrategy):
    """Local deterministic strategy used for testing and demos without API calls."""

    def generate(self, request: GenerationRequest) -> GenerationResult:
        # Minimal deterministic bytes that are enough for storage/download flows.
        fake_mp3 = b"ID3\x04\x00\x00\x00\x00\x00\x21MOCK-AUDIO:" + request.prompt.encode("utf-8")
        return GenerationResult(
            audio_bytes=fake_mp3,
            mime_type="audio/mpeg",
            source="mock",
        )