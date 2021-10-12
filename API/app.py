from dns.rdatatype import NULL
from flask import(
    Flask, redirect, render_template, url_for, request, jsonify
)
import os
import json
import requests
from pymongo import MongoClient
import certifi
from gp_hashing.generateHash import generateHash
import datetime
import uuid

ca = certifi.where()

app = Flask(__name__, static_url_path="")
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0
app.secret_key = "msaya1269"
APP_ROOT = os.path.dirname(os.path.abspath(__file__))

client = MongoClient(
    "MONGODB URL", tlsCAFile=ca)
socialMediaDataBase = client.get_database("socialMediaDataBase")

### REGISTER ###
@app.route("/api/user/register", methods=["POST"])
def register():
    form = request.form
    name = form.get("name")
    email = form.get("email")
    dob = form.get("dob")
    pinCode = form.get("pinCode")
    gender = form.get("gender")
    password = form.get("password")
    confirmPassword = form.get("confirmPassword")
    userId = ""
    allUser = socialMediaDataBase.usersDetails
    ifEmailAlreadyExist = allUser.find_one({"email": email})
    status = ""
    error = ""
    if ifEmailAlreadyExist == None:
        if password == confirmPassword:
            userId = str(uuid.uuid4())
            newUser = {
                "userId": userId,
                "email": email,
                "name": name,
                "gender": gender,
                "pinCode": pinCode,
                "dob": dob,
                "password": generateHash(password),
                "friendList": []
            }
            allUser.insert_one(newUser)
            status = "success"
            error = "no error"
        else:
            status = "fail"
            error = "password mismatched"
    else:
        status = "fail"
        error = "email already exist"
    resp = {
        "status": status,
        "error": error
    }
    return jsonify(resp)


### LOGIN ###
@app.route("/api/user/login", methods=["POST"])
def login():
    form = request.form
    email = form.get("email")
    hashedPassword = generateHash(form.get("password"))
    # hashedPassword = form.get("password")
    allUser = socialMediaDataBase["usersDetails"]
    user = allUser.find_one({"email": email})
    status = ""
    error = ""
    userId = ""
    if user == None:
        status = "fail"
        error = "user not exist"
    elif user["password"] == hashedPassword:
        status = "success"
        error = "no error"
        userId = user["userId"]
    else:
        status = "fail"
        error = "password mismatch"
    resp = {
        "status": status,
        "error": error,
        "userId": userId
    }
    return jsonify(resp)


### NEW FRIEND REQUEST ###
@app.route("/api/new/request/add/<senderId>/<recieverId>", methods=["POST"])
def newRequestAdd(senderId, recieverId):
    allRequests = socialMediaDataBase.friendRequests
    sender = socialMediaDataBase.usersDetails.find_one({"userId":senderId})
    newRequest = {
        "requestId": str(uuid.uuid4()),
        "senderId": senderId,
        "recieverId": recieverId,
        "requestStatus": 0,
        "senderName":sender["name"]
    }
    allRequests.insert_one(newRequest)
    resp = {
        "status": "success",
        "recieverId":recieverId
    }
    return jsonify(resp)

### CHECK SENDER AND RECIVER OF A REQUEST ###
@app.route("/api/check/request/<userId1>/<userId2>",methods=["GET"])
def checkRequest(userId1,userId2):
    allRequests = socialMediaDataBase.friendRequests
    sender=-1
    reciever=-1
    status=""
    flag=0
    requestId=""
    for request in allRequests.find():
        if request["senderId"]==userId1 and request["recieverId"]==userId2:
            flag=1
            sender=1
            reciever=2
            requestId=request["requestId"]
            break
        elif request["senderId"]==userId2 and request["recieverId"]==userId1:
            flag=1
            sender=2
            reciever=1
            requestId=request["requestId"]
            break
    resp ={
        "sender":sender,
        "reciever":reciever,
        "flag":flag,
        "status":"success",
        "requestId":requestId
    }
    return jsonify(resp)

