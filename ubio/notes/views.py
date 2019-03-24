import mimetypes
import os
import time

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import Http404, HttpResponseForbidden, HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_POST, require_GET

from .forms import NoteUpdateForm
from .models import Note
from .permissions import can_delete, can_edit, can_view

User = get_user_model()


@login_required
def note_list(request):
    notes = Note.objects.filter(Q(public=True) | Q(owner=request.user.pk))
    return render(request, 'notes/note_list.html', context={
        'notes': notes,
        'show_add': True,
    })


@login_required
def note_update(request, pk):
    note = get_object_or_404(Note, pk=pk)
    if can_edit(request, note):
        if request.method == 'POST':
            time.sleep(1)  # simulate long file upload
            form = NoteUpdateForm(request.POST, request.FILES, instance=note)
            # We save current file (if any) for two reasons:
            # 1) if this file is not empty and user uploaded a new file, we
            #    are going to delete this old file (in case of valid form); and
            # 2) it is going to be assigned instead of TemporaryUploadedFile
            #    object in case of form validation error.
            old_file = note.document.file if note.document else None
            if form.is_valid():
                # If the form is valid and user provided a new file, we delete
                # original file first. Otherwise Django will add a random
                # suffix which will break our storage strategy.
                if old_file and request.FILES:
                    note.document.storage.delete(old_file.name)
                messages.success(request, 'Note updated!')
                form.save()
                return redirect('note-update', pk=pk)
            else:
                # If the form is invalid (e.g. title is not provided), but the
                # user tried to upload a file, a new TemporaryUploadedFile
                # object will be created and, which is more important, it will
                # be assigned to `note.document` field. We want to avoid this
                # to make sure that until the form is completely valid
                # previous file is not re-written. To do it we assign the
                # `old_file` value to both cleaned_data and note.document:
                form.cleaned_data['document'] = old_file
                note.document = old_file
                messages.error(request, 'Errors during note update')
        else:
            form = NoteUpdateForm(instance=note)
        return render(request, 'notes/note_update.html', context={
            'note': note,
            'form': form,
        })
    return HttpResponseForbidden()


@login_required
def note_create(request):
    if request.method == 'POST':
        time.sleep(1)  # simulate long file upload
        form = NoteUpdateForm(request.POST, request.FILES)
        if form.is_valid():
            note = form.save(commit=False)
            note.owner = request.user
            note.save()
            messages.success(request, f'Note #{note.pk} created!')
            return redirect('home')
        else:
            messages.error(request, 'Errors during note creation')
            form.cleaned_data['document'] = None
    else:
        form = NoteUpdateForm()
    return render(request, 'notes/note_create.html', context={
        'form': form,
    })


@login_required
@require_POST
def note_delete(request, pk):
    note = get_object_or_404(Note, pk=pk)
    if can_delete(request, note):
        if note.document:
            note.document.delete()
        note.delete()
        return redirect('home')
    return HttpResponseForbidden()


@login_required
@require_GET
def get_note_document(request, pk):
    note = get_object_or_404(Note, pk=pk)
    if can_view(request, note):
        if note.document:
            filename = os.path.basename(note.document.name)
            mtype = mimetypes.guess_type(filename)[0]
            response = HttpResponse(note.document.file, content_type=mtype)
            response['Content-Disposition'] = f'filename={filename}'
            return response
    raise Http404


@login_required
@require_POST
def note_document_delete(request, pk):
    note = get_object_or_404(Note, pk=pk)
    if can_edit(request, note):
        file_name = note.get_document_name()
        if note.document:
            note.document.delete()
        return render(request, 'notes/partials/file_delete_message.html', context={
            'alert_class': 'warning',
            'file_name': file_name,
        })
    raise Http404
