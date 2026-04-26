import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import Http404, FileResponse
from django.core.files.base import ContentFile
import os

from .models import Song, SiteConfiguration
from application.music_generator import build_default_generator
from domain.music_generation import GenerationRequest

logger = logging.getLogger(__name__)


@login_required
def library_home(request):
    # display all songs owned by the current user
    songs = Song.objects.filter(owner=request.user).order_by('-time_created')
    return render(request, 'library/library_home.html', {'songs': songs})


def song_detail(request, song_id):
    # display a single song if it is public OR owned by current user
    song = get_object_or_404(Song, id=song_id)

    # access control >>> public or owned by user
    if not song.is_public and song.owner != request.user:
        raise Http404("Song not found or access denied.")

    return render(request, 'library/song_detail.html', {'song': song})


@login_required
def song_create(request):
    # create a new song or queue generation
    if request.method == 'POST':
        song_name = request.POST.get('song_name', '').strip()
        prompt = request.POST.get('prompt', '').strip()
        description = request.POST.get('description', '').strip()

        # validate required fields
        if not song_name or not prompt:
            return render(request, 'library/song_create.html',
                        {'error': 'Song name and prompt are required.'})

        # check if generation is enabled site-wide
        if not SiteConfiguration.get().generation_enabled:
            return render(request, 'library/song_create.html',
                        {'error': 'Music generation is currently disabled for maintenance. Please try again later.'})

        # create song record in a "generating" state
        song = Song.objects.create(
            owner=request.user,
            song_name=song_name,
            prompt=prompt,
            description=description,
            generation_status='generating',
        )

        # run the strategy chain: Suno >>> Replicate fallback
        try:
            generator = build_default_generator()
            result = generator.generate(GenerationRequest(prompt=prompt, genres=song.genres))
            song.song_file.save(
                f"song_{song.id}.mp3",
                ContentFile(result.audio_bytes),
                save=False,
            )
            song.generation_status = 'ready'
            song.ai_source = result.source
        except Exception as exc:
            logger.error("Music generation failed for song %s: %s", song.id, exc)
            song.generation_status = 'failed'

        song.save()
        return redirect('song_detail', song_id=song.id)

    # GET: show create form
    return render(request, 'library/song_create.html')


@login_required
def song_download(request, song_id):
    song = get_object_or_404(Song, id=song_id)

    if not song.is_public and song.owner != request.user:
        raise Http404("Song not found or access denied.")

    if not song.song_file:
        raise Http404("No audio file available for this song.")

    filename = f"{song.song_name}.mp3"
    response = FileResponse(song.song_file.open('rb'), content_type='audio/mpeg')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


@login_required
def song_edit(request, song_id):
    # Edit song data (title, description) if owner
    song = get_object_or_404(Song, id=song_id)

    # check if owner
    if song.owner != request.user:
        raise Http404("You do not own this song.")

    if request.method == 'POST':
        song.song_name = request.POST.get('song_name', song.song_name).strip()
        song.description = request.POST.get('description', song.description).strip()
        if 'cover_image' in request.FILES:
            song.cover_image = request.FILES['cover_image']
        song.save()

        return redirect('song_detail', song_id=song.id)

    # GET: show edit form with current values
    return render(request, 'library/song_edit.html', {'song': song})


@login_required
def song_delete(request, song_id):
    # delete song if owner + cofirmation prompt
    song = get_object_or_404(Song, id=song_id)

    # check if owner
    if song.owner != request.user:
        raise Http404("You do not own this song.")

    if request.method == 'POST':
        song.delete()
        return redirect('library_home')

    # GET: show confirmation page
    return render(request, 'library/song_delete.html', {'song': song})


@login_required
def song_toggle_public(request, song_id):
    # toggle song visibility (public/private) if owner
    song = get_object_or_404(Song, id=song_id)

    # ownership check
    if song.owner != request.user:
        raise Http404("You do not own this song.")

    if request.method == 'POST':
        song.is_public = not song.is_public
        song.save()
        return redirect('song_detail', song_id=song.id)

    # GET: show confirmation page
    return render(request, 'library/song_toggle_public.html', {'song': song})
