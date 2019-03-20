from django.forms import ModelForm, Form, ImageField

from .models import Profile, generate_avatar


class ProfileUpdateForm(ModelForm):
    class Meta:
        model = Profile
        fields = ('first_name', 'last_name')


class AvatarUpdateForm(Form):
    avatar = ImageField()

    def __init__(self, profile, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.profile = profile

    def clean_avatar(self):
        print('clean_avatar: ', type(self.cleaned_data['avatar']), self.cleaned_data['avatar'])
        return self.cleaned_data['avatar']

    def save(self):
        self.profile.avatar.delete()
        self.profile.avatar = self.cleaned_data['avatar']
        self.profile.save()
        return self.profile


class AvatarDeleteForm(ModelForm):
    class Meta:
        model = Profile
        fields = ()

    def save(self, commit=True):
        if self.instance.avatar:
            self.instance.avatar.delete()
            self.instance.avatar = generate_avatar(self.instance)
        return super().save(commit)
