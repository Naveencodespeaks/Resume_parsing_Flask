from flask import Flask, jsonify, request
import hashlib
import datetime
from flask_cors import CORS, cross_origin
from OpenSSL import SSL
from flask_jwt_extended import JWTManager, create_access_token, get_jwt, jwt_required
from core.bll import bllengine
from core.dbil import dbilayer
from reqhandlers.blocklist import BLOCKLIST
import socket  # importing socket module
import json
import redis
from rq import Queue
from flask_caching import Cache 
import threading
import time
import asyncio
from reqhandlers.send_reports import send_user_reports
from reqhandlers.request_set import file_request_carrier
from reqhandlers.date_conversion import json_serial
from reqhandlers.authenticate_authorize import authenticate_and_authorize
from reqhandlers.get_username import get_user_email
from reqhandlers.access_control import user_exist_in_access_control,user_details,user_plan_valid_days, user_organization, decrease_user_hits
from core.sendemailtousers import send_plan_expiry_dates
import requests
from bs4 import BeautifulSoup
import pandas as pd
from core.bll.bllengine import resume_parser_function

'''
config = {
"CACHE_TYPE": "redis",
"CACHE_REDIS_URL": "redis://10.11.19.110:6379",
#"CACHE_REDIS_URL": "redis://localhost:6379",
"CACHE_DEFAULT_TIMEOUT": 10
}


x = datetime.datetime.now()

# UPLOAD_FOLDER='/home/midadmin/fileserver/'


UPLOAD_FOLDER='/home'

context = SSL.Context(SSL.TLSv1_2_METHOD)
context = ('certs/certificate.crt', 'certs/private.key') 

# Initializing flask app
app = Flask(__name__)
cors = CORS(app)
jwt=JWTManager(app)

app.config['CORS_HEADERS'] = 'Content-Type'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SECRET_KEY'] = 'this is my top secret'

#This is to implement Logout feature of flask-jwt-extend
@jwt.token_in_blocklist_loader
def check_if_token_in_blocklist(jwt_header, jwt_payload): 
	return jwt_payload["jti"] in BLOCKLIST

#Callback function used to return custom response of flask-jwt-extend
@jwt.revoked_token_loader
def revoked_token_callback(jwt_header, jwt_payload):  
	return jsonify({"response":{"message":"User has Loggedout or token revoked","Description": "User has been Loggedout", "error": "Token Revoked"}})

print("allowed_hashlibs",hashlib.algorithms_available)

# redis_client = redis.Redis(host='10.11.19.110', port=6379)
redis_client = redis.Redis(host='localhost', port=6379)
queue = Queue(connection=redis_client)
app.config.from_mapping(config)
cache = Cache(app)

response_of_get_file={}
file_request_number=0

async def promise():
    await asyncio.sleep(1)
    return "Hello"

## getting the hostname by socket.gethostname() method
hostname = socket.gethostname()
## getting the IP address using socket.gethostbyname() method
ip_address = socket.gethostbyname(hostname)
## printing the hostname and ip_address
print(f"Hostname: {hostname}")
print(f"IP Address: {ip_address}")

'''



config = {
"CACHE_TYPE": "redis",
"CACHE_REDIS_URL": "redis://10.11.12.2:6380",
#"CACHE_REDIS_URL": "redis://localhost:6379",
"CACHE_DEFAULT_TIMEOUT": 2
}
# scan_folder='/python-docker/kyc_volume'
scan_folder='/home/midadmin/ta_application'
# # scan_folder='/home/m0/python_tasks/scan_folder'
# # scan_folder='/home/m0495/python_tasks/scan_folder'
# scan_folder = '/home/ganesh/startprojects/scan_folder'
context = SSL.Context(SSL.TLSv1_2_METHOD)
context = ('certs/certificate.crt', 'certs/private.key') 
app = Flask(__name__)
cors = CORS(app)
jwt=JWTManager(app)
app.config['CORS_HEADERS'] = 'Content-Type'
app.config['UPLOAD_FOLDER'] = scan_folder
app.config['SECRET_KEY'] = 'this is my top secret'
redis_client = redis.Redis(host='10.11.12.2', port=6380)
#redis_client = redis.Redis(host='localhost', port=6379)
queue = Queue(connection=redis_client)
app.config.from_mapping(config)
cache = Cache(app)
async def promise():
    await asyncio.sleep(0.001)
    return "Hello"
def process_queue(method, key_name):
    data = redis_client.lpop(key_name)
    if data is not None:
        resp=method(json.loads(data))
        redis_client.rpush(key_name+"_resp", json.dumps(resp))
    else:
        time.sleep(0.001)



# Route for seeing a data

@app.route('/sampleapi', methods=["POST"])
@cross_origin()
async def get_time():
	# createlogs(0)
	api_url=request.base_url
	# Returning an api for showing in reactjs
	return {
		'Name':"geek",
		"Age":"22",
		"Date":"2",
		"programming":"python",
		"api_url": api_url
		}

## BELOW APIS ARE RELATED TO LOGS

# Creating common function for redis-quque

def process_queue(method, key_name):
    data = redis_client.lpop(key_name)
    if data is not None:
        resp=method(json.loads(data))
        redis_client.rpush(key_name+"_resp", json.dumps(resp, default=json_serial))
    else:
        time.sleep(0.1)

#Common process_queue for only get file

def process_queue_for_getfile(method, key_name):
    global response_of_get_file
    data = redis_client.lpop(key_name)
    if data is not None:
        response_of_get_file[key_name+"_resp"]=method(json.loads(data))
    else:
        time.sleep(0.1)
        
## ALL APIs BELOW ARE USER, ACCESS RELATED

# I Register User

