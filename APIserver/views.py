
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
from wsgiref.util import FileWrapper
from django.http import HttpResponse
import pandas as pd


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
            RegisteredTeams = db.collection(u'RegisteredTeams')
            # print(request.data)
            # TeamUsersDetails = [team for team in RegisteredTeams.where(
            #     u'TeamName', u'==', request.data["teamName"]).stream()]
            # breakpoint()

            # if len(TeamUsersDetails) != 0:
            #     # print(TeamUsersDetails)
            #     return Response({"Message": "TeamName already exists"})

            # Validating Order
            PaymentDB = db.collection(u'Payments')
            queriedPay = PaymentDB.where(
                u'paymentId', u'==', request.data['paymentId']).stream()
            orderPresent = False
            for order in queriedPay:
                orderPresent = True
            if orderPresent:
                return Response({"Message": "Order already exists"})

            # Validating User
            TeamUsersdb = db.collection(u'TeamUsers')
            queriedUser1 = TeamUsersdb.where(
                u'email', u'==', request.data["email"]).where(u'eventName', u'==', request.data["eventName"]).stream()
            userpresent = False
            for user in queriedUser1:
                userpresent = True
            if userpresent:
                return Response({"Message": "User is already in a team for the event"})

            Users = db.collection(u'Users')
            userDetails = Users.where(
                u'uid', u'==', request.data['userId']).stream()
            mail = None
            for uDetail in userDetails:
                uDetail = uDetail.to_dict()
                mail = uDetail['email']
                print(mail)
            if mail is None:
                return Response({"Message": "UserId is incorrect. No such user exists"})

            Events = db.collection(u'Events')
            queriedEvents = Events.where(
                u'Title', u'==', request.data["eventName"]).stream()
            for event in queriedEvents:
                # print(f'{event.id} => {event.to_dict()}')
                id = event.id
                eventDict = event.to_dict()

            code = get_random_string(length=8)
            data = {
                'paymentId': request.data['paymentId'],
                'eventName': request.data['eventName'],
                'userId': request.data['userId'],
                'TeamCode': code,
                'email': mail,
                'amount': request.data['amount'],
                'whatsappLink': eventDict['whatsappLink']
            }

            db.collection('Payments').document().set(data)
            print("payments created")

            member = [request.data['userId']]

            # Login for isSolo and adding amt is pending
            data1 = {
                'TeamCode': code,
                'amount': request.data['amount'],
                'eventName': request.data['eventName'],
                'isSingle': eventDict['isSingle'],
                'maxMembers': request.data['maxMembers'],
                'member': member,
                'paymentId': request.data['paymentId'],
                'TeamName': request.data["teamName"],
                'paymentStatus': request.data['paymentStatus'],
                'slotTime': request.data['slotTime'],
                'link': request.data['link']
            }
            db.collection('RegisteredTeams').document().set(data1)

            print("RegisteredTeams created")
            data2 = {
                'email': mail,
                'teamCode': code,
                'eventName': request.data['eventName'],
                'UserId': request.data['userId']
            }
            db.collection('TeamUsers').document().set(data2)
            print("TeamUsers created")
            try:
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
            except:
                pass

            return Response({"registrationDetails": data1})
        except Exception as e:
            print(e)
            return Response({"Message": "Unsuccessful"})


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
    # update availableSlots
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
            if 'availableSlots' in data:
                updateEvent.update({
                    u'availableSlots': data['availableSlots'],
                })

            if 'whatsappLink' in data:
                updateEvent.update({
                    u'whatsappLink': data['whatsappLink'],
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

            if 'teamName' in data:
                updateTeam.update({
                    u'TeamName': data['teamName'],
                })

            if 'amount' in data:
                updateTeam.update({
                    u'amount': data['amount'],
                })

            if 'paymentStatus' in data:
                updateTeam.update({
                    u'paymentStatus': data['paymentStatus'],
                })

            if 'maxMembers' in data:
                updateTeam.update({
                    u'maxMembers': data['maxMembers'],
                })
            if 'slotTime' in data:
                updateTeam.update({
                    u'slotTime': data['slotTime'],
                })

            if 'link' in data:
                updateTeam.update({
                    u'link': data['link'],
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
        # params {"eventName":, "email":, "phone":, "name":, "paymentStatus":, "teamName":, "amount":, "maxMembers", "slotTime"} returns teamCode
        try:
            if not request.data["email"]:
                return Response({"Message": "Email not provided"})

            TeamUsersdb = db.collection(u'TeamUsers')
            queriedUser1 = TeamUsersdb.where(
                u'email', u'==', request.data["email"]).where(u'eventName', u'==', request.data["eventName"]).stream()
            userpresent = False
            for user in queriedUser1:
                userpresent = True
            if userpresent:
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
                # data1 = {

                #     'email': request.data["email"],
                #     'name': request.data["name"],
                #     'phoneNumber': request.data["phone"],
                # }
                # docref = Usersdb.document()
                # docref.set(data1)
                # id = docref.id
                # # adding uid = document id
                # docref.set({u'uid': id}, merge=True)

                print("No user present")
                return Response({"Message": "User Does not exists"})

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
            mail = userDict["email"]

            Events = db.collection(u'Events')
            queriedEvents = Events.where(
                u'Title', u'==', request.data["eventName"]).stream()
            for event in queriedEvents:
                #print(f'{event.id} => {event.to_dict()}')
                id = event.id
                eventDict = event.to_dict()

            # Adding to registeredteam
            code = get_random_string(length=8)

            data = {
                'paymentId': "offline",
                'eventName': request.data['eventName'],
                'userId': uid,
                'TeamCode': code,
                'email': mail,
                'amount': request.data['amount'],
                'whatsappLink': eventDict['whatsappLink']
            }

            db.collection('Payments').document().set(data)
            print("payments created")

            member = []
            member.append(uid)

            # Login for isSolo and adding amt is pending
            data1 = {

                'TeamCode': code,
                'TeamName': request.data['teamName'],
                'amount': request.data['amount'],
                'eventName': request.data['eventName'],
                'isSingle': eventDict['isSingle'],
                'maxMembers': request.data["maxMembers"],
                'member': member,
                'paymentId': "Offline",
                'paymentStatus': request.data['paymentStatus'],
                'slotTime': request.data['slotTime'],
                'link': request.data['link']
            }
            db.collection('RegisteredTeams').document().set(data1)
            print("RegisteredTeams created")

            # Adding to teamUsers
            data2 = {

                'teamCode': code,
                'eventName': request.data['eventName'],
                'UserId': uid,
                'email': request.data['email']
            }
            db.collection('TeamUsers').document().set(data2)
            print("TeamUsers created")
            try:
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
            except:
                pass
            return Response({"registrationDetails": data1})

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

        if dict1["eventName"] != request.data["eventName"]:
            return Response({"Message": "Incorrect teamcode"})

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
    users = db.collection(u'Users').stream()
    allUsers = []
    for user in users:
        allUsers.append(user.to_dict())
    # print(u)

    votes_db = db.collection(u'Voting').stream()
    allVotes = []
    for vote in votes_db:
        allVotes.append(vote.to_dict())

    for team in RegisteredTeams:
        teamDict = team.to_dict()
        # print(teamDict)

        voteCount = 0
        for vote in allVotes:
            if vote['teamCode'] == teamDict['TeamCode']:
                voteCount += 1

        # votingDetails = db.collection(u'Voting').where(
        #     u'teamCode', u'==', teamDict['TeamCode']).stream()
        # voteCount = 0
        # for votes in votingDetails:
        #     voteCount += 1
        teamDict['voteCount'] = voteCount
        memberList = []

        for player in teamDict["member"]:
            for i in allUsers:
                if i['uid'] == player:
                    memberList.append(i)
                    break
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
            db.collection(u'Chat').document().set(data)

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


@api_view(['POST'])
def updatePaymentStatus(request):
    # params {"paymentStatus":, "teamCode":}
    try:
        RegisteredTeams = db.collection(u'RegisteredTeams').where(
            u'TeamCode', u'==', request.data["teamCode"]).stream()
        data2 = {}
        for teams in RegisteredTeams:
            data2 = teams.to_dict()
            docid = teams.id
        data2["paymentStatus"] = request.data["paymentStatus"]
        db.collection(u'RegisteredTeams').document(docid).set(data2)

        return Response({"Message": "Updated Sucessfully"})
    except:
        return Response({"Message": "Could not update payment status"})


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
        print('Item is: ', item.id)
        query_data = item.to_dict()
        query_data['docId'] = item.id
        data.append(query_data)

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
    # getting chat from docId
    if request.method == 'PATCH':
        try:
            data = request.data
            id = data['docId']

            if 'answer' not in data:
                return Response({"Message": "Please Send Answer"})
            getChat = db.collection(u'Chat').document(id)
            getChat.update({u'answer': data['answer']})

            return Response({"Message": "Successful"})
        except Exception as e:
            print(e)
            return Response({"Message": "Unsuccessful"})

@api_view(['GET',])
def downloadCSV(request, eventName):
    # Calculating totalAmount, teamCount, allTeamDetails
    RegisteredTeams = db.collection(u'RegisteredTeams').where(
        u'eventName', u'==', eventName).stream()
    allTeamDetails = []
    totalAmount = 0
    teamCount = 0
    counter = 0
    users = db.collection(u'Users').stream()
    allUsers = []
    for user in users:
        allUsers.append(user.to_dict())
    # print(u)

    votes_db = db.collection(u'Voting').stream()
    allVotes = []
    for vote in votes_db:
        allVotes.append(vote.to_dict())

    for team in RegisteredTeams:
        teamDict = team.to_dict()
        # print(teamDict)

        voteCount = 0
        for vote in allVotes:
            if vote['teamCode'] == teamDict['TeamCode']:
                voteCount += 1

        # votingDetails = db.collection(u'Voting').where(
        #     u'teamCode', u'==', teamDict['TeamCode']).stream()
        # voteCount = 0
        # for votes in votingDetails:
        #     voteCount += 1
        teamDict['voteCount'] = voteCount
        memberList = []

        for player in teamDict["member"]:
            for i in allUsers:
                if i['uid'] == player:
                    memberList.append(i)
                    break
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

    file_path = "./APIserver/files/eventSummary.csv"
    FilePointer = open(file_path,"w+")

    normalizedTeamDetails = []
    for team in allTeamDetails:
        ele = {}
        for member in team['member']:
            for k,v in member.items():
                ele[k] = v
        for k,v in team.items():
            if k!= "member":
                ele[k] = v
        normalizedTeamDetails.append(ele)
    
    df = pd.DataFrame(normalizedTeamDetails)

    print(df)
    df.to_csv(FilePointer)

    detailsDict = {}
    detailsDict["totalAmount"] = totalAmount
    detailsDict["playerCount"] = playerCount
    detailsDict["teamCount"] = teamCount

    df = pd.DataFrame(detailsDict, index=[0])
    df.to_csv(FilePointer)
    FilePointer.close()
    FilePointer = open(file_path, "r")

    

    response = HttpResponse(FileWrapper(FilePointer),content_type='application/csv')
    response['Content-Disposition'] = 'attachment; filename=eventSummary.csv'

    return response
