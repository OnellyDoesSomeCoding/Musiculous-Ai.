# Musiculous AI

Musiculous AI is a Django web application for AI-powered music generation. Authenticated users describe music via text prompts, generate audio clips using external AI APIs, manage a personal library, and share public songs with guests.

---

## Architecture: Strategy Pattern

Music generation is implemented using the **Strategy design pattern** following Domain-Driven Design (DDD) layering:

```
domain/music_generation.py        # MusicGenerationStrategy ABC + data classes
infrastructure/suno_strategy.py   # Concrete: SunoStrategy
infrastructure/replicate_strategy.py  # Concrete: ReplicateStrategy
infrastructure/mock_strategy.py   # Concrete: MockStrategy (no API key needed)
application/music_generator.py    # MusicGenerator context + factory
```

### Strategy Interface

`MusicGenerationStrategy` is defined as a Python Abstract Base Class (ABC) in `domain/music_generation.py`:

```python
from abc import ABC, abstractmethod

class MusicGenerationStrategy(ABC):
    @abstractmethod
    def generate(self, request: GenerationRequest) -> GenerationResult:
        ...
```

All concrete strategies (`SunoStrategy`, `ReplicateStrategy`, `MockStrategy`) inherit from this interface and implement `generate()`.

### How the Strategy Is Selected

The active strategy chain is assembled in `application/music_generator.py` inside `build_default_generator()`:

```python
def build_default_generator() -> MusicGenerator:
    from infrastructure.suno_strategy import SunoStrategy
    from infrastructure.replicate_strategy import ReplicateStrategy
    return MusicGenerator([SunoStrategy(), ReplicateStrategy()])
```

`MusicGenerator` tries each strategy in order — if the first raises an exception, it falls back to the next. To switch strategies, edit this function. Examples:

**Use Suno only:**
```python
return MusicGenerator([SunoStrategy()])
```

**Use Mock (no API key required, for testing):**
```python
from infrastructure.mock_strategy import MockStrategy
return MusicGenerator([MockStrategy()])
```

**Use Replicate as primary, Suno as fallback:**
```python
return MusicGenerator([ReplicateStrategy(), SunoStrategy()])
```

### Externalised Strategy Selection via Environment Variable

The strategy used can also be controlled without changing code by setting `MUSIC_STRATEGY` in the `.env` file:

```
MUSIC_STRATEGY=suno        # uses SunoStrategy → ReplicateStrategy fallback (default)
MUSIC_STRATEGY=replicate   # uses ReplicateStrategy only
MUSIC_STRATEGY=mock        # uses MockStrategy (no API key required)
```

The factory in `build_default_generator()` reads this variable and selects accordingly.

---

## Setting Up API Keys

All secrets are stored in a `.env` file at the project root (next to `README.md`). Copy `.env.example` to `.env` and fill in your values.

### Suno API Key

1. Sign up at [sunoapi.org](https://sunoapi.org)
2. Copy your API key from the dashboard
3. In `.env`, set:

```
SUNO_API_KEY=your_key_here
SUNO_API_URL=https://api.sunoapi.org/api/v1
SUNO_MODEL=V4_5ALL
```

### Replicate API Key (fallback)

1. Sign up at [replicate.com](https://replicate.com)
2. Go to Account → API Tokens and copy your token
3. Add billing (required for MusicGen model)
4. In `.env`, set:

```
REPLICATE_API_KEY=r8_your_token_here
REPLICATE_MUSICGEN_VERSION=671ac645ce5e552cc63a54a2bbff63fcf798043055d2dac5fc9e36a837eedcfb
```

### No API Key (Mock Strategy)

To run generation without any API key (returns a silent WAV instantly):

1. Open `musiculousAI/application/music_generator.py`
2. Change `build_default_generator()` to use `MockStrategy` (see above)

---

## Features

- User authentication (sign up, log in, log out) with email/password
- AI music generation via Suno (primary) and Replicate/MusicGen (fallback)
- Mock strategy for offline testing with no API key
- Personal music library with cover art grid view
- Song detail page with HTML5 audio player
- MP3 download
- Public/private song visibility toggle
- Cover image upload per song
- Django admin: manage songs, users, and site-wide generation toggle
- AI source tag (Suno / Replicate / Mock) displayed per song

---

## Tech Stack

- Python 3.10+
- Django 6.0.3
- SQLite (development)
- HTML/CSS templates (dark-themed)
- `requests` for external API calls

---

## Project Structure

```text
musiculous/
  .env                  # secrets (gitignored)
  .env.example          # template for secrets
  README.md
  requirements.txt
  musiculousAI/
    manage.py
    db.sqlite3
    musiculousAI/       # project settings and root URLs
    domain/             # DDD domain layer: strategy interface, data classes
    infrastructure/     # DDD infrastructure layer: Suno, Replicate, Mock strategies
    application/        # DDD application layer: MusicGenerator context + factory
    login/              # authentication app
    library/            # song and library app
```

---

## Local Setup (Windows)

1. Clone this repository.
2. Navigate to the project root (`musiculous/`).
3. Create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

4. Install dependencies:

```powershell
pip install -r requirements.txt
```

5. Copy `.env.example` to `.env` and fill in your API keys:

```powershell
copy .env.example .env
```

6. Navigate into the Django project and run migrations:

```powershell
cd musiculousAI
python manage.py migrate
```

7. Create an admin account:

```powershell
python manage.py createsuperuser
```

8. Start the development server:

```powershell
python manage.py runserver
```

9. Open in browser:

```
http://127.0.0.1:8000/
```

---

## Main Routes

| URL | Description |
|-----|-------------|
| `/` | Public landing page |
| `/auth/signup/` | Register a new account |
| `/auth/login/` | Log in |
| `/auth/logout/` | Log out |
| `/library/` | Authenticated user library |
| `/library/create/` | Generate a new song |
| `/library/song/<id>/` | Song detail + audio player |
| `/library/song/<id>/download/` | Download MP3 |
| `/admin/` | Django admin panel |

---

## Security Notes

- All secrets loaded from `.env` via `_load_local_env()` — never hardcoded.
- Password validation uses Django built-in validators.
- Private song actions enforce ownership checks in views.
- Authentication required for all library write operations.
- Admin-only generation kill switch via `SiteConfiguration` model.
