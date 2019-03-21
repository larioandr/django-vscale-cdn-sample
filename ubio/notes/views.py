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
        'notes': notes
    })


@login_required
def note_update(request, pk):
    note = get_object_or_404(Note, pk=pk)
    if can_edit(request, note):
        if request.method == 'POST':
            form = NoteUpdateForm(request.POST, request.FILES, instance=note)
            if form.is_valid():
                form.save()
                return redirect('note-list')
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
        form = NoteUpdateForm(request.POST)
        if form.is_valid():
            note = form.save(commit=False)
            note.owner = request.user
            note.save()
            return redirect('note-list')
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
        print(f"Going to delete note pk={pk}: ", note)
        # note.delete()
        return redirect('note-list')
    return HttpResponseForbidden()


@login_required
@require_GET
def get_note_document(request, pk):
    note = get_object_or_404(Note, pk=pk)
    if can_view(request, note):
        if note.document:
            return HttpResponse(
                note.document.file.file,
                content_type='application/pdf'
            )
    raise Http404
