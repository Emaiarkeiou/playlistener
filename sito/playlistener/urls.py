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
    path('edit/', views.editView, name='edit'),
    path('logout/', views.logoutView, name='logout'),
    path('user/<str:username>', views.userView, name='user'),
    path('user/<str:username>/playlist/<str:id>/', views.playlistView, name='playlist'),
    path('user/<str:username>/playlist/', views.playlistView, name='playlist'),
]
