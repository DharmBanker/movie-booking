"""
Movies App — Database Models

Schema Design:
- Genre: Movie categories (Action, Drama, Comedy, etc.)
- Language: Available languages (Hindi, English, Tamil, etc.)
- Movie: Core movie entity with M2M relations to Genre and Language

Indexing Strategy:
- Indexes on all frequently filtered/sorted fields
- M2M through-table indexes for join performance
- Composite indexes for common query patterns
"""

from decimal import Decimal
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class Genre(models.Model):
    """
    Movie genre categories.
    Examples: Action, Drama, Comedy, Thriller, Romance, Horror
    """
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'genres'
        ordering = ['name']
        indexes = [
            # Index for active genre lookups (most common query)
            models.Index(fields=['is_active'], name='idx_genre_active'),
            models.Index(fields=['slug'], name='idx_genre_slug'),
        ]

    def __str__(self):
        return self.name


class Language(models.Model):
    """
    Movie language options.
    Examples: Hindi, English, Tamil, Telugu, Malayalam, Kannada
    """
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=10, unique=True)  # ISO 639-1 code: hi, en, ta
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'languages'
        ordering = ['name']
        indexes = [
            models.Index(fields=['is_active'], name='idx_language_active'),
            models.Index(fields=['code'], name='idx_language_code'),
        ]

    def __str__(self):
        return self.name


class Movie(models.Model):
    """
    Core movie entity.

    Relationships:
    - genres: M2M with Genre (a movie can belong to multiple genres)
    - languages: M2M with Language (a movie can be in multiple languages)

    Indexing:
    - release_date: Sorted/filtered frequently
    - rating: Sorted by rating_desc/rating_asc
    - is_active: All list queries filter by this
    - title: Search queries
    """

    STATUS_CHOICES = [
        ('upcoming', 'Upcoming'),
        ('now_showing', 'Now Showing'),
        ('ended', 'Ended'),
    ]

    # Core fields
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    description = models.TextField()
    duration_minutes = models.PositiveIntegerField(
        help_text="Movie duration in minutes"
    )

    # Classification
    genres = models.ManyToManyField(
        Genre,
        related_name='movies',
        blank=True,
        # Custom through table for better indexing control
        db_table='movie_genres',
    )
    languages = models.ManyToManyField(
        Language,
        related_name='movies',
        blank=True,
        db_table='movie_languages',
    )

    # Ratings
    rating = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        default=Decimal('0.0'),
        validators=[MinValueValidator(Decimal('0.0')), MaxValueValidator(Decimal('10.0'))],
        help_text="Rating out of 10"
    )
    votes_count = models.PositiveIntegerField(default=0)

    # Release info
    release_date = models.DateField(db_index=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='upcoming',
        db_index=True
    )

    # Media
    poster_url = models.URLField(blank=True)
    trailer_url = models.URLField(blank=True)

    # Metadata
    director = models.CharField(max_length=255, blank=True)
    cast = models.TextField(blank=True, help_text="Comma-separated cast names")
    certificate = models.CharField(
        max_length=10,
        blank=True,
        help_text="Age certificate: U, UA, A, S"
    )

    # Flags
    is_active = models.BooleanField(default=True, db_index=True)
    is_featured = models.BooleanField(default=False)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'movies'
        ordering = ['-release_date']
        indexes = [
            # Single-column indexes for common filters
            models.Index(fields=['rating'], name='idx_movie_rating'),
            models.Index(fields=['release_date'], name='idx_movie_release_date'),
            models.Index(fields=['status'], name='idx_movie_status'),
            models.Index(fields=['is_active'], name='idx_movie_active'),
            models.Index(fields=['is_featured'], name='idx_movie_featured'),

            # Composite index: active movies sorted by rating (most common query)
            models.Index(
                fields=['is_active', '-rating'],
                name='idx_movie_active_rating'
            ),
            # Composite index: active movies sorted by release date
            models.Index(
                fields=['is_active', '-release_date'],
                name='idx_movie_active_release'
            ),
            # Text search index on title
            models.Index(fields=['title'], name='idx_movie_title'),
        ]

    def __str__(self):
        year = self.release_date.year if hasattr(self.release_date, 'year') else str(self.release_date)[:4]
        return f"{self.title} ({year})"

    @property
    def cast_list(self):
        """Return cast as a list."""
        return [c.strip() for c in self.cast.split(',') if c.strip()]
