from unittest.mock import Mock, patch

from django.test import SimpleTestCase, override_settings

from domain.music_generation import GenerationRequest
from infrastructure.mock_strategy import MockStrategy
from infrastructure.suno_strategy import SunoStrategy


class MockStrategyTests(SimpleTestCase):
    def test_mock_strategy_returns_audio_result(self):
        strategy = MockStrategy()

        result = strategy.generate(GenerationRequest(prompt="Lo-fi study beats"))

        self.assertEqual(result.source, "mock")
        self.assertEqual(result.mime_type, "audio/mpeg")
        self.assertTrue(result.audio_bytes)
        self.assertIn(b"MOCK-AUDIO", result.audio_bytes)


@override_settings(
    SUNO_API_KEY="test-key",
    SUNO_API_URL="https://api.sunoapi.org/api/v1",
    SUNO_MODEL="V4_5ALL",
    SUNO_CALLBACK_URL="https://example.com/callback",
)
class SunoStrategyTaskApiTests(SimpleTestCase):
    @patch("infrastructure.suno_strategy.requests.post")
    def test_create_task_returns_task_id(self, post_mock):
        post_response = Mock()
        post_response.json.return_value = {
            "code": 200,
            "data": {"taskId": "task_123"},
        }
        post_response.raise_for_status.return_value = None
        post_mock.return_value = post_response

        strategy = SunoStrategy()
        task_id = strategy.create_task(GenerationRequest(prompt="Cinematic trailer"))

        self.assertEqual(task_id, "task_123")
        post_mock.assert_called_once()

    @patch("infrastructure.suno_strategy.requests.get")
    def test_get_task_details_returns_status_payload(self, get_mock):
        get_response = Mock()
        get_response.json.return_value = {
            "code": 200,
            "data": {
                "status": "RUNNING",
                "response": {"sunoData": []},
            },
        }
        get_response.raise_for_status.return_value = None
        get_mock.return_value = get_response

        strategy = SunoStrategy()
        details = strategy.get_task_details("task_123")

        self.assertEqual(details.get("status"), "RUNNING")
        get_mock.assert_called_once()

    @patch("infrastructure.suno_strategy.requests.get")
    def test_get_task_status_returns_uppercase(self, get_mock):
        get_response = Mock()
        get_response.json.return_value = {
            "code": 200,
            "data": {"status": "succeeded"},
        }
        get_response.raise_for_status.return_value = None
        get_mock.return_value = get_response

        strategy = SunoStrategy()
        status = strategy.get_task_status("task_abc")

        self.assertEqual(status, "SUCCEEDED")
