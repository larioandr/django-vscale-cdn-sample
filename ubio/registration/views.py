from django.contrib.auth import get_user_model, login
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.urls import reverse
from django.views.generic import FormView, RedirectView
from django.core.mail import send_mail

from .forms import SignUpForm

User = get_user_model()


class SignUpView(FormView):
    template_name = 'registration/signup.html'
    form_class = SignUpForm

    def form_valid(self, form):
        user = form.save()
        user.is_active = True
        user.save()
        login(self.request, user)
        send_mail(
            'Welcome to uBio!',
            message=render_to_string(
                'registration/email/welcome.txt',
                {'user': user}),
            from_email='admin@ubio.voidhost.xyz',
            recipient_list=[user.email],
            fail_silently=False
        )
        return redirect('profile-setup')
