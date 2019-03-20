from django.forms import ModelForm, Form, ImageField

from .models import Profile, generate_avatar


class ProfileUpdateForm(ModelForm):
    class Meta:
        model = Profile
        fields = ('first_name', 'last_name')


class AvatarDeleteForm(ModelForm):
    class Meta:
        model = Profile
        fields = ()

    def save(self, commit=True):
        if self.instance.avatar:
            self.instance.avatar.delete()
            self.instance.avatar = generate_avatar(self.instance)
        return super().save(commit)
