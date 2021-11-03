from django.contrib import admin
from django.urls import path

from APIserver.views import registrationDetails
from . import views
urlpatterns = [
    path('registrationDetails/', views.registrationDetails, name= 'registrationDetails'),
    path('addToTeam/', views.addToTeam, name= 'addToTeam'),
]