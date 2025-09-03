from django.shortcuts import render, redirect
from datetime import datetime
from main.models import Contact
from django.contrib import messages
from django.core.mail import send_mail
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.contrib import messages
from .recommender import recommend_with_dynamic_weights


def home(request):
    return render(request, 'home.html')

def services(request):
    return render(request, 'services.html')

def about_us(request):
    return render(request, 'about.html')

def contact(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        concern = request.POST.get('concern')

        if not email.endswith('.com'):
            messages.error(request, 'Email must end with .com')
            return render(request, 'contact.html')  # re-render form with error

        contact = Contact(name=name, email=email, concern=concern, date=datetime.today())
        contact.save()
        send_mail('New Contact Form', 'Message content', 'shrey1374@gmail.com', ['bateman312645@gmail.com'])
        messages.success(request, 'Your form has been submitted successfully!')
        return redirect('contact')  # redirect to clear form & avoid resubmission

    return render(request, 'contact.html')

def signup_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        email = request.POST['email']

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already taken')
            return redirect('signup')

        user = User.objects.create_user(username=username, email=email, password=password)
        user.save()
        messages.success(request, 'Account created successfully! You can now log in.')
        return redirect('login')

    return render(request, 'signup.html')


def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, 'You are now logged in!')
            return redirect('home')  # Redirect to a homepage
        else:
            messages.error(request, 'Invalid credentials')
            return redirect('login')

    return render(request, 'login.html')


def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out!')
    return redirect('login')

def profile_view(request):
    return render(request, 'profile.html', {'user': request.user})

def recommend_view(request):
    context = {}
    if request.method == "POST":
        title = request.POST.get('movie')
        genre = int(request.POST.get('genre', 0))
        cast = int(request.POST.get('cast', 0))
        director = int(request.POST.get('director', 0))
        rating = int(request.POST.get('rating', 0))
        year = int(request.POST.get('year', 0))

        weights = {
            'genre': genre,
            'cast': cast,
            'director': director,
            'rating': rating,
            'year': year,
        }

        context.update({
            'movie': title,
            "genre": weights['genre'],
            "cast": weights['cast'],
            "director": weights['director'],
            "rating": weights['rating'],
            "year": weights['year'],
        })

        try:
            results = recommend_with_dynamic_weights(title, weights)
            context['results'] = results.to_dict(orient='records')
        except Exception as e:
            context['error'] = str(e)

    return render(request, 'recommend.html', context)

