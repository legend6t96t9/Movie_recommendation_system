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

from .models import PasswordResetOTP
from .forms import ForgotPasswordForm, OTPVerificationForm, ResetPasswordForm
from django.utils.timezone import now, timedelta


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

def forgot_password(request):
    if request.method == "POST":
        form = ForgotPasswordForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                messages.error(request, "No account with this email exists.")
                return redirect('forgotpwd')

            otp = PasswordResetOTP.generate_otp()
            PasswordResetOTP.objects.create(user=user, otp=otp)

            # send OTP email
            send_mail(
                "Your Password Reset OTP",
                f"Your OTP is {otp}",
                "noreply@yourdomain.com",
                [email],
                fail_silently=False,
            )

            request.session['reset_user_id'] = user.id
            messages.success(request, "OTP sent to your email.")
            return redirect('verifyotp')
    else:
        form = ForgotPasswordForm()
    return render(request, "forgotpwd.html", {"form": form})


def verify_otp(request):
    if request.method == "POST":
        form = OTPVerificationForm(request.POST)
        if form.is_valid():
            otp = form.cleaned_data['otp']
            user_id = request.session.get('reset_user_id')
            if not user_id:
                messages.error(request, "Session expired. Try again.")
                return redirect('forgotpwd')

            try:
                otp_record = PasswordResetOTP.objects.filter(
                    user_id=user_id, otp=otp
                ).latest('created_at')
            except PasswordResetOTP.DoesNotExist:
                messages.error(request, "Invalid OTP.")
                return redirect('verifyotp')

            # check expiry (5 minutes)
            if otp_record.created_at < now() - timedelta(minutes=5):
                messages.error(request, "OTP expired. Try again.")
                return redirect('forgotpwd')

            request.session['otp_verified'] = True
            return redirect('resetpassword')
    else:
        form = OTPVerificationForm()
    return render(request, "verifyotp.html", {"form": form})


def reset_password(request):
    if not request.session.get('otp_verified'):
        return redirect('forgotpwd')

    if request.method == "POST":
        form = ResetPasswordForm(request.POST)
        if form.is_valid():
            new_password = form.cleaned_data['new_password']
            user_id = request.session.get('reset_user_id')
            user = User.objects.get(id=user_id)
            user.set_password(new_password)
            user.save()

            # clear session data
            request.session.flush()

            messages.success(request, "Password changed successfully! You can now log in.")
            return redirect('login')
    else:
        form = ResetPasswordForm()
    return render(request, "resetpassword.html", {"form": form})

