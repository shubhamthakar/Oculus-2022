from django.contrib import admin
from django.urls import path

from APIserver.views import registrationDetails
from . import views
urlpatterns = [
    path('registrationDetails/', views.registrationDetails, name= 'registrationDetails'),
    path('addToTeam/', views.addToTeam, name= 'addToTeam'),
    path('userRegistrationDetails/', views.userRegistrationDetails, name= 'userRegistrationDetails'),
    path('adminAddOfflineTeam/', views.adminAddOfflineTeam, name= 'adminAddOfflineTeam'),
    path('adminUpdateTeamMembers/', views.adminUpdateTeamMembers.as_view(), name='adminUpdateTeamMembers'),
    path('event/<str:eventName>', views.eventSummary, name = 'eventSummary')

]