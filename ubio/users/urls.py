from django.urls import path

from . import views


urlpatterns = [
    path('delete/', views.user_delete, name='user-delete'),
    path('update/', views.user_update, name='user-update'),
    path('home/', views.user_home, name='user-home'),
]
