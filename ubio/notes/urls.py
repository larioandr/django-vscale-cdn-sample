from django.urls import path

from . import views

urlpatterns = [
    path('', views.note_list, name='note-list'),
    path('<int:pk>/', views.note_update, name='note-update'),
    path('<int:pk>/delete/', views.note_delete, name='note-delete'),
    path('create/', views.note_create, name='note-create'),
    path('<int:pk>/document/', views.get_note_document, name='note-document'),
    path(
        '<int:pk>/document/delete/',
        views.note_document_delete,
        name='note-document-delete'
    ),
]
