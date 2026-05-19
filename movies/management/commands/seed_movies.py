"""
Management Command: seed_movies

Seeds the database with sample genres, languages, and movies for development/testing.

Usage:
    python manage.py seed_movies
    python manage.py seed_movies --count 50
"""

import random
from datetime import date, timedelta
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from movies.models import Genre, Language, Movie


GENRES = [
    ('Action', 'action'),
    ('Drama', 'drama'),
    ('Comedy', 'comedy'),
    ('Thriller', 'thriller'),
    ('Romance', 'romance'),
    ('Horror', 'horror'),
    ('Sci-Fi', 'sci-fi'),
    ('Animation', 'animation'),
    ('Documentary', 'documentary'),
    ('Biography', 'biography'),
    ('Crime', 'crime'),
    ('Fantasy', 'fantasy'),
]

LANGUAGES = [
    ('Hindi', 'hi'),
    ('English', 'en'),
    ('Tamil', 'ta'),
    ('Telugu', 'te'),
    ('Malayalam', 'ml'),
    ('Kannada', 'kn'),
    ('Bengali', 'bn'),
    ('Marathi', 'mr'),
]

SAMPLE_MOVIES = [
    {
        'title': 'The Dark Knight',
        'description': 'When the menace known as the Joker wreaks havoc and chaos on the people of Gotham.',
        'duration_minutes': 152,
        'rating': 9.0,
        'director': 'Christopher Nolan',
        'cast': 'Christian Bale, Heath Ledger, Aaron Eckhart',
        'certificate': 'UA',
        'genres': ['Action', 'Crime', 'Drama'],
        'languages': ['English', 'Hindi'],
    },
    {
        'title': 'Inception',
        'description': 'A thief who steals corporate secrets through dream-sharing technology.',
        'duration_minutes': 148,
        'rating': 8.8,
        'director': 'Christopher Nolan',
        'cast': 'Leonardo DiCaprio, Joseph Gordon-Levitt, Elliot Page',
        'certificate': 'UA',
        'genres': ['Action', 'Sci-Fi', 'Thriller'],
        'languages': ['English', 'Hindi', 'Tamil'],
    },
    {
        'title': 'Dangal',
        'description': 'Former wrestler Mahavir Singh Phogat trains his daughters to become world-class wrestlers.',
        'duration_minutes': 161,
        'rating': 8.4,
        'director': 'Nitesh Tiwari',
        'cast': 'Aamir Khan, Fatima Sana Shaikh, Sanya Malhotra',
        'certificate': 'U',
        'genres': ['Biography', 'Drama', 'Action'],
        'languages': ['Hindi'],
    },
    {
        'title': 'KGF Chapter 2',
        'description': 'Rocky takes control of the Kolar Gold Fields and his enemies grow.',
        'duration_minutes': 168,
        'rating': 8.2,
        'director': 'Prashanth Neel',
        'cast': 'Yash, Sanjay Dutt, Raveena Tandon',
        'certificate': 'UA',
        'genres': ['Action', 'Crime', 'Drama'],
        'languages': ['Kannada', 'Hindi', 'Tamil', 'Telugu'],
    },
    {
        'title': 'RRR',
        'description': 'A fictional story about two legendary revolutionaries and their journey away from home.',
        'duration_minutes': 187,
        'rating': 7.9,
        'director': 'S. S. Rajamouli',
        'cast': 'N. T. Rama Rao Jr., Ram Charan, Ajay Devgn',
        'certificate': 'UA',
        'genres': ['Action', 'Drama'],
        'languages': ['Telugu', 'Hindi', 'Tamil'],
    },
    {
        'title': 'Interstellar',
        'description': 'A team of explorers travel through a wormhole in space in an attempt to ensure humanity\'s survival.',
        'duration_minutes': 169,
        'rating': 8.6,
        'director': 'Christopher Nolan',
        'cast': 'Matthew McConaughey, Anne Hathaway, Jessica Chastain',
        'certificate': 'UA',
        'genres': ['Sci-Fi', 'Drama'],
        'languages': ['English', 'Hindi'],
    },
    {
        'title': '3 Idiots',
        'description': 'Two friends search for their long-lost companion and reminisce about their college days.',
        'duration_minutes': 170,
        'rating': 8.4,
        'director': 'Rajkumar Hirani',
        'cast': 'Aamir Khan, R. Madhavan, Sharman Joshi',
        'certificate': 'U',
        'genres': ['Comedy', 'Drama', 'Romance'],
        'languages': ['Hindi'],
    },
    {
        'title': 'Pushpa: The Rise',
        'description': 'A laborer rises through the ranks of a red sandalwood smuggling syndicate.',
        'duration_minutes': 179,
        'rating': 7.6,
        'director': 'Sukumar',
        'cast': 'Allu Arjun, Fahadh Faasil, Rashmika Mandanna',
        'certificate': 'UA',
        'genres': ['Action', 'Crime', 'Drama'],
        'languages': ['Telugu', 'Hindi', 'Tamil', 'Malayalam'],
    },
    {
        'title': 'Dune',
        'description': 'A noble family becomes embroiled in a war for control over the galaxy\'s most valuable asset.',
        'duration_minutes': 155,
        'rating': 8.0,
        'director': 'Denis Villeneuve',
        'cast': 'Timothée Chalamet, Rebecca Ferguson, Oscar Isaac',
        'certificate': 'UA',
        'genres': ['Sci-Fi', 'Action', 'Drama'],
        'languages': ['English', 'Hindi'],
    },
    {
        'title': 'Tumbbad',
        'description': 'A mythological story about a god who was the first to be born and the last to survive.',
        'duration_minutes': 104,
        'rating': 8.2,
        'director': 'Rahi Anil Barve',
        'cast': 'Sohum Shah, Jyoti Malshe, Anita Date',
        'certificate': 'A',
        'genres': ['Horror', 'Fantasy', 'Thriller'],
        'languages': ['Hindi', 'Marathi'],
    },
]


