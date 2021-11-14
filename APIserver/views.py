from django.shortcuts import render

from rest_framework.response import Response
from rest_framework.decorators import api_view
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from pathlib import Path
import os
from django.conf import settings
from django.utils.crypto import get_random_string

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

            db.collection('Payments').document().set(data)
            print("payments created")
            code = get_random_string(length=8)

            Events = db.collection(u'Events')
            queriedEvents = Events.where(u'Title', u'==', request.data["eventName"]).stream()
            for event in queriedEvents:
                #print(f'{event.id} => {event.to_dict()}')
                id = event.id
                eventDict = event.to_dict()
            member = [request.data['userId']]

            #Login for isSolo and adding amt is pending
            data1 = {

                'TeamCode': code,
                'amount':0,
                'eventName':request.data['eventName'],
                'isSingle':eventDict['isSingle'],
                'maxMembers':eventDict['max'],
                'member':member,
                'paymentId':request.data['paymentId'],
            }
            db.collection('RegisteredTeams').document().set(data1)
            print("RegisteredTeams created")
            data2 = {

                'teamCode': code,
                'eventName': request.data['eventName'],
                'UserId': request.data['userId']
            }
            db.collection('TeamUsers').document().set(data2)
            print("TeamUsers created")


            return Response({"registrationDetails": data1})
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
            RegisteredTeams = db.collection(u'RegisteredTeams')

            #queriedTeams = RegisteredTeams.where(u'code', u'==', request.data["teamCode"])
            queriedTeams = RegisteredTeams.where(u'TeamCode', u'==', request.data["teamCode"]).stream()
            # print(queriedTeams.to_dict())
            queriedTeam = None
            id = None
            for teams in queriedTeams:
                print(f'{teams.id} => {teams.to_dict()}')
                id = teams.id
                queriedTeam = teams.to_dict()
            print(queriedTeam)
            if queriedTeam['eventName'] != request.data['eventName']:
                return Response({"Error":"Wrong Event"})
            uids = queriedTeam['member']
            print(uids)
            if len(uids) == int(queriedTeam['maxMembers']):
                return Response({"Error":"Cannot add more members. Max Member Reached"})
        
            db.collection(u'RegisteredTeams').document(id).update({u'member': firestore.ArrayUnion([request.data['userId']])})
            data = {
                'UserId':request.data['userId'],
                'eventName':request.data['eventName'],
                'teamCode':request.data["teamCode"]
            }
            db.collection('TeamUsers').document().set(data)
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
            Users = db.collection(u'Users')
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
            members = RegisteredTeamdict['member']
            memberDetails = []
            for member in members:
                userDetails = Users.where(u'uid', u'==', member).stream()
                mail = None
                name = None
                for uDetail in userDetails:
                    uDetail = uDetail.to_dict()
                    mail = uDetail['email']
                    name = uDetail['name']
                memberDetails.append({"name":name,"email":mail,"uid":member})
            RegisteredTeamdict['member'] = memberDetails

            return Response({"teamDetails":RegisteredTeamdict})

        except Exception as e: 
            print(e)
            return Response({"Message": "Unsuccessful"})

@api_view(['PATCH',])
def updateEvent(request):

    if request.method == 'PATCH':
        try:
            data = request.data
            Events = db.collection(u'Events')

            if 'Title' not in data:
                return Response({"Message": "Please Enter Event Name"})

            
            eventName = Events.where(u'Title', u'==', data["Title"]).stream()
            id = None
            for event in eventName:
                id = event.id
            updateEvent = db.collection(u'Events').document(id)

            if 'Category' in data:
                updateEvent.update({
                    u'Category': data['Category'],
                })
            
            if 'Date' in data:
                updateEvent.update({
                    u'Date': data['Date'],
                })

            if 'Description' in data:
                updateEvent.update({
                    u'Description': data['Description'],
                })

            if 'Prizes' in data:
                updateEvent.update({
                    u'Prizes': data['Prizes'],
                })
            return Response({"Message": "Changed Successfully"})

        except Exception as e: 
            print(e)
            return Response({"Message": "Unsuccessful"})

@api_view(['DELETE',])
def deleteTeam(request):
    if request.method == 'DELETE':
        TeamUsers = db.collection(u'TeamUsers') 
        RegisteredTeams = db.collection(u'RegisteredTeams')
        RegisteredTeam = RegisteredTeams.where(u'TeamCode', u'==', request.data['teamCode']).stream()
        TeamUser = TeamUsers.where(u'teamCode', u'==', request.data['teamCode']).stream()
        for regTeam in RegisteredTeam:
            RegisteredTeams.document(regTeam.id).delete()
        for userTeam in TeamUser:
            TeamUsers.document(userTeam.id).delete()
        return Response({"Message": "Deleted Successfully"})

@api_view(['PATCH',])
def updateTeamsDetails(request):

    if request.method == 'PATCH':
        try:
            data = request.data
            Events = db.collection(u'RegisteredTeams')
            Users = db.collection(u'Users')

            if 'TeamCode' not in data:
                return Response({"Message": "Please Enter Team Code"})

            
            teams = Events.where(u'TeamCode', u'==', data["TeamCode"]).stream()
            id = None
            for team in teams:
                id = team.id

            updateTeam = db.collection(u'RegisteredTeams').document(id)

            if 'amount' in data:
                updateTeam.update({
                    u'amount': data['amount'],
                })
            
            if 'maxMembers' in data:
                updateTeam.update({
                    u'maxMembers': data['maxMembers'],
                })
            updatedTeam = db.collection(u'RegisteredTeams').document(id).get().to_dict()
            event =  updatedTeam['eventName'] 
            members = updatedTeam['member']
            memberDetails = []
            for member in members:
                userDetails = Users.where(u'uid', u'==', member).stream()
                mail = None
                name = None
                for uDetail in userDetails:
                    uDetail = uDetail.to_dict()
                    mail = uDetail['email']
                    name = uDetail['name']
                memberDetails.append({"name":name,"email":mail,"uid":member})
            updatedTeam['member'] = memberDetails

            allTeams = db.collection(u'RegisteredTeams').where(u'eventName', u'==', event).stream()
            allTeamsList = []
            for team in allTeams:
                allTeamsList.append(team.to_dict())

            return Response({
                "updatedTeam": updatedTeam,
                "allTeams":allTeamsList
                })

        except Exception as e: 
            print(e)
            return Response({"Message": "Unsuccessful"})

@api_view(['POST',])
def addNotification(request):
    if request.method == 'POST':
        data = request.data
        Events = db.collection(u'Events')
        events = Events.where(u'eventName', u'==', data["eventName"]).stream()
        id = None
        for event in events:
            id = event.id
        data = {
            "imageURL" : data['imageURL'],
            "notificationText" : data['notificationText'],
            "timeStamp" : data['timeStamp']
        }
        db.collection(u'Events').document(id).collection(u'notification').add(data)
        return Response({"Message": "Unsuccessful"})