### GET ALL RECIEVED REQUESTS OF A USER ###
@app.route("/api/get/requets/<userId>",methods=["GET"])
def getAllRecievedRequest(userId):
    allRequests = socialMediaDataBase.friendRequests
    allRecievedRequests=[]
    for request in allRequests.find():
        if request["recieverId"]==userId and request["requestStatus"]==0:
            temp = {
                "requestId":request["requestId"],
                "senderId":request["senderId"],
                "recieverId":userId,
                "senderName":request["senderName"]
            }
            allRecievedRequests.append(temp)
    resp = {
        "status":"success",
        "count":len(allRecievedRequests),
        "recievedRequests":allRecievedRequests
    }
    return jsonify(resp)

### ACCEPT FRIEND REQUEST ###
@app.route("/api/friendrequest/accept/<requestId>", methods=["POST"])
def acceptFriendRequest(requestId):
    allRequests = socialMediaDataBase.friendRequests
    requestToBeAccepted = allRequests.find_one({"requestId": requestId})
    allUser = socialMediaDataBase.usersDetails
    allUser.update({"userId": requestToBeAccepted["senderId"]}, {
        "$push": {"friendList": requestToBeAccepted["recieverId"]}})
    allUser.update({"userId": requestToBeAccepted["recieverId"]}, {
        "$push": {"friendList": requestToBeAccepted["senderId"]}})
    # allRequests.delete_one({"requestId": requestId})
    allRequests.update_one({"requestId":requestId},{"$set":{"requestStatus":1}})
    resp = {
        "status": "success",
        "senderId":requestToBeAccepted["senderId"]
    }
    return jsonify(resp)


### MUTUAL FRIEND ###
@app.route("/api/get/mutualfriend/<userId1>/<userId2>", methods=["GET"])
def getMutualFriend(userId1, userId2):
    allUser = socialMediaDataBase.usersDetails
    user1 = allUser.find_one({"userId": userId1})
    user2 = allUser.find_one({"userId": userId2})
    status = ""
    error = ""
    mutualFriendsId = []
    mutualFriends = []
    if user1 == None or user2 == None:
        error = "invalid user id"
        status = "fail"
    else:
        friendListOfUser1 = user1["friendList"]
        friendListOfUser2 = user2["friendList"]
        mutualFriendsId = list(set(friendListOfUser1) & set(friendListOfUser2))
        error = "no error"
        status = "success"
        for user in allUser.find():
            if user["userId"] in mutualFriendsId:
                mutualFriend = {
                    "userId": user["userId"],
                    "email": user["email"],
                    "name": user["name"],
                    "gender": user["gender"],
                    "pinCode": user["pinCode"],
                    "dob": user["dob"]
                    # "friendList": user["friendList"]
                }
                mutualFriends.append(mutualFriend)
    resp = {
        "status": status,
        "error": error,
        "mutualFriends": mutualFriends,
        "count": len(mutualFriends)
    }
    return jsonify(resp)


### PROFILE DETAILS OF A USER ###
@app.route("/api/get/profiledetail/<userId>/<currentuserId>", methods=["GET"])
def getProfileDetail(userId,currentuserId):
    allUser = socialMediaDataBase.usersDetails
    user = allUser.find_one({"userId": userId})
    currentUser = allUser.find_one({"userId":currentuserId})
    status = ""
    error = ""
    if user == None:
        status = "fail"
        error = "invalid user id"
        user = {}
    else:
        status = "success"
        error = "no error"
        friendship=0
        friendList=[]
        noOfFriend=0
        if userId==currentuserId:
            friendship=-1
            friendList=user["friendList"]
            noOfFriend=len(user["friendList"])
        elif userId in currentUser["friendList"]:
            friendship=1
            noOfFriend=len(user["friendList"])
        user = {
            "userId": user["userId"],
            "email": user["email"],
            "name": user["name"],
            "gender": user["gender"],
            "pinCode": user["pinCode"],
            "dob": user["dob"],
            "friendList": friendList,
            "friendship":friendship,
            "noOfFriend":noOfFriend
        }
    resp = {
        "status": status,
        "error": error,
        "userDetail": user
    }
    return jsonify(resp)

