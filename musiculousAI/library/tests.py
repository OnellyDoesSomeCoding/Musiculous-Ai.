from unittest.mock import Mock, patch
import tempfile

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from domain.music_generation import GenerationRequest
from library.models import Song
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


@override_settings(MEDIA_ROOT=tempfile.gettempdir())
class SongSharingTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.owner = user_model.objects.create_user(
            username="owner",
            password="test-pass-123",
        )
        self.song = Song.objects.create(
            owner=self.owner,
            song_name="Shared Track",
            prompt="Bright upbeat groove",
            generation_status="ready",
        )
        self.song.song_file.save("shared.mp3", ContentFile(b"ID3test-audio"), save=True)

    def test_song_share_view_sets_public_and_generates_token(self):
        self.client.login(username="owner", password="test-pass-123")

        response = self.client.get(reverse("song_share", args=[self.song.id]))
        self.song.refresh_from_db()

        self.assertEqual(response.status_code, 200)
        self.assertTrue(self.song.is_public)
        self.assertIsNotNone(self.song.share_token)

    def test_guest_can_open_public_shared_link(self):
        self.song.is_public = True
        self.song.share_token = "11111111-1111-1111-1111-111111111111"
        self.song.save(update_fields=["is_public", "share_token"])

        response = self.client.get(reverse("song_shared_detail", args=[self.song.share_token]))

        self.assertEqual(response.status_code, 200)

    def test_private_song_shared_link_returns_404(self):
        self.song.is_public = False
        self.song.share_token = "22222222-2222-2222-2222-222222222222"
        self.song.save(update_fields=["is_public", "share_token"])

        response = self.client.get(reverse("song_shared_detail", args=[self.song.share_token]))

        self.assertEqual(response.status_code, 404)

    def test_guest_can_download_public_shared_song(self):
        self.song.is_public = True
        self.song.share_token = "33333333-3333-3333-3333-333333333333"
        self.song.save(update_fields=["is_public", "share_token"])

        response = self.client.get(reverse("song_shared_download", args=[self.song.share_token]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "audio/mpeg")
