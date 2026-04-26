import logging
import uuid
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import Http404, FileResponse
from django.core.files.base import ContentFile
from django.db import IntegrityError
from django.db.models import Count
from django.urls import reverse

from .models import Folder, Song, SiteConfiguration
from application.music_generator import build_default_generator
from domain.music_generation import GenerationRequest

logger = logging.getLogger(__name__)


def _user_songs_queryset(user):
    return Song.objects.filter(owner=user).order_by('-time_created')


def _folder_sidebar_context(user, active_folder_id=None):
    folders = Folder.objects.filter(owner=user).annotate(song_count=Count('songs'))
    return {
        'folder_list': folders,
        'active_folder_id': active_folder_id,
    }


def _ensure_song_share_token(song):
    if song.share_token:
        return song.share_token
    song.share_token = uuid.uuid4()
    song.save(update_fields=['share_token'])
    return song.share_token


@login_required
def library_home(request):
    # display all songs owned by the current user
    songs = _user_songs_queryset(request.user)
    context = {
        'songs': songs,
        'current_folder_name': 'All Songs',
        'all_songs_count': songs.count(),
        **_folder_sidebar_context(request.user),
    }
    return render(request, 'library/library_home.html', context)


@login_required
def folder_create(request):
    if request.method != 'POST':
        return redirect('library_home')

    name = request.POST.get('name', '').strip()
    image = request.FILES.get('image')
    if not name:
        return redirect('library_home')

    try:
        folder = Folder.objects.create(owner=request.user, name=name, image=image)
    except IntegrityError:
        # If the folder exists already, route user to that folder.
        folder = Folder.objects.filter(owner=request.user, name=name).first()

    if folder:
        return redirect('folder_detail', folder_id=folder.id)
    return redirect('library_home')


@login_required
def folder_detail(request, folder_id):
    folder = get_object_or_404(Folder, id=folder_id, owner=request.user)
    songs = folder.songs.filter(owner=request.user).order_by('-time_created')
    available_songs = _user_songs_queryset(request.user).exclude(id__in=songs.values_list('id', flat=True))

    context = {
        'folder': folder,
        'songs': songs,
        'available_songs': available_songs,
        'current_folder_name': folder.name,
        'all_songs_count': _user_songs_queryset(request.user).count(),
        **_folder_sidebar_context(request.user, active_folder_id=folder.id),
    }
    return render(request, 'library/folder_detail.html', context)


@login_required
def folder_add_song(request, folder_id):
    if request.method != 'POST':
        return redirect('folder_detail', folder_id=folder_id)

    folder = get_object_or_404(Folder, id=folder_id, owner=request.user)
    song_id = request.POST.get('song_id')
    if song_id:
        song = get_object_or_404(Song, id=song_id, owner=request.user)
        folder.songs.add(song)

    return redirect('folder_detail', folder_id=folder.id)


def song_detail(request, song_id):
    # display a single song if it is public OR owned by current user
    song = get_object_or_404(Song, id=song_id)

    # access control >>> public or owned by user
    if not song.is_public and song.owner != request.user:
        raise Http404("Song not found or access denied.")

    share_url = None
    if request.user.is_authenticated and request.user == song.owner and song.is_public:
        token = _ensure_song_share_token(song)
        share_url = request.build_absolute_uri(
            reverse('song_shared_detail', kwargs={'share_token': token})
        )

    return render(request, 'library/song_detail.html', {'song': song, 'share_url': share_url})


@login_required
def song_share(request, song_id):
    song = get_object_or_404(Song, id=song_id, owner=request.user)

    if not song.is_public:
        song.is_public = True
        song.save(update_fields=['is_public'])

    token = _ensure_song_share_token(song)
    share_url = request.build_absolute_uri(
        reverse('song_shared_detail', kwargs={'share_token': token})
    )
    return render(
        request,
        'library/song_share.html',
        {
            'song': song,
            'share_url': share_url,
        },
    )


def song_shared_detail(request, share_token):
    song = get_object_or_404(Song, share_token=share_token, is_public=True)
    return render(request, 'library/song_shared_detail.html', {'song': song})


def song_shared_download(request, share_token):
    song = get_object_or_404(Song, share_token=share_token, is_public=True)

    if not song.song_file:
        raise Http404("No audio file available for this song.")

    filename = f"{song.song_name}.mp3"
    response = FileResponse(song.song_file.open('rb'), content_type='audio/mpeg')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


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

    user_folders = Folder.objects.filter(owner=request.user).order_by('name')

    if request.method == 'POST':
        song.song_name = request.POST.get('song_name', song.song_name).strip()
        song.description = request.POST.get('description', song.description).strip()
        if 'cover_image' in request.FILES:
            song.cover_image = request.FILES['cover_image']
        song.save()

        selected_folder_ids = request.POST.getlist('folder_ids')
        allowed_folders = user_folders.filter(id__in=selected_folder_ids)
        song.folders.set(allowed_folders)

        return redirect('song_detail', song_id=song.id)

    # GET: show edit form with current values
    selected_folder_ids = set(song.folders.values_list('id', flat=True))
    return render(
        request,
        'library/song_edit.html',
        {
            'song': song,
            'user_folders': user_folders,
            'selected_folder_ids': selected_folder_ids,
        },
    )


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
        if song.is_public:
            _ensure_song_share_token(song)
        song.save()
        return redirect('song_detail', song_id=song.id)

    # GET: show confirmation page
    return render(request, 'library/song_toggle_public.html', {'song': song})
