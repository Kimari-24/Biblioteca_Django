from django.urls import path

from . import views

app_name = 'books'

urlpatterns = [
    path('', views.book_list, name='list'),
    path('new/', views.book_create, name='create'),
    path('<str:book_id>/edit/', views.book_edit, name='edit'),
    path('<str:book_id>/delete/', views.book_delete, name='delete'),
]
