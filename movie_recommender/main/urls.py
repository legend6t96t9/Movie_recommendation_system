from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('services/', views.services, name='services'),
    path('about/', views.about_us, name='about'),
    path('contact/', views.contact, name='contact'),
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('recommend/', views.recommend_view, name='recommend'),
    
    path('forgot-password/', views.forgot_password, name='forgotpwd'),
    path('verify-otp/', views.verify_otp, name='verifyotp'),
    path('reset-password/', views.reset_password, name='resetpassword'),
]
