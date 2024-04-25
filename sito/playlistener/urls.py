from django.urls import path
from . import views

"""
playlistener/login
playlistener/signup
playlistener/user/<username>/
playlistener/user/<username>/playlist/<id><nome>

"""
urlpatterns = [
    path('login/', views.loginView, name='login'),
    path('signup/', views.signupView, name='signup'),
    path('logout/', views.logoutView, name='logout'),
    path('user/<str:username>', views.user, name='user'),
]