@app.route('/register', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def register():
    req=request.json
    redis_client.rpush("registeruser_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.register_user, "registeruser_queue"))
    thread.start()
    resp = redis_client.lpop("registeruser_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})

# II Get Users

@app.route('/getUsers', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def get_users():
    user_email=get_user_email()
    req=request.json
    req['request_data']['user_email']=user_email
    redis_client.rpush("get_users_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.read_all_users, "get_users_queue"))
    thread.start()
    resp = redis_client.lpop("get_users_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})

# III Delete User

@app.route('/deleteUser', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin', 'user'])
@cache.cached(timeout=1)
async def delete_user():
    user_email=get_user_email()
    req=request.json
    req['request_data']['user_email']=user_email
    redis_client.rpush("delete_user_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.delete_user, "delete_user_queue"))
    thread.start()
    resp = redis_client.lpop("delete_user_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})

# IV Update User Details(Including Password, other allowed details only)

@app.route('/updateUser', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin', 'user'])
@cache.cached(timeout=1)
async def update_user():
    user_email=get_user_email()
    req=request.json
    req['request_data']['user_email']=user_email
    redis_client.rpush("update_user_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.update_user, "update_user_queue"))
    thread.start()
    resp = redis_client.lpop("update_user_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})
   
####Login======================>
        
@app.route('/login', methods=['POST'])
@cross_origin()
@cache.cached(timeout=1)
async def login():
    # createlogs()
    req=request.json
    redis_client.rpush("loginuser_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.login_user, "loginuser_queue"))
    thread.start()
    resp = redis_client.lpop("loginuser_queue_resp")
    if resp is not None:
        print("response from db final:------",json.loads(resp)) 
        if 'user_details' in json.loads(resp):
            try:
                print("access_token", json.loads(resp)['user_details']['user_email'])
                token=create_access_token(identity=json.loads(resp)['user_details']['user_email'], expires_delta=datetime.timedelta(days=1))
                print("token generated successfully",token)
                return jsonify({"response_id": req['request_id'], "response_for": "User Login", "response_set_to": "UI", "response_data": {'message':json.loads(resp)['message'],"status_code":200,'user_details':json.loads(resp)["user_details"], 'jwt_token': token}})
            except Exception as e:
                print(e,"Error=================>")
                return jsonify({"response_id": req['request_id'], "response_for": "User Login", "response_set_to": "UI", "response_data": "Error Ocuured"})
        else:
            return jsonify({"response_id": req['request_id'], "response_for": "User Login", "response_set_to": "UI", "response_data": json.loads(resp)})
    else:
    	return jsonify({"response":{"message": "No response yet"}})
 
 
@app.route('/generateOTP', methods=['POST'])
@cross_origin()
@cache.cached(timeout=1)
async def generate_otp():
    req = request.json
    redis_client.rpush("generateOTP_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.generate_otp_for_reset_password, "generateOTP_queue"))
    thread.start()
    resp = redis_client.lpop("generateOTP_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})
   
@app.route('/verifyOTP', methods=['POST'])
@cross_origin()
@cache.cached(timeout=1)
async def verify_otp():
    req = request.json
    redis_client.rpush("verify_OTP_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.verify_otp_for_reset_password, "verify_OTP_queue"))
    thread.start()
    resp = redis_client.lpop("verify_OTP_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})
   
   
@app.route('/resendOTP', methods=['POST'])
@cross_origin()
@cache.cached(timeout=1)
async def resend_otp():
    req = request.json
    redis_client.rpush("resend_OTP_queue", json.dumps(req))
    print("END POINT")
    thread=threading.Thread(target=process_queue(bllengine.resend_otp_for_reset_password, "resend_OTP_queue"))
    thread.start()
    resp = redis_client.lpop("resend_OTP_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})
   
   
#APIS===========================================>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>   
# RECUISITIONS API'S
#CREATE
@app.route('/jobOpening/create', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def jobOpening_create():
    user_email=get_user_email()
    req=request.json
    req['request_data']['user_email']=user_email
    redis_client.rpush("jobOpening_create_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.jobOpening_create, "jobOpening_create_queue"))
    thread.start()
    resp = redis_client.lpop("jobOpening_create_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})
   
#READ ONE CONDITION
@app.route('/jobOpening/readOneCond', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def jobOpening_readOneCond():
    user_email=get_user_email()
    req=request.json
    req['request_data']['user_email']=user_email
    redis_client.rpush("jobOpening_readOneCond_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.jobOpening_readOneCond, "jobOpening_readOneCond_queue"))
    thread.start()
    resp = redis_client.lpop("jobOpening_readOneCond_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})


#READ ALL CONDITION
@app.route('/jobOpening/readAllCond', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def jobOpening_readAllCond():
    user_email=get_user_email()
    req=request.json
    req['request_data']['user_email']=user_email
    redis_client.rpush("jobOpening_readAllCond_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.jobOpening_readAllCond, "jobOpening_readAllCond_queue"))
    thread.start()
    resp = redis_client.lpop("jobOpening_readAllCond_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})
   
#READ ALL 
@app.route('/jobOpening/readAll', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def jobOpening_readAll():
    user_email=get_user_email()
    req=request.json
    req['request_data']['user_email']=user_email
    redis_client.rpush("jobOpening_readAll_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.jobOpening_readAll, "jobOpening_readAll_queue"))
    thread.start()
    resp = redis_client.lpop("jobOpening_readAll_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})

#UPDATE
@app.route('/jobOpening/update', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def jobOpening_update():
    user_email=get_user_email()
    req=request.json
    req['request_data']['user_email']=user_email
    redis_client.rpush("jobOpening_update_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.jobOpening_update, "jobOpening_update_queue"))
    thread.start()
    resp = redis_client.lpop("jobOpening_update_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})
   
#DELETE
@app.route('/jobOpening/delete', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def jobOpening_delete():
    user_email=get_user_email()
    req=request.json
    req['request_data']['user_email']=user_email
    redis_client.rpush("jobOpening_delete_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.jobOpening_delete, "jobOpening_delete_queue"))
    thread.start()
    resp = redis_client.lpop("jobOpening_delete_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})
   
#INTERVIEW SCHEDULES==========>
#CREATE
@app.route('/interview/create', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def interview_create():
    user_email=get_user_email()
    req=request.json
    req['request_data']['user_email']=user_email
    redis_client.rpush("interview_create_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.interview_create, "interview_create_queue"))
    thread.start()
    resp = redis_client.lpop("interview_create_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})
   
#READ ONE CONDITION
@app.route('/interview/readOneCond', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def interview_readOneCond():
    user_email=get_user_email()
    req=request.json
    req['request_data']['user_email']=user_email
    redis_client.rpush("interview_readOneCond_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.interview_readOneCond, "interview_readOneCond_queue"))
    thread.start()
    resp = redis_client.lpop("interview_readOneCond_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})


#READ ALL CONDITION
@app.route('/interview/readAllCond', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def interview_readAllCond():
    user_email=get_user_email()
    req=request.json
    req['request_data']['user_email']=user_email
    redis_client.rpush("interview_readAllCond_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.interview_readAllCond, "interview_readAllCond_queue"))
    thread.start()
    resp = redis_client.lpop("interview_readAllCond_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})
   
#READ ALL 
@app.route('/interview/readAll', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def interview_readAll():
    user_email=get_user_email()
    req=request.json
    req['request_data']['user_email']=user_email
    redis_client.rpush("interview_readAll_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.interview_readAll, "interview_readAll_queue"))
    thread.start()
    resp = redis_client.lpop("interview_readAll_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})

#UPDATE
@app.route('/interview/update', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def interview_update():
    user_email=get_user_email()
    req=request.json
    req['request_data']['user_email']=user_email
    redis_client.rpush("interview_update_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.interview_update, "interview_update_queue"))
    thread.start()
    resp = redis_client.lpop("interview_update_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})
   
#DELETE
@app.route('/interview/delete', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def interview_delete():
    user_email=get_user_email()
    req=request.json
    req['request_data']['user_email']=user_email
    redis_client.rpush("interview_delete_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.interview_delete, "interview_delete_queue"))
    thread.start()
    resp = redis_client.lpop("interview_delete_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})
    
#########GOOGLE CALENDAR EVENT CREATION###### 

@app.route('/event-create', methods=['POST'])
@cross_origin()
# @authenticate_and_authorize(['super-admin','admin'])
@jwt_required(optional=True)
@cache.cached(timeout=1)
async def event_create():
      # user_email=get_user_email()
      req=request.json
      # req['request_data']['user_email']=user_email
      redis_client.rpush("event_create_queue", json.dumps(req))
      thread=threading.Thread(target=process_queue(bllengine.event_create, "event_create_queue"))
      thread.start()
      resp = redis_client.lpop("event_create_queue_resp")
      if resp is not None:
       return jsonify(json.loads(resp))
      else:
       return jsonify({"response":{"message": "No response yet"}})

   
   
#CANDIDATES API"S==================================================>
#CREATE
@app.route('/candidate/create', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def candidate_create():
    user_email=get_user_email()
    req=request.json
    req['request_data']['user_email']=user_email
    redis_client.rpush("candidate_create_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.candidate_create, "candidate_create_queue"))
    thread.start()
    resp = redis_client.lpop("candidate_create_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})
    
#CREATE
@app.route('/candidate/create/bulk', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def candidate_create_bulk():
    user_email=get_user_email()
    req=request.json
    req['request_data']['user_email']=user_email
    redis_client.rpush("candidate_create_bulk_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.candidate_create_bulk, "candidate_create_bulk_queue"))
    thread.start()
    resp = redis_client.lpop("candidate_create_bulk_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})
   
#READ ONE CONDITION
@app.route('/candidate/readOneCond', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def candidate_readOneCond():
    user_email=get_user_email()
    req=request.json
    req['request_data']['user_email']=user_email
    redis_client.rpush("candidate_readOneCond_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.candidate_readOneCond, "candidate_readOneCond_queue"))
    thread.start()
    resp = redis_client.lpop("candidate_readOneCond_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})


#READ ALL CONDITION
@app.route('/candidate/readAllCond', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def candidate_readAllCond():
    user_email=get_user_email()
    req=request.json
    req['request_data']['user_email']=user_email
    redis_client.rpush("candidate_readAllCond_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.candidate_readAllCond, "candidate_readAllCond_queue"))
    thread.start()
    resp = redis_client.lpop("candidate_readAllCond_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})
    
#READ ALL RECENT
@app.route('/candidate/readRecent', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def candidate_readRecent():
    user_email=get_user_email()
    req=request.json
    req['request_data']['user_email']=user_email
    redis_client.rpush("candidate_readRecent_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.candidate_readRecent, "candidate_readRecent_queue"))
    thread.start()
    resp = redis_client.lpop("candidate_readRecent_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})
   
#READ ALL 
@app.route('/candidate/readAll', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def candidate_readAll():
    user_email=get_user_email()
    req=request.json
    req['request_data']['user_email']=user_email
    redis_client.rpush("candidate_readAll_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.candidate_readAll, "candidate_readAll_queue"))
    thread.start()
    resp = redis_client.lpop("candidate_readAll_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})

#UPDATE
@app.route('/candidate/update', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def candidate_update():
    user_email=get_user_email()
    req=request.json
    req['request_data']['user_email']=user_email
    redis_client.rpush("candidate_update_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.candidate_update, "candidate_update_queue"))
    thread.start()
    resp = redis_client.lpop("candidate_update_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})
   
#DELETE
@app.route('/candidate/delete', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def candidate_delete():
    user_email=get_user_email()
    req=request.json
    req['request_data']['user_email']=user_email
    redis_client.rpush("candidate_delete_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.candidate_delete, "candidate_delete_queue"))
    thread.start()
    resp = redis_client.lpop("candidate_delete_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})
    
    
#EMPLOYEE DETAILS API"S==================================================>
#CREATE
@app.route('/employeeDetails/create', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def employee_details_create():
    user_email=get_user_email()
    req=request.json
    req['request_data']['user_email']=user_email
    redis_client.rpush("employee_details_create_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.employee_details_create, "employee_details_create_queue"))
    thread.start()
    resp = redis_client.lpop("employee_details_create_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})
    
#CREATE
@app.route('/employeeDetails/create/bulk', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def employee_details_create_bulk():
    user_email=get_user_email()
    req=request.json
    req['request_data']['user_email']=user_email
    redis_client.rpush("employee_details_create_bulk_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.employee_details_create_bulk, "employee_details_create_bulk_queue"))
    thread.start()
    resp = redis_client.lpop("employee_details_create_bulk_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})
   
#READ ONE CONDITION
@app.route('/employeeDetails/readOneCond', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def employee_details_readOneCond():
    user_email=get_user_email()
    req=request.json
    req['request_data']['user_email']=user_email
    redis_client.rpush("employee_details_readOneCond_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.employee_details_readOneCond, "employee_details_readOneCond_queue"))
    thread.start()
    resp = redis_client.lpop("employee_details_readOneCond_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})


#READ ALL CONDITION
@app.route('/employeeDetails/readAllCond', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def employee_details_readAllCond():
    user_email=get_user_email()
    req=request.json
    req['request_data']['user_email']=user_email
    redis_client.rpush("employee_details_readAllCond_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.employee_details_readAllCond, "employee_details_readAllCond_queue"))
    thread.start()
    resp = redis_client.lpop("employee_details_readAllCond_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})
   
#READ ALL 
@app.route('/employeeDetails/readAll', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def employee_details_readAll():
    user_email=get_user_email()
    req=request.json
    req['request_data']['user_email']=user_email
    redis_client.rpush("employee_details_readAll_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.employee_details_readAll, "employee_details_readAll_queue"))
    thread.start()
    resp = redis_client.lpop("employee_details_readAll_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})

#UPDATE
@app.route('/employeeDetails/update', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def employee_details_update():
    user_email=get_user_email()
    req=request.json
    req['request_data']['user_email']=user_email
    redis_client.rpush("employee_details_update_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.employee_details_update, "employee_details_update_queue"))
    thread.start()
    resp = redis_client.lpop("employee_details_update_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})
   
#DELETE
@app.route('/employeeDetails/delete', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def employee_details_delete():
    user_email=get_user_email()
    req=request.json
    req['request_data']['user_email']=user_email
    redis_client.rpush("employee_details_delete_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.employee_details_delete, "employee_details_delete_queue"))
    thread.start()
    resp = redis_client.lpop("employee_details_delete_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})
    
#DROP DOWN API'S===============================================================================================================>>>>>>>>>>>>>
# EMPLOYEMENT TYPE
#CREATE
@app.route('/employmentType/create', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def employmentType_create():
   #  user_email=get_user_email()
    req=request.json
   #  req['request_data']['user_email']=user_email
    redis_client.rpush("employmentType_create_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.employmentType_create, "employmentType_create_queue"))
    thread.start()
    resp = redis_client.lpop("employmentType_create_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})

#READ ALL 
@app.route('/employmentType/readAll', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def employementType_readAll():
   #  user_email=get_user_email()
    req=request.json
   #  req['request_data']['user_email']=user_email
    redis_client.rpush("employmentType_readAll_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.employmentType_readAll, "employmentType_readAll_queue"))
    thread.start()
    resp = redis_client.lpop("employmentType_readAll_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})

#UPDATE
@app.route('/employmentType/update', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def employmentType_update():
   #  user_email=get_user_email()
    req=request.json
   #  req['request_data']['user_email']=user_email
    redis_client.rpush("employmentType_update_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.employmentType_update, "employmentType_update_queue"))
    thread.start()
    resp = redis_client.lpop("employmentType_update_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})
   
#DELETE
@app.route('/employmentType/delete', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def employmentType_delete():
   #  user_email=get_user_email()
    req=request.json
   #  req['request_data']['user_email']=user_email
    redis_client.rpush("employmentType_delete_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.employmentType_delete, "employmentType_delete_queue"))
    thread.start()
    resp = redis_client.lpop("employmentType_delete_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})
    

# SENIORITY LEVEL
#CREATE
@app.route('/seniorityLevel/create', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def seniorityLevel_create():
   #  user_email=get_user_email()
    req=request.json
   #  req['request_data']['user_email']=user_email
    redis_client.rpush("seniorityLevel_create_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.seniorityLevel_create, "seniorityLevel_create_queue"))
    thread.start()
    resp = redis_client.lpop("seniorityLevel_create_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})

#READ ALL 
@app.route('/seniorityLevel/readAll', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def seniorityLevel_readAll():
   #  user_email=get_user_email()
    req=request.json
   #  req['request_data']['user_email']=user_email
    redis_client.rpush("seniorityLevel_readAll_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.seniorityLevel_readAll, "seniorityLevel_readAll_queue"))
    thread.start()
    resp = redis_client.lpop("seniorityLevel_readAll_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})

#UPDATE
@app.route('/seniorityLevel/update', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def seniorityLevel_update():
   #  user_email=get_user_email()
    req=request.json
   #  req['request_data']['user_email']=user_email
    redis_client.rpush("seniorityLevel_update_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.seniorityLevel_update, "seniorityLevel_update_queue"))
    thread.start()
    resp = redis_client.lpop("seniorityLevel_update_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})
   
#DELETE
@app.route('/seniorityLevel/delete', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def seniorityLevel_delete():
   #  user_email=get_user_email()
    req=request.json
   #  req['request_data']['user_email']=user_email
    redis_client.rpush("seniorityLevel_delete_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.seniorityLevel_delete, "seniorityLevel_delete_queue"))
    thread.start()
    resp = redis_client.lpop("seniorityLevel_delete_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})
    
# JOB FUNCTION
#CREATE
@app.route('/jobFunction/create', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def jobFunction_create():
   #  user_email=get_user_email()
    req=request.json
   #  req['request_data']['user_email']=user_email
    redis_client.rpush("jobFunction_create_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.jobFunction_create, "jobFunction_create_queue"))
    thread.start()
    resp = redis_client.lpop("jobFunction_create_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})

#READ ALL 
@app.route('/jobFunction/readAll', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def jobFunction_readAll():
   #  user_email=get_user_email()
    req=request.json
   #  req['request_data']['user_email']=user_email
    redis_client.rpush("jobFunction_readAll_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.jobFunction_readAll, "jobFunction_readAll_queue"))
    thread.start()
    resp = redis_client.lpop("jobFunction_readAll_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})

#UPDATE
@app.route('/jobFunction/update', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def jobFunction_update():
   #  user_email=get_user_email()
    req=request.json
   #  req['request_data']['user_email']=user_email
    redis_client.rpush("jobFunction_update_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.jobFunction_update, "jobFunction_update_queue"))
    thread.start()
    resp = redis_client.lpop("jobFunction_update_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})
   
#DELETE
@app.route('/jobFunction/delete', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def jobFunction_delete():
   #  user_email=get_user_email()
    req=request.json
   #  req['request_data']['user_email']=user_email
    redis_client.rpush("jobFunction_delete_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.jobFunction_delete, "jobFunction_delete_queue"))
    thread.start()
    resp = redis_client.lpop("jobFunction_delete_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})


# CUSTOMER
#CREATE
@app.route('/customer/create', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def customer_create():
   #  user_email=get_user_email()
    req=request.json
   #  req['request_data']['user_email']=user_email
    redis_client.rpush("customer_create_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.customer_create, "customer_create_queue"))
    thread.start()
    resp = redis_client.lpop("customer_create_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})

#READ ALL 
@app.route('/customer/readAll', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def customer_readAll():
   #  user_email=get_user_email()
    req=request.json
   #  req['request_data']['user_email']=user_email
    redis_client.rpush("customer_readAll_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.customer_readAll, "customer_readAll_queue"))
    thread.start()
    resp = redis_client.lpop("customer_readAll_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})

#UPDATE
@app.route('/customer/update', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def customer_update():
   #  user_email=get_user_email()
    req=request.json
   #  req['request_data']['user_email']=user_email
    redis_client.rpush("customer_update_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.customer_update, "customer_update_queue"))
    thread.start()
    resp = redis_client.lpop("customer_update_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})
   
#DELETE
@app.route('/customer/delete', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def customer_delete():
   #  user_email=get_user_email()
    req=request.json
   #  req['request_data']['user_email']=user_email
    redis_client.rpush("customer_delete_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.customer_delete, "customer_delete_queue"))
    thread.start()
    resp = redis_client.lpop("customer_delete_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})


# PROJECT
#CREATE
@app.route('/project/create', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def project_create():
   #  user_email=get_user_email()
    req=request.json
   #  req['request_data']['user_email']=user_email
    redis_client.rpush("project_create_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.project_create, "project_create_queue"))
    thread.start()
    resp = redis_client.lpop("project_create_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})

#READ ALL 
@app.route('/project/readAll', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def project_readAll():
   #  user_email=get_user_email()
    req=request.json
   #  req['request_data']['user_email']=user_email
    redis_client.rpush("project_readAll_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.project_readAll, "project_readAll_queue"))
    thread.start()
    resp = redis_client.lpop("project_readAll_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})

#UPDATE
@app.route('/project/update', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def project_update():
   #  user_email=get_user_email()
    req=request.json
   #  req['request_data']['user_email']=user_email
    redis_client.rpush("project_update_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.project_update, "project_update_queue"))
    thread.start()
    resp = redis_client.lpop("project_update_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})
   
#DELETE
@app.route('/project/delete', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def project_delete():
   #  user_email=get_user_email()
    req=request.json
   #  req['request_data']['user_email']=user_email
    redis_client.rpush("project_delete_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.project_delete, "project_delete_queue"))
    thread.start()
    resp = redis_client.lpop("project_delete_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})


# preferred work mode
#CREATE
@app.route('/preferredWorkMode/create', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def preferredWorkMode_create():
   #  user_email=get_user_email()
    req=request.json
   #  req['request_data']['user_email']=user_email
    redis_client.rpush("preferredWorkMode_create_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.preferredWorkMode_create, "preferredWorkMode_create_queue"))
    thread.start()
    resp = redis_client.lpop("preferredWorkMode_create_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})

#READ ALL 
@app.route('/preferredWorkMode/readAll', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def preferredWorkMode_readAll():
   #  user_email=get_user_email()
    req=request.json
   #  req['request_data']['user_email']=user_email
    redis_client.rpush("preferredWorkMode_readAll_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.preferredWorkMode_readAll, "preferredWorkMode_readAll_queue"))
    thread.start()
    resp = redis_client.lpop("preferredWorkMode_readAll_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})

#UPDATE
@app.route('/preferredWorkMode/update', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def preferredWorkMode_update():
   #  user_email=get_user_email()
    req=request.json
   #  req['request_data']['user_email']=user_email
    redis_client.rpush("preferredWorkMode_update_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.preferredWorkMode_update, "preferredWorkMode_update_queue"))
    thread.start()
    resp = redis_client.lpop("preferredWorkMode_update_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})
   
#DELETE
@app.route('/preferredWorkMode/delete', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def preferredWorkMode_delete():
   #  user_email=get_user_email()
    req=request.json
   #  req['request_data']['user_email']=user_email
    redis_client.rpush("preferredWorkMode_delete_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.preferredWorkMode_delete, "preferredWorkMode_delete_queue"))
    thread.start()
    resp = redis_client.lpop("preferredWorkMode_delete_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})


#COMPANY
#CREATE
@app.route('/company/create', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def company_create():
   #  user_email=get_user_email()
    req=request.json
   #  req['request_data']['user_email']=user_email
    redis_client.rpush("company_create_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.company_create, "company_create_queue"))
    thread.start()
    resp = redis_client.lpop("company_create_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})

#READ ALL 
@app.route('/company/readAll', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def company_readAll():
   #  user_email=get_user_email()
    req=request.json
   #  req['request_data']['user_email']=user_email
    redis_client.rpush("company_readAll_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.company_readAll, "company_readAll_queue"))
    thread.start()
    resp = redis_client.lpop("company_readAll_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})

#UPDATE
@app.route('/company/update', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def company_update():
   #  user_email=get_user_email()
    req=request.json
   #  req['request_data']['user_email']=user_email
    redis_client.rpush("company_update_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.company_update, "company_update_queue"))
    thread.start()
    resp = redis_client.lpop("company_update_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})
   
#DELETE
@app.route('/company/delete', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def company_delete():
   #  user_email=get_user_email()
    req=request.json
   #  req['request_data']['user_email']=user_email
    redis_client.rpush("company_delete_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.company_delete, "company_delete_queue"))
    thread.start()
    resp = redis_client.lpop("company_delete_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})

#BUSINESS UNIT
#CREATE
@app.route('/businessUnit/create', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def businessUnit_create():
   #  user_email=get_user_email()
    req=request.json
   #  req['request_data']['user_email']=user_email
    redis_client.rpush("businessUnit_create_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.businessUnit_create, "businessUnit_create_queue"))
    thread.start()
    resp = redis_client.lpop("businessUnit_create_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})

#READ ALL 
@app.route('/businessUnit/readAll', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def businessUnit_readAll():
   #  user_email=get_user_email()
    req=request.json
   #  req['request_data']['user_email']=user_email
    redis_client.rpush("businessUnit_readAll_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.businessUnit_readAll, "businessUnit_readAll_queue"))
    thread.start()
    resp = redis_client.lpop("businessUnit_readAll_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})

#UPDATE
@app.route('/businessUnit/update', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def businessUnit_update():
   #  user_email=get_user_email()
    req=request.json
   #  req['request_data']['user_email']=user_email
    redis_client.rpush("businessUnit_update_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.businessUnit_update, "businessUnit_update_queue"))
    thread.start()
    resp = redis_client.lpop("businessUnit_update_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})
   
#DELETE
@app.route('/businessUnit/delete', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def businessUnit_delete():
   #  user_email=get_user_email()
    req=request.json
   #  req['request_data']['user_email']=user_email
    redis_client.rpush("businessUnit_delete_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.businessUnit_delete, "businessUnit_delete_queue"))
    thread.start()
    resp = redis_client.lpop("businessUnit_delete_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})


#DEPARTMENT
#CREATE
@app.route('/department/create', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def department_create():
   #  user_email=get_user_email()
    req=request.json
   #  req['request_data']['user_email']=user_email
    redis_client.rpush("department_create_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.department_create, "department_create_queue"))
    thread.start()
    resp = redis_client.lpop("department_create_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})

#READ ALL 
@app.route('/department/readAll', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def department_readAll():
   #  user_email=get_user_email()
    req=request.json
   #  req['request_data']['user_email']=user_email
    redis_client.rpush("department_readAll_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.department_readAll, "department_readAll_queue"))
    thread.start()
    resp = redis_client.lpop("department_readAll_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})

#UPDATE
@app.route('/department/update', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def department_update():
   #  user_email=get_user_email()
    req=request.json
   #  req['request_data']['user_email']=user_email
    redis_client.rpush("department_update_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.department_update, "department_update_queue"))
    thread.start()
    resp = redis_client.lpop("department_update_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})
   
#DELETE
@app.route('/department/delete', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def department_delete():
   #  user_email=get_user_email()
    req=request.json
   #  req['request_data']['user_email']=user_email
    redis_client.rpush("department_delete_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.department_delete, "department_delete_queue"))
    thread.start()
    resp = redis_client.lpop("department_delete_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})
    
#practice
#CREATE
@app.route('/practice/create', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def practice_create():
   #  user_email=get_user_email()
    req=request.json
   #  req['request_data']['user_email']=user_email
    redis_client.rpush("practice_create_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.practice_create, "practice_create_queue"))
    thread.start()
    resp = redis_client.lpop("practice_create_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})

#READ ALL 
@app.route('/practice/readAll', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def practice_readAll():
   #  user_email=get_user_email()
    req=request.json
   #  req['request_data']['user_email']=user_email
    redis_client.rpush("practice_readAll_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.practice_readAll, "practice_readAll_queue"))
    thread.start()
    resp = redis_client.lpop("practice_readAll_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})

#UPDATE
@app.route('/practice/update', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def practice_update():
   #  user_email=get_user_email()
    req=request.json
   #  req['request_data']['user_email']=user_email
    redis_client.rpush("practice_update_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.practice_update, "practice_update_queue"))
    thread.start()
    resp = redis_client.lpop("practice_update_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})
   
#DELETE
@app.route('/practice/delete', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def practice_delete():
   #  user_email=get_user_email()
    req=request.json
   #  req['request_data']['user_email']=user_email
    redis_client.rpush("practice_delete_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.practice_delete, "practice_delete_queue"))
    thread.start()
    resp = redis_client.lpop("practice_delete_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})

#DESIGNATION
#CREATE
@app.route('/designation/create', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def designation_create():
   #  user_email=get_user_email()
    req=request.json
   #  req['request_data']['user_email']=user_email
    redis_client.rpush("designation_create_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.designation_create, "designation_create_queue"))
    thread.start()
    resp = redis_client.lpop("designation_create_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})

#READ ALL 
@app.route('/designation/readAll', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def designation_readAll():
   #  user_email=get_user_email()
    req=request.json
   #  req['request_data']['user_email']=user_email
    redis_client.rpush("designation_readAll_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.designation_readAll, "designation_readAll_queue"))
    thread.start()
    resp = redis_client.lpop("designation_readAll_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})

#UPDATE
@app.route('/designation/update', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def designation_update():
   #  user_email=get_user_email()
    req=request.json
   #  req['request_data']['user_email']=user_email
    redis_client.rpush("designation_update_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.designation_update, "designation_update_queue"))
    thread.start()
    resp = redis_client.lpop("designation_update_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})
   
#DELETE
@app.route('/designation/delete', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def designation_delete():
   #  user_email=get_user_email()
    req=request.json
   #  req['request_data']['user_email']=user_email
    redis_client.rpush("designation_delete_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.designation_delete, "designation_delete_queue"))
    thread.start()
    resp = redis_client.lpop("designation_delete_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})
    
#GRADE
#CREATE
@app.route('/grade/create', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def grade_create():
   #  user_email=get_user_email()
    req=request.json
   #  req['request_data']['user_email']=user_email
    redis_client.rpush("grade_create_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.grade_create, "grade_create_queue"))
    thread.start()
    resp = redis_client.lpop("grade_create_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})

#READ ALL 
@app.route('/grade/readAll', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def grade_readAll():
   #  user_email=get_user_email()
    req=request.json
   #  req['request_data']['user_email']=user_email
    redis_client.rpush("grade_readAll_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.grade_readAll, "grade_readAll_queue"))
    thread.start()
    resp = redis_client.lpop("grade_readAll_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})

#UPDATE
@app.route('/grade/update', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def grade_update():
   #  user_email=get_user_email()
    req=request.json
   #  req['request_data']['user_email']=user_email
    redis_client.rpush("grade_update_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.grade_update, "grade_update_queue"))
    thread.start()
    resp = redis_client.lpop("grade_update_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})
   
#DELETE
@app.route('/grade/delete', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def grade_delete():
   #  user_email=get_user_email()
    req=request.json
   #  req['request_data']['user_email']=user_email
    redis_client.rpush("grade_delete_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.grade_delete, "grade_delete_queue"))
    thread.start()
    resp = redis_client.lpop("grade_delete_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})

#REGION
#CREATE
@app.route('/region/create', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def region_create():
   #  user_email=get_user_email()
    req=request.json
   #  req['request_data']['user_email']=user_email
    redis_client.rpush("region_create_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.region_create, "region_create_queue"))
    thread.start()
    resp = redis_client.lpop("region_create_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})

#READ ALL 
@app.route('/region/readAll', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def region_readAll():
   #  user_email=get_user_email()
    req=request.json
   #  req['request_data']['user_email']=user_email
    redis_client.rpush("region_readAll_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.region_readAll, "region_readAll_queue"))
    thread.start()
    resp = redis_client.lpop("region_readAll_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})

#UPDATE
@app.route('/region/update', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def region_update():
   #  user_email=get_user_email()
    req=request.json
   #  req['request_data']['user_email']=user_email
    redis_client.rpush("region_update_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.region_update, "region_update_queue"))
    thread.start()
    resp = redis_client.lpop("region_update_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})
   
#DELETE
@app.route('/region/delete', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def region_delete():
   #  user_email=get_user_email()
    req=request.json
   #  req['request_data']['user_email']=user_email
    redis_client.rpush("region_delete_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.region_delete, "region_delete_queue"))
    thread.start()
    resp = redis_client.lpop("region_delete_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})


#BRANCH
#CREATE
@app.route('/branch/create', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def branch_create():
   #  user_email=get_user_email()
    req=request.json
   #  req['request_data']['user_email']=user_email
    redis_client.rpush("branch_create_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.branch_create, "branch_create_queue"))
    thread.start()
    resp = redis_client.lpop("branch_create_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})

#READ ALL 
@app.route('/branch/readAll', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def branch_readAll():
   #  user_email=get_user_email()
    req=request.json
   #  req['request_data']['user_email']=user_email
    redis_client.rpush("branch_readAll_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.branch_readAll, "branch_readAll_queue"))
    thread.start()
    resp = redis_client.lpop("branch_readAll_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})

#UPDATE
@app.route('/branch/update', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def branch_update():
   #  user_email=get_user_email()
    req=request.json
   #  req['request_data']['user_email']=user_email
    redis_client.rpush("branch_update_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.branch_update, "branch_update_queue"))
    thread.start()
    resp = redis_client.lpop("branch_update_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})
   
#DELETE
@app.route('/branch/delete', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def branch_delete():
   #  user_email=get_user_email()
    req=request.json
   #  req['request_data']['user_email']=user_email
    redis_client.rpush("branch_delete_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.branch_delete, "branch_delete_queue"))
    thread.start()
    resp = redis_client.lpop("branch_delete_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})
    
    
    
#SUBBRANCH
#CREATE
@app.route('/subBranch/create', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def subBranch_create():
   #  user_email=get_user_email()
    req=request.json
   #  req['request_data']['user_email']=user_email
    redis_client.rpush("subBranch_create_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.subBranch_create, "subBranch_create_queue"))
    thread.start()
    resp = redis_client.lpop("subBranch_create_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})

#READ ALL 
@app.route('/subBranch/readAll', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def subBranch_readAll():
   #  user_email=get_user_email()
    req=request.json
   #  req['request_data']['user_email']=user_email
    redis_client.rpush("subBranch_readAll_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.subBranch_readAll, "subBranch_readAll_queue"))
    thread.start()
    resp = redis_client.lpop("subBranch_readAll_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})

#UPDATE
@app.route('/subBranch/update', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def subBranch_update():
   #  user_email=get_user_email()
    req=request.json
   #  req['request_data']['user_email']=user_email
    redis_client.rpush("subBranch_update_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.subBranch_update, "subBranch_update_queue"))
    thread.start()
    resp = redis_client.lpop("subBranch_update_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})
   
#DELETE
@app.route('/subBranch/delete', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def subBranch_delete():
   #  user_email=get_user_email()
    req=request.json
   #  req['request_data']['user_email']=user_email
    redis_client.rpush("subBranch_delete_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.subBranch_delete, "subBranch_delete_queue"))
    thread.start()
    resp = redis_client.lpop("subBranch_delete_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})
    
   
#QUALIFICATION
#CREATE
@app.route('/qualification/create', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def qualification_create():
   #  user_email=get_user_email()
    req=request.json
   #  req['request_data']['user_email']=user_email
    redis_client.rpush("qualification_create_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.qualification_create, "qualification_create_queue"))
    thread.start()
    resp = redis_client.lpop("qualification_create_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})

#READ ALL 
@app.route('/qualification/readAll', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def qualification_readAll():
   #  user_email=get_user_email()
    req=request.json
   #  req['request_data']['user_email']=user_email
    redis_client.rpush("qualification_readAll_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.qualification_readAll, "qualification_readAll_queue"))
    thread.start()
    resp = redis_client.lpop("qualification_readAll_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})

#UPDATE
@app.route('/qualification/update', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def qualification_update():
   #  user_email=get_user_email()
    req=request.json
   #  req['request_data']['user_email']=user_email
    redis_client.rpush("qualification_update_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.qualification_update, "qualification_update_queue"))
    thread.start()
    resp = redis_client.lpop("qualification_update_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})
   
#DELETE
@app.route('/qualification/delete', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def qualification_delete():
   #  user_email=get_user_email()
    req=request.json
   #  req['request_data']['user_email']=user_email
    redis_client.rpush("qualification_delete_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.qualification_delete, "qualification_delete_queue"))
    thread.start()
    resp = redis_client.lpop("qualification_delete_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})   
    
#CURRENCY
#CREATE
@app.route('/currency/create', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def currency_create():
   #  user_email=get_user_email()
    req=request.json
   #  req['request_data']['user_email']=user_email
    redis_client.rpush("currency_create_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.currency_create, "currency_create_queue"))
    thread.start()
    resp = redis_client.lpop("currency_create_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})

#READ ALL 
@app.route('/currency/readAll', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def currency_readAll():
   #  user_email=get_user_email()
    req=request.json
   #  req['request_data']['user_email']=user_email
    redis_client.rpush("currency_readAll_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.currency_readAll, "currency_readAll_queue"))
    thread.start()
    resp = redis_client.lpop("currency_readAll_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})

#UPDATE
@app.route('/currency/update', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def currency_update():
   #  user_email=get_user_email()
    req=request.json
   #  req['request_data']['user_email']=user_email
    redis_client.rpush("currency_update_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.currency_update, "currency_update_queue"))
    thread.start()
    resp = redis_client.lpop("currency_update_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})
   
#DELETE
@app.route('/currency/delete', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def currency_delete():
   #  user_email=get_user_email()
    req=request.json
   #  req['request_data']['user_email']=user_email
    redis_client.rpush("currency_delete_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.currency_delete, "currency_delete_queue"))
    thread.start()
    resp = redis_client.lpop("currency_delete_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})

#prefix
#CREATE
@app.route('/prefix/create', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def prefix_create():
   #  user_email=get_user_email()
    req=request.json
   #  req['request_data']['user_email']=user_email
    redis_client.rpush("prefix_create_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.prefix_create, "prefix_create_queue"))
    thread.start()
    resp = redis_client.lpop("prefix_create_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})

#READ ALL 
@app.route('/prefix/readAll', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def prefix_readAll():
   #  user_email=get_user_email()
    req=request.json
   #  req['request_data']['user_email']=user_email
    redis_client.rpush("prefix_readAll_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.prefix_readAll, "prefix_readAll_queue"))
    thread.start()
    resp = redis_client.lpop("prefix_readAll_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})

#UPDATE
@app.route('/prefix/update', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def prefix_update():
   #  user_email=get_user_email()
    req=request.json
   #  req['request_data']['user_email']=user_email
    redis_client.rpush("prefix_update_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.prefix_update, "prefix_update_queue"))
    thread.start()
    resp = redis_client.lpop("prefix_update_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})
   
#DELETE
@app.route('/prefix/delete', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def prefix_delete():
   #  user_email=get_user_email()
    req=request.json
   #  req['request_data']['user_email']=user_email
    redis_client.rpush("prefix_delete_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.prefix_delete, "prefix_delete_queue"))
    thread.start()
    resp = redis_client.lpop("prefix_delete_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})


#GENDER
#CREATE
@app.route('/gender/create', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def gender_create():
   #  user_email=get_user_email()
    req=request.json
   #  req['request_data']['user_email']=user_email
    redis_client.rpush("gender_create_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.gender_create, "gender_create_queue"))
    thread.start()
    resp = redis_client.lpop("gender_create_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})

#READ ALL 
@app.route('/gender/readAll', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def gender_readAll():
   #  user_email=get_user_email()
    req=request.json
   #  req['request_data']['user_email']=user_email
    redis_client.rpush("gender_readAll_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.gender_readAll, "gender_readAll_queue"))
    thread.start()
    resp = redis_client.lpop("gender_readAll_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})

#UPDATE
@app.route('/gender/update', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def gender_update():
   #  user_email=get_user_email()
    req=request.json
   #  req['request_data']['user_email']=user_email
    redis_client.rpush("gender_update_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.gender_update, "gender_update_queue"))
    thread.start()
    resp = redis_client.lpop("gender_update_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})
   
#DELETE
@app.route('/gender/delete', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def gender_delete():
   #  user_email=get_user_email()
    req=request.json
   #  req['request_data']['user_email']=user_email
    redis_client.rpush("gender_delete_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.gender_delete, "gender_delete_queue"))
    thread.start()
    resp = redis_client.lpop("gender_delete_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})
 
#BLOOD GROUP
#CREATE
@app.route('/bloodGroup/create', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def bloodGroup_create():
   #  user_email=get_user_email()
    req=request.json
   #  req['request_data']['user_email']=user_email
    redis_client.rpush("bloodGroup_create_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.bloodGroup_create, "bloodGroup_create_queue"))
    thread.start()
    resp = redis_client.lpop("bloodGroup_create_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})

#READ ALL 
@app.route('/bloodGroup/readAll', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def bloodGroup_readAll():
   #  user_email=get_user_email()
    req=request.json
   #  req['request_data']['user_email']=user_email
    redis_client.rpush("bloodGroup_readAll_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.bloodGroup_readAll, "bloodGroup_readAll_queue"))
    thread.start()
    resp = redis_client.lpop("bloodGroup_readAll_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})

#UPDATE
@app.route('/bloodGroup/update', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def bloodGroup_update():
   #  user_email=get_user_email()
    req=request.json
   #  req['request_data']['user_email']=user_email
    redis_client.rpush("bloodGroup_update_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.bloodGroup_update, "bloodGroup_update_queue"))
    thread.start()
    resp = redis_client.lpop("bloodGroup_update_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})
   
#DELETE
@app.route('/bloodGroup/delete', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def bloodGroup_delete():
   #  user_email=get_user_email()
    req=request.json
   #  req['request_data']['user_email']=user_email
    redis_client.rpush("bloodGroup_delete_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.bloodGroup_delete, "bloodGroup_delete_queue"))
    thread.start()
    resp = redis_client.lpop("bloodGroup_delete_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})
 
#NATIONALITY
#CREATE
@app.route('/nationality/create', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def nationality_create():
   #  user_email=get_user_email()
    req=request.json
   #  req['request_data']['user_email']=user_email
    redis_client.rpush("nationality_create_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.nationality_create, "nationality_create_queue"))
    thread.start()
    resp = redis_client.lpop("nationality_create_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})

#READ ALL 
@app.route('/nationality/readAll', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def nationality_readAll():
   #  user_email=get_user_email()
    req=request.json
   #  req['request_data']['user_email']=user_email
    redis_client.rpush("nationality_readAll_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.nationality_readAll, "nationality_readAll_queue"))
    thread.start()
    resp = redis_client.lpop("nationality_readAll_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})

#UPDATE
@app.route('/nationality/update', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def nationality_update():
   #  user_email=get_user_email()
    req=request.json
   #  req['request_data']['user_email']=user_email
    redis_client.rpush("nationality_update_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.nationality_update, "nationality_update_queue"))
    thread.start()
    resp = redis_client.lpop("nationality_update_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})
   
#DELETE
@app.route('/nationality/delete', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def nationality_delete():
   #  user_email=get_user_email()
    req=request.json
   #  req['request_data']['user_email']=user_email
    redis_client.rpush("nationality_delete_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.nationality_delete, "nationality_delete_queue"))
    thread.start()
    resp = redis_client.lpop("nationality_delete_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})

#ISDCODE
#CREATE
@app.route('/ISDCode/create', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def ISDCode_create():
   #  user_email=get_user_email()
    req=request.json
   #  req['request_data']['user_email']=user_email
    redis_client.rpush("ISDCode_create_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.ISDCode_create, "ISDCode_create_queue"))
    thread.start()
    resp = redis_client.lpop("ISDCode_create_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})

#READ ALL 
@app.route('/ISDCode/readAll', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def ISDCode_readAll():
   #  user_email=get_user_email()
    req=request.json
   #  req['request_data']['user_email']=user_email
    redis_client.rpush("ISDCode_readAll_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.ISDCode_readAll, "ISDCode_readAll_queue"))
    thread.start()
    resp = redis_client.lpop("ISDCode_readAll_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})

#UPDATE
@app.route('/ISDCode/update', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def ISDCode_update():
   #  user_email=get_user_email()
    req=request.json
   #  req['request_data']['user_email']=user_email
    redis_client.rpush("ISDCode_update_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.ISDCode_update, "ISDCode_update_queue"))
    thread.start()
    resp = redis_client.lpop("ISDCode_update_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})
   
#DELETE
@app.route('/ISDCode/delete', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def ISDCode_delete():
   #  user_email=get_user_email()
    req=request.json
   #  req['request_data']['user_email']=user_email
    redis_client.rpush("ISDCode_delete_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.ISDCode_delete, "ISDCode_delete_queue"))
    thread.start()
    resp = redis_client.lpop("ISDCode_delete_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})

#SOURCE
#CREATE
@app.route('/source/create', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def source_create():
   #  user_email=get_user_email()
    req=request.json
   #  req['request_data']['user_email']=user_email
    redis_client.rpush("source_create_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.source_create, "source_create_queue"))
    thread.start()
    resp = redis_client.lpop("source_create_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})

#READ ALL 
@app.route('/source/readAll', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def source_readAll():
   #  user_email=get_user_email()
    req=request.json
   #  req['request_data']['user_email']=user_email
    redis_client.rpush("source_readAll_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.source_readAll, "source_readAll_queue"))
    thread.start()
    resp = redis_client.lpop("source_readAll_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})

#UPDATE
@app.route('/source/update', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def source_update():
   #  user_email=get_user_email()
    req=request.json
   #  req['request_data']['user_email']=user_email
    redis_client.rpush("source_update_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.source_update, "source_update_queue"))
    thread.start()
    resp = redis_client.lpop("source_update_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})
   
#DELETE
@app.route('/source/delete', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def source_delete():
   #  user_email=get_user_email()
    req=request.json
   #  req['request_data']['user_email']=user_email
    redis_client.rpush("source_delete_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.source_delete, "source_delete_queue"))
    thread.start()
    resp = redis_client.lpop("source_delete_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})


#source category
#CREATE
@app.route('/sourceCategory/create', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def sourceCategory_create():
   #  user_email=get_user_email()
    req=request.json
   #  req['request_data']['user_email']=user_email
    redis_client.rpush("sourceCategory_create_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.sourceCategory_create, "sourceCategory_create_queue"))
    thread.start()
    resp = redis_client.lpop("sourceCategory_create_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})

#READ ALL 
@app.route('/sourceCategory/readAll', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def sourceCategory_readAll():
   #  user_email=get_user_email()
    req=request.json
   #  req['request_data']['user_email']=user_email
    redis_client.rpush("sourceCategory_readAll_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.sourceCategory_readAll, "sourceCategory_readAll_queue"))
    thread.start()
    resp = redis_client.lpop("sourceCategory_readAll_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})

#UPDATE
@app.route('/sourceCategory/update', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def sourceCategory_update():
   #  user_email=get_user_email()
    req=request.json
   #  req['request_data']['user_email']=user_email
    redis_client.rpush("sourceCategory_update_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.sourceCategory_update, "sourceCategory_update_queue"))
    thread.start()
    resp = redis_client.lpop("sourceCategory_update_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})
   
#DELETE
@app.route('/sourceCategory/delete', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def sourceCategory_delete():
   #  user_email=get_user_email()
    req=request.json
   #  req['request_data']['user_email']=user_email
    redis_client.rpush("sourceCategory_delete_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.sourceCategory_delete, "sourceCategory_delete_queue"))
    thread.start()
    resp = redis_client.lpop("sourceCategory_delete_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})

#PREFERRED LOCATION
#CREATE
@app.route('/preferredLocation/create', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def preferredLocation_create():
   #  user_email=get_user_email()
    req=request.json
   #  req['request_data']['user_email']=user_email
    redis_client.rpush("preferredLocation_create_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.preferredLocation_create, "preferredLocation_create_queue"))
    thread.start()
    resp = redis_client.lpop("preferredLocation_create_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})

#READ ALL 
@app.route('/preferredLocation/readAll', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def preferredLocation_readAll():
   #  user_email=get_user_email()
    req=request.json
   #  req['request_data']['user_email']=user_email
    redis_client.rpush("preferredLocation_readAll_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.preferredLocation_readAll, "preferredLocation_readAll_queue"))
    thread.start()
    resp = redis_client.lpop("preferredLocation_readAll_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})

#UPDATE
@app.route('/preferredLocation/update', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def preferredLocation_update():
   #  user_email=get_user_email()
    req=request.json
   #  req['request_data']['user_email']=user_email
    redis_client.rpush("preferredLocation_update_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.preferredLocation_update, "preferredLocation_update_queue"))
    thread.start()
    resp = redis_client.lpop("preferredLocation_update_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})
   
#DELETE
@app.route('/preferredLocation/delete', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def preferredLocation_delete():
   #  user_email=get_user_email()
    req=request.json
   #  req['request_data']['user_email']=user_email
    redis_client.rpush("preferredLocation_delete_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.preferredLocation_delete, "preferredLocation_delete_queue"))
    thread.start()
    resp = redis_client.lpop("preferredLocation_delete_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})
    
#NOTICE PERIOD
#CREATE
@app.route('/noticePeriod/create', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def noticePeriod_create():
   #  user_email=get_user_email()
    req=request.json
   #  req['request_data']['user_email']=user_email
    redis_client.rpush("noticePeriod_create_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.noticePeriod_create, "noticePeriod_create_queue"))
    thread.start()
    resp = redis_client.lpop("noticePeriod_create_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})

#READ ALL 
@app.route('/noticePeriod/readAll', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def noticePeriod_readAll():
   #  user_email=get_user_email()
    req=request.json
   #  req['request_data']['user_email']=user_email
    redis_client.rpush("noticePeriod_readAll_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.noticePeriod_readAll, "noticePeriod_readAll_queue"))
    thread.start()
    resp = redis_client.lpop("noticePeriod_readAll_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})

#UPDATE
@app.route('/noticePeriod/update', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def noticePeriod_update():
   #  user_email=get_user_email()
    req=request.json
   #  req['request_data']['user_email']=user_email
    redis_client.rpush("noticePeriod_update_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.noticePeriod_update, "noticePeriod_update_queue"))
    thread.start()
    resp = redis_client.lpop("noticePeriod_update_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})
   
#DELETE
@app.route('/noticePeriod/delete', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def noticePeriod_delete():
   #  user_email=get_user_email()
    req=request.json
   #  req['request_data']['user_email']=user_email
    redis_client.rpush("noticePeriod_delete_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.noticePeriod_delete, "noticePeriod_delete_queue"))
    thread.start()
    resp = redis_client.lpop("noticePeriod_delete_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})

#ROUND TYPE
#CREATE
@app.route('/roundType/create', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def roundType_create():
   #  user_email=get_user_email()
    req=request.json
   #  req['request_data']['user_email']=user_email
    redis_client.rpush("roundType_create_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.roundType_create, "roundType_create_queue"))
    thread.start()
    resp = redis_client.lpop("roundType_create_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})
    
#READ ALL 
@app.route('/roundType/readAll', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def roundType_readAll():
   #  user_email=get_user_email()
    req=request.json
   #  req['request_data']['user_email']=user_email
    redis_client.rpush("roundType_readAll_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.roundType_readAll, "roundType_readAll_queue"))
    thread.start()
    resp = redis_client.lpop("roundType_readAll_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})

#UPDATE
@app.route('/roundType/update', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def roundType_update():
   #  user_email=get_user_email()
    req=request.json
   #  req['request_data']['user_email']=user_email
    redis_client.rpush("roundType_update_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.roundType_update, "roundType_update_queue"))
    thread.start()
    resp = redis_client.lpop("roundType_update_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})
   
#DELETE
@app.route('/roundType/delete', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def roundType_delete():
   #  user_email=get_user_email()
    req=request.json
   #  req['request_data']['user_email']=user_email
    redis_client.rpush("roundType_delete_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.roundType_delete, "roundType_delete_queue"))
    thread.start()
    resp = redis_client.lpop("roundType_delete_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})


#CANDIDATE STATUS
#CREATE
@app.route('/candidateStatus/create', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def candidateStatus_create():
   #  user_email=get_user_email()
    req=request.json
   #  req['request_data']['user_email']=user_email
    redis_client.rpush("candidateStatus_create_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.candidateStatus_create, "candidateStatus_create_queue"))
    thread.start()
    resp = redis_client.lpop("candidateStatus_create_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})
    
#READ ALL 
@app.route('/candidateStatus/readAll', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def candidateStatus_readAll():
   #  user_email=get_user_email()
    req=request.json
   #  req['request_data']['user_email']=user_email
    redis_client.rpush("candidateStatus_readAll_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.candidateStatus_readAll, "candidateStatus_readAll_queue"))
    thread.start()
    resp = redis_client.lpop("candidateStatus_readAll_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})

#UPDATE
@app.route('/candidateStatus/update', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def candidateStatus_update():
   #  user_email=get_user_email()
    req=request.json
   #  req['request_data']['user_email']=user_email
    redis_client.rpush("candidateStatus_update_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.candidateStatus_update, "candidateStatus_update_queue"))
    thread.start()
    resp = redis_client.lpop("candidateStatus_update_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})
   
#DELETE
@app.route('/candidateStatus/delete', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def candidateStatus_delete():
   #  user_email=get_user_email()
    req=request.json
   #  req['request_data']['user_email']=user_email
    redis_client.rpush("candidateStatus_delete_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.candidateStatus_delete, "candidateStatus_delete_queue"))
    thread.start()
    resp = redis_client.lpop("candidateStatus_delete_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})
    
    

#TEMPLATES JOB
#CREATE
@app.route('/templateJob/create', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def templateJob_create():
   #  user_email=get_user_email()
    req=request.json
   #  req['request_data']['user_email']=user_email
    redis_client.rpush("templateJob_create_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.templateJob_create, "templateJob_create_queue"))
    thread.start()
    resp = redis_client.lpop("templateJob_create_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})
    
#READ ALL 
@app.route('/templateJob/readAll', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def templateJob_readAll():
   #  user_email=get_user_email()
    req=request.json
   #  req['request_data']['user_email']=user_email
    redis_client.rpush("templateJob_readAll_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.templateJob_readAll, "templateJob_readAll_queue"))
    thread.start()
    resp = redis_client.lpop("templateJob_readAll_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})

#UPDATE
@app.route('/templateJob/update', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def templateJob_update():
   #  user_email=get_user_email()
    req=request.json
   #  req['request_data']['user_email']=user_email
    redis_client.rpush("templateJob_update_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.templateJob_update, "templateJob_update_queue"))
    thread.start()
    resp = redis_client.lpop("templateJob_update_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})
   
#DELETE
@app.route('/templateJob/delete', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def templateJob_delete():
   #  user_email=get_user_email()
    req=request.json
   #  req['request_data']['user_email']=user_email
    redis_client.rpush("templateJob_delete_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.templateJob_delete, "templateJob_delete_queue"))
    thread.start()
    resp = redis_client.lpop("templateJob_delete_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})

#TEMPLATES QUESTION
#CREATE
@app.route('/templateQuestion/create', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def templateQuestion_create():
   #  user_email=get_user_email()
    req=request.json
   #  req['request_data']['user_email']=user_email
    redis_client.rpush("templateQuestion_create_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.templateQuestion_create, "templateQuestion_create_queue"))
    thread.start()
    resp = redis_client.lpop("templateQuestion_create_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})
    
#READ ALL 
@app.route('/templateQuestion/readAll', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def templateQuestion_readAll():
   #  user_email=get_user_email()
    req=request.json
   #  req['request_data']['user_email']=user_email
    redis_client.rpush("templateQuestion_readAll_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.templateQuestion_readAll, "templateQuestion_readAll_queue"))
    thread.start()
    resp = redis_client.lpop("templateQuestion_readAll_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})

#UPDATE
@app.route('/templateQuestion/update', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def templateQuestion_update():
   #  user_email=get_user_email()
    req=request.json
   #  req['request_data']['user_email']=user_email
    redis_client.rpush("templateQuestion_update_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.templateQuestion_update, "templateQuestion_update_queue"))
    thread.start()
    resp = redis_client.lpop("templateQuestion_update_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})
   
#DELETE
@app.route('/templateQuestion/delete', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def templateQuestion_delete():
   #  user_email=get_user_email()
    req=request.json
   #  req['request_data']['user_email']=user_email
    redis_client.rpush("templateQuestion_delete_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.templateQuestion_delete, "templateQuestion_delete_queue"))
    thread.start()
    resp = redis_client.lpop("templateQuestion_delete_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})
    
#TEMPLATES QUESTION
#CREATE
@app.route('/interviewStatus/create', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def interviewStatus_create():
   #  user_email=get_user_email()
    req=request.json
   #  req['request_data']['user_email']=user_email
    redis_client.rpush("interviewStatus_create_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.interviewStatus_create, "interviewStatus_create_queue"))
    thread.start()
    resp = redis_client.lpop("interviewStatus_create_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})
    
#READ ALL 
@app.route('/interviewStatus/readAll', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def interviewStatus_readAll():
   #  user_email=get_user_email()
    req=request.json
   #  req['request_data']['user_email']=user_email
    redis_client.rpush("interviewStatus_readAll_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.interviewStatus_readAll, "interviewStatus_readAll_queue"))
    thread.start()
    resp = redis_client.lpop("interviewStatus_readAll_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})

#UPDATE
@app.route('/interviewStatus/update', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def interviewStatus_update():
   #  user_email=get_user_email()
    req=request.json
   #  req['request_data']['user_email']=user_email
    redis_client.rpush("interviewStatus_update_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.interviewStatus_update, "interviewStatus_update_queue"))
    thread.start()
    resp = redis_client.lpop("interviewStatus_update_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})
   
#DELETE
@app.route('/interviewStatus/delete', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def interviewStatus_delete():
   #  user_email=get_user_email()
    req=request.json
   #  req['request_data']['user_email']=user_email
    redis_client.rpush("interviewStatus_delete_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.interviewStatus_delete, "interviewStatus_delete_queue"))
    thread.start()
    resp = redis_client.lpop("interviewStatus_delete_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})
    
    
    
#STATIC API's
#READ ALL 
@app.route('/countryAndNationality/readAll', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def countryAndNationality_readAll():
   #  user_email=get_user_email()
    req=request.json
   #  req['request_data']['user_email']=user_email
    redis_client.rpush("countryAndNationality_readAll_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.countryAndNationality_readAll, "countryAndNationality_readAll_queue"))
    thread.start()
    resp = redis_client.lpop("countryAndNationality_readAll_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})
    
#READ ALL 
@app.route('/stateCity/readAll', methods=['POST'])
@cross_origin()
@authenticate_and_authorize(['super-admin','admin'])
@cache.cached(timeout=1)
async def stateCity_readAll():
   #  user_email=get_user_email()
    req=request.json
   #  req['request_data']['user_email']=user_email
    redis_client.rpush("stateCity_readAll_queue", json.dumps(req))
    thread=threading.Thread(target=process_queue(bllengine.stateCity_readAll, "stateCity_readAll_queue"))
    thread.start()
    resp = redis_client.lpop("stateCity_readAll_queue_resp")
    if resp is not None:
       return jsonify(json.loads(resp))
    else:
       return jsonify({"response":{"message": "No response yet"}})

# resume_parsing 
#Resume Parsing
#Parsing the resume===============================================>>>>>>>>>>>>>>>>>>>>>>
@app.route('/resume', methods=['POST'])
async def parse_resume():
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file part"}), 400
        
        file = request.files['file']
        if file and file.filename.endswith('.pdf'):
            file_content = file.read()
            
            result = await resume_parser_function({
                'file_content': file_content,
                'skills_file_path': 'reqhandlers/skills.txt',
                'education_file_path':'reqhandlers/education.txt'
            })

            return jsonify(result)
        else:
            return jsonify({"error": "Invalid file format. Only PDF files are allowed."}), 400
    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500


#COUNT API's============================================================>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
async def main():
    asyncio.get_event_loop()
    await asyncio.ensure_future(promise())

asyncio.run(main())   ## This is for gunicorn

if __name__ == "__main__":
    asyncio.run(main())
    #app.run(host="0.0.0.0",debug=True)
    app.run(host="0.0.0.0",port=5012,debug=True,ssl_context=context)
   
