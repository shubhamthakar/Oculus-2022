from django.shortcuts import render

# Create your views here.

# import pyrebase

# config = {
#   "apiKey":"AIzaSyCda49a3JCXnyOhcmLlv4nnLcXVBbJhg_0",
#   "authDomain": "oculus2022-75997.firebaseapp.com",
#   "projectId": "oculus2022-75997",
#   "storageBucket": "oculus2022-75997.appspot.com",
#   "messagingSenderId": "379210659404",
#   "appId": "1:379210659404:web:c5c2b6c56af7a895f866e9",
#   "measurementId": "G-Q0M6S2CCW0"
# }
# firebase = pyrebase.initialize_app(config)
# db = firebase.database()
# db.child("users").child("Morty")

# def registrationDetails(request, paymentId, eventName, userId):
#     data = {"name": "Mortimer 'Morty' Smith"}
#     db.child("Users").push(data)
from rest_framework.response import Response
from rest_framework.decorators import api_view
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from pathlib import Path
import os
from django.conf import settings


#cred = credentials.Certificate(os.path.join(settings.BASE_DIR,'/OculusSite/creditials.json'))
cred = credentials.Certificate('C:/Users/Shubham Thakar/Documents/shubham files/Development/Oculus 2022/APIserver/credentials.json')
firebase_admin.initialize_app(cred)
db = firestore.client()
@api_view(['POST',])
def registrationDetails(request):

    if request.method == 'POST':

        #print(request.data)
        try: 
            
            data = {
            'paymentId': request.data['paymentId'],
            'eventName': request.data['eventName'],
            'userId': request.data['userId']
            }

            # Add a new doc in collection 'cities' with ID 'LA'
            print(db.collection('Payments').document().set(data))
            return Response({"Message": "Added Successfully"})
        except Exception as e: 
            print(e)
            return Response({"Message": "Unsuccessful"})

        # cars_ref = db.collection(u'Users')
        # docs = cars_ref.stream()
        # cars_list = []
        # for doc in docs:
        #     cars_list.append(doc.to_dict())
        #     print(u'{} => {}'.format(doc.id, doc.to_dict()))

@api_view(['POST',])
def addToTeam(request):
    if request.method == 'POST':
        # Create a reference to the cities collection
        RegisteredTeams = db.collection('RegisteredTeams')

        # Create a query against the collection
        #queriedTeams = RegisteredTeams.where(u'code', u'==', request.data["teamCode"])
        queriedTeams = RegisteredTeams.where(u'code', u'==', 'Bhushan')
        print(queriedTeams)