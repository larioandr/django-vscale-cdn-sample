from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import Model
from django.db.models.signals import post_save
from django.dispatch import receiver

User = get_user_model()


class Profile(Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    first_name = models.CharField(
        max_length=100, default="", verbose_name="First Name"
    )

    last_name = models.CharField(
        max_length=100, default="", verbose_name="Last Name"
    )

    @property
    def email(self):
        return self.user.email

    def get_short_name(self):
        return self.first_name

    def get_full_name(self):
        return f'{self.first_name} {self.last_name}'

    def __str__(self):
        return self.get_full_name()


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()
