from django.conf import settings
from django.contrib.auth import get_user_model, login
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.views.generic import FormView
from django.core.mail import send_mail, EmailMultiAlternatives

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

        context = {
            'email': user.email,
            'protocol': 'https' if self.request.is_secure() else "http",
            'domain': self.request.get_host(),
        }
        html = render_to_string('registration/email/welcome.html', context)
        text = strip_tags(html)


        # html_content = render_to_string('registration/email/welcome.txt')
        # text_content = strip_tags(html_content)
        #
        # msg = EmailMultiAlternatives(
        #     subject,
        #     text_content,
        #     from_email,
        #     [to])
        send_mail(
            'Welcome to uBio!',
            message=text,
            html_message=html,
            recipient_list=[user.email],
            from_email=settings.DEFAULT_FROM_EMAIL,
            fail_silently=False,
        )
        return redirect('profile-setup')
