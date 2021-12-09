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
import datetime


import os
dirname = os.path.dirname(__file__)
cred = credentials.Certificate(os.path.join(dirname, 'credentials.json'))
#cred = credentials.Certificate('C:/Users/Shubham Thakar/Documents/shubham files/Development/Oculus 2022/APIserver/credentials.json')
#cred = credentials.Certificate('C:/Users/KashMir/Desktop/Kashish/Oculus-2022/Oculus-2022/credentials.json')

firebase_admin.initialize_app(cred)
db = firestore.client()


@api_view(['POST', ])
def registrationDetails(request):
    if request.method == 'POST':

        try:
            TeamUsers = db.collection(u'TeamUsers')
            TeamUsersDetails = TeamUsers.where(
                u'teamName', u'==', request.data["teamName"]).stream()
            # if TeamUsersDetails != None:
            #     return Response({"Message": "TeamName already exists"})
            # request.data["teamName"]
            data = {
                'paymentId': request.data['paymentId'],
                'eventName': request.data['eventName'],
                'userId': request.data['userId'],
                'teamName': request.data["teamName"]
            }

            db.collection('Payments').document().set(data)
            print("payments created")
            code = get_random_string(length=8)

            Events = db.collection(u'Events')
            queriedEvents = Events.where(
                u'Title', u'==', request.data["eventName"]).stream()
            for event in queriedEvents:
                #print(f'{event.id} => {event.to_dict()}')
                id = event.id
                eventDict = event.to_dict()
            member = [request.data['userId']]

            # Login for isSolo and adding amt is pending
            data1 = {
                'TeamCode': code,
                'amount': 0,
                'eventName': request.data['eventName'],
                'isSingle': eventDict['isSingle'],
                'maxMembers': eventDict['max'],
                'member': member,
                'paymentId': request.data['paymentId'],
                'TeamName': request.data["teamName"]
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

            if "inviteCode" in request.data:
                id = None
                code = request.data["inviteCode"]
                Users = db.collection(u'Users')
                userDetails = Users.where(
                    u'inviteCode', u'==', request.data["inviteCode"]).stream()
                for uDetail in userDetails:
                    id = uDetail.id
                user = db.collection(u'Users').document(id)
                user.update({"invited": firestore.Increment(1)})

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


@api_view(['POST', ])
def addToTeam(request):
    if request.method == 'POST':
        try:
            RegisteredTeams = db.collection(u'RegisteredTeams')

            #queriedTeams = RegisteredTeams.where(u'code', u'==', request.data["teamCode"])
            queriedTeams = RegisteredTeams.where(
                u'TeamCode', u'==', request.data["teamCode"]).stream()
            # print(queriedTeams.to_dict())
            queriedTeam = None
            id = None
            for teams in queriedTeams:
                print(f'{teams.id} => {teams.to_dict()}')
                id = teams.id
                queriedTeam = teams.to_dict()
            print(queriedTeam)
            if queriedTeam['eventName'] != request.data['eventName']:
                return Response({"Message": "Wrong Event"})
            uids = queriedTeam['member']
            print(uids)
            if len(uids) == int(queriedTeam['maxMembers']):
                return Response({"Message": "Cannot add more members. Max Member Reached"})

            db.collection(u'RegisteredTeams').document(id).update(
                {u'member': firestore.ArrayUnion([request.data['userId']])})
            data = {
                'UserId': request.data['userId'],
                'eventName': request.data['eventName'],
                'teamCode': request.data["teamCode"]
            }
            db.collection('TeamUsers').document().set(data)
            return Response({"Message": "Added Successfully"})
        except Exception as e:
            print(e)
            return Response({"Message": "Unsuccessful"})


@api_view(['POST', ])
def userRegistrationDetails(request):
    if request.method == 'POST':
        try:
            TeamUsers = db.collection(u'TeamUsers')
            queriedTeamUser = TeamUsers.where(u'UserId', u'==', request.data['userId']).where(
                u'eventName', u'==', request.data['eventName']).stream()

            RegisteredTeams = db.collection(u'RegisteredTeams')
            Users = db.collection(u'Users')
            dict1 = None
            for team in queriedTeamUser:
                #print(f'{team.id} => {team.to_dict()}')
                id = team.id
                dict1 = team.to_dict()
            if dict1 == None:
                return Response({"Message": "User not a part of any team"})
            teamCode = dict1['teamCode']
            RegisteredTeam = RegisteredTeams.where(
                u'TeamCode', u'==', teamCode).stream()
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
                memberDetails.append(
                    {"name": name, "email": mail, "uid": member})
            RegisteredTeamdict['member'] = memberDetails

            return Response({"teamDetails": RegisteredTeamdict})

        except Exception as e:
            print(e)
            return Response({"Message": "Unsuccessful"})


@api_view(['PATCH', ])
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

            if 'faq' in data:
                updateEvent.update({
                    u'faq': data['faq'],
                })

            if 'Fee' in data:
                updateEvent.update({
                    u'Fee': data['Fee'],
                })
            if 'rules' in data:
                updateEvent.update({
                    u'rules': data['rules'],
                })
            return Response({"Message": "Changed Successfully"})

        except Exception as e:
            print(e)
            return Response({"Message": "Unsuccessful"})


@api_view(['DELETE', ])
def deleteTeam(request):
    if request.method == 'DELETE':
        TeamUsers = db.collection(u'TeamUsers')
        RegisteredTeams = db.collection(u'RegisteredTeams')
        RegisteredTeam = RegisteredTeams.where(
            u'TeamCode', u'==', request.data['teamCode']).stream()
        TeamUser = TeamUsers.where(
            u'teamCode', u'==', request.data['teamCode']).stream()
        for regTeam in RegisteredTeam:
            RegisteredTeams.document(regTeam.id).delete()
        for userTeam in TeamUser:
            TeamUsers.document(userTeam.id).delete()
        return Response({"Message": "Deleted Successfully"})


@api_view(['PATCH', ])
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
            updatedTeam = db.collection(
                u'RegisteredTeams').document(id).get().to_dict()
            event = updatedTeam['eventName']
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
                memberDetails.append(
                    {"name": name, "email": mail, "uid": member})
            updatedTeam['member'] = memberDetails

            allTeams = db.collection(u'RegisteredTeams').where(
                u'eventName', u'==', event).stream()
            allTeamsList = []
            for team in allTeams:
                allTeamsList.append(team.to_dict())

            return Response({
                "updatedTeam": updatedTeam,
                "allTeams": allTeamsList
            })
        except Exception as e:
            print(e)
            return Response({"Message": "Unsuccessful"})


@api_view(['POST', ])
def adminAddOfflineTeam(request):
    # addUserHere
    if request.method == 'POST':
        # params {"eventName":, "email":, "phone":, "name":} returns teamCode
        try:
            if not request.data["email"]:
                return Response({"Message": "Email not provided"})

            TeamUsersdb = db.collection(u'TeamUsers')
            queriedUser1 = TeamUsersdb.where(
                u'email', u'==', request.data["email"]).stream()
            for user in queriedUser1:
                print("For loop: ", user)
            print(request.data["email"], queriedUser1)
            if queriedUser1 != None:
                return Response({"Message": "User is already in a team for the event"})

            Usersdb = db.collection(u'Users')
            queriedUser = Usersdb.where(
                u'email', u'==', request.data["email"]).stream()
            userDict = None
            for user in queriedUser:
                #print(f'{event.id} => {event.to_dict()}')
                userDict = user.to_dict()
            if userDict == None:
                # Creating a new user
                data1 = {

                    'email': request.data["email"],
                    'name': request.data["name"],
                    'phoneNumber': request.data["phone"],
                }
                docref = Usersdb.document()
                docref.set(data1)
                id = docref.id
                # adding uid = document id
                docref.set({u'uid': id}, merge=True)
                print("New user created")
            else:
                print("User already present")

            # getting users uid
            Usersdb = db.collection(u'Users')
            queriedUser = Usersdb.where(
                u'email', u'==', request.data["email"]).stream()
            userDict = None
            for user in queriedUser:
                #print(f'{event.id} => {event.to_dict()}')
                userDict = user.to_dict()
            uid = userDict["uid"]

            # Adding to registeredteam
            code = get_random_string(length=8)
            Events = db.collection(u'Events')
            queriedEvents = Events.where(
                u'Title', u'==', request.data["eventName"]).stream()
            for event in queriedEvents:
                #print(f'{event.id} => {event.to_dict()}')
                id = event.id
                eventDict = event.to_dict()
            member = []
            member.append(uid)

            # Login for isSolo and adding amt is pending
            data1 = {

                'TeamCode': code,
                'amount': 0,
                'eventName': request.data['eventName'],
                'isSingle': eventDict['isSingle'],
                'maxMembers': eventDict['max'],
                'member': member,
                'paymentId': "Offline",
            }
            db.collection('RegisteredTeams').document().set(data1)
            print("RegisteredTeams created")

            # Adding to teamUsers
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
    # params {"email":, "teamCode", "eventName"}
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
        print(request.data)
        uid = self.getUserId(request.data["email"])
        # Checking whether email is registered
        if uid == None:
            return Response({"Message": "Email not registered"})

        # querying registered teams
        RegisteredTeams = db.collection(u'RegisteredTeams').where(
            u'TeamCode', u'==', request.data["teamCode"]).stream()
        dict1 = None
        docref = None
        for team in RegisteredTeams:
            docid = team.id
            dict1 = team.to_dict()

        # Checking whether teamCode is correct
        if dict1 == None:
            return Response({"Message": "Incorrect teamCode"})

        # Checking whether user is already a part a team for that event
        TeamUsers = db.collection(u'TeamUsers').where(u'UserId', u'==', uid).where(
            u'eventName', u'==', request.data["eventName"]).stream()
        teamUserDict = None
        for team in TeamUsers:
            teamUserDict = team.to_dict()
        if teamUserDict != None:
            return Response({"Message": "User is already a part of team with teamcode "+str(teamUserDict["teamCode"])})

        arr = dict1["member"].copy()
        arr.append(uid)
        # Checking whether team is full
        if len(arr) > int(dict1["maxMembers"]):
            return Response({"Message": "Cannot add more than "+str(dict1["maxMembers"])+" members"})
        else:
            # Adding memeber to team
            print("Intial dict", dict1)
            dict1["member"] = arr
            db.collection("RegisteredTeams").document(docid).set(dict1)
            RegisteredTeams = db.collection(u'RegisteredTeams').where(
                u'TeamCode', u'==', request.data["teamCode"]).stream()
            for team in RegisteredTeams:
                #print(f'{team.id} => {team.to_dict()}')
                docref = team
                dict1 = team.to_dict()

            # Adding to teamUsers
            TeamUserAddDict = {

                "UserId": uid,
                "teamCode": request.data["teamCode"],
                "eventName": request.data["eventName"]
            }
            db.collection("TeamUsers").document().set(TeamUserAddDict)

            return Response({"registeredTeam": dict1})

    def delete(self, request):
        print(request.data)
        '''cases: email not there, not in teamUsers, delete entire team, delete team member'''
        uid = self.getUserId(request.data["email"])
        # Checking whether email is registered
        if uid == None:
            return Response({"Message": "Email not registered"})
        print(uid)
        TeamUsers = db.collection(u'TeamUsers').where(u'UserId', u'==', uid).where(
            u'eventName', u'==', request.data["eventName"]).stream()
        teamUserDict = None
        for team in TeamUsers:
            id = team.id
            teamUserDict = team.to_dict()
        if teamUserDict == None:
            return Response({"Message": "User has not registered for the event"})
        # Deleting from teamUsers
        TeamUsers = db.collection(u'TeamUsers').document(id).delete()

        teamCode = teamUserDict["teamCode"]
        RegisteredTeams = db.collection(u'RegisteredTeams').where(
            u'TeamCode', u'==', teamCode).stream()
        for team in RegisteredTeams:
            docid = team.id
            dict1 = team.to_dict()

        arr = dict1["member"].copy()

        if len(arr) == 1:
            RegisteredTeams = db.collection(
                u'RegisteredTeams').document(docid).delete()
            return Response({"Message": "Entire team deleted"})
        else:
            arr.remove(uid)
            print(arr)
            dict1["member"] = arr
            db.collection("RegisteredTeams").document(docid).set(dict1)

        return Response({"registeredTeam": dict1})


@api_view(['GET', ])
def eventSummary(request, eventName):

    # Calculating totalAmount, teamCount, allTeamDetails
    RegisteredTeams = db.collection(u'RegisteredTeams').where(
        u'eventName', u'==', eventName).stream()
    allTeamDetails = []
    totalAmount = 0
    teamCount = 0
    counter = 0

    for team in RegisteredTeams:
        teamDict = team.to_dict()
        print(teamDict)

        memberList = []
        for player in teamDict["member"]:
            currentUser = db.collection(u'Users').where(
                u'uid', u'==', player).stream()
            for user in currentUser:
                print(user.to_dict())
                memberList.append(user.to_dict())
        teamDict["member"] = memberList

        print(len(memberList), teamDict["maxMembers"])
        if len(memberList) == teamDict["maxMembers"]:
            teamDict["isComplete"] = True
        else:
            teamDict["isComplete"] = False
        allTeamDetails.append(teamDict)
        totalAmount += allTeamDetails[counter]['amount']
        teamCount += 1
        counter += 1
        # team["memberList"] = memberList
    # Calculating playerCount
    TeamUsers = db.collection(u'TeamUsers').where(
        u'eventName', u'==', eventName).stream()
    playerCount = 0
    for team in TeamUsers:
        id = team.id
        playerCount += 1

    return Response({'teamCount': teamCount, 'playerCount': playerCount, 'totalAmount': totalAmount, 'allTeamDetails': allTeamDetails})


@api_view(['POST', ])
def addNotification(request):
    if request.method == 'POST':
        try:
            data = request.data
            data = {
                "event": data['event'],
                "imgUrl": data['imgUrl'],
                "text": data['text'],
                "date": data['date'],
                "reads": []
            }
            db.collection(u'Notification').document().set(data)

            return Response({"Message": "Successful"})
        except Exception as e:
            print(e)
            return Response({"Message": "Unsuccessful"})


@api_view(['POST', ])
def addChat(request):
    if request.method == 'POST':
        try:
            data = request.data
            data = {
                "event": data['event'],
                "isRead": False,
                "question": data['question'],
                "date": data['date'],
                "answer": data['answer'],
                "userId": "",
                "id": data["id"]
            }
            print(data)
            # db.collection(u'Chat').document().set(data)

            return Response({"Message": "Successful"})
        except Exception as e:
            print(e)
            return Response({"Message": "Unsuccessful"})


@api_view(['GET'])
def getEventDetails(request, eventName):
    eventDetails = db.collection(u'Events').where(
        u'Title', u'==', eventName).stream()
    print(eventDetails)
    data = {}
    for item in eventDetails:
        data = item.to_dict()
        # print("Printing itemns")
        print(data)
    return Response(data)


@api_view(['GET'])
def getChats(request, eventName):
    print(eventName)

    if eventName == "null":
        return Response({"Message": "Event name is not defined"})
    chats = db.collection(u'Chat').where(
        u'event', u'==', eventName).stream()
    print("Chats: ", chats)
    data = []
    for item in chats:
        data.append(item.to_dict())

    return Response(data)


@api_view(['GET'])
def getNofications(request, eventName):
    print(eventName)

    if eventName == "null":
        return Response({"Message": "Event name is not defined"})
    notifs = db.collection(u'Notification').where(
        u'event', u'==', eventName).stream()
    print("Notifications: ", notifs)
    data = []
    for item in notifs:
        data.append(item.to_dict())

    print(data)
    return Response(data)


@api_view(['PATCH', ])
def updateChat(request):
    if request.method == 'PATCH':
        try:
            data = request.data
            chats = db.collection(u'Chat').where(
                u'id', u'==', data['id']).stream()
            id = None
            for chat in chats:
                id = chat.id

            if 'answer' not in data:
                return Response({"Message": "Please Send Answer"})
            getChat = db.collection(u'Chat').document(id)
            getChat.update({u'answer': data['answer']})

            return Response({"Message": "Successful"})
        except Exception as e:
            print(e)
            return Response({"Message": "Unsuccessful"})
