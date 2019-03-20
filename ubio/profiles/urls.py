from django.urls import path

from . import views


urlpatterns = [
    path('setup/', views.profile_setup, name='profile-setup'),
    path('<int:pk>/', views.profile_detail, name='profile-detail'),
    path('<int:pk>/update/', views.profile_update, name='profile-update'),
    path('<int:pk>/avatar/update/', views.avatar_update, name='avatar-update'),
    path('<int:pk>/avatar/delete/', views.avatar_delete, name='avatar-delete'),
]
