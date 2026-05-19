"""
Movies App — Views

Endpoints:
  GET /api/v1/movies/          → Movie list with filtering, sorting, pagination
  GET /api/v1/movies/<slug>/   → Movie detail
  GET /api/v1/genres/          → Genre list with movie counts
  GET /api/v1/languages/       → Language list with movie counts
"""

import logging
from rest_framework import generics
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiParameter

from .models import Movie, Genre, Language
from .serializers import (
    MovieListSerializer,
    MovieDetailSerializer,
    GenreWithCountSerializer,
    LanguageWithCountSerializer,
    MovieListResponseSerializer,
)
from .pagination import StandardResultsPagination
from .services import MovieQueryService, GenreService, LanguageService

logger = logging.getLogger(__name__)


class MovieListView(generics.ListAPIView):
    """
    GET /api/v1/movies/

    Paginated movie list with multi-select genre/language filtering,
    sorting, and dynamic filter counts.

    Query params:
      genres    — comma-separated genre IDs     e.g. ?genres=1,2
      languages — comma-separated language IDs  e.g. ?languages=1,3
      sort      — rating_desc | rating_asc | release_desc | release_asc | title_asc
      min_rating / max_rating — decimal range   e.g. ?min_rating=7.0
      search    — title / director search       e.g. ?search=nolan
      status    — now_showing | upcoming | ended
      page / limit — pagination                 e.g. ?page=2&limit=10
    """
    serializer_class = MovieListSerializer
    pagination_class = StandardResultsPagination

    def get_queryset(self):
        qs = MovieQueryService.get_base_queryset()
        qs = MovieQueryService.apply_filters(qs, self.request.query_params)
        qs = MovieQueryService.apply_sorting(qs, self.request.query_params.get('sort', ''))
        return qs

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)

        genre_counts = list(MovieQueryService.get_genre_counts(queryset))
        language_counts = list(MovieQueryService.get_language_counts(queryset))
        applied_filters = MovieQueryService.get_applied_filters(request.query_params)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            response = self.get_paginated_response(serializer.data)
            response.data['applied_filters'] = applied_filters
            response.data['genre_counts'] = genre_counts
            response.data['language_counts'] = language_counts
            return response

        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'count': queryset.count(),
            'applied_filters': applied_filters,
            'genre_counts': genre_counts,
            'language_counts': language_counts,
            'results': serializer.data,
        })



class MovieDetailView(generics.RetrieveAPIView):
    """GET /api/v1/movies/<slug>/"""
    serializer_class = MovieDetailSerializer
    lookup_field = 'slug'

    def get_queryset(self):
        return MovieQueryService.get_base_queryset()


class GenreListView(generics.GenericAPIView):
    """
    GET /api/v1/genres/

    All active genres with total movie count.
    No pagination — genre list is small and static.
    """
    serializer_class = GenreWithCountSerializer
    pagination_class = None
    queryset = Genre.objects.none()  # satisfies drf-spectacular introspection

    @extend_schema(responses=GenreWithCountSerializer(many=True))
    def get(self, request, *args, **kwargs):
        genres = GenreService.get_genres_with_movie_count()
        data = [
            {'id': g.id, 'name': g.name, 'slug': g.slug, 'movie_count': g.movie_count}
            for g in genres
        ]
        serializer = self.get_serializer(data, many=True)
        return Response(serializer.data)


class LanguageListView(generics.GenericAPIView):
    """
    GET /api/v1/languages/

    All active languages with total movie count.
    No pagination — language list is small and static.
    """
    serializer_class = LanguageWithCountSerializer
    pagination_class = None
    queryset = Language.objects.none()  # satisfies drf-spectacular introspection

    @extend_schema(responses=LanguageWithCountSerializer(many=True))
    def get(self, request, *args, **kwargs):
        languages = LanguageService.get_languages_with_movie_count()
        data = [
            {'id': l.id, 'name': l.name, 'code': l.code, 'movie_count': l.movie_count}
            for l in languages
        ]
        serializer = self.get_serializer(data, many=True)
        return Response(serializer.data)
