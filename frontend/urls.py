from django.urls import path
from . import views

urlpatterns = [
    path('', views.movies_page, name='movies-page'),
    path('movies/<slug:slug>/', views.movie_detail_page, name='movie-detail-page'),
    path('my-bookings/', views.my_bookings_page, name='my-bookings-page'),
]
