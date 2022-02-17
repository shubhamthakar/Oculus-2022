from django.contrib import admin
from django.urls import path

from APIserver.views import registrationDetails
from . import views
urlpatterns = [
    path('registrationDetails/', views.registrationDetails,
         name='registrationDetails'),
    path('addToTeam/', views.addToTeam, name='addToTeam'),
    path('adminAddOfflineTeam/', views.adminAddOfflineTeam,
         name='adminAddOfflineTeam'),
    path('adminUpdateTeamMembers/', views.adminUpdateTeamMembers.as_view(),
         name='adminUpdateTeamMembers'),
    path('event/<str:eventName>', views.eventSummary, name='eventSummary'),
    path('updateEvent/', views.updateEvent, name='updateEvent'),
    path('deleteTeam/', views.deleteTeam, name='deleteTeam'),
    path('updateTeamsDetails/', views.updateTeamsDetails,
         name='updateTeamsDetails'),
    path('addNotification/', views.addNotification, name='addNotification'),
    path('getEventDetails/<str:eventName>',
         views.getEventDetails, name='getEventDetails'),
    path('addChat/', views.addChat, name='addChat'),
    path('updatePaymentStatus/', views.updatePaymentStatus, name='updatePaymentStatus'),
    path('getChats/<str:eventName>', views.getChats, name='getChats'),
    path('getNofications/<str:eventName>',
         views.getNofications, name='getNofications'),
    path('updateChat/',
         views.updateChat, name='updateChat'),
    path("userRegistrationDetails/", views.userRegistrationDetails,
         name="userRegistrationDetails"),
     path("downloadCSV/<str:eventName>", views.downloadCSV,
         name="downloadCSV"),
]
