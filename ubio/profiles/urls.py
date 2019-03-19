from django.urls import path

from . import views


urlpatterns = [
    path('<int:pk>/', views.profile_detail, name='profile-detail'),
    path('<int:pk>/update/', views.profile_update, name='profile-update'),
]
