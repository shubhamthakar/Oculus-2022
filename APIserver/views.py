from django.shortcuts import render

from rest_framework.response import Response
from rest_framework.decorators import api_view
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from pathlib import Path
import os
from django.conf import settings

import os
dirname = os.path.dirname(__file__)
cred = credentials.Certificate(os.path.join(dirname, 'credentials.json'))
#cred = credentials.Certificate('C:/Users/Shubham Thakar/Documents/shubham files/Development/Oculus 2022/APIserver/credentials.json')
#cred = credentials.Certificate('C:/Users/KashMir/Desktop/Kashish/Oculus-2022/Oculus-2022/credentials.json')

firebase_admin.initialize_app(cred)
db = firestore.client()
@api_view(['POST',])
def registrationDetails(request):

    if request.method == 'POST':

        try: 
            
            data = {
            'paymentId': request.data['paymentId'],
            'eventName': request.data['eventName'],
            'userId': request.data['userId']
            }

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
        try:
            print("okay")
            RegisteredTeams = db.collection(u'RegisteredTeams')

            #queriedTeams = RegisteredTeams.where(u'code', u'==', request.data["teamCode"])
            queriedTeams = RegisteredTeams.where(u'TeamCode', u'==', u'Bhushan').stream()
            # print(queriedTeams.to_dict())
            queriedTeam = None
            id = None
            for teams in queriedTeams:
                print(f'{teams.id} => {teams.to_dict()}')
                id = teams.id
                queriedTeam = teams.to_dict()
            print(queriedTeam)
            if queriedTeam['eventName'] != request.data['eventName']:
                return Response({"Wrong Event"})
            uids = queriedTeam['member']
            print(uids)
            if len(uids) == int(queriedTeam['maxMembers']):
                return Response({"Cannot add more members. Max Member Reached"})
        
            db.collection(u'RegisteredTeams').document(id).update({u'member': firestore.ArrayUnion([request.data['userId']])})
            return Response({"Message": "Added Successfully"})
        except Exception as e: 
            print(e)
            return Response({"Message": "Unsuccessful"})

@api_view(['POST',])
def userRegistrationDetails(request):
    if request.method == 'POST':
        try:
            TeamUsers = db.collection(u'TeamUsers')
            queriedTeamUser = TeamUsers.where(u'UserId', u'==', request.data['userId']).where(u'eventName', u'==', request.data['eventName']).stream()
            
            RegisteredTeams = db.collection(u'RegisteredTeams')
            dict1 = None
            for team in queriedTeamUser:
                #print(f'{team.id} => {team.to_dict()}')
                id = team.id
                dict1 = team.to_dict()
            if dict1 == None:
                return Response({"Error":"User not a part of any team"})
            teamCode = dict1['teamCode']
            RegisteredTeam = RegisteredTeams.where(u'TeamCode', u'==', teamCode).stream()
            for teams in RegisteredTeam:
                #print(f'{teams.id} => {teams.to_dict()}')
                id = teams.id
                RegisteredTeamdict = teams.to_dict()
            return Response({"teamDetails":RegisteredTeamdict})

        except Exception as e: 
            print(e)
            return Response({"Message": "Unsuccessful"})


