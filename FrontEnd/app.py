from flask import(
    Flask, redirect, render_template, url_for, request, jsonify
)
import os
import json
from flask.helpers import make_response
from flask.wrappers import Response
import requests
app = Flask(__name__, static_url_path="")
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0
app.secret_key = "msaya1269"
APP_ROOT = os.path.dirname(os.path.abspath(__file__))

api="http://127.0.0.1:5002/api"

@app.route("/")
def home():
    if request.cookies.get("user"):
        userId=request.cookies.get("user")
        redirectUrl = f"/get/newsfeed/{userId}"
        return redirect(redirectUrl)
    else:
        return redirect(url_for("login"))

@app.route("/login")
def login():
    return render_template("login.html")

@app.route("/loggingin",methods=["POST"])
def LoggingIn():
    form = request.form
    response = requests.post(f"{api}/user/login",data=form)
    resp=response.json()
    if resp["status"]=="success":
        redirectUrl = f"/user/profile/{resp['userId']}"
        loggendIn = make_response(redirect(redirectUrl))
        loggendIn.set_cookie("user",resp["userId"],max_age=30*24*60*60)
        return loggendIn
    else:
        return redirect(url_for("login"))

@app.route("/user/register")
def register():
    return render_template("register.html")

@app.route("/registering",methods=["POST"])
def Registering():
    form = request.form
    response = requests.post(f"{api}/user/register",data=form)
    resp=response.json()
    if resp["status"]=="success":
        return redirect(url_for("login"))
    else:
        return redirect(url_for("register"))

### PROFILE DETAILS ###
@app.route("/user/profile/<userId>")
def userProfile(userId):
    if request.cookies.get("user"):
        currentUserId = request.cookies.get("user")
        response1 = requests.get(f"{api}/get/profiledetail/{userId}/{currentUserId}")
        resp1 = response1.json()
        friendship=resp1["userDetail"]["friendship"]
        count=0
        requestStatus=""
        requestId=""
        postToShow=[]
        if friendship==1: ### CURRENT USER VISITS A FRIEND'S PROFILE ###
            response2 = requests.get(f"{api}/get/mutualfriend/{userId}/{currentUserId}")
            resp2 = response2.json()
            count = resp2["count"]
        elif friendship==0: ### CURRENT USER VISITS A NORMAL PROFILE ###
            response2 = requests.get(f"{api}/get/mutualfriend/{userId}/{currentUserId}")
            resp2 = response2.json()
            count = resp2["count"]
            response3 = requests.get(f"{api}/check/request/{userId}/{currentUserId}")
            resp3 = response3.json()
            if resp3["flag"]==1: ### A  PENDING REQUEST EXIST ###
                if resp3["sender"]==2:
                    requestStatus="Pending"
                else:
                    requestStatus="Accept"
                requestId=resp3["requestId"]
            else:
                requestStatus="None"
        if friendship != 0: ### SHOW OWN POST WHEN VISITS OWN PROFILE ###
            flag = "inProfile"
            response = requests.get(f"{api}/get/post/{userId}/{currentUserId}/{flag}")
            resp = response.json()
            postToShow = resp["posts"]
        return render_template("profile.html",user=resp1["userDetail"],friendship=friendship,count=count,currentUserId=currentUserId,requestStatus=requestStatus,requestId=requestId,posts=postToShow)
    else:
        return redirect(url_for("login"))

### USER FRIEND LIST ###
@app.route("/user/friendlist/<userId>")
def userFriendList(userId):
    if request.cookies.get("user"):
        response = requests.get(f"{api}/get/friendlist/{userId}")
        resp = response.json()
        return render_template("friendList.html",resp=resp)
    else:
        return redirect(url_for("login")) 

### MUTUAL FRIEND LIST ###
@app.route("/mutual/friend/<userId1>/<userId2>")
def getMutualFriend(userId1,userId2):
    if request.cookies.get("user"):
            response=requests.get(f"{api}/get/mutualfriend/{userId1}/{userId2}")
            resp=response.json()
            userId = request.cookies.get("user")
            return render_template("mutualFriend.html",resp=resp,userId=userId)
    
### SEARCH ###
@app.route("/search")
def search():
    return render_template("search.html")

### SEARCH RESULT ###
@app.route("/search/result",methods=["POST"])
def searchResult():
    if request.cookies.get("user"):
        form = request.form
        userId = request.cookies.get("user")
        response = requests.post(f"{api}/search/{userId}",data=form)
        resp = response.json()
        return render_template("searchResult.html",resp=resp)
    else:
        return redirect(url_for("login"))  

### ALL RECIEVED FRIEND REQUESTS ###
@app.route("/get/friend/requests")
def friendRequests():
    userId = request.cookies.get("user")
    if userId:
        response = requests.get(f"{api}/get/requets/{userId}")
        resp = response.json()
        return render_template("friendRequest.html",resp=resp,currentUserId=userId)
    else:
       return redirect(url_for("login")) 

### ACCEPT REQUEST ###
@app.route("/accept/request/<requestId>")
def acceptFriendRequest(requestId):
    userId = request.cookies.get("user")
    if userId:
        response = requests.post    (f"{api}/friendrequest/accept/{requestId}")
        resp = response.json()
        redirectUrl = f"/user/profile/{resp['senderId']}"
        return redirect(redirectUrl)
    else:
       return redirect(url_for("login")) 

### SEND REQUSET ###
@app.route("/send/request/<recieverId>")
def sendRequest(recieverId):
    userId = request.cookies.get("user")
    if userId:
        response = requests.post(f"{api}/new/request/add/{userId}/{recieverId}")
        resp = response.json()
        redirectUrl = f"/user/profile/{resp['recieverId']}"
        return redirect(redirectUrl)
    else:
       return redirect(url_for("login"))

### CREATE POST ###
@app.route("/create/post/form")
def createPostForm():
    currenUsertId = request.cookies.get("user")
    if currenUsertId:
        return render_template("createPost.html",currenUsertId=currenUsertId)
    else:
       return redirect(url_for("login"))
@app.route("/create/post/<userId>",methods=["POST"])
def createPost(userId):
    currenUsertId = request.cookies.get("user")
    if currenUsertId:
        form = request.form
        response = requests.post(f"{api}/create/post/{currenUsertId}",data=form)
        resp = response.json()
        if resp["status"]=="success":
            redirectUrl = f"/user/profile/{currenUsertId}"
            return redirect(redirectUrl)
        else:
            return render_template("createPost.html")
    else:
       return redirect(url_for("login"))

### GET NEWS FEED ###
@app.route("/get/newsfeed/<userId>")
def getNewsFeed(userId):
    currentUserId = request.cookies.get("user")
    if currentUserId:
        flag = "inNewsFeed"
        response = requests.get(f"{api}/get/post/{userId}/{currentUserId}/{flag}")
        resp = response.json()
        return render_template("newsFeed.html",resp=resp,currentUserId=currentUserId)
    else:
        return redirect(url_for("login"))

@app.route("/user/logout")
def userLogout():
    resp = make_response(redirect(url_for('home')))
    resp.set_cookie('user', expires=0)
    return resp



if __name__ == "__main__":
    app.run(port=3000, debug=True, host='0.0.0.0')