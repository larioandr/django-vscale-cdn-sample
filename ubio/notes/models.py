from django.contrib.auth import get_user_model
from django.db import models


User = get_user_model()


def get_note_full_path(instance, filename):
    ext = filename.split('.')[-1]
    return f'private/notes/NOTE_{instance.owner.pk}_{instance.pk}.{ext}'


# noinspection PyUnresolvedReferences
class Note(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    text = models.TextField(blank=True)
    document = models.FileField(upload_to=get_note_full_path, blank=True)
    public = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.owner.profile.get_full_name()} note #{self.pk}'
    