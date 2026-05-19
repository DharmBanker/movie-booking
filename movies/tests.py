"""
Movies App — Tests

Covers:
- Genre model creation
- Language model creation
- Movie model creation with M2M relations
- MovieListView: pagination, genre filter, language filter, sort, search
- MovieDetailView: slug lookup
- GenreListView: movie counts
- LanguageListView: movie counts
- MovieQueryService: filter counts, sorting
"""

from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status

from .models import Genre, Language, Movie
from .services import MovieQueryService


# ============================================================
# Model Tests
# ============================================================

class GenreModelTest(TestCase):
    def test_create_genre(self):
        genre = Genre.objects.create(name='Action', slug='action')
        self.assertEqual(str(genre), 'Action')
        self.assertTrue(genre.is_active)

    def test_genre_unique_slug(self):
        Genre.objects.create(name='Action', slug='action')
        with self.assertRaises(Exception):
            Genre.objects.create(name='Action 2', slug='action')


class LanguageModelTest(TestCase):
    def test_create_language(self):
        lang = Language.objects.create(name='Hindi', code='hi')
        self.assertEqual(str(lang), 'Hindi')
        self.assertTrue(lang.is_active)

    def test_language_unique_code(self):
        Language.objects.create(name='Hindi', code='hi')
        with self.assertRaises(Exception):
            Language.objects.create(name='Hindi 2', code='hi')


class MovieModelTest(TestCase):
    def setUp(self):
        self.genre = Genre.objects.create(name='Action', slug='action')
        self.language = Language.objects.create(name='Hindi', code='hi')

    def test_create_movie(self):
        movie = Movie.objects.create(
            title='Test Movie',
            slug='test-movie',
            description='A test movie',
            duration_minutes=120,
            rating=Decimal('8.5'),
            release_date='2024-01-01',
            status='now_showing',
        )
        movie.genres.add(self.genre)
        movie.languages.add(self.language)

        self.assertEqual(str(movie), 'Test Movie (2024)')
        self.assertEqual(movie.genres.count(), 1)
        self.assertEqual(movie.languages.count(), 1)

    def test_cast_list_property(self):
        movie = Movie.objects.create(
            title='Cast Movie',
            slug='cast-movie',
            description='desc',
            duration_minutes=100,
            release_date='2024-01-01',
            cast='Actor One, Actor Two, Actor Three',
        )
        self.assertEqual(movie.cast_list, ['Actor One', 'Actor Two', 'Actor Three'])

    def test_cast_list_empty(self):
        movie = Movie.objects.create(
            title='No Cast',
            slug='no-cast',
            description='desc',
            duration_minutes=100,
            release_date='2024-01-01',
        )
        self.assertEqual(movie.cast_list, [])


# ============================================================
# API Tests — Movie List
# ============================================================

