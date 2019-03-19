from django import forms
from django.contrib.auth import get_user_model
from django.forms import ModelForm, Form
from django.utils.translation import ugettext_lazy as _

User = get_user_model()


class PasswordProtectedForm(Form):
    password = forms.CharField(
        strip=False,
        label=_('Enter your password'),
        widget=forms.PasswordInput(attrs={'placeholder': _('Password')})
    )

    def clean_password(self):
        """Validate that the entered password is correct.
        """
        password = self.cleaned_data['password']
        if not self.user.check_password(password):
            raise forms.ValidationError(
                _("The password is incorrect"),
                code='password_incorrect'
            )
        return password


class DeleteUserForm(PasswordProtectedForm):
    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def save(self):
        self.user.delete()


class UpdateUserForm(PasswordProtectedForm):
    email = forms.EmailField(label=_('Enter your new email'))

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def save(self):
        self.user.email = self.cleaned_data['email']
        self.user.save()
