"""
Movies App — Serializers
"""

from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from .models import Genre, Language, Movie


class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ['id', 'name', 'slug']


class LanguageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Language
        fields = ['id', 'name', 'code']


class MovieListSerializer(serializers.ModelSerializer):
    """Optimized for list views — only fields needed for cards."""
    genres = GenreSerializer(many=True, read_only=True)
    languages = LanguageSerializer(many=True, read_only=True)

    class Meta:
        model = Movie
        fields = [
            'id', 'title', 'slug', 'duration_minutes',
            'genres', 'languages', 'rating', 'votes_count',
            'release_date', 'status', 'poster_url',
            'certificate', 'is_featured',
        ]


class MovieDetailSerializer(serializers.ModelSerializer):
    """Full movie data for detail views."""
    genres = GenreSerializer(many=True, read_only=True)
    languages = LanguageSerializer(many=True, read_only=True)
    # SerializerMethodField so drf-spectacular can resolve the return type
    cast_list = serializers.SerializerMethodField()

    class Meta:
        model = Movie
        fields = [
            'id', 'title', 'slug', 'description', 'duration_minutes',
            'genres', 'languages', 'rating', 'votes_count',
            'release_date', 'status', 'poster_url', 'trailer_url',
            'director', 'cast', 'cast_list', 'certificate',
            'is_featured', 'created_at', 'updated_at',
        ]

    @extend_schema_field(serializers.ListField(child=serializers.CharField()))
    def get_cast_list(self, obj) -> list:
        """Return cast as a list of strings."""
        return [c.strip() for c in obj.cast.split(',') if c.strip()]


class GenreWithCountSerializer(serializers.Serializer):
    """Genre with movie count — used by /api/v1/genres/."""
    id = serializers.IntegerField()
    name = serializers.CharField()
    slug = serializers.CharField()
    movie_count = serializers.IntegerField()


class LanguageWithCountSerializer(serializers.Serializer):
    """Language with movie count — used by /api/v1/languages/."""
    id = serializers.IntegerField()
    name = serializers.CharField()
    code = serializers.CharField()
    movie_count = serializers.IntegerField()


class FilterCountItemSerializer(serializers.Serializer):
    """Single filter option with dynamic movie count."""
    id = serializers.IntegerField()
    name = serializers.CharField()
    count = serializers.IntegerField()


class MovieListResponseSerializer(serializers.Serializer):
    """Full movie list response shape (for schema docs)."""
    count = serializers.IntegerField()
    total_pages = serializers.IntegerField()
    current_page = serializers.IntegerField()
    next = serializers.URLField(allow_null=True)
    previous = serializers.URLField(allow_null=True)
    applied_filters = serializers.DictField()
    genre_counts = FilterCountItemSerializer(many=True)
    language_counts = FilterCountItemSerializer(many=True)
    results = MovieListSerializer(many=True)