class MovieListAPITest(APITestCase):
    def setUp(self):
        self.action = Genre.objects.create(name='Action', slug='action')
        self.drama = Genre.objects.create(name='Drama', slug='drama')
        self.hindi = Language.objects.create(name='Hindi', code='hi')
        self.english = Language.objects.create(name='English', code='en')

        self.m1 = Movie.objects.create(
            title='Action Hindi Movie',
            slug='action-hindi',
            description='desc',
            duration_minutes=120,
            rating=Decimal('8.0'),
            release_date='2024-06-01',
            status='now_showing',
            is_active=True,
        )
        self.m1.genres.add(self.action)
        self.m1.languages.add(self.hindi)

        self.m2 = Movie.objects.create(
            title='Drama English Movie',
            slug='drama-english',
            description='desc',
            duration_minutes=150,
            rating=Decimal('7.0'),
            release_date='2024-05-01',
            status='now_showing',
            is_active=True,
        )
        self.m2.genres.add(self.drama)
        self.m2.languages.add(self.english)

        self.m3 = Movie.objects.create(
            title='Inactive Movie',
            slug='inactive-movie',
            description='desc',
            duration_minutes=90,
            rating=Decimal('6.0'),
            release_date='2024-04-01',
            status='now_showing',
            is_active=False,  # should never appear in results
        )

        self.url = reverse('movies:movie-list')

    def test_list_returns_only_active_movies(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        titles = [m['title'] for m in response.data['results']]
        self.assertIn('Action Hindi Movie', titles)
        self.assertIn('Drama English Movie', titles)
        self.assertNotIn('Inactive Movie', titles)

    def test_list_has_pagination_fields(self):
        response = self.client.get(self.url)
        self.assertIn('count', response.data)
        self.assertIn('total_pages', response.data)
        self.assertIn('current_page', response.data)
        self.assertIn('next', response.data)
        self.assertIn('previous', response.data)

    def test_list_has_filter_counts(self):
        response = self.client.get(self.url)
        self.assertIn('genre_counts', response.data)
        self.assertIn('language_counts', response.data)
        self.assertIn('applied_filters', response.data)

    def test_filter_by_single_genre(self):
        response = self.client.get(self.url, {'genres': str(self.action.id)})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['title'], 'Action Hindi Movie')

    def test_filter_by_multiple_genres(self):
        response = self.client.get(self.url, {'genres': f'{self.action.id},{self.drama.id}'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)

    def test_filter_by_language(self):
        response = self.client.get(self.url, {'languages': str(self.hindi.id)})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['title'], 'Action Hindi Movie')

    def test_filter_by_multiple_languages(self):
        response = self.client.get(self.url, {'languages': f'{self.hindi.id},{self.english.id}'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)

    def test_sort_by_rating_desc(self):
        response = self.client.get(self.url, {'sort': 'rating_desc'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ratings = [float(m['rating']) for m in response.data['results']]
        self.assertEqual(ratings, sorted(ratings, reverse=True))

    def test_sort_by_rating_asc(self):
        response = self.client.get(self.url, {'sort': 'rating_asc'})
        ratings = [float(m['rating']) for m in response.data['results']]
        self.assertEqual(ratings, sorted(ratings))

    def test_search_by_title(self):
        response = self.client.get(self.url, {'search': 'Action'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['title'], 'Action Hindi Movie')

    def test_min_rating_filter(self):
        response = self.client.get(self.url, {'min_rating': '7.5'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['title'], 'Action Hindi Movie')

    def test_pagination_limit(self):
        response = self.client.get(self.url, {'limit': '1'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertIsNotNone(response.data['next'])

    def test_applied_filters_in_response(self):
        response = self.client.get(self.url, {'genres': str(self.action.id), 'sort': 'rating_desc'})
        self.assertEqual(response.data['applied_filters']['genres'], str(self.action.id))
        self.assertEqual(response.data['applied_filters']['sort'], 'rating_desc')

    def test_dynamic_genre_counts_reflect_filter(self):
        # When filtering by Hindi language, genre counts should only count Hindi movies
        response = self.client.get(self.url, {'languages': str(self.hindi.id)})
        genre_names = [g['name'] for g in response.data['genre_counts']]
        # Only Action genre should appear (Hindi movie is Action)
        self.assertIn('Action', genre_names)
        self.assertNotIn('Drama', genre_names)


# ============================================================
# API Tests — Movie Detail
# ============================================================

class MovieDetailAPITest(APITestCase):
    def setUp(self):
        self.genre = Genre.objects.create(name='Thriller', slug='thriller')
        self.language = Language.objects.create(name='Tamil', code='ta')
        self.movie = Movie.objects.create(
            title='Vikram',
            slug='vikram',
            description='An action thriller.',
            duration_minutes=174,
            rating=Decimal('8.4'),
            release_date='2022-06-03',
            status='now_showing',
            director='Lokesh Kanagaraj',
            cast='Kamal Haasan, Vijay Sethupathi, Fahadh Faasil',
            certificate='UA',
            is_active=True,
        )
        self.movie.genres.add(self.genre)
        self.movie.languages.add(self.language)

    def test_detail_returns_correct_movie(self):
        url = reverse('movies:movie-detail', kwargs={'slug': 'vikram'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Vikram')
        self.assertEqual(response.data['director'], 'Lokesh Kanagaraj')

    def test_detail_includes_cast_list(self):
        url = reverse('movies:movie-detail', kwargs={'slug': 'vikram'})
        response = self.client.get(url)
        self.assertIn('cast_list', response.data)
        self.assertIsInstance(response.data['cast_list'], list)
        self.assertIn('Kamal Haasan', response.data['cast_list'])

    def test_detail_404_for_unknown_slug(self):
        url = reverse('movies:movie-detail', kwargs={'slug': 'does-not-exist'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_detail_404_for_inactive_movie(self):
        Movie.objects.create(
            title='Hidden', slug='hidden', description='x',
            duration_minutes=90, release_date='2024-01-01', is_active=False,
        )
        url = reverse('movies:movie-detail', kwargs={'slug': 'hidden'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


# ============================================================
# API Tests — Genre & Language Lists
# ============================================================

class GenreListAPITest(APITestCase):
    def setUp(self):
        self.genre = Genre.objects.create(name='Action', slug='action')
        self.movie = Movie.objects.create(
            title='M1', slug='m1', description='d', duration_minutes=100,
            release_date='2024-01-01', is_active=True,
        )
        self.movie.genres.add(self.genre)

    def test_genre_list_returns_counts(self):
        url = reverse('movies:genre-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'Action')
        self.assertEqual(response.data[0]['movie_count'], 1)

    def test_genre_list_no_pagination(self):
        url = reverse('movies:genre-list')
        response = self.client.get(url)
        # Should be a plain list, not paginated dict
        self.assertIsInstance(response.data, list)


class LanguageListAPITest(APITestCase):
    def setUp(self):
        self.lang = Language.objects.create(name='Hindi', code='hi')
        self.movie = Movie.objects.create(
            title='M1', slug='m1', description='d', duration_minutes=100,
            release_date='2024-01-01', is_active=True,
        )
        self.movie.languages.add(self.lang)

    def test_language_list_returns_counts(self):
        url = reverse('movies:language-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'Hindi')
        self.assertEqual(response.data[0]['movie_count'], 1)


# ============================================================
# Service Tests
# ============================================================

class MovieQueryServiceTest(TestCase):
    def setUp(self):
        self.action = Genre.objects.create(name='Action', slug='action')
        self.drama = Genre.objects.create(name='Drama', slug='drama')
        self.hindi = Language.objects.create(name='Hindi', code='hi')
        self.english = Language.objects.create(name='English', code='en')

        self.m1 = Movie.objects.create(
            title='Movie A', slug='movie-a', description='d',
            duration_minutes=100, rating=Decimal('9.0'),
            release_date='2024-01-01', is_active=True,
        )
        self.m1.genres.add(self.action)
        self.m1.languages.add(self.hindi)

        self.m2 = Movie.objects.create(
            title='Movie B', slug='movie-b', description='d',
            duration_minutes=120, rating=Decimal('7.0'),
            release_date='2024-02-01', is_active=True,
        )
        self.m2.genres.add(self.drama)
        self.m2.languages.add(self.english)

    def test_base_queryset_excludes_inactive(self):
        Movie.objects.create(
            title='Inactive', slug='inactive', description='d',
            duration_minutes=90, release_date='2024-01-01', is_active=False,
        )
        qs = MovieQueryService.get_base_queryset()
        self.assertEqual(qs.count(), 2)

    def test_sort_rating_desc(self):
        qs = MovieQueryService.get_base_queryset()
        qs = MovieQueryService.apply_sorting(qs, 'rating_desc')
        self.assertEqual(qs.first().title, 'Movie A')

    def test_sort_rating_asc(self):
        qs = MovieQueryService.get_base_queryset()
        qs = MovieQueryService.apply_sorting(qs, 'rating_asc')
        self.assertEqual(qs.first().title, 'Movie B')

    def test_genre_counts(self):
        qs = MovieQueryService.get_base_queryset()
        counts = list(MovieQueryService.get_genre_counts(qs))
        names = [c['name'] for c in counts]
        self.assertIn('Action', names)
        self.assertIn('Drama', names)

    def test_language_counts(self):
        qs = MovieQueryService.get_base_queryset()
        counts = list(MovieQueryService.get_language_counts(qs))
        names = [c['name'] for c in counts]
        self.assertIn('Hindi', names)
        self.assertIn('English', names)

    def test_invalid_sort_falls_back_to_default(self):
        qs = MovieQueryService.get_base_queryset()
        # Should not raise — falls back to default sort
        qs = MovieQueryService.apply_sorting(qs, 'invalid_sort_param')
        self.assertEqual(qs.count(), 2)
