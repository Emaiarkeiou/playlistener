from django.urls import path
from . import views

"""
playlistener/login
playlistener/signup
playlistener/user/<username>/
playlistener/user/<username>/playlist/<id><nome>

"""
urlpatterns = [
    path('login/', views.loginView, name='loginView'),
    path('loggingin/', views.loginReq, name='login'),
    path('loggingout/', views.logoutReq, name='logout'),
    path('signup/', views.signup, name='signup'),
    path('user/<str:username>', views.user, name='user'),
]