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
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.parsers import JSONParser
from rest_framework.views import APIView


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



@api_view(['POST',])
def adminAddOfflineTeam(request):

    if request.method == 'POST':
        #params {"eventName":, "email":, "phone":, "name":} returns teamCode
        try: 
            if not request.data["email"]:
                return Response({"Error":"Email not provided"})
            
            Usersdb = db.collection(u'Users')
            queriedUser = Usersdb.where(u'email', u'==', request.data["email"]).stream()
            userDict = None
            for user in queriedUser:
                #print(f'{event.id} => {event.to_dict()}')
                userDict = user.to_dict()
            if userDict == None:
                #Creating a new user
                data1 = {

                'email': request.data["email"],
                'name':request.data["name"],
                'phoneNumber':request.data["phone"],
                }
                docref = Usersdb.document()
                docref.set(data1)
                id = docref.id
                docref.set({u'uid': id}, merge=True)    ##adding uid = document id
                print("New user created")
            else:
                print("User already present")
            
            #getting users uid
            Usersdb = db.collection(u'Users')
            queriedUser = Usersdb.where(u'email', u'==', request.data["email"]).stream()
            userDict = None
            for user in queriedUser:
                #print(f'{event.id} => {event.to_dict()}')
                userDict = user.to_dict()
            uid = userDict["uid"]

            ##Adding to registeredteam
            code = get_random_string(length=8)
            Events = db.collection(u'Events')
            queriedEvents = Events.where(u'Title', u'==', request.data["eventName"]).stream()
            for event in queriedEvents:
                #print(f'{event.id} => {event.to_dict()}')
                id = event.id
                eventDict = event.to_dict()
            member = uid

            #Login for isSolo and adding amt is pending
            data1 = {

                'TeamCode': code,
                'amount':0,
                'eventName':request.data['eventName'],
                'isSingle':eventDict['isSingle'],
                'maxMembers':eventDict['max'],
                'member':member,
                'paymentId':"Offline",
            }
            db.collection('RegisteredTeams').document().set(data1)
            print("RegisteredTeams created")

            ##Adding to teamUsers
            data2 = {

                'teamCode': code,
                'eventName': request.data['eventName'],
                'UserId': uid
            }
            db.collection('TeamUsers').document().set(data2)
            print("TeamUsers created")

            return Response({"TeamCode": code})
        except Exception as e: 
            print(e)
            return Response({"Message": "Unsuccessful"})




@method_decorator(csrf_exempt, name='dispatch')
class adminUpdateTeamMembers(APIView):
    ## params {"email":, "teamCode", "eventName"}
    parser_classes = [JSONParser]

    def getUserId(self, email):
        Usersdb = db.collection(u'Users')
        queriedUser = Usersdb.where(u'email', u'==', email).stream()
        userDict = None
        
        for user in queriedUser:
            userDict = user.to_dict()
        if userDict == None:
            return None
        uid = userDict["uid"]
        return uid
        
    def post(self, request):
        '''cases: email not there, teamcode wrong, user already in a team, team full, add to team'''
        uid = self.getUserId(request.data["email"])    
        #Checking whether email is registered
        if uid == None:
            return Response({"error": "Email not registered"})


        #querying registered teams 
        RegisteredTeams = db.collection(u'RegisteredTeams').where(u'TeamCode', u'==', request.data["teamCode"]).stream()
        dict1 = None
        docref = None
        for team in RegisteredTeams:
            docid = team.id
            dict1 = team.to_dict()


        #Checking whether teamCode is correct
        if dict1 == None:
            return Response({"error": "Incorrect teamCode"})


        #Checking whether user is already a part a team for that event
        TeamUsers = db.collection(u'TeamUsers').where(u'UserId', u'==', uid).where(u'eventName', u'==', request.data["eventName"]).stream()
        teamUserDict = None
        for team in TeamUsers:
            teamUserDict = team.to_dict()
        if teamUserDict != None:
            return Response({"error":"User is already a part of team with teamcode "+str(teamUserDict["teamCode"])})
            



        arr = dict1["member"].copy()
        arr.append(uid)
        #Checking whether team is full
        if len(arr) > int(dict1["maxMembers"]):
            return Response({"Error": "Cannot add more than "+str(dict1["maxMembers"])+" members"})
        else:
            ##Adding memeber to team
            print("Intial dict",dict1)
            dict1["member"] = arr
            db.collection("RegisteredTeams").document(docid).set(dict1)
            RegisteredTeams = db.collection(u'RegisteredTeams').where(u'TeamCode', u'==', request.data["teamCode"]).stream()
            for team in RegisteredTeams:
                #print(f'{team.id} => {team.to_dict()}')
                docref = team
                dict1 = team.to_dict()

            ##Adding to teamUsers
            TeamUserAddDict = {

                "UserId":uid,
                "teamCode":request.data["teamCode"],
                "eventName":request.data["eventName"]
            }
            db.collection("TeamUsers").document().set(TeamUserAddDict)
            
            return Response({"registeredTeam":dict1})


    def delete(self, request):
        '''cases: email not there, not in teamUsers, delete entire team, delete team member'''
        uid = self.getUserId(request.data["email"])    
        #Checking whether email is registered
        if uid == None:
            return Response({"error": "Email not registered"})
        print(uid)
        TeamUsers = db.collection(u'TeamUsers').where(u'UserId', u'==', uid).where(u'eventName', u'==', request.data["eventName"]).stream()
        teamUserDict = None
        for team in TeamUsers:
            id = team.id
            teamUserDict = team.to_dict()
        if teamUserDict == None:
            return Response({"error": "User has not registered for the event"})
        #Deleting from teamUsers 
        TeamUsers = db.collection(u'TeamUsers').document(id).delete()

        teamCode = teamUserDict["teamCode"]
        RegisteredTeams = db.collection(u'RegisteredTeams').where(u'TeamCode', u'==', teamCode).stream()
        for team in RegisteredTeams:
            docid = team.id
            dict1 = team.to_dict()
        
        arr = dict1["member"].copy()
        
        if len(arr) == 1:
            RegisteredTeams = db.collection(u'RegisteredTeams').document(docid).delete()
            return Response({"Message": "Entire team deleted"})
        else:
            arr.remove(uid)
            print(arr)
            dict1["member"] = arr
            db.collection("RegisteredTeams").document(docid).set(dict1)


        return Response({"registeredTeam": dict1})

@api_view(['GET',])
def eventSummary(request, eventName):
    
    # Calculating totalAmount, teamCount, allTeamDetails
    RegisteredTeams = db.collection(u'RegisteredTeams').where(u'eventName', u'==', eventName).stream()
    allTeamDetails = {}
    totalAmount = 0
    teamCount = 0
    for team in RegisteredTeams:
        print(team.id)
        print(team.to_dict())
        allTeamDetails[team.id] = team.to_dict()
        totalAmount += allTeamDetails[team.id]['amount']
        teamCount += 1 
    
    # Calculating playerCount
    TeamUsers = db.collection(u'TeamUsers').where(u'eventName', u'==', eventName).stream()
    playerCount = 0
    for team in TeamUsers:
        id = team.id
        playerCount += 1




    return Response({'teamCount': teamCount, 'playerCount': playerCount, 'totalAmount': totalAmount, 'allTeamDetails': allTeamDetails})



