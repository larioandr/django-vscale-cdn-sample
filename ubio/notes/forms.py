from django.forms import ModelForm

from .models import Note


class NoteUpdateForm(ModelForm):
    class Meta:
        model = Note
        exclude = ('owner',)