### FRIEND LIST OF A USER ###
@app.route("/api/get/friendlist/<userId>", methods=["GET"])
def getFriendList(userId):
    allUser = socialMediaDataBase.usersDetails
    currentUser = allUser.find_one({"userId": userId})
    status = ""
    error = ""
    if currentUser == None:
        status = "fail"
        error = "invalid user id"
        friendList = []
    else:
        friendList = []
        status = "success"
        error = "no error"
        idListOfFriends = currentUser["friendList"]
        for user in allUser.find():
            if user["userId"] in idListOfFriends:
                friend = {
                    "userId": user["userId"],
                    "email": user["email"],
                    "name": user["name"],
                    "gender": user["gender"],
                    "pinCode": user["pinCode"],
                    "dob": user["dob"]
                    # "friendList": user["friendList"]
                }
                friendList.append(friend)
    resp = {
        "status": status,
        "error": error,
        "userId": userId,
        "friendList": friendList,
        "count": len(friendList),
        "userName": currentUser["name"]
    }
    return jsonify(resp)

### SEARCH ###
@app.route("/api/search/<userId>", methods=["POST"])
def search(userId):
    form = request.form
    searchName = form.get("searchName")
    allUser = socialMediaDataBase.usersDetails
    currentUser = allUser.find_one({"userId":userId})
    result = []
    for user in allUser.find():
        if searchName.lower() in user["name"].lower() and user["userId"]!=userId:
            friendship=0
            if user["userId"] in currentUser["friendList"]:
                friendship=1
            temp = {
                "userId": user["userId"],
                "name": user["name"],
                "pinCode": user["pinCode"],
                "friendship":friendship
            }
            result.append(temp)
    resp = {
        "status": "success",
        "result": result,
        "serachName":searchName,
        "count":len(result),
        "userId":userId
    }
    return jsonify(resp)

### CREATE POST ###
@app.route("/api/create/post/<userId>", methods=["POST"])
def createPost(userId):
    form = request.form
    postText = form.get("postText")
    allUser = socialMediaDataBase.usersDetails
    user = allUser.find_one({"userId": userId})
    if user == None:
        resp = {
            "status": "fail",
            "error": "in valid user"
        }
    else:
        allPosts = socialMediaDataBase.allPosts
        newPost = {
            "userId": userId,
            "postId": str(uuid.uuid4()),
            "postText": postText,
            "dateTime": datetime.datetime.now()
        }
        allPosts.insert_one(newPost)
        resp = {
            "status": "success",
            "error": "no error"
        }
    return jsonify(resp)

### GET POST'S FOR A USER ###
@app.route("/api/get/post/<userId>/<currentUserId>/<flag>", methods=["GET"])
def getPosts(userId,currentUserId,flag):
    allUser = socialMediaDataBase.usersDetails
    user = allUser.find_one({"userId": userId})
    currentUser = allUser.find_one({"userId":currentUserId})
    posts=[]
    # if user == None or currentUser==None:
    if 0==1:
        resp = {
            "status": "fail",
            "error": "in valid user",
            "posts":posts
        }
    else:
        allPost = socialMediaDataBase.allPosts
        if userId==currentUserId and flag=="inProfile":
            for post in allPost.find():
                if post["userId"]==currentUserId:
                    temp = {
                        "ownerName":user["name"],
                        "postText":post["postText"],
                        "dateTime":post["dateTime"],
                        "ownerId":post["userId"]
                    }
                    posts.append(temp)
        if userId in currentUser["friendList"]:
            for post in allPost.find():
                if post["userId"]==userId:
                    temp = {
                        "ownerName":user["name"],
                        "postText":post["postText"],
                        "dateTime":post["dateTime"],
                        "ownerId":post["userId"]
                    }
                    posts.append(temp)
        if userId==currentUserId and flag=="inNewsFeed":
            for post in allPost.find():
                if post["userId"] in currentUser["friendList"]:
                    postOwner = allUser.find_one({"userId":post["userId"]})
                    temp = {
                        "ownerName":postOwner["name"],
                        "postText":post["postText"],
                        "dateTime":post["dateTime"],
                        "ownerId":post["userId"]
                    }
                    posts.append(temp)
        posts = [ele for ele in reversed(posts)]
        resp = {
            "status": "success",
            "error": "no error",
            "posts":posts
        }
        return jsonify(resp)


if __name__ == "__main__":
    app.run(port=5002, debug=True, host='0.0.0.0')