class Command(BaseCommand):
    help = 'Seed the database with sample movies, genres, and languages'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=10,
            help='Number of additional random movies to create (default: 10)'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before seeding'
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing data...')
            Movie.objects.all().delete()
            Genre.objects.all().delete()
            Language.objects.all().delete()

        self.stdout.write('Creating genres...')
        genre_objects = {}
        for name, slug in GENRES:
            genre, created = Genre.objects.get_or_create(
                slug=slug,
                defaults={'name': name, 'is_active': True}
            )
            genre_objects[name] = genre
            if created:
                self.stdout.write(f'  Created genre: {name}')

        self.stdout.write('Creating languages...')
        language_objects = {}
        for name, code in LANGUAGES:
            language, created = Language.objects.get_or_create(
                code=code,
                defaults={'name': name, 'is_active': True}
            )
            language_objects[name] = language
            if created:
                self.stdout.write(f'  Created language: {name}')

        self.stdout.write('Creating sample movies...')
        today = date.today()

        for movie_data in SAMPLE_MOVIES:
            slug = slugify(movie_data['title'])
            # Ensure unique slug
            base_slug = slug
            counter = 1
            while Movie.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1

            release_date = today - timedelta(days=random.randint(30, 365))

            movie, created = Movie.objects.get_or_create(
                slug=slug,
                defaults={
                    'title': movie_data['title'],
                    'description': movie_data['description'],
                    'duration_minutes': movie_data['duration_minutes'],
                    'rating': movie_data['rating'],
                    'votes_count': random.randint(1000, 500000),
                    'director': movie_data['director'],
                    'cast': movie_data['cast'],
                    'certificate': movie_data['certificate'],
                    'release_date': release_date,
                    'status': 'now_showing',
                    'is_active': True,
                    'is_featured': random.choice([True, False]),
                }
            )

            if created:
                # Add genres
                for genre_name in movie_data['genres']:
                    if genre_name in genre_objects:
                        movie.genres.add(genre_objects[genre_name])

                # Add languages
                for lang_name in movie_data['languages']:
                    if lang_name in language_objects:
                        movie.languages.add(language_objects[lang_name])

                self.stdout.write(f'  Created movie: {movie.title}')

        # Create additional random movies if requested
        extra_count = options['count']
        if extra_count > 0:
            self.stdout.write(f'Creating {extra_count} additional random movies...')
            genre_list = list(genre_objects.values())
            language_list = list(language_objects.values())

            for i in range(extra_count):
                title = f"Movie Title {random.randint(1000, 9999)}"
                slug = slugify(title)
                base_slug = slug
                counter = 1
                while Movie.objects.filter(slug=slug).exists():
                    slug = f"{base_slug}-{counter}"
                    counter += 1

                release_date = today - timedelta(days=random.randint(1, 730))
                movie = Movie.objects.create(
                    title=title,
                    slug=slug,
                    description=f"Description for {title}. An exciting movie experience.",
                    duration_minutes=random.randint(90, 200),
                    rating=round(random.uniform(4.0, 9.5), 1),
                    votes_count=random.randint(100, 100000),
                    director=f"Director {random.randint(1, 50)}",
                    cast=f"Actor {random.randint(1, 100)}, Actor {random.randint(1, 100)}",
                    certificate=random.choice(['U', 'UA', 'A']),
                    release_date=release_date,
                    status=random.choice(['now_showing', 'upcoming', 'ended']),
                    is_active=True,
                    is_featured=False,
                )

                # Add 1-3 random genres
                selected_genres = random.sample(genre_list, random.randint(1, 3))
                movie.genres.set(selected_genres)

                # Add 1-3 random languages
                selected_languages = random.sample(language_list, random.randint(1, 3))
                movie.languages.set(selected_languages)

        total_movies = Movie.objects.count()
        total_genres = Genre.objects.count()
        total_languages = Language.objects.count()

        self.stdout.write(self.style.SUCCESS(
            f'\n✓ Seeding complete!\n'
            f'  Movies: {total_movies}\n'
            f'  Genres: {total_genres}\n'
            f'  Languages: {total_languages}\n'
        ))
