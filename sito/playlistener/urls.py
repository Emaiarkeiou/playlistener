from django.urls import path
from . import views

"""
playlistener/
playlistener/login
playlistener/signin
playlistener/user/<name>/
playlistener/user/<name>/playlist/<id><nome>

"""
urlpatterns = [
    path('', views.index, name='index'),
]