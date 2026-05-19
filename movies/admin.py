"""
Movies App — Django Admin Configuration
"""

from django.contrib import admin
from .models import Genre, Language, Movie


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Language)
class LanguageAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['name', 'code']


@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = ['title', 'status', 'rating', 'release_date', 'is_active', 'is_featured']
    list_filter = ['status', 'is_active', 'is_featured', 'genres', 'languages']
    search_fields = ['title', 'director', 'cast']
    prepopulated_fields = {'slug': ('title',)}
    filter_horizontal = ['genres', 'languages']
    readonly_fields = ['created_at', 'updated_at']
    list_per_page = 50

    fieldsets = (
        ('Basic Info', {
            'fields': ('title', 'slug', 'description', 'duration_minutes', 'certificate')
        }),
        ('Classification', {
            'fields': ('genres', 'languages', 'status')
        }),
        ('Ratings', {
            'fields': ('rating', 'votes_count')
        }),
        ('Release', {
            'fields': ('release_date',)
        }),
        ('Media', {
            'fields': ('poster_url', 'trailer_url')
        }),
        ('Credits', {
            'fields': ('director', 'cast')
        }),
        ('Flags', {
            'fields': ('is_active', 'is_featured')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
