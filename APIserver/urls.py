from django.contrib import admin
from django.urls import path

from APIserver.views import registrationDetails
from . import views
urlpatterns = [
    path('registrationDetails/', views.registrationDetails, name= 'registrationDetails'),
    path('addToTeam/', views.addToTeam, name= 'addToTeam'),
    path('userRegistrationDetails/', views.userRegistrationDetails, name= 'userRegistrationDetails'),
    path('updateEvent/', views.updateEvent , name= 'updateEvent'),
    path('deleteTeam/', views.deleteTeam , name= 'deleteTeam'),
]