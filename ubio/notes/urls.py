from django.urls import path

from . import views

urlpatterns = [
    path('', views.note_list, name='note-list'),
    path('<int:pk>/', views.note_update, name='note-update'),
    path('<int:pk>/delete/', views.note_delete, name='note-delete'),
    path('create/', views.note_create, name='note-create'),
]
