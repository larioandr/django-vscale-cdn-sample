from django.urls import path

from . import views


urlpatterns = [
    path('setup/', views.profile_setup, name='profile-setup'),
    path('<int:pk>/', views.profile_detail, name='profile-detail'),
    path('<int:pk>/update/', views.profile_update, name='profile-update'),
]
