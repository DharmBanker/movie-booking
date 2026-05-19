"""
Movies App — Service Layer

Encapsulates business logic and complex query operations.
Keeps views thin and logic reusable.

Services:
- MovieQueryService: Handles all movie listing, filtering, and filter count logic
- GenreService: Genre-related operations
- LanguageService: Language-related operations
"""

import logging
from django.db.models import Count, Q, Prefetch

from .models import Movie, Genre, Language
from .filters import MovieFilter

logger = logging.getLogger(__name__)


class MovieQueryService:
    """
    Service class for movie query operations.

    Centralizes:
    - Base queryset construction with proper prefetching
    - Filter application
    - Sorting
    - Dynamic filter count calculation
    """

    # Valid sort options mapped to ORM field expressions
    SORT_OPTIONS = {
        'rating_desc': '-rating',
        'rating_asc': 'rating',
        'release_desc': '-release_date',
        'release_asc': 'release_date',
        'title_asc': 'title',
        'title_desc': '-title',
        'votes_desc': '-votes_count',
    }

    DEFAULT_SORT = '-release_date'

    @classmethod
    def get_base_queryset(cls):
        """
        Returns the base queryset for active movies with optimized prefetching.

        Optimization decisions:
        - prefetch_related for M2M (genres, languages) avoids N+1 queries
        - select_related not needed here (no FK on Movie to prefetch)
        - only() not used to keep serializer flexibility
        - Filter by is_active=True to exclude soft-deleted movies
        """
        return (
            Movie.objects
            .filter(is_active=True)
            # prefetch_related batches M2M queries into 2 extra queries
            # instead of N queries (one per movie) — critical for 5000+ records
            .prefetch_related(
                Prefetch('genres', queryset=Genre.objects.filter(is_active=True)),
                Prefetch('languages', queryset=Language.objects.filter(is_active=True)),
            )
        )

    @classmethod
    def apply_filters(cls, queryset, request_params):
        """
        Apply MovieFilter to the queryset using request query params.
        Returns filtered queryset.
        """
        movie_filter = MovieFilter(request_params, queryset=queryset)
        return movie_filter.qs

    @classmethod
    def apply_sorting(cls, queryset, sort_param):
        """
        Apply sorting to queryset based on sort parameter.

        Falls back to default sort if invalid sort param provided.
        This prevents potential ORM injection via sort param.
        """
        sort_field = cls.SORT_OPTIONS.get(sort_param, cls.DEFAULT_SORT)
        return queryset.order_by(sort_field)

    @classmethod
    def get_genre_counts(cls, filtered_queryset):
        """
        Calculate movie count per genre for the CURRENT filtered result set.

        This is the "dynamic filter counts" feature:
        - When user selects Action genre, show how many Hindi/English/etc. movies exist
        - Counts are based on the already-filtered queryset, not all movies

        Uses annotate + Count for a single aggregation query.
        Much more efficient than looping and counting individually.

        Returns: [{"id": 1, "name": "Action", "count": 45}, ...]
        """
        return (
            Genre.objects
            .filter(
                is_active=True,
                movies__in=filtered_queryset  # Only count genres in filtered set
            )
            .annotate(count=Count('movies', distinct=True))
            .values('id', 'name', 'count')
            .order_by('-count')  # Most popular genres first
        )

    @classmethod
    def get_language_counts(cls, filtered_queryset):
        """
        Calculate movie count per language for the CURRENT filtered result set.

        Same dynamic counting approach as get_genre_counts.
        Returns: [{"id": 1, "name": "Hindi", "count": 120}, ...]
        """
        return (
            Language.objects
            .filter(
                is_active=True,
                movies__in=filtered_queryset
            )
            .annotate(count=Count('movies', distinct=True))
            .values('id', 'name', 'count')
            .order_by('-count')  # Most popular languages first
        )

    @classmethod
    def get_applied_filters(cls, request_params):
        """
        Extract and return the currently applied filter values.
        Included in API response so clients know what filters are active.
        """
        applied = {}

        if request_params.get('genres'):
            applied['genres'] = request_params.get('genres')
        if request_params.get('languages'):
            applied['languages'] = request_params.get('languages')
        if request_params.get('status'):
            applied['status'] = request_params.get('status')
        if request_params.get('min_rating'):
            applied['min_rating'] = request_params.get('min_rating')
        if request_params.get('max_rating'):
            applied['max_rating'] = request_params.get('max_rating')
        if request_params.get('search'):
            applied['search'] = request_params.get('search')
        if request_params.get('sort'):
            applied['sort'] = request_params.get('sort')

        return applied


class GenreService:
    """Service for genre-related operations."""

    @classmethod
    def get_active_genres(cls):
        """Return all active genres ordered by name."""
        return Genre.objects.filter(is_active=True).order_by('name')

    @classmethod
    def get_genres_with_movie_count(cls):
        """
        Return genres with total movie count.
        Used for filter sidebar in frontend.
        """
        return (
            Genre.objects
            .filter(is_active=True)
            .annotate(movie_count=Count('movies', filter=Q(movies__is_active=True)))
            .order_by('-movie_count')
        )


class LanguageService:
    """Service for language-related operations."""

    @classmethod
    def get_active_languages(cls):
        """Return all active languages ordered by name."""
        return Language.objects.filter(is_active=True).order_by('name')

    @classmethod
    def get_languages_with_movie_count(cls):
        """
        Return languages with total movie count.
        Used for filter sidebar in frontend.
        """
        return (
            Language.objects
            .filter(is_active=True)
            .annotate(movie_count=Count('movies', filter=Q(movies__is_active=True)))
            .order_by('-movie_count')
        )
