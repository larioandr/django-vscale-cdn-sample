import io

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.db import models
from django.db.models import Model
from django.db.models.signals import post_save
from django.dispatch import receiver

import pyavagen


User = get_user_model()


def get_avatar_full_path(instance, filename):
    ext = filename.split('.')[-1]
    return f'{settings.MEDIA_PUBLIC_ROOT}/avatars/{instance.pk}.{ext}'


class Profile(Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    first_name = models.CharField(
        max_length=100, default="", verbose_name="First Name"
    )

    last_name = models.CharField(
        max_length=100, default="", verbose_name="Last Name"
    )

    avatar = models.ImageField(upload_to=get_avatar_full_path, blank=True)

    @property
    def email(self):
        return self.user.email

    def get_short_name(self):
        return self.first_name

    def get_full_name(self):
        return f'{self.first_name} {self.last_name}'

    def __str__(self):
        return self.get_full_name()


def generate_avatar(profile):
    img_io = io.BytesIO()
    avatar = pyavagen.Avatar(
        pyavagen.CHAR_SQUARE_AVATAR,
        size=500,
        string=profile.get_full_name(),
        blur_radius=100
    )
    avatar.generate().save(img_io, format='PNG', quality=100)
    img_content = ContentFile(img_io.getvalue(), f'{profile.pk}.png')
    return img_content


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()
