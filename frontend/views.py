from django.shortcuts import render

def movies_page(request):
    return render(request, 'frontend/movies.html')

def movie_detail_page(request, slug):
    return render(request, 'frontend/movie_detail.html', {'slug': slug})

def my_bookings_page(request):
    return render(request, 'frontend/my_bookings.html')
