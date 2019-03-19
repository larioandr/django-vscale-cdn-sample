from django.urls import path
from django.contrib.auth.views import LoginView, LogoutView, \
    PasswordResetView, PasswordResetConfirmView, PasswordResetCompleteView, \
    PasswordResetDoneView
from django.views.generic import RedirectView

from .views import SignUpView

urlpatterns = [
    path('signup/', SignUpView.as_view(), name='signup'),

    path('login/', LoginView.as_view(
        redirect_authenticated_user=True
    ), name='login'),

    path('logout/', LogoutView.as_view(), name='logout'),

    path('password_reset/', PasswordResetView.as_view(
        template_name='registration/password_reset.html',
        email_template_name='registration/email/password_reset.txt',
        subject_template_name='registration/email/password_reset_subject.txt'
    ), name='password_reset'),

    path(
        'password_reset/done/',
        PasswordResetDoneView.as_view(),
        name='password_reset_done'),

    path(
        'password_reset/<str:uidb64>/<str:token>/',
        PasswordResetConfirmView.as_view(),
        name='password_reset_confirm'),

    path(
        'password_reset/complete/',
        PasswordResetCompleteView.as_view(),
        name='password_reset_complete'
    ),
]
