"""
Movies App — Filter Classes

Custom FilterSet for advanced multi-select filtering:
- genres: comma-separated genre IDs (e.g., ?genres=1,2,3)
- languages: comma-separated language IDs (e.g., ?languages=1,2)
- status: movie status filter
- min_rating / max_rating: rating range filter
- search: title search

Uses django-filter for clean, reusable filter logic.
"""

import django_filters
from django.db.models import Q
from .models import Movie


class MovieFilter(django_filters.FilterSet):
    """
    Advanced filter set for the Movie model.

    Supports:
    - Multi-select genre filtering via comma-separated IDs
    - Multi-select language filtering via comma-separated IDs
    - Rating range filtering
    - Status filtering
    - Title search
    """

    # Multi-select genre filter: ?genres=1,2,3
    genres = django_filters.CharFilter(
        method='filter_genres',
        label='Genre IDs (comma-separated)'
    )

    # Multi-select language filter: ?languages=1,2
    languages = django_filters.CharFilter(
        method='filter_languages',
        label='Language IDs (comma-separated)'
    )

    # Rating range filters
    min_rating = django_filters.NumberFilter(
        field_name='rating',
        lookup_expr='gte',
        label='Minimum rating'
    )
    max_rating = django_filters.NumberFilter(
        field_name='rating',
        lookup_expr='lte',
        label='Maximum rating'
    )

    # Status filter
    status = django_filters.ChoiceFilter(
        choices=Movie.STATUS_CHOICES,
        label='Movie status'
    )

    # Title search (case-insensitive contains)
    search = django_filters.CharFilter(
        method='filter_search',
        label='Search by title or director'
    )

    class Meta:
        model = Movie
        fields = ['genres', 'languages', 'min_rating', 'max_rating', 'status', 'search']

    def filter_genres(self, queryset, name, value):
        """
        Filter movies by multiple genre IDs.
        Input: comma-separated string "1,2,3"
        Returns movies that have ANY of the specified genres (OR logic).

        Uses __in lookup which translates to a single SQL IN clause —
        much more efficient than multiple OR conditions.
        """
        if not value:
            return queryset

        try:
            genre_ids = [int(gid.strip()) for gid in value.split(',') if gid.strip()]
        except ValueError:
            return queryset

        if not genre_ids:
            return queryset

        # Filter movies that have at least one of the specified genres
        # distinct() prevents duplicate movies when a movie matches multiple genres
        return queryset.filter(genres__id__in=genre_ids).distinct()

    def filter_languages(self, queryset, name, value):
        """
        Filter movies by multiple language IDs.
        Input: comma-separated string "1,2"
        Returns movies available in ANY of the specified languages.
        """
        if not value:
            return queryset

        try:
            language_ids = [int(lid.strip()) for lid in value.split(',') if lid.strip()]
        except ValueError:
            return queryset

        if not language_ids:
            return queryset

        return queryset.filter(languages__id__in=language_ids).distinct()

    def filter_search(self, queryset, name, value):
        """
        Full-text search across title and director fields.
        Uses Q objects for OR condition across multiple fields.
        """
        if not value:
            return queryset

        return queryset.filter(
            Q(title__icontains=value) | Q(director__icontains=value)
        )
