"""
Movies App — URL Configuration
"""

from django.urls import path
from . import views

app_name = 'movies'

urlpatterns = [
    # Movie endpoints
    path('movies/', views.MovieListView.as_view(), name='movie-list'),
    path('movies/<slug:slug>/', views.MovieDetailView.as_view(), name='movie-detail'),

    # Filter data endpoints
    path('genres/', views.GenreListView.as_view(), name='genre-list'),
    path('languages/', views.LanguageListView.as_view(), name='language-list'),
]
