import re
import asyncio
import aiofiles
import fitz  # PyMuPDF
import os
import hashlib
import datetime
import requests
from bs4 import BeautifulSoup
import pandas as pd
from dateutil.relativedelta import relativedelta
import mimetypes
from random import randint
from werkzeug.security import check_password_hash
from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename
from flask import send_from_directory, jsonify,current_app
from core.dbil import dbilayer
from core import constants
from core import sendemailtousers
from core.data_types_convert_to_respective_types import convert_data_types_for_insert, convert_data_types_for_update,convert_data_types_for_conditions
from reqhandlers.access_control import user_organization
from reqhandlers.access_control import user_details
from reqhandlers.request_set import file_request_carrier
import uuid
import random
from core.database_name import database_name
from reqhandlers.create_google_event import create_event
from core.sendemailtousers import send_opt_to_user_email_for_reset_password
from core.state_city_list import indian_states_and_cities


def resend_otp_for_reset_password(request_data):
    if isinstance(request_data, dict):
        user_data=request_data['request_data']
        table_name = "otps"
        fields = "*"
        count = "many"
        check_user = dbilayer.read_with_condition(table_name, fields, user_data,count)
        if ((check_user is not None) and (isinstance(check_user, list))):
            if(len(check_user) > 0):
                resp_data = check_user[0]
                otp = resp_data['otp']
                if otp:
                    user_data["otp"] = otp
                    resent_otp_resp = send_opt_to_user_email_for_reset_password(user_data)
                    if resent_otp_resp["message"] == "Success":
                        print("POINT___1")
                        respsucc={"response_id": request_data['request_id'], "response_for": "Generate OTP", "response_set_to": request_data['request_src'], "response_data":  {"message":resent_otp_resp["message"],"status_code":200}}
                        return respsucc
                    else:
                        respfail={"response_id": request_data['request_id'], "response_for": "Read", "response_set_to": request_data['request_src'], "response_data": {"message": "Failed"}}
                        return respfail      
                else:
                    otp = str(random.randint(100000, 999999))
                    # user_data['otp'] = otp
                    table_name = "otps"
                    update_data = {"otp":otp}
                    store_resp = dbilayer.update_table(table_name,update_data,user_data)
                    if store_resp == "Success":
                        user_details["otp"] = otp
                        resent_otp_resp = send_opt_to_user_email_for_reset_password(user_data)
                        if resent_otp_resp["message"] == "Success":
                            print("POINT___2")
                            respsucc={"response_id": request_data['request_id'], "response_for": "Generate OTP", "response_set_to": request_data['request_src'], "response_data":  {"message":"Success","status_code":200}}
                            return respsucc
                        else:
                            respfail={"response_id": request_data['request_id'], "response_for": "Read", "response_set_to": request_data['request_src'], "response_data": {"message": "Failed"}}
                            return respfail
                    else:
                        respfail={"response_id": request_data['request_id'], "response_for": "Read", "response_set_to": request_data['request_src'], "response_data": {"message": "Failed"}}
                        return respfail    
            else:
                r = generate_otp_for_reset_password(request_data)
                return r     
        else:
            respfail={"response_id": request_data['request_id'], "response_for": "Read", "response_set_to": request_data['request_src'], "response_data": {"message": "Failed"}}
            return respfail 
    else:
        respfail={"response_id": request_data['request_id'], "response_for": "Read", "response_set_to": request_data['request_src'], "response_data": {"message": "Failed"}}
        return respfail         
                        
                        
def verify_otp_for_reset_password(request_data):
    if isinstance(request_data, dict):
        user_data=request_data['request_data']
        table_name = "otps"
        fields = "*"
        count = "many"
        check_user = dbilayer.read_with_condition(table_name, fields, user_data,count)
        print(check_user)
        if ((check_user is not None) and (isinstance(check_user, list))):
            if(len(check_user) > 0):
                respsucc={"response_id": request_data['request_id'], "response_for": "Generate OTP", "response_set_to": request_data['request_src'], "response_data":  {"message":"Success","status_code":200}}
                return respsucc
            else:
                respfail={"response_id": request_data['request_id'], "response_for": "Read", "response_set_to": request_data['request_src'], "response_data": {"message": "Invalid OTP!"}}
                return respfail
        else:
            respfail={"response_id": request_data['request_id'], "response_for": "Read", "response_set_to": request_data['request_src'], "response_data": {"message": "User Email Not registred"}}
            return respfail
    else:
        respfail={"response_id": request_data['request_id'], "response_for": "Generate OTP", "response_set_to": request_data['request_src'], "response_data": {"message": "Error Encountered"}}
        return respfail
    


def generate_otp_for_reset_password(request_data):
    if isinstance(request_data, dict):
        user_data=request_data['request_data']
        user_data["status"] = "1"
        check_user = dbilayer.get_user('users', '*', user_data)
        if ((check_user is not None) and (isinstance(check_user, dict))):
            if(len(check_user) > 0):
                del user_data["status"]
                check_otp = dbilayer.delete_records('otps', user_data)
                sta=dbilayer.otp_store_into_table('otps', constants.columns_otps_table, user_data)
                if ((sta is not None) and (sta != 'Failed')):
                    print("POINT___3")
                    respsucc={"response_id": request_data['request_id'], "response_for": "Generate OTP", "response_set_to": request_data['request_src'], "response_data":  {"message":sta["message"],"status_code":200}}
                    return respsucc
                else:
                    respfail={"response_id": request_data['request_id'], "response_for": "Generate OTP", "response_set_to": request_data['request_src'], "response_data": {"message": "Invalid Email!"}}
                    return respfail
            else:
                respfail={"response_id": request_data['request_id'], "response_for": "Read", "response_set_to": request_data['request_src'], "response_data": {"message": "Invalid Email!"}}
                return respfail
        else:
            respfail={"response_id": request_data['request_id'], "response_for": "Read", "response_set_to": request_data['request_src'], "response_data": {"message": "Invalid Email!"}}
            return respfail
    else:
        respfail={"response_id": request_data['request_id'], "response_for": "Generate OTP", "response_set_to": request_data['request_src'], "response_data": {"message": "Error Encountered"}}
        return respfail
    
    

# I Register User
def register_user(request_data):
    if isinstance(request_data, dict):
        userData=request_data['request_data']
        sta=dbilayer.register_user_now('users', constants.columns_users_table, userData)
        if ((sta is not None) and (sta != 'Failed')):
            respsucc={"response_id": request_data['request_id'], "response_for": "Create User", "response_set_to": request_data['request_src'], "response_data": {"message": sta}}
            return respsucc
        else:
            respfail={"response_id": request_data['request_id'], "response_for": "Create User", "response_set_to": request_data['request_src'], "response_data": {"message": "Some Error in Request for to Create User"}}
            return respfail
    else:
        respfail={"response_id": request_data['request_id'], "response_for": "Create User", "response_set_to": request_data['request_src'], "response_data": {"message": "Error Encountered"}}
        return respfail
    
# II user login
def login_user(request_data):
    response={}
    print(request_data,"========>=============")
    if isinstance(request_data, dict):
        userData=request_data['request_data']
        sta=dbilayer.get_user('users', '*', userData)
        if ((sta is not None) and (isinstance(sta,dict))):
            if ('user_email' in sta and 'user_email' in userData and userData['user_email'] !=""):
                user_email=sta['user_email']
                password=sta['password']
                if (user_email and password):
                    if ((user_email == userData['user_email']) and (check_password_hash(password,userData['password']))):
                        response={"message": "User Loggedin Successfully", "user_details": sta}
                    else:
                        response={"message": "Password Doesn't Matched"}
                else:
                    response={"message": "Email or Password Doesn't Matched"}
            else:
                response={"message": "Invalid credentials!"}
        else:
            response={"message": "Invalid credentials!"}
    else:
        response={"message": "Error Encountered"}
    return response
#READ ===========>USER
def read_all_users(request_data):
    if isinstance(request_data, dict):
        condition_data=request_data['request_data']
        sta=dbilayer.read_without_condition('users')
        if ((sta is not None) and (isinstance(sta, list))):
            if(len(sta) > 0):
                respsucc={"response_id": request_data['request_id'], "response_for": "Read", "response_set_to": request_data['request_src'], "response_data": {"message": "Success", "data":sta}}
                return respsucc
            else:
                respfail={"response_id": request_data['request_id'], "response_for": "Read", "response_set_to": request_data['request_src'], "response_data": {"message": "No Results Found"}}
                return respfail
        else:
            respfail={"response_id": request_data['request_id'], "response_for": "Read", "response_set_to": request_data['request_src'], "response_data": {"message": "Some Error in Request"}}
            return respfail
    else:
        respfail={"response_id": request_data['request_id'], "response_for": "Read", "response_set_to": request_data['request_src'], "response_data": {"message": "Error Encountered"}}
        return respfail
    
#DELETE========>USER
def delete_user(request_data):
    if request_data['request_data']['user_email']:
        table_name = 'users'
        update_data= {"status":"9"}
        condition= request_data['request_data']
        sta = dbilayer.update_table(table_name,update_data,condition)
        print(sta)
        if((sta is not None) and (sta == "Success")):
            respsucc = {"response_id": request_data['request_id'], "response_for":"Delete","response_set_to": request_data['request_src'],"response_data": {"message":"Deleted Successfully"}}
            return  respsucc
        elif(sta == 'Failed'):
            respfail = {"response_id": request_data['request_id'], "response_for":"Delete","response_set_to": request_data['request_src'],"response_data": {"message":"Delete request Failed"}}
            return  respfail
    else:
        respfail = {"response_id": request_data['request_id'], "response_for":"Delete","response_set_to": request_data['request_src'],"response_data": {"message":"Error in Request"}}
        return  respfail
#UPDATE================>USER
def update_user(request_data):
    if request_data['request_data']['user_email']:
        userpassword=request_data['request_data']['password']
        hashed_password=generate_password_hash(userpassword)
        request_data['request_data']['password']=hashed_password
        table_name = 'users'
        update_data= request_data['request_data']
        condition= {"user_email":request_data['request_data']['user_email']}
        sta = dbilayer.update_table(table_name,update_data,condition)
        print(sta)
        if((sta is not None) and (sta == "Success")):
            respsucc = {"response_id": request_data['request_id'], "response_for":"update","response_set_to": request_data['request_src'],"response_data": {"message":"Success","status_code":200}}
            return  respsucc
        elif(sta == 'Failed'):
            respfail = {"response_id": request_data['request_id'], "response_for":"update","response_set_to": request_data['request_src'],"response_data": {"message":"Update request Failed"}}
            return  respfail
    else:
        respfail = {"response_id": request_data['request_id'], "response_for":"update","response_set_to": request_data['request_src'],"response_data": {"message":"Error in Request"}}
        return  respfail 
    
#GOOGLE CALENDAR EVENT CREATE#######################

def event_create(request_data):
    if isinstance(request_data, dict):
        data_to_create_google_meet = request_data['request_data']
        google_meet_setup_status=create_event(data_to_create_google_meet)
        if (google_meet_setup_status):
            respsucc={"response_id": request_data['request_id'], "response_for": "Event_Create", "response_set_to": request_data['request_src'], "response": {"message": "Google meetup created successfully!"}}
            return respsucc
            # data='","'.join(data_to_insert.values())
            # data='"' + data + '"'
            # # sta=dbilayer.insert_into_table('requisition', constants.columns_requisition_table, data)
            # if(sta is not None):
            #     if ('message' in sta):
            #         if (sta['message'] == 'Success'):
            #             respsucc={"response_id": request_data['request_id'], "response_for": "Event_Create", "response_set_to": request_data['request_src'], "response": {"message": "Calendar Event Created Successfully","status_code":200, "last_id": sta["last_insert_id"]}}
            #             return respsucc
            #         else:
            #             respfail={"response_id": request_data['request_id'], "response_for": "Event_Create", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request"}}
            #             return respfail
            #     else:
            #         respfail={"response_id": request_data['request_id'], "response_for": "Event_Create", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request"}}
            #         return respfail
            # else:
            #     respfail={"response_id": request_data['request_id'], "response_for": "Event_Create", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request"}}
            #     return respfail
        else:
            respfail={"response_id": request_data['request_id'], "response_for": "Event_Create", "response_set_to": request_data['request_src'], "response": {"message": "Error to create google meet"}}
            return respfail
    else:
        respfail={"response_id": request_data['request_id'], "response_for": "Event_Create", "response_set_to": request_data['request_src'], "response": {"message": "Error Encountered"}}
        return respfail
    
#jobOpening ===========================>>>>>>>>>>>>>>>>>>>>>>
def jobOpening_create(request_data):
    if isinstance(request_data, dict):
        data_to_insert = request_data['request_data']
        print(len(data_to_insert),"BEFORE===============")
        final_data_to_insert=convert_data_types_for_insert('ta_application', 'job_opening_requests', data_to_insert)
        print(final_data_to_insert,"==========FINAL DATA to insert")
        print(len(final_data_to_insert.split(",")),"after===============")
        keys = list(data_to_insert.keys())
        columns_output = ",".join([f"`{key}`" for key in keys])
        sta=dbilayer.insert_into_table('job_opening_requests', columns_output, final_data_to_insert)
        if(sta is not None):
            if ('message' in sta):
                if (sta['message'] == 'Success'):
                    respsucc={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Created Successfully","status_code":200, "last_id": sta["last_insert_id"]}}
                    return respsucc
                else:
                    respfail={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request"}}
                    return respfail
            else:
                respfail={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request"}}
                return respfail
        else:
            respfail={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request"}}
            return respfail
    else:
        respfail={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Error Encountered"}}
        return respfail
    
def jobOpening_readOneCond(request_data):
    if isinstance(request_data, dict):
        data=request_data['request_data']
        data["status"] = 1
        condition_data = convert_data_types_for_conditions('ta_application', 'job_opening_requests', data)
        sta=dbilayer.read_with_condition('job_opening_requests', '*', condition_data)
        if ((sta is not None) and (isinstance(sta, list))):
            if(len(sta) > 0):
                respsucc={"response_id": request_data['request_id'], "response_for": "Read One With Condition", "response_set_to": request_data['request_src'], "response": {"message": "Success","status_code":200, "data":sta[0]}}
                return respsucc
            else:
                respfail={"response_id": request_data['request_id'], "response_for": "Read One With Condition", "response_set_to": request_data['request_src'], "response": {"message": "No Results Found"}}
                return respfail
        else:
            respfail={"response_id": request_data['request_id'], "response_for": "Read One With Condition", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request"}}
            return respfail
    else:
        respfail={"response_id": request_data['request_id'], "response_for": "Read One With Condition", "response_set_to": request_data['request_src'], "response": {"message": "Error Encountered"}}
        return respfail
    
def jobOpening_readAllCond(request_data):
    if isinstance(request_data, dict):
        data=request_data['request_data']
        data["status"] = 1
        condition_data = convert_data_types_for_conditions('ta_application', 'job_opening_requests', data)
        sta=dbilayer.read_with_condition('job_opening_requests', '*', condition_data)
        print("sta in bll engine---->", sta)
        if ((sta is not None) and (isinstance(sta, list))):
            if (len(sta) > 0):
                respsucc={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "Success", "status_code":200,"data":sta}}
                return respsucc
            else:
                respfail={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "No Results Found"}}
                return respfail
        else:
            respfail={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request or Requested Items All Are Inactive"}}
            return respfail
    else:
        respfail={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "Error Encountered"}}
        return respfail
    
def jobOpening_readAll(request_data):
    if isinstance(request_data, dict):
        sta=dbilayer.read_all_without_condition('job_opening_requests')
        if ((sta is not None) and (isinstance(sta, list))):
            if (len(sta) > 0):
                respsucc={"response_id": request_data['request_id'], "response_for": "Read All", "response_set_to": request_data['request_src'], "response": {"message": "Success","status_code":200,"data":sta}}
                return respsucc
            else:
                respfail={"response_id": request_data['request_id'], "response_for": "Read All", "response_set_to": request_data['request_src'], "response": {"message": "No Results Found"}}
                return respfail
        else:
            respfail={"response_id": request_data['request_id'], "response_for": "Read All", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request"}}
            return respfail
    else:
        respfail={"response_id": request_data['request_id'], "response_for": "Read All", "response_set_to": request_data['request_src'], "response": {"message": "Error Encountered"}}
        return respfail
def jobOpening_update(request_data):
    if request_data['request_data']['job_request_id']:
        data=request_data['request_data']
        user_email=data['user_email']
        stored_layout_ids_by_specific_user=dbilayer.return_specific_list_with_cond("job_request_id", "job_opening_requests", "user_email='{}'".format(user_email))
        print("layout ids stored by user", stored_layout_ids_by_specific_user)
        job_request_id = data['job_request_id']
        if (int(job_request_id) in stored_layout_ids_by_specific_user):
            id_dict={}
            id_dict['job_request_id']=data['job_request_id']
            id_dict['status']=1
            id_dict['user_email'] = data['user_email']
            del data["user_email"]
            del data["job_request_id"]
            to_be_updated_data=convert_data_types_for_update('ta_application', 'job_opening_requests', request_data["request_data"])
            condition_data = convert_data_types_for_conditions('ta_application', 'job_opening_requests', id_dict)
            sta = dbilayer.update_table("job_opening_requests", to_be_updated_data, condition_data)
            print(sta)
            if((sta is not None) and (sta == "Success")):
                respsucc = {"response_id": request_data['request_id'], "response_for":"Update","response_set_to":request_data['request_src'],"response_data": {"message":"Updated Successfully","status_code":200}}
                return  respsucc
            elif(sta == 'Failed'):
                respfail = {"response_id": request_data['request_id'], "response_for":"Update","response_set_to":request_data['request_src'],"response_data": {"message":"Update request Failed"}}
                return  respfail
        else:
            respfail = {"response_id": request_data['request_id'], "response_for":"Update","response_set_to":request_data['request_src'],"response_data": {"message":"Job opening Id requested for updation not yet stored by user"}}
            return  respfail
    else:
        respfail = {"response_id": request_data['request_id'], "response_for":"Update","response_set_to":request_data['request_src'],"response_data": {"message":"Error in Request"}}
        return  respfail 
def jobOpening_delete(request_data):
    if request_data['request_data']['job_request_id']:
        data = request_data['request_data']
        stored_layout_ids_by_specific_user=dbilayer.return_specific_list_with_cond("job_request_id", "job_opening_requests", "user_email='{}'".format(request_data['request_data']['user_email']))
        print("layout ids stored by user", stored_layout_ids_by_specific_user)
        jobOpening_id = request_data['request_data']['job_request_id']
        if (int(jobOpening_id) in stored_layout_ids_by_specific_user):
            id_dict={}
            id_dict['job_request_id']=data['job_request_id']
            id_dict['status']=1
            id_dict['user_email'] = data['user_email']

            to_be_updated_data=convert_data_types_for_update('ta_application', 'job_opening_requests', {"status":9})
            condition_data = convert_data_types_for_conditions('ta_application', 'job_opening_requests', id_dict)
            sta = dbilayer.update_table("job_opening_requests", to_be_updated_data, condition_data)
            print(sta)
            if((sta is not None) and (sta == "Success")):
                respsucc = {"response_id": request_data['request_id'], "response_for":"Delete","response_set_to":request_data['request_src'],"response_data": {"message":"Deleted Successfully","status_code":200}}
                return  respsucc
            elif(sta == 'Failed'):
                respfail = {"response_id": request_data['request_id'], "response_for":"Delete","response_set_to":request_data['request_src'],"response_data": {"message":"Delete request Failed"}}
                return  respfail
        else:
            respfail = {"response_id": request_data['request_id'], "response_for":"Delete","response_set_to":request_data['request_src'],"response_data": {"message":"Job opening Id requested for deletion not yet stored by user"}}
            return  respfail
    else:
        respfail = {"response_id": request_data['request_id'], "response_for":"Delete","response_set_to":request_data['request_src'],"response_data": {"message":"Error in Request"}}
        return  respfail


#interview ===========================>>>>>>>>>>>>>>>>>>>>>>
def interview_create(request_data):
    pass
def interview_readOneCond(request_data):
    pass
    
def interview_readAllCond(request_data):
    pass
def interview_readAll(request_data):
    pass
def interview_update(request_data):
    pass
def interview_delete(request_data):
    pass


#EMPLOYEE DETAILS ===========================>>>>>>>>>>>>>>>>>>>>>>
def employee_details_create(request_data):
    if isinstance(request_data, dict):
        data_to_insert = request_data['request_data']
        final_data_to_insert=convert_data_types_for_insert('ta_application', 'employee_details', data_to_insert)
        print(final_data_to_insert,"==========FINAL DATA to insert")
        keys = list(data_to_insert.keys())
        columns_output = ",".join([f"`{key}`" for key in keys])
        sta=dbilayer.insert_into_table('employee_details', columns_output, final_data_to_insert)
        if(sta is not None):
            if ('message' in sta):
                if (sta['message'] == 'Success'):
                    respsucc={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Created Successfully","status_code":200, "last_id": sta["last_insert_id"]}}
                    return respsucc
                else:
                    respfail={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request"}}
                    return respfail
            else:
                respfail={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request"}}
                return respfail
        else:
            respfail={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request"}}
            return respfail
    else:
        respfail={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Error Encountered"}}
        return respfail
    
def employee_details_create_bulk(request_data):
    try:
        success_ids=[]
        failure_ids=[]
        for data in request_data:
            resp = employee_details_create(data)
            if "status_code" in resp["response"]:
                success_ids.append(data["request_data"]["personal_email"])
            else:
                failure_ids.append(data["request_data"]["personal_email"])
        respsucc={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Created Successfully","status_code":200, "success_email_ids": success_ids,"failure_email_ids":failure_ids}}
        return respsucc
    except Exception as e:
        respfail={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Error In Request"}}
        return respfail    
    
def employee_details_readOneCond(request_data):
    if isinstance(request_data, dict):
        data=request_data['request_data']
        data["status"] = 1
        condition_data = convert_data_types_for_conditions('ta_application', 'employee_details', data)
        sta=dbilayer.read_with_condition('employee_details', '*', condition_data)
        if ((sta is not None) and (isinstance(sta, list))):
            if(len(sta) > 0):
                respsucc={"response_id": request_data['request_id'], "response_for": "Read One With Condition", "response_set_to": request_data['request_src'], "response": {"message": "Success","status_code":200, "data":sta[0]}}
                return respsucc
            else:
                respfail={"response_id": request_data['request_id'], "response_for": "Read One With Condition", "response_set_to": request_data['request_src'], "response": {"message": "No Results Found"}}
                return respfail
        else:
            respfail={"response_id": request_data['request_id'], "response_for": "Read One With Condition", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request"}}
            return respfail
    else:
        respfail={"response_id": request_data['request_id'], "response_for": "Read One With Condition", "response_set_to": request_data['request_src'], "response": {"message": "Error Encountered"}}
        return respfail
    
def employee_details_readAllCond(request_data):
    if isinstance(request_data, dict):
        data=request_data['request_data']
        data["status"] = 1
        condition_data = convert_data_types_for_conditions('ta_application', 'employee_details', data)
        sta=dbilayer.read_with_condition('employee_details', '*', condition_data)
        print("sta in bll engine---->", sta)
        if ((sta is not None) and (isinstance(sta, list))):
            if (len(sta) > 0):
                respsucc={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "Success", "status_code":200,"data":sta}}
                return respsucc
            else:
                respfail={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "No Results Found"}}
                return respfail
        else:
            respfail={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request or Requested Items All Are Inactive"}}
            return respfail
    else:
        respfail={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "Error Encountered"}}
        return respfail
def employee_details_readAll(request_data):
    if isinstance(request_data, dict):
        sta=dbilayer.read_all_without_condition('employee_details')
        if ((sta is not None) and (isinstance(sta, list))):
            if (len(sta) > 0):
                respsucc={"response_id": request_data['request_id'], "response_for": "Read All", "response_set_to": request_data['request_src'], "response": {"message": "Success","status_code":200,"data":sta}}
                return respsucc
            else:
                respfail={"response_id": request_data['request_id'], "response_for": "Read All", "response_set_to": request_data['request_src'], "response": {"message": "No Results Found"}}
                return respfail
        else:
            respfail={"response_id": request_data['request_id'], "response_for": "Read All", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request"}}
            return respfail
    else:
        respfail={"response_id": request_data['request_id'], "response_for": "Read All", "response_set_to": request_data['request_src'], "response": {"message": "Error Encountered"}}
        return respfail
def employee_details_update(request_data):
    if request_data['request_data']['candidate_id']:
        data=request_data['request_data']
        user_email=data['user_email']
        stored_layout_ids_by_specific_user=dbilayer.return_specific_list_with_cond("candidate_id", "employee_details", "user_email='{}'".format(user_email))
        print("layout ids stored by user", stored_layout_ids_by_specific_user)
        candidate_id = data['candidate_id']
        if (int(candidate_id) in stored_layout_ids_by_specific_user):
            id_dict={}
            id_dict['candidate_id']=data['candidate_id']
            id_dict['status']=1
            id_dict['user_email'] = data['user_email']
            del data["user_email"]
            del data["candidate_id"]
            to_be_updated_data=convert_data_types_for_update('ta_application', 'employee_details', request_data["request_data"])
            condition_data = convert_data_types_for_conditions('ta_application', 'employee_details', id_dict)
            sta = dbilayer.update_table("employee_details", to_be_updated_data, condition_data)
            print(sta)
            if((sta is not None) and (sta == "Success")):
                respsucc = {"response_id": request_data['request_id'], "response_for":"Update","response_set_to":request_data['request_src'],"response_data": {"message":"Updated Successfully","status_code":200}}
                return  respsucc
            elif(sta == 'Failed'):
                respfail = {"response_id": request_data['request_id'], "response_for":"Update","response_set_to":request_data['request_src'],"response_data": {"message":"Update request Failed"}}
                return  respfail
        else:
            respfail = {"response_id": request_data['request_id'], "response_for":"Update","response_set_to":request_data['request_src'],"response_data": {"message":"Candidate Id requested for updation not yet stored by user"}}
            return  respfail
    else:
        respfail = {"response_id": request_data['request_id'], "response_for":"Update","response_set_to":request_data['request_src'],"response_data": {"message":"Error in Request"}}
        return  respfail 
def employee_details_delete(request_data):
    if request_data['request_data']['candidate_id']:
        data = request_data['request_data']
        stored_layout_ids_by_specific_user=dbilayer.return_specific_list_with_cond("candidate_id", "employee_details", "user_email='{}'".format(request_data['request_data']['user_email']))
        print("layout ids stored by user", stored_layout_ids_by_specific_user)
        jobOpening_id = request_data['request_data']['candidate_id']
        if (int(jobOpening_id) in stored_layout_ids_by_specific_user):
            id_dict={}
            id_dict['candidate_id']=data['candidate_id']
            id_dict['status']=1
            id_dict['user_email'] = data['user_email']

            to_be_updated_data=convert_data_types_for_update('ta_application', 'employee_details', {"status":9})
            condition_data = convert_data_types_for_conditions('ta_application', 'employee_details', id_dict)
            sta = dbilayer.update_table("employee_details", to_be_updated_data, condition_data)
            print(sta)
            if((sta is not None) and (sta == "Success")):
                respsucc = {"response_id": request_data['request_id'], "response_for":"Delete","response_set_to":request_data['request_src'],"response_data": {"message":"Deleted Successfully","status_code":200}}
                return  respsucc
            elif(sta == 'Failed'):
                respfail = {"response_id": request_data['request_id'], "response_for":"Delete","response_set_to":request_data['request_src'],"response_data": {"message":"Delete request Failed"}}
                return  respfail
        else:
            respfail = {"response_id": request_data['request_id'], "response_for":"Delete","response_set_to":request_data['request_src'],"response_data": {"message":"Job opening Id requested for deletion not yet stored by user"}}
            return  respfail
    else:
        respfail = {"response_id": request_data['request_id'], "response_for":"Delete","response_set_to":request_data['request_src'],"response_data": {"message":"Error in Request"}}
        return  respfail

#candidate ===========================>>>>>>>>>>>>>>>>>>>>>>....
def candidate_create(request_data):
    if isinstance(request_data, dict):
        data_to_insert = request_data['request_data']
        final_data_to_insert=convert_data_types_for_insert('ta_application', 'interview_candidates', data_to_insert)
        print(final_data_to_insert,"==========FINAL DATA to insert")
        keys = list(data_to_insert.keys())
        columns_output = ",".join([f"`{key}`" for key in keys])
        sta=dbilayer.insert_into_table('interview_candidates', columns_output, final_data_to_insert)
        if(sta is not None):
            if ('message' in sta):
                if (sta['message'] == 'Success'):
                    respsucc={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Created Successfully","status_code":200, "last_id": sta["last_insert_id"]}}
                    return respsucc
                else:
                    respfail={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request"}}
                    return respfail
            else:
                respfail={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request"}}
                return respfail
        else:
            respfail={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request"}}
            return respfail
    else:
        respfail={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Error Encountered"}}
        return respfail
    
def candidate_create_bulk(request_data):
    try:
        success_ids=[]
        failure_ids=[]
        for data in request_data:
            resp = candidate_create(data)
            if "status_code" in resp["response"]:
                success_ids.append(data["request_data"]["personal_email"])
            else:
                failure_ids.append(data["request_data"]["personal_email"])
        respsucc={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Created Successfully","status_code":200, "success_email_ids": success_ids,"failure_email_ids":failure_ids}}
        return respsucc
    except Exception as e:
        respfail={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Error In Request"}}
        return respfail
        
    
    
    
def candidate_readOneCond(request_data):
    if isinstance(request_data, dict):
        data=request_data['request_data']
        data["status"] = 1
        condition_data = convert_data_types_for_conditions('ta_application', 'interview_candidates', data)
        sta=dbilayer.read_with_condition('interview_candidates', '*', condition_data)
        if ((sta is not None) and (isinstance(sta, list))):
            if(len(sta) > 0):
                respsucc={"response_id": request_data['request_id'], "response_for": "Read One With Condition", "response_set_to": request_data['request_src'], "response": {"message": "Success","status_code":200, "data":sta[0]}}
                return respsucc
            else:
                respfail={"response_id": request_data['request_id'], "response_for": "Read One With Condition", "response_set_to": request_data['request_src'], "response": {"message": "No Results Found"}}
                return respfail
        else:
            respfail={"response_id": request_data['request_id'], "response_for": "Read One With Condition", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request"}}
            return respfail
    else:
        respfail={"response_id": request_data['request_id'], "response_for": "Read One With Condition", "response_set_to": request_data['request_src'], "response": {"message": "Error Encountered"}}
        return respfail
def candidate_readAllCond(request_data):
    if isinstance(request_data, dict):
        data=request_data['request_data']
        data["status"] = 1
        condition_data = convert_data_types_for_conditions('ta_application', 'interview_candidates', data)
        sta=dbilayer.read_with_condition('interview_candidates', '*', condition_data)
        print("sta in bll engine---->", sta)
        if ((sta is not None) and (isinstance(sta, list))):
            if (len(sta) > 0):
                respsucc={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "Success", "status_code":200,"data":sta}}
                return respsucc
            else:
                respfail={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "No Results Found"}}
                return respfail
        else:
            respfail={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request or Requested Items All Are Inactive"}}
            return respfail
    else:
        respfail={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "Error Encountered"}}
        return respfail
def candidate_readRecent(request_data):
    if isinstance(request_data, dict):
        data=request_data['request_data']
        data["status"] = 1
        condition_data = convert_data_types_for_conditions('ta_application', 'interview_candidates', data)
        sta=dbilayer.read_recent_five('interview_candidates')
        print("sta in bll engine---->", sta)
        if ((sta is not None) and (isinstance(sta, list))):
            if (len(sta) > 0):
                respsucc={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "Success", "status_code":200,"data":sta}}
                return respsucc
            else:
                respfail={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "No Results Found"}}
                return respfail
        else:
            respfail={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request or Requested Items All Are Inactive"}}
            return respfail
    else:
        respfail={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "Error Encountered"}}
        return respfail
    
def candidate_readAll(request_data):
    if isinstance(request_data, dict):
        sta=dbilayer.read_all_without_condition('interview_candidates')
        if ((sta is not None) and (isinstance(sta, list))):
            if (len(sta) > 0):
                respsucc={"response_id": request_data['request_id'], "response_for": "Read All", "response_set_to": request_data['request_src'], "response": {"message": "Success","status_code":200,"data":sta}}
                return respsucc
            else:
                respfail={"response_id": request_data['request_id'], "response_for": "Read All", "response_set_to": request_data['request_src'], "response": {"message": "No Results Found"}}
                return respfail
        else:
            respfail={"response_id": request_data['request_id'], "response_for": "Read All", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request"}}
            return respfail
    else:
        respfail={"response_id": request_data['request_id'], "response_for": "Read All", "response_set_to": request_data['request_src'], "response": {"message": "Error Encountered"}}
        return respfail
def candidate_update(request_data):
    if request_data['request_data']['candidate_id']:
        data=request_data['request_data']
        user_email=data['user_email']
        stored_layout_ids_by_specific_user=dbilayer.return_specific_list_with_cond("candidate_id", "interview_candidates", "user_email='{}'".format(user_email))
        print("layout ids stored by user", stored_layout_ids_by_specific_user)
        candidate_id = data['candidate_id']
        if (int(candidate_id) in stored_layout_ids_by_specific_user):
            id_dict={}
            id_dict['candidate_id']=data['candidate_id']
            id_dict['status']=1
            id_dict['user_email'] = data['user_email']
            del data["user_email"]
            del data["candidate_id"]
            to_be_updated_data=convert_data_types_for_update('ta_application', 'interview_candidates', request_data["request_data"])
            condition_data = convert_data_types_for_conditions('ta_application', 'interview_candidates', id_dict)
            sta = dbilayer.update_table("interview_candidates", to_be_updated_data, condition_data)
            print(sta)
            if((sta is not None) and (sta == "Success")):
                respsucc = {"response_id": request_data['request_id'], "response_for":"Update","response_set_to":request_data['request_src'],"response_data": {"message":"Updated Successfully","status_code":200}}
                return  respsucc
            elif(sta == 'Failed'):
                respfail = {"response_id": request_data['request_id'], "response_for":"Update","response_set_to":request_data['request_src'],"response_data": {"message":"Update request Failed"}}
                return  respfail
        else:
            respfail = {"response_id": request_data['request_id'], "response_for":"Update","response_set_to":request_data['request_src'],"response_data": {"message":"Candidate Id requested for updation not yet stored by user"}}
            return  respfail
    else:
        respfail = {"response_id": request_data['request_id'], "response_for":"Update","response_set_to":request_data['request_src'],"response_data": {"message":"Error in Request"}}
        return  respfail 
def candidate_delete(request_data):
    if request_data['request_data']['candidate_id']:
        data = request_data['request_data']
        stored_layout_ids_by_specific_user=dbilayer.return_specific_list_with_cond("candidate_id", "interview_candidates", "user_email='{}'".format(request_data['request_data']['user_email']))
        print("layout ids stored by user", stored_layout_ids_by_specific_user)
        jobOpening_id = request_data['request_data']['candidate_id']
        if (int(jobOpening_id) in stored_layout_ids_by_specific_user):
            id_dict={}
            id_dict['candidate_id']=data['candidate_id']
            id_dict['status']=1
            id_dict['user_email'] = data['user_email']

            to_be_updated_data=convert_data_types_for_update('ta_application', 'interview_candidates', {"status":9})
            condition_data = convert_data_types_for_conditions('ta_application', 'interview_candidates', id_dict)
            sta = dbilayer.update_table("interview_candidates", to_be_updated_data, condition_data)
            print(sta)
            if((sta is not None) and (sta == "Success")):
                respsucc = {"response_id": request_data['request_id'], "response_for":"Delete","response_set_to":request_data['request_src'],"response_data": {"message":"Deleted Successfully","status_code":200}}
                return  respsucc
            elif(sta == 'Failed'):
                respfail = {"response_id": request_data['request_id'], "response_for":"Delete","response_set_to":request_data['request_src'],"response_data": {"message":"Delete request Failed"}}
                return  respfail
        else:
            respfail = {"response_id": request_data['request_id'], "response_for":"Delete","response_set_to":request_data['request_src'],"response_data": {"message":"Job opening Id requested for deletion not yet stored by user"}}
            return  respfail
    else:
        respfail = {"response_id": request_data['request_id'], "response_for":"Delete","response_set_to":request_data['request_src'],"response_data": {"message":"Error in Request"}}
        return  respfail
    




#DROP DOWN API'S===============================================================================================================>>>>>>>>>>>>>
# EMPLOYEMENT TYPE
def employmentType_create(request_data):
    if isinstance(request_data, dict):
        data_to_insert = request_data['request_data']
        final_data_to_insert=convert_data_types_for_insert('ta_application', 'employment_type', data_to_insert)
        print(final_data_to_insert,"==========FINAL DATA to insert")
        keys = list(data_to_insert.keys())
        columns_output = ",".join([f"`{key}`" for key in keys])
        sta=dbilayer.insert_into_table('employment_type', columns_output, final_data_to_insert)
        if(sta is not None):
            if ('message' in sta):
                if (sta['message'] == 'Success'):
                    respsucc={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Created Successfully","status_code":200, "last_id": sta["last_insert_id"]}}
                    return respsucc
                else:
                    respfail={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request"}}
                    return respfail
            else:
                respfail={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request"}}
                return respfail
        else:
            respfail={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request"}}
            return respfail
    else:
        respfail={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Error Encountered"}}
        return respfail
    
def employmentType_readAll(request_data):
    if isinstance(request_data, dict):
        data=request_data['request_data']
        condition_dict = {}
        condition_dict["status"] = 1
        condition_data = convert_data_types_for_conditions('ta_application', 'employment_type', condition_dict)
        sta=dbilayer.read_with_condition('employment_type','*',condition_data)
        print("sta in bll engine---->", sta)
        if ((sta is not None) and (isinstance(sta, list))):
            if (len(sta) > 0):
                respsucc={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "Success", "status_code":200,"data":sta}}
                return respsucc
            else:
                respfail={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "No Results Found"}}
                return respfail
        else:
            respfail={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request or Requested Items All Are Inactive"}}
            return respfail
    else:
        respfail={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "Error Encountered"}}
        return respfail
    
def employmentType_update(request_data):
    if request_data['request_data']['id']:
        data=request_data['request_data']
        id_dict={}
        id_dict['id']=data['id']
        id_dict['status']=1
        condition_data = convert_data_types_for_conditions('ta_application', 'employment_type', id_dict)
        del data['id']
        to_be_updated_data=convert_data_types_for_update('ta_application', 'employment_type', data)
        sta = dbilayer.update_table("employment_type", to_be_updated_data, condition_data)
        print(sta)
        if((sta is not None) and (sta == "Success")):
            respsucc = {"response_id": request_data['request_id'], "response_for":"Update","response_set_to":request_data['request_src'],"response_data": {"message":"Updated Successfully","status_code":200}}
            return  respsucc
        elif(sta == 'Failed'):
            respfail = {"response_id": request_data['request_id'], "response_for":"Update","response_set_to":request_data['request_src'],"response_data": {"message":"Update request Failed"}}
            return  respfail
    else:
        respfail = {"response_id": request_data['request_id'], "response_for":"Update","response_set_to":request_data['request_src'],"response_data": {"message":"Error in Request"}}
        return  respfail 
    
def employmentType_delete(request_data):
    if request_data['request_data']['id']:
        data = request_data['request_data']
        id_dict={}
        id_dict['id']=data['id']
        to_be_updated_data=convert_data_types_for_update('ta_application', 'employment_type', {"status":9})
        condition_data = convert_data_types_for_conditions('ta_application', 'employment_type', id_dict)
        sta = dbilayer.update_table("employment_type", to_be_updated_data, condition_data)
        print(sta)
        if((sta is not None) and (sta == "Success")):
            respsucc = {"response_id": request_data['request_id'], "response_for":"Delete","response_set_to":request_data['request_src'],"response_data": {"message":"Deleted Successfully","status_code":200}}
            return  respsucc
        elif(sta == 'Failed'):
            respfail = {"response_id": request_data['request_id'], "response_for":"Delete","response_set_to":request_data['request_src'],"response_data": {"message":"Delete request Failed"}}
            return  respfail
    
    else:
        respfail = {"response_id": request_data['request_id'], "response_for":"Delete","response_set_to":request_data['request_src'],"response_data": {"message":"Error in Request"}}
        return  respfail
    
    
    
    
# SENIORITY LEVEL
def seniorityLevel_create(request_data):
    if isinstance(request_data, dict):
        data_to_insert = request_data['request_data']
        final_data_to_insert=convert_data_types_for_insert('ta_application', 'seniority_level', data_to_insert)
        print(final_data_to_insert,"==========FINAL DATA to insert")
        keys = list(data_to_insert.keys())
        columns_output = ",".join([f"`{key}`" for key in keys])
        sta=dbilayer.insert_into_table('seniority_level', columns_output, final_data_to_insert)
        if(sta is not None):
            if ('message' in sta):
                if (sta['message'] == 'Success'):
                    respsucc={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Created Successfully","status_code":200, "last_id": sta["last_insert_id"]}}
                    return respsucc
                else:
                    respfail={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request"}}
                    return respfail
            else:
                respfail={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request"}}
                return respfail
        else:
            respfail={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request"}}
            return respfail
    else:
        respfail={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Error Encountered"}}
        return respfail
    
def seniorityLevel_readAll(request_data):
    if isinstance(request_data, dict):
        data=request_data['request_data']
        condition_dict = {}
        condition_dict["status"] = 1
        condition_data = convert_data_types_for_conditions('ta_application', 'seniority_level', condition_dict)
        sta=dbilayer.read_with_condition('seniority_level', '*', condition_data)
        print("sta in bll engine---->", sta)
        if ((sta is not None) and (isinstance(sta, list))):
            if (len(sta) > 0):
                respsucc={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "Success", "status_code":200,"data":sta}}
                return respsucc
            else:
                respfail={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "No Results Found"}}
                return respfail
        else:
            respfail={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request or Requested Items All Are Inactive"}}
            return respfail
    else:
        respfail={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "Error Encountered"}}
        return respfail
    
def seniorityLevel_update(request_data):
    if request_data['request_data']['id']:
        data=request_data['request_data']
        id_dict={}
        id_dict['id']=data['id']
        id_dict['status']=1
        condition_data = convert_data_types_for_conditions('ta_application', 'seniority_level', id_dict)
        del data['id']
        to_be_updated_data=convert_data_types_for_update('ta_application', 'seniority_level', data)
        sta = dbilayer.update_table("seniority_level", to_be_updated_data, condition_data)
        print(sta)
        if((sta is not None) and (sta == "Success")):
            respsucc = {"response_id": request_data['request_id'], "response_for":"Update","response_set_to":request_data['request_src'],"response_data": {"message":"Updated Successfully","status_code":200}}
            return  respsucc
        elif(sta == 'Failed'):
            respfail = {"response_id": request_data['request_id'], "response_for":"Update","response_set_to":request_data['request_src'],"response_data": {"message":"Update request Failed"}}
            return  respfail
    else:
        respfail = {"response_id": request_data['request_id'], "response_for":"Update","response_set_to":request_data['request_src'],"response_data": {"message":"Error in Request"}}
        return  respfail 
    
def seniorityLevel_delete(request_data):
    if request_data['request_data']['id']:
        data = request_data['request_data']
        id_dict={}
        id_dict['id']=data['id']
        to_be_updated_data=convert_data_types_for_update('ta_application', 'seniority_level', {"status":9})
        condition_data = convert_data_types_for_conditions('ta_application', 'seniority_level', id_dict)
        sta = dbilayer.update_table("seniority_level", to_be_updated_data, condition_data)
        print(sta)
        if((sta is not None) and (sta == "Success")):
            respsucc = {"response_id": request_data['request_id'], "response_for":"Delete","response_set_to":request_data['request_src'],"response_data": {"message":"Deleted Successfully","status_code":200}}
            return  respsucc
        elif(sta == 'Failed'):
            respfail = {"response_id": request_data['request_id'], "response_for":"Delete","response_set_to":request_data['request_src'],"response_data": {"message":"Delete request Failed"}}
            return  respfail
    
    else:
        respfail = {"response_id": request_data['request_id'], "response_for":"Delete","response_set_to":request_data['request_src'],"response_data": {"message":"Error in Request"}}
        return  respfail
    
    
# JOB FUNCTION
def jobFunction_create(request_data):
    if isinstance(request_data, dict):
        data_to_insert = request_data['request_data']
        final_data_to_insert=convert_data_types_for_insert('ta_application', 'job_function', data_to_insert)
        print(final_data_to_insert,"==========FINAL DATA to insert")
        keys = list(data_to_insert.keys())
        columns_output = ",".join([f"`{key}`" for key in keys])
        sta=dbilayer.insert_into_table('job_function', columns_output, final_data_to_insert)
        if(sta is not None):
            if ('message' in sta):
                if (sta['message'] == 'Success'):
                    respsucc={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Created Successfully","status_code":200, "last_id": sta["last_insert_id"]}}
                    return respsucc
                else:
                    respfail={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request"}}
                    return respfail
            else:
                respfail={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request"}}
                return respfail
        else:
            respfail={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request"}}
            return respfail
    else:
        respfail={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Error Encountered"}}
        return respfail
    
def jobFunction_readAll(request_data):
    if isinstance(request_data, dict):
        data=request_data['request_data']
        condition_dict = {}
        condition_dict["status"] = 1
        condition_data = convert_data_types_for_conditions('ta_application', 'job_function', condition_dict)
        sta=dbilayer.read_with_condition('job_function', '*', condition_data)
        print("sta in bll engine---->", sta)
        if ((sta is not None) and (isinstance(sta, list))):
            if (len(sta) > 0):
                respsucc={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "Success", "status_code":200,"data":sta}}
                return respsucc
            else:
                respfail={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "No Results Found"}}
                return respfail
        else:
            respfail={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request or Requested Items All Are Inactive"}}
            return respfail
    else:
        respfail={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "Error Encountered"}}
        return respfail
    
def jobFunction_update(request_data):
    if request_data['request_data']['id']:
        data=request_data['request_data']
        id_dict={}
        id_dict['id']=data['id']
        id_dict['status']=1
        condition_data = convert_data_types_for_conditions('ta_application', 'job_function', id_dict)
        del data['id']
        to_be_updated_data=convert_data_types_for_update('ta_application', 'job_function', data)
        sta = dbilayer.update_table("job_function", to_be_updated_data, condition_data)
        print(sta)
        if((sta is not None) and (sta == "Success")):
            respsucc = {"response_id": request_data['request_id'], "response_for":"Update","response_set_to":request_data['request_src'],"response_data": {"message":"Updated Successfully","status_code":200}}
            return  respsucc
        elif(sta == 'Failed'):
            respfail = {"response_id": request_data['request_id'], "response_for":"Update","response_set_to":request_data['request_src'],"response_data": {"message":"Update request Failed"}}
            return  respfail
    else:
        respfail = {"response_id": request_data['request_id'], "response_for":"Update","response_set_to":request_data['request_src'],"response_data": {"message":"Error in Request"}}
        return  respfail 
    
def jobFunction_delete(request_data):
    if request_data['request_data']['id']:
        data = request_data['request_data']
        id_dict={}
        id_dict['id']=data['id']
        to_be_updated_data=convert_data_types_for_update('ta_application', 'job_function', {"status":9})
        condition_data = convert_data_types_for_conditions('ta_application', 'job_function', id_dict)
        sta = dbilayer.update_table("job_function", to_be_updated_data, condition_data)
        print(sta)
        if((sta is not None) and (sta == "Success")):
            respsucc = {"response_id": request_data['request_id'], "response_for":"Delete","response_set_to":request_data['request_src'],"response_data": {"message":"Deleted Successfully","status_code":200}}
            return  respsucc
        elif(sta == 'Failed'):
            respfail = {"response_id": request_data['request_id'], "response_for":"Delete","response_set_to":request_data['request_src'],"response_data": {"message":"Delete request Failed"}}
            return  respfail
    
    else:
        respfail = {"response_id": request_data['request_id'], "response_for":"Delete","response_set_to":request_data['request_src'],"response_data": {"message":"Error in Request"}}
        return  respfail
    

# CUSTOMER
def customer_create(request_data):
    if isinstance(request_data, dict):
        data_to_insert = request_data['request_data']
        final_data_to_insert=convert_data_types_for_insert('ta_application', 'customer', data_to_insert)
        print(final_data_to_insert,"==========FINAL DATA to insert")
        keys = list(data_to_insert.keys())
        columns_output = ",".join([f"`{key}`" for key in keys])
        sta=dbilayer.insert_into_table('customer', columns_output, final_data_to_insert)
        if(sta is not None):
            if ('message' in sta):
                if (sta['message'] == 'Success'):
                    respsucc={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Created Successfully","status_code":200, "last_id": sta["last_insert_id"]}}
                    return respsucc
                else:
                    respfail={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request"}}
                    return respfail
            else:
                respfail={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request"}}
                return respfail
        else:
            respfail={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request"}}
            return respfail
    else:
        respfail={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Error Encountered"}}
        return respfail
    
def customer_readAll(request_data):
    if isinstance(request_data, dict):
        data=request_data['request_data']
        condition_dict = {}
        condition_dict["status"] = 1
        condition_data = convert_data_types_for_conditions('ta_application', 'customer', condition_dict)
        sta=dbilayer.read_with_condition('customer', '*', condition_data)
        print("sta in bll engine---->", sta)
        if ((sta is not None) and (isinstance(sta, list))):
            if (len(sta) > 0):
                respsucc={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "Success", "status_code":200,"data":sta}}
                return respsucc
            else:
                respfail={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "No Results Found"}}
                return respfail
        else:
            respfail={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request or Requested Items All Are Inactive"}}
            return respfail
    else:
        respfail={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "Error Encountered"}}
        return respfail
    
def customer_update(request_data):
    if request_data['request_data']['id']:
        data=request_data['request_data']
        id_dict={}
        id_dict['id']=data['id']
        id_dict['status']=1
        condition_data = convert_data_types_for_conditions('ta_application', 'customer', id_dict)
        del data['id']
        to_be_updated_data=convert_data_types_for_update('ta_application', 'customer', data)
        sta = dbilayer.update_table("customer", to_be_updated_data, condition_data)
        print(sta)
        if((sta is not None) and (sta == "Success")):
            respsucc = {"response_id": request_data['request_id'], "response_for":"Update","response_set_to":request_data['request_src'],"response_data": {"message":"Updated Successfully","status_code":200}}
            return  respsucc
        elif(sta == 'Failed'):
            respfail = {"response_id": request_data['request_id'], "response_for":"Update","response_set_to":request_data['request_src'],"response_data": {"message":"Update request Failed"}}
            return  respfail
    else:
        respfail = {"response_id": request_data['request_id'], "response_for":"Update","response_set_to":request_data['request_src'],"response_data": {"message":"Error in Request"}}
        return  respfail 
    
def customer_delete(request_data):
    if request_data['request_data']['id']:
        data = request_data['request_data']
        id_dict={}
        id_dict['id']=data['id']
        to_be_updated_data=convert_data_types_for_update('ta_application', 'customer', {"status":9})
        condition_data = convert_data_types_for_conditions('ta_application', 'customer', id_dict)
        sta = dbilayer.update_table("customer", to_be_updated_data, condition_data)
        print(sta)
        if((sta is not None) and (sta == "Success")):
            respsucc = {"response_id": request_data['request_id'], "response_for":"Delete","response_set_to":request_data['request_src'],"response_data": {"message":"Deleted Successfully","status_code":200}}
            return  respsucc
        elif(sta == 'Failed'):
            respfail = {"response_id": request_data['request_id'], "response_for":"Delete","response_set_to":request_data['request_src'],"response_data": {"message":"Delete request Failed"}}
            return  respfail
    
    else:
        respfail = {"response_id": request_data['request_id'], "response_for":"Delete","response_set_to":request_data['request_src'],"response_data": {"message":"Error in Request"}}
        return  respfail
    
    
    
# PROJECT
def project_create(request_data):
    if isinstance(request_data, dict):
        data_to_insert = request_data['request_data']
        final_data_to_insert=convert_data_types_for_insert('ta_application', 'project', data_to_insert)
        print(final_data_to_insert,"==========FINAL DATA to insert")
        keys = list(data_to_insert.keys())
        columns_output = ",".join([f"`{key}`" for key in keys])
        sta=dbilayer.insert_into_table('project', columns_output, final_data_to_insert)
        if(sta is not None):
            if ('message' in sta):
                if (sta['message'] == 'Success'):
                    respsucc={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Created Successfully","status_code":200, "last_id": sta["last_insert_id"]}}
                    return respsucc
                else:
                    respfail={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request"}}
                    return respfail
            else:
                respfail={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request"}}
                return respfail
        else:
            respfail={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request"}}
            return respfail
    else:
        respfail={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Error Encountered"}}
        return respfail
    
def project_readAll(request_data):
    if isinstance(request_data, dict):
        data=request_data['request_data']
        condition_dict = {}
        condition_dict["status"] = 1
        condition_data = convert_data_types_for_conditions('ta_application', 'project', condition_dict)
        sta=dbilayer.read_with_condition('project', '*', condition_data)
        print("sta in bll engine---->", sta)
        if ((sta is not None) and (isinstance(sta, list))):
            if (len(sta) > 0):
                respsucc={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "Success", "status_code":200,"data":sta}}
                return respsucc
            else:
                respfail={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "No Results Found"}}
                return respfail
        else:
            respfail={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request or Requested Items All Are Inactive"}}
            return respfail
    else:
        respfail={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "Error Encountered"}}
        return respfail
    
def project_update(request_data):
    if request_data['request_data']['id']:
        data=request_data['request_data']
        id_dict={}
        id_dict['id']=data['id']
        id_dict['status']=1
        condition_data = convert_data_types_for_conditions('ta_application', 'project', id_dict)
        del data['id']
        to_be_updated_data=convert_data_types_for_update('ta_application', 'project', data)
        sta = dbilayer.update_table("project", to_be_updated_data, condition_data)
        print(sta)
        if((sta is not None) and (sta == "Success")):
            respsucc = {"response_id": request_data['request_id'], "response_for":"Update","response_set_to":request_data['request_src'],"response_data": {"message":"Updated Successfully","status_code":200}}
            return  respsucc
        elif(sta == 'Failed'):
            respfail = {"response_id": request_data['request_id'], "response_for":"Update","response_set_to":request_data['request_src'],"response_data": {"message":"Update request Failed"}}
            return  respfail
    else:
        respfail = {"response_id": request_data['request_id'], "response_for":"Update","response_set_to":request_data['request_src'],"response_data": {"message":"Error in Request"}}
        return  respfail 
    
def project_delete(request_data):
    if request_data['request_data']['id']:
        data = request_data['request_data']
        id_dict={}
        id_dict['id']=data['id']
        to_be_updated_data=convert_data_types_for_update('ta_application', 'project', {"status":9})
        condition_data = convert_data_types_for_conditions('ta_application', 'project', id_dict)
        sta = dbilayer.update_table("project", to_be_updated_data, condition_data)
        print(sta)
        if((sta is not None) and (sta == "Success")):
            respsucc = {"response_id": request_data['request_id'], "response_for":"Delete","response_set_to":request_data['request_src'],"response_data": {"message":"Deleted Successfully","status_code":200}}
            return  respsucc
        elif(sta == 'Failed'):
            respfail = {"response_id": request_data['request_id'], "response_for":"Delete","response_set_to":request_data['request_src'],"response_data": {"message":"Delete request Failed"}}
            return  respfail
    
    else:
        respfail = {"response_id": request_data['request_id'], "response_for":"Delete","response_set_to":request_data['request_src'],"response_data": {"message":"Error in Request"}}
        return  respfail
    
    
    
# PREFERRED WORK MODE
def preferredWorkMode_create(request_data):
    if isinstance(request_data, dict):
        data_to_insert = request_data['request_data']
        final_data_to_insert=convert_data_types_for_insert('ta_application', 'preferred_work_mode', data_to_insert)
        print(final_data_to_insert,"==========FINAL DATA to insert")
        keys = list(data_to_insert.keys())
        columns_output = ",".join([f"`{key}`" for key in keys])
        sta=dbilayer.insert_into_table('preferred_work_mode', columns_output, final_data_to_insert)
        if(sta is not None):
            if ('message' in sta):
                if (sta['message'] == 'Success'):
                    respsucc={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Created Successfully","status_code":200, "last_id": sta["last_insert_id"]}}
                    return respsucc
                else:
                    respfail={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request"}}
                    return respfail
            else:
                respfail={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request"}}
                return respfail
        else:
            respfail={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request"}}
            return respfail
    else:
        respfail={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Error Encountered"}}
        return respfail
    
def preferredWorkMode_readAll(request_data):
    if isinstance(request_data, dict):
        data=request_data['request_data']
        condition_dict = {}
        condition_dict["status"] = 1
        condition_data = convert_data_types_for_conditions('ta_application', 'preferred_work_mode', condition_dict)
        sta=dbilayer.read_with_condition('preferred_work_mode', '*', condition_data)
        print("sta in bll engine---->", sta)
        if ((sta is not None) and (isinstance(sta, list))):
            if (len(sta) > 0):
                respsucc={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "Success", "status_code":200,"data":sta}}
                return respsucc
            else:
                respfail={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "No Results Found"}}
                return respfail
        else:
            respfail={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request or Requested Items All Are Inactive"}}
            return respfail
    else:
        respfail={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "Error Encountered"}}
        return respfail
    
def preferredWorkMode_update(request_data):
    if request_data['request_data']['id']:
        data=request_data['request_data']
        id_dict={}
        id_dict['id']=data['id']
        id_dict['status']=1
        condition_data = convert_data_types_for_conditions('ta_application', 'preferred_work_mode', id_dict)
        del data['id']
        to_be_updated_data=convert_data_types_for_update('ta_application', 'preferred_work_mode', data)
        sta = dbilayer.update_table("preferred_work_mode", to_be_updated_data, condition_data)
        print(sta)
        if((sta is not None) and (sta == "Success")):
            respsucc = {"response_id": request_data['request_id'], "response_for":"Update","response_set_to":request_data['request_src'],"response_data": {"message":"Updated Successfully","status_code":200}}
            return  respsucc
        elif(sta == 'Failed'):
            respfail = {"response_id": request_data['request_id'], "response_for":"Update","response_set_to":request_data['request_src'],"response_data": {"message":"Update request Failed"}}
            return  respfail
    else:
        respfail = {"response_id": request_data['request_id'], "response_for":"Update","response_set_to":request_data['request_src'],"response_data": {"message":"Error in Request"}}
        return  respfail 
    
def preferredWorkMode_delete(request_data):
    if request_data['request_data']['id']:
        data = request_data['request_data']
        id_dict={}
        id_dict['id']=data['id']
        to_be_updated_data=convert_data_types_for_update('ta_application', 'preferred_work_mode', {"status":9})
        condition_data = convert_data_types_for_conditions('ta_application', 'preferred_work_mode', id_dict)
        sta = dbilayer.update_table("preferred_work_mode", to_be_updated_data, condition_data)
        print(sta)
        if((sta is not None) and (sta == "Success")):
            respsucc = {"response_id": request_data['request_id'], "response_for":"Delete","response_set_to":request_data['request_src'],"response_data": {"message":"Deleted Successfully","status_code":200}}
            return  respsucc
        elif(sta == 'Failed'):
            respfail = {"response_id": request_data['request_id'], "response_for":"Delete","response_set_to":request_data['request_src'],"response_data": {"message":"Delete request Failed"}}
            return  respfail
    
    else:
        respfail = {"response_id": request_data['request_id'], "response_for":"Delete","response_set_to":request_data['request_src'],"response_data": {"message":"Error in Request"}}
        return  respfail
    

# COMPANY
def company_create(request_data):
    if isinstance(request_data, dict):
        data_to_insert = request_data['request_data']
        final_data_to_insert=convert_data_types_for_insert('ta_application', 'company', data_to_insert)
        print(final_data_to_insert,"==========FINAL DATA to insert")
        keys = list(data_to_insert.keys())
        columns_output = ",".join([f"`{key}`" for key in keys])
        sta=dbilayer.insert_into_table('company', columns_output, final_data_to_insert)
        if(sta is not None):
            if ('message' in sta):
                if (sta['message'] == 'Success'):
                    respsucc={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Created Successfully","status_code":200, "last_id": sta["last_insert_id"]}}
                    return respsucc
                else:
                    respfail={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request"}}
                    return respfail
            else:
                respfail={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request"}}
                return respfail
        else:
            respfail={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request"}}
            return respfail
    else:
        respfail={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Error Encountered"}}
        return respfail
    
def company_readAll(request_data):
    if isinstance(request_data, dict):
        data=request_data['request_data']
        condition_dict = {}
        condition_dict["status"] = 1
        condition_data = convert_data_types_for_conditions('ta_application', 'company', condition_dict)
        sta=dbilayer.read_with_condition('company', '*', condition_data)
        print("sta in bll engine---->", sta)
        if ((sta is not None) and (isinstance(sta, list))):
            if (len(sta) > 0):
                respsucc={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "Success", "status_code":200,"data":sta}}
                return respsucc
            else:
                respfail={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "No Results Found"}}
                return respfail
        else:
            respfail={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request or Requested Items All Are Inactive"}}
            return respfail
    else:
        respfail={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "Error Encountered"}}
        return respfail
    
def company_update(request_data):
    if request_data['request_data']['id']:
        data=request_data['request_data']
        id_dict={}
        id_dict['id']=data['id']
        id_dict['status']=1
        condition_data = convert_data_types_for_conditions('ta_application', 'company', id_dict)
        del data['id']
        to_be_updated_data=convert_data_types_for_update('ta_application', 'company', data)
        sta = dbilayer.update_table("company", to_be_updated_data, condition_data)
        print(sta)
        if((sta is not None) and (sta == "Success")):
            respsucc = {"response_id": request_data['request_id'], "response_for":"Update","response_set_to":request_data['request_src'],"response_data": {"message":"Updated Successfully","status_code":200}}
            return  respsucc
        elif(sta == 'Failed'):
            respfail = {"response_id": request_data['request_id'], "response_for":"Update","response_set_to":request_data['request_src'],"response_data": {"message":"Update request Failed"}}
            return  respfail
    else:
        respfail = {"response_id": request_data['request_id'], "response_for":"Update","response_set_to":request_data['request_src'],"response_data": {"message":"Error in Request"}}
        return  respfail 
    
def company_delete(request_data):
    if request_data['request_data']['id']:
        data = request_data['request_data']
        id_dict={}
        id_dict['id']=data['id']
        to_be_updated_data=convert_data_types_for_update('ta_application', 'company', {"status":9})
        condition_data = convert_data_types_for_conditions('ta_application', 'company', id_dict)
        sta = dbilayer.update_table("company", to_be_updated_data, condition_data)
        print(sta)
        if((sta is not None) and (sta == "Success")):
            respsucc = {"response_id": request_data['request_id'], "response_for":"Delete","response_set_to":request_data['request_src'],"response_data": {"message":"Deleted Successfully","status_code":200}}
            return  respsucc
        elif(sta == 'Failed'):
            respfail = {"response_id": request_data['request_id'], "response_for":"Delete","response_set_to":request_data['request_src'],"response_data": {"message":"Delete request Failed"}}
            return  respfail
    
    else:
        respfail = {"response_id": request_data['request_id'], "response_for":"Delete","response_set_to":request_data['request_src'],"response_data": {"message":"Error in Request"}}
        return  respfail
    
    
    
    
# BUSINESS UNIT
def businessUnit_create(request_data):
    if isinstance(request_data, dict):
        data_to_insert = request_data['request_data']
        final_data_to_insert=convert_data_types_for_insert('ta_application', 'business_unit', data_to_insert)
        print(final_data_to_insert,"==========FINAL DATA to insert")
        keys = list(data_to_insert.keys())
        columns_output = ",".join([f"`{key}`" for key in keys])
        sta=dbilayer.insert_into_table('business_unit', columns_output, final_data_to_insert)
        if(sta is not None):
            if ('message' in sta):
                if (sta['message'] == 'Success'):
                    respsucc={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Created Successfully","status_code":200, "last_id": sta["last_insert_id"]}}
                    return respsucc
                else:
                    respfail={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request"}}
                    return respfail
            else:
                respfail={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request"}}
                return respfail
        else:
            respfail={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request"}}
            return respfail
    else:
        respfail={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Error Encountered"}}
        return respfail
    
def businessUnit_readAll(request_data):
    if isinstance(request_data, dict):
        data=request_data['request_data']
        condition_dict = {}
        condition_dict["status"] = 1
        condition_data = convert_data_types_for_conditions('ta_application', 'business_unit', condition_dict)
        sta=dbilayer.read_with_condition('business_unit', '*', condition_data)
        print("sta in bll engine---->", sta)
        if ((sta is not None) and (isinstance(sta, list))):
            if (len(sta) > 0):
                respsucc={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "Success", "status_code":200,"data":sta}}
                return respsucc
            else:
                respfail={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "No Results Found"}}
                return respfail
        else:
            respfail={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request or Requested Items All Are Inactive"}}
            return respfail
    else:
        respfail={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "Error Encountered"}}
        return respfail
    
def businessUnit_update(request_data):
    if request_data['request_data']['id']:
        data=request_data['request_data']
        id_dict={}
        id_dict['id']=data['id']
        id_dict['status']=1
        condition_data = convert_data_types_for_conditions('ta_application', 'business_unit', id_dict)
        del data['id']
        to_be_updated_data=convert_data_types_for_update('ta_application', 'business_unit', data)
        sta = dbilayer.update_table("business_unit", to_be_updated_data, condition_data)
        print(sta)
        if((sta is not None) and (sta == "Success")):
            respsucc = {"response_id": request_data['request_id'], "response_for":"Update","response_set_to":request_data['request_src'],"response_data": {"message":"Updated Successfully","status_code":200}}
            return  respsucc
        elif(sta == 'Failed'):
            respfail = {"response_id": request_data['request_id'], "response_for":"Update","response_set_to":request_data['request_src'],"response_data": {"message":"Update request Failed"}}
            return  respfail
    else:
        respfail = {"response_id": request_data['request_id'], "response_for":"Update","response_set_to":request_data['request_src'],"response_data": {"message":"Error in Request"}}
        return  respfail 
    
def businessUnit_delete(request_data):
    if request_data['request_data']['id']:
        data = request_data['request_data']
        id_dict={}
        id_dict['id']=data['id']
        to_be_updated_data=convert_data_types_for_update('ta_application', 'business_unit', {"status":9})
        condition_data = convert_data_types_for_conditions('ta_application', 'business_unit', id_dict)
        sta = dbilayer.update_table("business_unit", to_be_updated_data, condition_data)
        print(sta)
        if((sta is not None) and (sta == "Success")):
            respsucc = {"response_id": request_data['request_id'], "response_for":"Delete","response_set_to":request_data['request_src'],"response_data": {"message":"Deleted Successfully","status_code":200}}
            return  respsucc
        elif(sta == 'Failed'):
            respfail = {"response_id": request_data['request_id'], "response_for":"Delete","response_set_to":request_data['request_src'],"response_data": {"message":"Delete request Failed"}}
            return  respfail
    
    else:
        respfail = {"response_id": request_data['request_id'], "response_for":"Delete","response_set_to":request_data['request_src'],"response_data": {"message":"Error in Request"}}
        return  respfail
    
    
    
# DEPARTMENT
def department_create(request_data):
    if isinstance(request_data, dict):
        data_to_insert = request_data['request_data']
        final_data_to_insert=convert_data_types_for_insert('ta_application', 'department', data_to_insert)
        print(final_data_to_insert,"==========FINAL DATA to insert")
        keys = list(data_to_insert.keys())
        columns_output = ",".join([f"`{key}`" for key in keys])
        sta=dbilayer.insert_into_table('department', columns_output, final_data_to_insert)
        if(sta is not None):
            if ('message' in sta):
                if (sta['message'] == 'Success'):
                    respsucc={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Created Successfully","status_code":200, "last_id": sta["last_insert_id"]}}
                    return respsucc
                else:
                    respfail={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request"}}
                    return respfail
            else:
                respfail={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request"}}
                return respfail
        else:
            respfail={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request"}}
            return respfail
    else:
        respfail={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Error Encountered"}}
        return respfail
    
def department_readAll(request_data):
    if isinstance(request_data, dict):
        data=request_data['request_data']
        condition_dict = {}
        condition_dict["status"] = 1
        condition_data = convert_data_types_for_conditions('ta_application', 'department', condition_dict)
        sta=dbilayer.read_with_condition('department', '*', condition_data)
        print("sta in bll engine---->", sta)
        if ((sta is not None) and (isinstance(sta, list))):
            if (len(sta) > 0):
                respsucc={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "Success", "status_code":200,"data":sta}}
                return respsucc
            else:
                respfail={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "No Results Found"}}
                return respfail
        else:
            respfail={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request or Requested Items All Are Inactive"}}
            return respfail
    else:
        respfail={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "Error Encountered"}}
        return respfail
    
def department_update(request_data):
    if request_data['request_data']['id']:
        data=request_data['request_data']
        id_dict={}
        id_dict['id']=data['id']
        id_dict['status']=1
        condition_data = convert_data_types_for_conditions('ta_application', 'department', id_dict)
        del data['id']
        to_be_updated_data=convert_data_types_for_update('ta_application', 'department', data)
        sta = dbilayer.update_table("department", to_be_updated_data, condition_data)
        print(sta)
        if((sta is not None) and (sta == "Success")):
            respsucc = {"response_id": request_data['request_id'], "response_for":"Update","response_set_to":request_data['request_src'],"response_data": {"message":"Updated Successfully","status_code":200}}
            return  respsucc
        elif(sta == 'Failed'):
            respfail = {"response_id": request_data['request_id'], "response_for":"Update","response_set_to":request_data['request_src'],"response_data": {"message":"Update request Failed"}}
            return  respfail
    else:
        respfail = {"response_id": request_data['request_id'], "response_for":"Update","response_set_to":request_data['request_src'],"response_data": {"message":"Error in Request"}}
        return  respfail 
    
def department_delete(request_data):
    if request_data['request_data']['id']:
        data = request_data['request_data']
        id_dict={}
        id_dict['id']=data['id']
        to_be_updated_data=convert_data_types_for_update('ta_application', 'department', {"status":9})
        condition_data = convert_data_types_for_conditions('ta_application', 'department', id_dict)
        sta = dbilayer.update_table("department", to_be_updated_data, condition_data)
        print(sta)
        if((sta is not None) and (sta == "Success")):
            respsucc = {"response_id": request_data['request_id'], "response_for":"Delete","response_set_to":request_data['request_src'],"response_data": {"message":"Deleted Successfully","status_code":200}}
            return  respsucc
        elif(sta == 'Failed'):
            respfail = {"response_id": request_data['request_id'], "response_for":"Delete","response_set_to":request_data['request_src'],"response_data": {"message":"Delete request Failed"}}
            return  respfail
    
    else:
        respfail = {"response_id": request_data['request_id'], "response_for":"Delete","response_set_to":request_data['request_src'],"response_data": {"message":"Error in Request"}}
        return  respfail    
    

# PRACTICE
def practice_create(request_data):
    if isinstance(request_data, dict):
        data_to_insert = request_data['request_data']
        final_data_to_insert=convert_data_types_for_insert('ta_application', 'practice', data_to_insert)
        print(final_data_to_insert,"==========FINAL DATA to insert")
        keys = list(data_to_insert.keys())
        columns_output = ",".join([f"`{key}`" for key in keys])
        sta=dbilayer.insert_into_table('practice', columns_output, final_data_to_insert)
        if(sta is not None):
            if ('message' in sta):
                if (sta['message'] == 'Success'):
                    respsucc={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Created Successfully","status_code":200, "last_id": sta["last_insert_id"]}}
                    return respsucc
                else:
                    respfail={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request"}}
                    return respfail
            else:
                respfail={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request"}}
                return respfail
        else:
            respfail={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request"}}
            return respfail
    else:
        respfail={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Error Encountered"}}
        return respfail
    
def practice_readAll(request_data):
    if isinstance(request_data, dict):
        data=request_data['request_data']
        condition_dict = {}
        condition_dict["status"] = 1
        condition_data = convert_data_types_for_conditions('ta_application', 'practice', condition_dict)
        sta=dbilayer.read_with_condition('practice', '*', condition_data)
        print("sta in bll engine---->", sta)
        if ((sta is not None) and (isinstance(sta, list))):
            if (len(sta) > 0):
                respsucc={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "Success", "status_code":200,"data":sta}}
                return respsucc
            else:
                respfail={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "No Results Found"}}
                return respfail
        else:
            respfail={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request or Requested Items All Are Inactive"}}
            return respfail
    else:
        respfail={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "Error Encountered"}}
        return respfail
    
def practice_update(request_data):
    if request_data['request_data']['id']:
        data=request_data['request_data']
        id_dict={}
        id_dict['id']=data['id']
        id_dict['status']=1
        condition_data = convert_data_types_for_conditions('ta_application', 'practice', id_dict)
        del data['id']
        to_be_updated_data=convert_data_types_for_update('ta_application', 'practice', data)
        sta = dbilayer.update_table("practice", to_be_updated_data, condition_data)
        print(sta)
        if((sta is not None) and (sta == "Success")):
            respsucc = {"response_id": request_data['request_id'], "response_for":"Update","response_set_to":request_data['request_src'],"response_data": {"message":"Updated Successfully","status_code":200}}
            return  respsucc
        elif(sta == 'Failed'):
            respfail = {"response_id": request_data['request_id'], "response_for":"Update","response_set_to":request_data['request_src'],"response_data": {"message":"Update request Failed"}}
            return  respfail
    else:
        respfail = {"response_id": request_data['request_id'], "response_for":"Update","response_set_to":request_data['request_src'],"response_data": {"message":"Error in Request"}}
        return  respfail 
    
def practice_delete(request_data):
    if request_data['request_data']['id']:
        data = request_data['request_data']
        id_dict={}
        id_dict['id']=data['id']
        to_be_updated_data=convert_data_types_for_update('ta_application', 'practice', {"status":9})
        condition_data = convert_data_types_for_conditions('ta_application', 'practice', id_dict)
        sta = dbilayer.update_table("practice", to_be_updated_data, condition_data)
        print(sta)
        if((sta is not None) and (sta == "Success")):
            respsucc = {"response_id": request_data['request_id'], "response_for":"Delete","response_set_to":request_data['request_src'],"response_data": {"message":"Deleted Successfully","status_code":200}}
            return  respsucc
        elif(sta == 'Failed'):
            respfail = {"response_id": request_data['request_id'], "response_for":"Delete","response_set_to":request_data['request_src'],"response_data": {"message":"Delete request Failed"}}
            return  respfail
    
    else:
        respfail = {"response_id": request_data['request_id'], "response_for":"Delete","response_set_to":request_data['request_src'],"response_data": {"message":"Error in Request"}}
        return  respfail    
    

# DESIGNATION
def designation_create(request_data):
    if isinstance(request_data, dict):
        data_to_insert = request_data['request_data']
        final_data_to_insert=convert_data_types_for_insert('ta_application', 'designation', data_to_insert)
        print(final_data_to_insert,"==========FINAL DATA to insert")
        keys = list(data_to_insert.keys())
        columns_output = ",".join([f"`{key}`" for key in keys])
        sta=dbilayer.insert_into_table('designation', columns_output, final_data_to_insert)
        if(sta is not None):
            if ('message' in sta):
                if (sta['message'] == 'Success'):
                    respsucc={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Created Successfully","status_code":200, "last_id": sta["last_insert_id"]}}
                    return respsucc
                else:
                    respfail={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request"}}
                    return respfail
            else:
                respfail={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request"}}
                return respfail
        else:
            respfail={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request"}}
            return respfail
    else:
        respfail={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Error Encountered"}}
        return respfail
    
def designation_readAll(request_data):
    if isinstance(request_data, dict):
        data=request_data['request_data']
        condition_dict = {}
        condition_dict["status"] = 1
        condition_data = convert_data_types_for_conditions('ta_application', 'designation', condition_dict)
        sta=dbilayer.read_with_condition('designation', '*', condition_data)
        print("sta in bll engine---->", sta)
        if ((sta is not None) and (isinstance(sta, list))):
            if (len(sta) > 0):
                respsucc={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "Success", "status_code":200,"data":sta}}
                return respsucc
            else:
                respfail={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "No Results Found"}}
                return respfail
        else:
            respfail={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request or Requested Items All Are Inactive"}}
            return respfail
    else:
        respfail={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "Error Encountered"}}
        return respfail
    
def designation_update(request_data):
    if request_data['request_data']['id']:
        data=request_data['request_data']
        id_dict={}
        id_dict['id']=data['id']
        id_dict['status']=1
        condition_data = convert_data_types_for_conditions('ta_application', 'designation', id_dict)
        del data['id']
        to_be_updated_data=convert_data_types_for_update('ta_application', 'designation', data)
        sta = dbilayer.update_table("designation", to_be_updated_data, condition_data)
        print(sta)
        if((sta is not None) and (sta == "Success")):
            respsucc = {"response_id": request_data['request_id'], "response_for":"Update","response_set_to":request_data['request_src'],"response_data": {"message":"Updated Successfully","status_code":200}}
            return  respsucc
        elif(sta == 'Failed'):
            respfail = {"response_id": request_data['request_id'], "response_for":"Update","response_set_to":request_data['request_src'],"response_data": {"message":"Update request Failed"}}
            return  respfail
    else:
        respfail = {"response_id": request_data['request_id'], "response_for":"Update","response_set_to":request_data['request_src'],"response_data": {"message":"Error in Request"}}
        return  respfail 
    
def designation_delete(request_data):
    if request_data['request_data']['id']:
        data = request_data['request_data']
        id_dict={}
        id_dict['id']=data['id']
        to_be_updated_data=convert_data_types_for_update('ta_application', 'designation', {"status":9})
        condition_data = convert_data_types_for_conditions('ta_application', 'designation', id_dict)
        sta = dbilayer.update_table("designation", to_be_updated_data, condition_data)
        print(sta)
        if((sta is not None) and (sta == "Success")):
            respsucc = {"response_id": request_data['request_id'], "response_for":"Delete","response_set_to":request_data['request_src'],"response_data": {"message":"Deleted Successfully","status_code":200}}
            return  respsucc
        elif(sta == 'Failed'):
            respfail = {"response_id": request_data['request_id'], "response_for":"Delete","response_set_to":request_data['request_src'],"response_data": {"message":"Delete request Failed"}}
            return  respfail
    
    else:
        respfail = {"response_id": request_data['request_id'], "response_for":"Delete","response_set_to":request_data['request_src'],"response_data": {"message":"Error in Request"}}
        return  respfail    
    
    
# GRADE
def grade_create(request_data):
    if isinstance(request_data, dict):
        data_to_insert = request_data['request_data']
        final_data_to_insert=convert_data_types_for_insert('ta_application', 'grade', data_to_insert)
        print(final_data_to_insert,"==========FINAL DATA to insert")
        keys = list(data_to_insert.keys())
        columns_output = ",".join([f"`{key}`" for key in keys])
        sta=dbilayer.insert_into_table('grade', columns_output, final_data_to_insert)
        if(sta is not None):
            if ('message' in sta):
                if (sta['message'] == 'Success'):
                    respsucc={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Created Successfully","status_code":200, "last_id": sta["last_insert_id"]}}
                    return respsucc
                else:
                    respfail={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request"}}
                    return respfail
            else:
                respfail={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request"}}
                return respfail
        else:
            respfail={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request"}}
            return respfail
    else:
        respfail={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Error Encountered"}}
        return respfail
    
def grade_readAll(request_data):
    if isinstance(request_data, dict):
        data=request_data['request_data']
        condition_dict = {}
        condition_dict["status"] = 1
        condition_data = convert_data_types_for_conditions('ta_application', 'grade', condition_dict)
        sta=dbilayer.read_with_condition('grade', '*', condition_data)
        print("sta in bll engine---->", sta)
        if ((sta is not None) and (isinstance(sta, list))):
            if (len(sta) > 0):
                respsucc={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "Success", "status_code":200,"data":sta}}
                return respsucc
            else:
                respfail={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "No Results Found"}}
                return respfail
        else:
            respfail={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request or Requested Items All Are Inactive"}}
            return respfail
    else:
        respfail={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "Error Encountered"}}
        return respfail
    
def grade_update(request_data):
    if request_data['request_data']['id']:
        data=request_data['request_data']
        id_dict={}
        id_dict['id']=data['id']
        id_dict['status']=1
        condition_data = convert_data_types_for_conditions('ta_application', 'grade', id_dict)
        del data['id']
        to_be_updated_data=convert_data_types_for_update('ta_application', 'grade', data)
        sta = dbilayer.update_table("grade", to_be_updated_data, condition_data)
        print(sta)
        if((sta is not None) and (sta == "Success")):
            respsucc = {"response_id": request_data['request_id'], "response_for":"Update","response_set_to":request_data['request_src'],"response_data": {"message":"Updated Successfully","status_code":200}}
            return  respsucc
        elif(sta == 'Failed'):
            respfail = {"response_id": request_data['request_id'], "response_for":"Update","response_set_to":request_data['request_src'],"response_data": {"message":"Update request Failed"}}
            return  respfail
    else:
        respfail = {"response_id": request_data['request_id'], "response_for":"Update","response_set_to":request_data['request_src'],"response_data": {"message":"Error in Request"}}
        return  respfail 
    
def grade_delete(request_data):
    if request_data['request_data']['id']:
        data = request_data['request_data']
        id_dict={}
        id_dict['id']=data['id']
        to_be_updated_data=convert_data_types_for_update('ta_application', 'grade', {"status":9})
        condition_data = convert_data_types_for_conditions('ta_application', 'grade', id_dict)
        sta = dbilayer.update_table("grade", to_be_updated_data, condition_data)
        print(sta)
        if((sta is not None) and (sta == "Success")):
            respsucc = {"response_id": request_data['request_id'], "response_for":"Delete","response_set_to":request_data['request_src'],"response_data": {"message":"Deleted Successfully","status_code":200}}
            return  respsucc
        elif(sta == 'Failed'):
            respfail = {"response_id": request_data['request_id'], "response_for":"Delete","response_set_to":request_data['request_src'],"response_data": {"message":"Delete request Failed"}}
            return  respfail
    
    else:
        respfail = {"response_id": request_data['request_id'], "response_for":"Delete","response_set_to":request_data['request_src'],"response_data": {"message":"Error in Request"}}
        return  respfail    
 
    
# REGION
def region_create(request_data):
    if isinstance(request_data, dict):
        data_to_insert = request_data['request_data']
        final_data_to_insert=convert_data_types_for_insert('ta_application', 'region', data_to_insert)
        print(final_data_to_insert,"==========FINAL DATA to insert")
        keys = list(data_to_insert.keys())
        columns_output = ",".join([f"`{key}`" for key in keys])
        sta=dbilayer.insert_into_table('region', columns_output, final_data_to_insert)
        if(sta is not None):
            if ('message' in sta):
                if (sta['message'] == 'Success'):
                    respsucc={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Created Successfully","status_code":200, "last_id": sta["last_insert_id"]}}
                    return respsucc
                else:
                    respfail={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request"}}
                    return respfail
            else:
                respfail={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request"}}
                return respfail
        else:
            respfail={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request"}}
            return respfail
    else:
        respfail={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Error Encountered"}}
        return respfail
    
def region_readAll(request_data):
    if isinstance(request_data, dict):
        data=request_data['request_data']
        condition_dict = {}
        condition_dict["status"] = 1
        condition_data = convert_data_types_for_conditions('ta_application', 'region', condition_dict)
        sta=dbilayer.read_with_condition('region', '*', condition_data)
        print("sta in bll engine---->", sta)
        if ((sta is not None) and (isinstance(sta, list))):
            if (len(sta) > 0):
                respsucc={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "Success", "status_code":200,"data":sta}}
                return respsucc
            else:
                respfail={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "No Results Found"}}
                return respfail
        else:
            respfail={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request or Requested Items All Are Inactive"}}
            return respfail
    else:
        respfail={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "Error Encountered"}}
        return respfail
    
def region_update(request_data):
    if request_data['request_data']['id']:
        data=request_data['request_data']
        id_dict={}
        id_dict['id']=data['id']
        id_dict['status']=1
        condition_data = convert_data_types_for_conditions('ta_application', 'region', id_dict)
        del data['id']
        to_be_updated_data=convert_data_types_for_update('ta_application', 'region', data)
        sta = dbilayer.update_table("region", to_be_updated_data, condition_data)
        print(sta)
        if((sta is not None) and (sta == "Success")):
            respsucc = {"response_id": request_data['request_id'], "response_for":"Update","response_set_to":request_data['request_src'],"response_data": {"message":"Updated Successfully","status_code":200}}
            return  respsucc
        elif(sta == 'Failed'):
            respfail = {"response_id": request_data['request_id'], "response_for":"Update","response_set_to":request_data['request_src'],"response_data": {"message":"Update request Failed"}}
            return  respfail
    else:
        respfail = {"response_id": request_data['request_id'], "response_for":"Update","response_set_to":request_data['request_src'],"response_data": {"message":"Error in Request"}}
        return  respfail 
    
def region_delete(request_data):
    if request_data['request_data']['id']:
        data = request_data['request_data']
        id_dict={}
        id_dict['id']=data['id']
        to_be_updated_data=convert_data_types_for_update('ta_application', 'region', {"status":9})
        condition_data = convert_data_types_for_conditions('ta_application', 'region', id_dict)
        sta = dbilayer.update_table("region", to_be_updated_data, condition_data)
        print(sta)
        if((sta is not None) and (sta == "Success")):
            respsucc = {"response_id": request_data['request_id'], "response_for":"Delete","response_set_to":request_data['request_src'],"response_data": {"message":"Deleted Successfully","status_code":200}}
            return  respsucc
        elif(sta == 'Failed'):
            respfail = {"response_id": request_data['request_id'], "response_for":"Delete","response_set_to":request_data['request_src'],"response_data": {"message":"Delete request Failed"}}
            return  respfail
    
    else:
        respfail = {"response_id": request_data['request_id'], "response_for":"Delete","response_set_to":request_data['request_src'],"response_data": {"message":"Error in Request"}}
        return  respfail    
    
# BRANCH
def branch_create(request_data):
    if isinstance(request_data, dict):
        data_to_insert = request_data['request_data']
        final_data_to_insert=convert_data_types_for_insert('ta_application', 'branch', data_to_insert)
        print(final_data_to_insert,"==========FINAL DATA to insert")
        keys = list(data_to_insert.keys())
        columns_output = ",".join([f"`{key}`" for key in keys])
        sta=dbilayer.insert_into_table('branch', columns_output, final_data_to_insert)
        if(sta is not None):
            if ('message' in sta):
                if (sta['message'] == 'Success'):
                    respsucc={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Created Successfully","status_code":200, "last_id": sta["last_insert_id"]}}
                    return respsucc
                else:
                    respfail={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request"}}
                    return respfail
            else:
                respfail={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request"}}
                return respfail
        else:
            respfail={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request"}}
            return respfail
    else:
        respfail={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Error Encountered"}}
        return respfail
    
def branch_readAll(request_data):
    if isinstance(request_data, dict):
        data=request_data['request_data']
        condition_dict = {}
        condition_dict["status"] = 1
        condition_data = convert_data_types_for_conditions('ta_application', 'branch', condition_dict)
        sta=dbilayer.read_with_condition('branch', '*', condition_data)
        print("sta in bll engine---->", sta)
        if ((sta is not None) and (isinstance(sta, list))):
            if (len(sta) > 0):
                respsucc={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "Success", "status_code":200,"data":sta}}
                return respsucc
            else:
                respfail={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "No Results Found"}}
                return respfail
        else:
            respfail={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request or Requested Items All Are Inactive"}}
            return respfail
    else:
        respfail={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "Error Encountered"}}
        return respfail
    
def branch_update(request_data):
    if request_data['request_data']['id']:
        data=request_data['request_data']
        id_dict={}
        id_dict['id']=data['id']
        id_dict['status']=1
        condition_data = convert_data_types_for_conditions('ta_application', 'branch', id_dict)
        del data['id']
        to_be_updated_data=convert_data_types_for_update('ta_application', 'branch', data)
        sta = dbilayer.update_table("branch", to_be_updated_data, condition_data)
        print(sta)
        if((sta is not None) and (sta == "Success")):
            respsucc = {"response_id": request_data['request_id'], "response_for":"Update","response_set_to":request_data['request_src'],"response_data": {"message":"Updated Successfully","status_code":200}}
            return  respsucc
        elif(sta == 'Failed'):
            respfail = {"response_id": request_data['request_id'], "response_for":"Update","response_set_to":request_data['request_src'],"response_data": {"message":"Update request Failed"}}
            return  respfail
    else:
        respfail = {"response_id": request_data['request_id'], "response_for":"Update","response_set_to":request_data['request_src'],"response_data": {"message":"Error in Request"}}
        return  respfail 
    
def branch_delete(request_data):
    if request_data['request_data']['id']:
        data = request_data['request_data']
        id_dict={}
        id_dict['id']=data['id']
        to_be_updated_data=convert_data_types_for_update('ta_application', 'branch', {"status":9})
        condition_data = convert_data_types_for_conditions('ta_application', 'branch', id_dict)
        sta = dbilayer.update_table("branch", to_be_updated_data, condition_data)
        print(sta)
        if((sta is not None) and (sta == "Success")):
            respsucc = {"response_id": request_data['request_id'], "response_for":"Delete","response_set_to":request_data['request_src'],"response_data": {"message":"Deleted Successfully","status_code":200}}
            return  respsucc
        elif(sta == 'Failed'):
            respfail = {"response_id": request_data['request_id'], "response_for":"Delete","response_set_to":request_data['request_src'],"response_data": {"message":"Delete request Failed"}}
            return  respfail
    
    else:
        respfail = {"response_id": request_data['request_id'], "response_for":"Delete","response_set_to":request_data['request_src'],"response_data": {"message":"Error in Request"}}
        return  respfail    


# SUB BRANCH
def subBranch_create(request_data):
    if isinstance(request_data, dict):
        data_to_insert = request_data['request_data']
        final_data_to_insert=convert_data_types_for_insert('ta_application', 'sub_branch', data_to_insert)
        print(final_data_to_insert,"==========FINAL DATA to insert")
        keys = list(data_to_insert.keys())
        columns_output = ",".join([f"`{key}`" for key in keys])
        sta=dbilayer.insert_into_table('sub_branch', columns_output, final_data_to_insert)
        if(sta is not None):
            if ('message' in sta):
                if (sta['message'] == 'Success'):
                    respsucc={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Created Successfully","status_code":200, "last_id": sta["last_insert_id"]}}
                    return respsucc
                else:
                    respfail={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request"}}
                    return respfail
            else:
                respfail={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request"}}
                return respfail
        else:
            respfail={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request"}}
            return respfail
    else:
        respfail={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Error Encountered"}}
        return respfail
    
def subBranch_readAll(request_data):
    if isinstance(request_data, dict):
        data=request_data['request_data']
        condition_dict = {}
        condition_dict["status"] = 1
        condition_data = convert_data_types_for_conditions('ta_application', 'sub_branch', condition_dict)
        sta=dbilayer.read_with_condition('sub_branch', '*', condition_data)
        print("sta in bll engine---->", sta)
        if ((sta is not None) and (isinstance(sta, list))):
            if (len(sta) > 0):
                respsucc={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "Success", "status_code":200,"data":sta}}
                return respsucc
            else:
                respfail={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "No Results Found"}}
                return respfail
        else:
            respfail={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request or Requested Items All Are Inactive"}}
            return respfail
    else:
        respfail={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "Error Encountered"}}
        return respfail
    
def subBranch_update(request_data):
    if request_data['request_data']['id']:
        data=request_data['request_data']
        id_dict={}
        id_dict['id']=data['id']
        id_dict['status']=1
        condition_data = convert_data_types_for_conditions('ta_application', 'sub_branch', id_dict)
        del data['id']
        to_be_updated_data=convert_data_types_for_update('ta_application', 'sub_branch', data)
        sta = dbilayer.update_table("sub_branch", to_be_updated_data, condition_data)
        print(sta)
        if((sta is not None) and (sta == "Success")):
            respsucc = {"response_id": request_data['request_id'], "response_for":"Update","response_set_to":request_data['request_src'],"response_data": {"message":"Updated Successfully","status_code":200}}
            return  respsucc
        elif(sta == 'Failed'):
            respfail = {"response_id": request_data['request_id'], "response_for":"Update","response_set_to":request_data['request_src'],"response_data": {"message":"Update request Failed"}}
            return  respfail
    else:
        respfail = {"response_id": request_data['request_id'], "response_for":"Update","response_set_to":request_data['request_src'],"response_data": {"message":"Error in Request"}}
        return  respfail 
    
def subBranch_delete(request_data):
    if request_data['request_data']['id']:
        data = request_data['request_data']
        id_dict={}
        id_dict['id']=data['id']
        to_be_updated_data=convert_data_types_for_update('ta_application', 'sub_branch', {"status":9})
        condition_data = convert_data_types_for_conditions('ta_application', 'sub_branch', id_dict)
        sta = dbilayer.update_table("sub_branch", to_be_updated_data, condition_data)
        print(sta)
        if((sta is not None) and (sta == "Success")):
            respsucc = {"response_id": request_data['request_id'], "response_for":"Delete","response_set_to":request_data['request_src'],"response_data": {"message":"Deleted Successfully","status_code":200}}
            return  respsucc
        elif(sta == 'Failed'):
            respfail = {"response_id": request_data['request_id'], "response_for":"Delete","response_set_to":request_data['request_src'],"response_data": {"message":"Delete request Failed"}}
            return  respfail
    
    else:
        respfail = {"response_id": request_data['request_id'], "response_for":"Delete","response_set_to":request_data['request_src'],"response_data": {"message":"Error in Request"}}
        return  respfail    


# QUALIFICATION
def qualification_create(request_data):
    if isinstance(request_data, dict):
        data_to_insert = request_data['request_data']
        final_data_to_insert=convert_data_types_for_insert('ta_application', 'qualification', data_to_insert)
        print(final_data_to_insert,"==========FINAL DATA to insert")
        keys = list(data_to_insert.keys())
        columns_output = ",".join([f"`{key}`" for key in keys])
        sta=dbilayer.insert_into_table('qualification', columns_output, final_data_to_insert)
        if(sta is not None):
            if ('message' in sta):
                if (sta['message'] == 'Success'):
                    respsucc={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Created Successfully","status_code":200, "last_id": sta["last_insert_id"]}}
                    return respsucc
                else:
                    respfail={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request"}}
                    return respfail
            else:
                respfail={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request"}}
                return respfail
        else:
            respfail={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request"}}
            return respfail
    else:
        respfail={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Error Encountered"}}
        return respfail
    
def qualification_readAll(request_data):
    if isinstance(request_data, dict):
        data=request_data['request_data']
        condition_dict = {}
        condition_dict["status"] = 1
        condition_data = convert_data_types_for_conditions('ta_application', 'qualification', condition_dict)
        sta=dbilayer.read_with_condition('qualification', '*', condition_data)
        print("sta in bll engine---->", sta)
        if ((sta is not None) and (isinstance(sta, list))):
            if (len(sta) > 0):
                respsucc={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "Success", "status_code":200,"data":sta}}
                return respsucc
            else:
                respfail={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "No Results Found"}}
                return respfail
        else:
            respfail={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request or Requested Items All Are Inactive"}}
            return respfail
    else:
        respfail={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "Error Encountered"}}
        return respfail
    
def qualification_update(request_data):
    if request_data['request_data']['id']:
        data=request_data['request_data']
        id_dict={}
        id_dict['id']=data['id']
        id_dict['status']=1
        condition_data = convert_data_types_for_conditions('ta_application', 'qualification', id_dict)
        del data['id']
        to_be_updated_data=convert_data_types_for_update('ta_application', 'qualification', data)
        sta = dbilayer.update_table("qualification", to_be_updated_data, condition_data)
        print(sta)
        if((sta is not None) and (sta == "Success")):
            respsucc = {"response_id": request_data['request_id'], "response_for":"Update","response_set_to":request_data['request_src'],"response_data": {"message":"Updated Successfully","status_code":200}}
            return  respsucc
        elif(sta == 'Failed'):
            respfail = {"response_id": request_data['request_id'], "response_for":"Update","response_set_to":request_data['request_src'],"response_data": {"message":"Update request Failed"}}
            return  respfail
    else:
        respfail = {"response_id": request_data['request_id'], "response_for":"Update","response_set_to":request_data['request_src'],"response_data": {"message":"Error in Request"}}
        return  respfail 
    
def qualification_delete(request_data):
    if request_data['request_data']['id']:
        data = request_data['request_data']
        id_dict={}
        id_dict['id']=data['id']
        to_be_updated_data=convert_data_types_for_update('ta_application', 'qualification', {"status":9})
        condition_data = convert_data_types_for_conditions('ta_application', 'qualification', id_dict)
        sta = dbilayer.update_table("qualification", to_be_updated_data, condition_data)
        print(sta)
        if((sta is not None) and (sta == "Success")):
            respsucc = {"response_id": request_data['request_id'], "response_for":"Delete","response_set_to":request_data['request_src'],"response_data": {"message":"Deleted Successfully","status_code":200}}
            return  respsucc
        elif(sta == 'Failed'):
            respfail = {"response_id": request_data['request_id'], "response_for":"Delete","response_set_to":request_data['request_src'],"response_data": {"message":"Delete request Failed"}}
            return  respfail
    
    else:
        respfail = {"response_id": request_data['request_id'], "response_for":"Delete","response_set_to":request_data['request_src'],"response_data": {"message":"Error in Request"}}
        return  respfail    

# CURRENCY
def currency_create(request_data):
    if isinstance(request_data, dict):
        data_to_insert = request_data['request_data']
        final_data_to_insert=convert_data_types_for_insert('ta_application', 'currency', data_to_insert)
        print(final_data_to_insert,"==========FINAL DATA to insert")
        keys = list(data_to_insert.keys())
        columns_output = ",".join([f"`{key}`" for key in keys])
        sta=dbilayer.insert_into_table('currency', columns_output, final_data_to_insert)
        if(sta is not None):
            if ('message' in sta):
                if (sta['message'] == 'Success'):
                    respsucc={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Created Successfully","status_code":200, "last_id": sta["last_insert_id"]}}
                    return respsucc
                else:
                    respfail={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request"}}
                    return respfail
            else:
                respfail={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request"}}
                return respfail
        else:
            respfail={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request"}}
            return respfail
    else:
        respfail={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Error Encountered"}}
        return respfail
    
def currency_readAll(request_data):
    if isinstance(request_data, dict):
        data=request_data['request_data']
        condition_dict = {}
        condition_dict["status"] = 1
        condition_data = convert_data_types_for_conditions('ta_application', 'currency', condition_dict)
        sta=dbilayer.read_with_condition('currency', '*', condition_data)
        print("sta in bll engine---->", sta)
        if ((sta is not None) and (isinstance(sta, list))):
            if (len(sta) > 0):
                respsucc={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "Success", "status_code":200,"data":sta}}
                return respsucc
            else:
                respfail={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "No Results Found"}}
                return respfail
        else:
            respfail={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request or Requested Items All Are Inactive"}}
            return respfail
    else:
        respfail={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "Error Encountered"}}
        return respfail
    
def currency_update(request_data):
    if request_data['request_data']['id']:
        data=request_data['request_data']
        id_dict={}
        id_dict['id']=data['id']
        id_dict['status']=1
        condition_data = convert_data_types_for_conditions('ta_application', 'currency', id_dict)
        del data['id']
        to_be_updated_data=convert_data_types_for_update('ta_application', 'currency', data)
        sta = dbilayer.update_table("currency", to_be_updated_data, condition_data)
        print(sta)
        if((sta is not None) and (sta == "Success")):
            respsucc = {"response_id": request_data['request_id'], "response_for":"Update","response_set_to":request_data['request_src'],"response_data": {"message":"Updated Successfully","status_code":200}}
            return  respsucc
        elif(sta == 'Failed'):
            respfail = {"response_id": request_data['request_id'], "response_for":"Update","response_set_to":request_data['request_src'],"response_data": {"message":"Update request Failed"}}
            return  respfail
    else:
        respfail = {"response_id": request_data['request_id'], "response_for":"Update","response_set_to":request_data['request_src'],"response_data": {"message":"Error in Request"}}
        return  respfail 
    
def currency_delete(request_data):
    if request_data['request_data']['id']:
        data = request_data['request_data']
        id_dict={}
        id_dict['id']=data['id']
        to_be_updated_data=convert_data_types_for_update('ta_application', 'currency', {"status":9})
        condition_data = convert_data_types_for_conditions('ta_application', 'currency', id_dict)
        sta = dbilayer.update_table("currency", to_be_updated_data, condition_data)
        print(sta)
        if((sta is not None) and (sta == "Success")):
            respsucc = {"response_id": request_data['request_id'], "response_for":"Delete","response_set_to":request_data['request_src'],"response_data": {"message":"Deleted Successfully","status_code":200}}
            return  respsucc
        elif(sta == 'Failed'):
            respfail = {"response_id": request_data['request_id'], "response_for":"Delete","response_set_to":request_data['request_src'],"response_data": {"message":"Delete request Failed"}}
            return  respfail
    
    else:
        respfail = {"response_id": request_data['request_id'], "response_for":"Delete","response_set_to":request_data['request_src'],"response_data": {"message":"Error in Request"}}
        return  respfail    


# PREFIX
def prefix_create(request_data):
    if isinstance(request_data, dict):
        data_to_insert = request_data['request_data']
        final_data_to_insert=convert_data_types_for_insert('ta_application', 'prefix', data_to_insert)
        print(final_data_to_insert,"==========FINAL DATA to insert")
        keys = list(data_to_insert.keys())
        columns_output = ",".join([f"`{key}`" for key in keys])
        sta=dbilayer.insert_into_table('prefix', columns_output, final_data_to_insert)
        if(sta is not None):
            if ('message' in sta):
                if (sta['message'] == 'Success'):
                    respsucc={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Created Successfully","status_code":200, "last_id": sta["last_insert_id"]}}
                    return respsucc
                else:
                    respfail={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request"}}
                    return respfail
            else:
                respfail={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request"}}
                return respfail
        else:
            respfail={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request"}}
            return respfail
    else:
        respfail={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Error Encountered"}}
        return respfail
    
def prefix_readAll(request_data):
    if isinstance(request_data, dict):
        data=request_data['request_data']
        condition_dict = {}
        condition_dict["status"] = 1
        condition_data = convert_data_types_for_conditions('ta_application', 'prefix', condition_dict)
        sta=dbilayer.read_with_condition('prefix', '*', condition_data)
        print("sta in bll engine---->", sta)
        if ((sta is not None) and (isinstance(sta, list))):
            if (len(sta) > 0):
                respsucc={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "Success", "status_code":200,"data":sta}}
                return respsucc
            else:
                respfail={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "No Results Found"}}
                return respfail
        else:
            respfail={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request or Requested Items All Are Inactive"}}
            return respfail
    else:
        respfail={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "Error Encountered"}}
        return respfail
    
def prefix_update(request_data):
    if request_data['request_data']['id']:
        data=request_data['request_data']
        id_dict={}
        id_dict['id']=data['id']
        id_dict['status']=1
        condition_data = convert_data_types_for_conditions('ta_application', 'prefix', id_dict)
        del data['id']
        to_be_updated_data=convert_data_types_for_update('ta_application', 'prefix', data)
        sta = dbilayer.update_table("prefix", to_be_updated_data, condition_data)
        print(sta)
        if((sta is not None) and (sta == "Success")):
            respsucc = {"response_id": request_data['request_id'], "response_for":"Update","response_set_to":request_data['request_src'],"response_data": {"message":"Updated Successfully","status_code":200}}
            return  respsucc
        elif(sta == 'Failed'):
            respfail = {"response_id": request_data['request_id'], "response_for":"Update","response_set_to":request_data['request_src'],"response_data": {"message":"Update request Failed"}}
            return  respfail
    else:
        respfail = {"response_id": request_data['request_id'], "response_for":"Update","response_set_to":request_data['request_src'],"response_data": {"message":"Error in Request"}}
        return  respfail 
    
def prefix_delete(request_data):
    if request_data['request_data']['id']:
        data = request_data['request_data']
        id_dict={}
        id_dict['id']=data['id']
        to_be_updated_data=convert_data_types_for_update('ta_application', 'prefix', {"status":9})
        condition_data = convert_data_types_for_conditions('ta_application', 'prefix', id_dict)
        sta = dbilayer.update_table("prefix", to_be_updated_data, condition_data)
        print(sta)
        if((sta is not None) and (sta == "Success")):
            respsucc = {"response_id": request_data['request_id'], "response_for":"Delete","response_set_to":request_data['request_src'],"response_data": {"message":"Deleted Successfully","status_code":200}}
            return  respsucc
        elif(sta == 'Failed'):
            respfail = {"response_id": request_data['request_id'], "response_for":"Delete","response_set_to":request_data['request_src'],"response_data": {"message":"Delete request Failed"}}
            return  respfail
    
    else:
        respfail = {"response_id": request_data['request_id'], "response_for":"Delete","response_set_to":request_data['request_src'],"response_data": {"message":"Error in Request"}}
        return  respfail    


# GENDER
def gender_create(request_data):
    if isinstance(request_data, dict):
        data_to_insert = request_data['request_data']
        final_data_to_insert=convert_data_types_for_insert('ta_application', 'gender', data_to_insert)
        print(final_data_to_insert,"==========FINAL DATA to insert")
        keys = list(data_to_insert.keys())
        columns_output = ",".join([f"`{key}`" for key in keys])
        sta=dbilayer.insert_into_table('gender', columns_output, final_data_to_insert)
        if(sta is not None):
            if ('message' in sta):
                if (sta['message'] == 'Success'):
                    respsucc={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Created Successfully","status_code":200, "last_id": sta["last_insert_id"]}}
                    return respsucc
                else:
                    respfail={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request"}}
                    return respfail
            else:
                respfail={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request"}}
                return respfail
        else:
            respfail={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request"}}
            return respfail
    else:
        respfail={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Error Encountered"}}
        return respfail
    
def gender_readAll(request_data):
    if isinstance(request_data, dict):
        data=request_data['request_data']
        condition_dict = {}
        condition_dict["status"] = 1
        condition_data = convert_data_types_for_conditions('ta_application', 'gender', condition_dict)
        sta=dbilayer.read_with_condition('gender', '*', condition_data)
        print("sta in bll engine---->", sta)
        if ((sta is not None) and (isinstance(sta, list))):
            if (len(sta) > 0):
                respsucc={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "Success", "status_code":200,"data":sta}}
                return respsucc
            else:
                respfail={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "No Results Found"}}
                return respfail
        else:
            respfail={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request or Requested Items All Are Inactive"}}
            return respfail
    else:
        respfail={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "Error Encountered"}}
        return respfail
    
def gender_update(request_data):
    if request_data['request_data']['id']:
        data=request_data['request_data']
        id_dict={}
        id_dict['id']=data['id']
        id_dict['status']=1
        condition_data = convert_data_types_for_conditions('ta_application', 'gender', id_dict)
        del data['id']
        to_be_updated_data=convert_data_types_for_update('ta_application', 'gender', data)
        sta = dbilayer.update_table("gender", to_be_updated_data, condition_data)
        print(sta)
        if((sta is not None) and (sta == "Success")):
            respsucc = {"response_id": request_data['request_id'], "response_for":"Update","response_set_to":request_data['request_src'],"response_data": {"message":"Updated Successfully","status_code":200}}
            return  respsucc
        elif(sta == 'Failed'):
            respfail = {"response_id": request_data['request_id'], "response_for":"Update","response_set_to":request_data['request_src'],"response_data": {"message":"Update request Failed"}}
            return  respfail
    else:
        respfail = {"response_id": request_data['request_id'], "response_for":"Update","response_set_to":request_data['request_src'],"response_data": {"message":"Error in Request"}}
        return  respfail 
    
def gender_delete(request_data):
    if request_data['request_data']['id']:
        data = request_data['request_data']
        id_dict={}
        id_dict['id']=data['id']
        to_be_updated_data=convert_data_types_for_update('ta_application', 'gender', {"status":9})
        condition_data = convert_data_types_for_conditions('ta_application', 'gender', id_dict)
        sta = dbilayer.update_table("gender", to_be_updated_data, condition_data)
        print(sta)
        if((sta is not None) and (sta == "Success")):
            respsucc = {"response_id": request_data['request_id'], "response_for":"Delete","response_set_to":request_data['request_src'],"response_data": {"message":"Deleted Successfully","status_code":200}}
            return  respsucc
        elif(sta == 'Failed'):
            respfail = {"response_id": request_data['request_id'], "response_for":"Delete","response_set_to":request_data['request_src'],"response_data": {"message":"Delete request Failed"}}
            return  respfail
    
    else:
        respfail = {"response_id": request_data['request_id'], "response_for":"Delete","response_set_to":request_data['request_src'],"response_data": {"message":"Error in Request"}}
        return  respfail    


# BLOOD GROUP
def bloodGroup_create(request_data):
    if isinstance(request_data, dict):
        data_to_insert = request_data['request_data']
        final_data_to_insert=convert_data_types_for_insert('ta_application', 'blood_group', data_to_insert)
        print(final_data_to_insert,"==========FINAL DATA to insert")
        keys = list(data_to_insert.keys())
        columns_output = ",".join([f"`{key}`" for key in keys])
        sta=dbilayer.insert_into_table('blood_group', columns_output, final_data_to_insert)
        if(sta is not None):
            if ('message' in sta):
                if (sta['message'] == 'Success'):
                    respsucc={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Created Successfully","status_code":200, "last_id": sta["last_insert_id"]}}
                    return respsucc
                else:
                    respfail={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request"}}
                    return respfail
            else:
                respfail={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request"}}
                return respfail
        else:
            respfail={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request"}}
            return respfail
    else:
        respfail={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Error Encountered"}}
        return respfail
    
def bloodGroup_readAll(request_data):
    if isinstance(request_data, dict):
        data=request_data['request_data']
        condition_dict = {}
        condition_dict["status"] = 1
        condition_data = convert_data_types_for_conditions('ta_application', 'blood_group', condition_dict)
        sta=dbilayer.read_with_condition('blood_group', '*', condition_data)
        print("sta in bll engine---->", sta)
        if ((sta is not None) and (isinstance(sta, list))):
            if (len(sta) > 0):
                respsucc={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "Success", "status_code":200,"data":sta}}
                return respsucc
            else:
                respfail={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "No Results Found"}}
                return respfail
        else:
            respfail={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request or Requested Items All Are Inactive"}}
            return respfail
    else:
        respfail={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "Error Encountered"}}
        return respfail
    
def bloodGroup_update(request_data):
    if request_data['request_data']['id']:
        data=request_data['request_data']
        id_dict={}
        id_dict['id']=data['id']
        id_dict['status']=1
        condition_data = convert_data_types_for_conditions('ta_application', 'blood_group', id_dict)
        del data['id']
        to_be_updated_data=convert_data_types_for_update('ta_application', 'blood_group', data)
        sta = dbilayer.update_table("blood_group", to_be_updated_data, condition_data)
        print(sta)
        if((sta is not None) and (sta == "Success")):
            respsucc = {"response_id": request_data['request_id'], "response_for":"Update","response_set_to":request_data['request_src'],"response_data": {"message":"Updated Successfully","status_code":200}}
            return  respsucc
        elif(sta == 'Failed'):
            respfail = {"response_id": request_data['request_id'], "response_for":"Update","response_set_to":request_data['request_src'],"response_data": {"message":"Update request Failed"}}
            return  respfail
    else:
        respfail = {"response_id": request_data['request_id'], "response_for":"Update","response_set_to":request_data['request_src'],"response_data": {"message":"Error in Request"}}
        return  respfail 
    
def bloodGroup_delete(request_data):
    if request_data['request_data']['id']:
        data = request_data['request_data']
        id_dict={}
        id_dict['id']=data['id']
        to_be_updated_data=convert_data_types_for_update('ta_application', 'blood_group', {"status":9})
        condition_data = convert_data_types_for_conditions('ta_application', 'blood_group', id_dict)
        sta = dbilayer.update_table("blood_group", to_be_updated_data, condition_data)
        print(sta)
        if((sta is not None) and (sta == "Success")):
            respsucc = {"response_id": request_data['request_id'], "response_for":"Delete","response_set_to":request_data['request_src'],"response_data": {"message":"Deleted Successfully","status_code":200}}
            return  respsucc
        elif(sta == 'Failed'):
            respfail = {"response_id": request_data['request_id'], "response_for":"Delete","response_set_to":request_data['request_src'],"response_data": {"message":"Delete request Failed"}}
            return  respfail
    else:
        respfail = {"response_id": request_data['request_id'], "response_for":"Delete","response_set_to":request_data['request_src'],"response_data": {"message":"Error in Request"}}
        return  respfail    
    
    
# NATIONALITY
def nationality_create(request_data):
    if isinstance(request_data, dict):
        data_to_insert = request_data['request_data']
        final_data_to_insert=convert_data_types_for_insert('ta_application', 'nationality', data_to_insert)
        print(final_data_to_insert,"==========FINAL DATA to insert")
        keys = list(data_to_insert.keys())
        columns_output = ",".join([f"`{key}`" for key in keys])
        sta=dbilayer.insert_into_table('nationality', columns_output, final_data_to_insert)
        if(sta is not None):
            if ('message' in sta):
                if (sta['message'] == 'Success'):
                    respsucc={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Created Successfully","status_code":200, "last_id": sta["last_insert_id"]}}
                    return respsucc
                else:
                    respfail={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request"}}
                    return respfail
            else:
                respfail={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request"}}
                return respfail
        else:
            respfail={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request"}}
            return respfail
    else:
        respfail={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Error Encountered"}}
        return respfail
    
def nationality_readAll(request_data):
    if isinstance(request_data, dict):
        data=request_data['request_data']
        condition_dict = {}
        condition_dict["status"] = 1
        condition_data = convert_data_types_for_conditions('ta_application', 'nationality', condition_dict)
        sta=dbilayer.read_with_condition('nationality', '*', condition_data)
        print("sta in bll engine---->", sta)
        if ((sta is not None) and (isinstance(sta, list))):
            if (len(sta) > 0):
                respsucc={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "Success", "status_code":200,"data":sta}}
                return respsucc
            else:
                respfail={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "No Results Found"}}
                return respfail
        else:
            respfail={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request or Requested Items All Are Inactive"}}
            return respfail
    else:
        respfail={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "Error Encountered"}}
        return respfail
    
def nationality_update(request_data):
    if request_data['request_data']['id']:
        data=request_data['request_data']
        id_dict={}
        id_dict['id']=data['id']
        id_dict['status']=1
        condition_data = convert_data_types_for_conditions('ta_application', 'nationality', id_dict)
        del data['id']
        to_be_updated_data=convert_data_types_for_update('ta_application', 'nationality', data)
        sta = dbilayer.update_table("nationality", to_be_updated_data, condition_data)
        print(sta)
        if((sta is not None) and (sta == "Success")):
            respsucc = {"response_id": request_data['request_id'], "response_for":"Update","response_set_to":request_data['request_src'],"response_data": {"message":"Updated Successfully","status_code":200}}
            return  respsucc
        elif(sta == 'Failed'):
            respfail = {"response_id": request_data['request_id'], "response_for":"Update","response_set_to":request_data['request_src'],"response_data": {"message":"Update request Failed"}}
            return  respfail
    else:
        respfail = {"response_id": request_data['request_id'], "response_for":"Update","response_set_to":request_data['request_src'],"response_data": {"message":"Error in Request"}}
        return  respfail 
    
def nationality_delete(request_data):
    if request_data['request_data']['id']:
        data = request_data['request_data']
        id_dict={}
        id_dict['id']=data['id']
        to_be_updated_data=convert_data_types_for_update('ta_application', 'nationality', {"status":9})
        condition_data = convert_data_types_for_conditions('ta_application', 'nationality', id_dict)
        sta = dbilayer.update_table("nationality", to_be_updated_data, condition_data)
        print(sta)
        if((sta is not None) and (sta == "Success")):
            respsucc = {"response_id": request_data['request_id'], "response_for":"Delete","response_set_to":request_data['request_src'],"response_data": {"message":"Deleted Successfully","status_code":200}}
            return  respsucc
        elif(sta == 'Failed'):
            respfail = {"response_id": request_data['request_id'], "response_for":"Delete","response_set_to":request_data['request_src'],"response_data": {"message":"Delete request Failed"}}
            return  respfail
    
    else:
        respfail = {"response_id": request_data['request_id'], "response_for":"Delete","response_set_to":request_data['request_src'],"response_data": {"message":"Error in Request"}}
        return  respfail    



# ISD Code
def ISDCode_create(request_data):
    if isinstance(request_data, dict):
        data_to_insert = request_data['request_data']
        final_data_to_insert=convert_data_types_for_insert('ta_application', 'isd_code', data_to_insert)
        print(final_data_to_insert,"==========FINAL DATA to insert")
        keys = list(data_to_insert.keys())
        columns_output = ",".join([f"`{key}`" for key in keys])
        sta=dbilayer.insert_into_table('isd_code', columns_output, final_data_to_insert)
        if(sta is not None):
            if ('message' in sta):
                if (sta['message'] == 'Success'):
                    respsucc={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Created Successfully","status_code":200, "last_id": sta["last_insert_id"]}}
                    return respsucc
                else:
                    respfail={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request"}}
                    return respfail
            else:
                respfail={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request"}}
                return respfail
        else:
            respfail={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request"}}
            return respfail
    else:
        respfail={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Error Encountered"}}
        return respfail
    
def ISDCode_readAll(request_data):
    if isinstance(request_data, dict):
        data=request_data['request_data']
        condition_dict = {}
        condition_dict["status"] = 1
        condition_data = convert_data_types_for_conditions('ta_application', 'isd_code', condition_dict)
        sta=dbilayer.read_with_condition('isd_code', '*', condition_data)
        print("sta in bll engine---->", sta)
        if ((sta is not None) and (isinstance(sta, list))):
            if (len(sta) > 0):
                respsucc={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "Success", "status_code":200,"data":sta}}
                return respsucc
            else:
                respfail={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "No Results Found"}}
                return respfail
        else:
            respfail={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request or Requested Items All Are Inactive"}}
            return respfail
    else:
        respfail={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "Error Encountered"}}
        return respfail
    
def ISDCode_update(request_data):
    if request_data['request_data']['id']:
        data=request_data['request_data']
        id_dict={}
        id_dict['id']=data['id']
        id_dict['status']=1
        condition_data = convert_data_types_for_conditions('ta_application', 'isd_code', id_dict)
        del data['id']
        to_be_updated_data=convert_data_types_for_update('ta_application', 'isd_code', data)
        sta = dbilayer.update_table("isd_code", to_be_updated_data, condition_data)
        print(sta)
        if((sta is not None) and (sta == "Success")):
            respsucc = {"response_id": request_data['request_id'], "response_for":"Update","response_set_to":request_data['request_src'],"response_data": {"message":"Updated Successfully","status_code":200}}
            return  respsucc
        elif(sta == 'Failed'):
            respfail = {"response_id": request_data['request_id'], "response_for":"Update","response_set_to":request_data['request_src'],"response_data": {"message":"Update request Failed"}}
            return  respfail
    else:
        respfail = {"response_id": request_data['request_id'], "response_for":"Update","response_set_to":request_data['request_src'],"response_data": {"message":"Error in Request"}}
        return  respfail 
    
def ISDCode_delete(request_data):
    if request_data['request_data']['id']:
        data = request_data['request_data']
        id_dict={}
        id_dict['id']=data['id']
        to_be_updated_data=convert_data_types_for_update('ta_application', 'isd_code', {"status":9})
        condition_data = convert_data_types_for_conditions('ta_application', 'isd_code', id_dict)
        sta = dbilayer.update_table("isd_code", to_be_updated_data, condition_data)
        print(sta)
        if((sta is not None) and (sta == "Success")):
            respsucc = {"response_id": request_data['request_id'], "response_for":"Delete","response_set_to":request_data['request_src'],"response_data": {"message":"Deleted Successfully","status_code":200}}
            return  respsucc
        elif(sta == 'Failed'):
            respfail = {"response_id": request_data['request_id'], "response_for":"Delete","response_set_to":request_data['request_src'],"response_data": {"message":"Delete request Failed"}}
            return  respfail
    
    else:
        respfail = {"response_id": request_data['request_id'], "response_for":"Delete","response_set_to":request_data['request_src'],"response_data": {"message":"Error in Request"}}
        return  respfail  


# SOURCE
def source_create(request_data):
    if isinstance(request_data, dict):
        data_to_insert = request_data['request_data']
        final_data_to_insert=convert_data_types_for_insert('ta_application', 'source', data_to_insert)
        print(final_data_to_insert,"==========FINAL DATA to insert")
        keys = list(data_to_insert.keys())
        columns_output = ",".join([f"`{key}`" for key in keys])
        sta=dbilayer.insert_into_table('source', columns_output, final_data_to_insert)
        if(sta is not None):
            if ('message' in sta):
                if (sta['message'] == 'Success'):
                    respsucc={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Created Successfully","status_code":200, "last_id": sta["last_insert_id"]}}
                    return respsucc
                else:
                    respfail={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request"}}
                    return respfail
            else:
                respfail={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request"}}
                return respfail
        else:
            respfail={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request"}}
            return respfail
    else:
        respfail={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Error Encountered"}}
        return respfail
    
def source_readAll(request_data):
    if isinstance(request_data, dict):
        data=request_data['request_data']
        condition_dict = {}
        condition_dict["status"] = 1
        condition_data = convert_data_types_for_conditions('ta_application', 'source', condition_dict)
        sta=dbilayer.read_with_condition('source', '*', condition_data)
        print("sta in bll engine---->", sta)
        if ((sta is not None) and (isinstance(sta, list))):
            if (len(sta) > 0):
                respsucc={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "Success", "status_code":200,"data":sta}}
                return respsucc
            else:
                respfail={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "No Results Found"}}
                return respfail
        else:
            respfail={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request or Requested Items All Are Inactive"}}
            return respfail
    else:
        respfail={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "Error Encountered"}}
        return respfail
    
def source_update(request_data):
    if request_data['request_data']['id']:
        data=request_data['request_data']
        id_dict={}
        id_dict['id']=data['id']
        id_dict['status']=1
        condition_data = convert_data_types_for_conditions('ta_application', 'source', id_dict)
        del data['id']
        to_be_updated_data=convert_data_types_for_update('ta_application', 'source', data)
        sta = dbilayer.update_table("source", to_be_updated_data, condition_data)
        print(sta)
        if((sta is not None) and (sta == "Success")):
            respsucc = {"response_id": request_data['request_id'], "response_for":"Update","response_set_to":request_data['request_src'],"response_data": {"message":"Updated Successfully","status_code":200}}
            return  respsucc
        elif(sta == 'Failed'):
            respfail = {"response_id": request_data['request_id'], "response_for":"Update","response_set_to":request_data['request_src'],"response_data": {"message":"Update request Failed"}}
            return  respfail
    else:
        respfail = {"response_id": request_data['request_id'], "response_for":"Update","response_set_to":request_data['request_src'],"response_data": {"message":"Error in Request"}}
        return  respfail 
    
def source_delete(request_data):
    if request_data['request_data']['id']:
        data = request_data['request_data']
        id_dict={}
        id_dict['id']=data['id']
        to_be_updated_data=convert_data_types_for_update('ta_application', 'source', {"status":9})
        condition_data = convert_data_types_for_conditions('ta_application', 'source', id_dict)
        sta = dbilayer.update_table("source", to_be_updated_data, condition_data)
        print(sta)
        if((sta is not None) and (sta == "Success")):
            respsucc = {"response_id": request_data['request_id'], "response_for":"Delete","response_set_to":request_data['request_src'],"response_data": {"message":"Deleted Successfully","status_code":200}}
            return  respsucc
        elif(sta == 'Failed'):
            respfail = {"response_id": request_data['request_id'], "response_for":"Delete","response_set_to":request_data['request_src'],"response_data": {"message":"Delete request Failed"}}
            return  respfail
    
    else:
        respfail = {"response_id": request_data['request_id'], "response_for":"Delete","response_set_to":request_data['request_src'],"response_data": {"message":"Error in Request"}}
        return  respfail  

# SOURCE CATEGORY
def sourceCategory_create(request_data):
    if isinstance(request_data, dict):
        data_to_insert = request_data['request_data']
        final_data_to_insert=convert_data_types_for_insert('ta_application', 'source_category', data_to_insert)
        print(final_data_to_insert,"==========FINAL DATA to insert")
        keys = list(data_to_insert.keys())
        columns_output = ",".join([f"`{key}`" for key in keys])
        sta=dbilayer.insert_into_table('source_category', columns_output, final_data_to_insert)
        if(sta is not None):
            if ('message' in sta):
                if (sta['message'] == 'Success'):
                    respsucc={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Created Successfully","status_code":200, "last_id": sta["last_insert_id"]}}
                    return respsucc
                else:
                    respfail={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request"}}
                    return respfail
            else:
                respfail={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request"}}
                return respfail
        else:
            respfail={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request"}}
            return respfail
    else:
        respfail={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Error Encountered"}}
        return respfail
    
def sourceCategory_readAll(request_data):
    if isinstance(request_data, dict):
        data=request_data['request_data']
        condition_dict = {}
        condition_dict["status"] = 1
        condition_data = convert_data_types_for_conditions('ta_application', 'source_category', condition_dict)
        sta=dbilayer.read_with_condition('source_category', '*', condition_data)
        print("sta in bll engine---->", sta)
        if ((sta is not None) and (isinstance(sta, list))):
            if (len(sta) > 0):
                respsucc={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "Success", "status_code":200,"data":sta}}
                return respsucc
            else:
                respfail={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "No Results Found"}}
                return respfail
        else:
            respfail={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request or Requested Items All Are Inactive"}}
            return respfail
    else:
        respfail={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "Error Encountered"}}
        return respfail
    
def sourceCategory_update(request_data):
    if request_data['request_data']['id']:
        data=request_data['request_data']
        id_dict={}
        id_dict['id']=data['id']
        id_dict['status']=1
        condition_data = convert_data_types_for_conditions('ta_application', 'source_category', id_dict)
        del data['id']
        to_be_updated_data=convert_data_types_for_update('ta_application', 'source_category', data)
        sta = dbilayer.update_table("source_category", to_be_updated_data, condition_data)
        print(sta)
        if((sta is not None) and (sta == "Success")):
            respsucc = {"response_id": request_data['request_id'], "response_for":"Update","response_set_to":request_data['request_src'],"response_data": {"message":"Updated Successfully","status_code":200}}
            return  respsucc
        elif(sta == 'Failed'):
            respfail = {"response_id": request_data['request_id'], "response_for":"Update","response_set_to":request_data['request_src'],"response_data": {"message":"Update request Failed"}}
            return  respfail
    else:
        respfail = {"response_id": request_data['request_id'], "response_for":"Update","response_set_to":request_data['request_src'],"response_data": {"message":"Error in Request"}}
        return  respfail 
    
def sourceCategory_delete(request_data):
    if request_data['request_data']['id']:
        data = request_data['request_data']
        id_dict={}
        id_dict['id']=data['id']
        to_be_updated_data=convert_data_types_for_update('ta_application', 'sourceCategory', {"status":9})
        condition_data = convert_data_types_for_conditions('ta_application', 'sourceCategory', id_dict)
        sta = dbilayer.update_table("sourceCategory", to_be_updated_data, condition_data)
        print(sta)
        if((sta is not None) and (sta == "Success")):
            respsucc = {"response_id": request_data['request_id'], "response_for":"Delete","response_set_to":request_data['request_src'],"response_data": {"message":"Deleted Successfully","status_code":200}}
            return  respsucc
        elif(sta == 'Failed'):
            respfail = {"response_id": request_data['request_id'], "response_for":"Delete","response_set_to":request_data['request_src'],"response_data": {"message":"Delete request Failed"}}
            return  respfail
    
    else:
        respfail = {"response_id": request_data['request_id'], "response_for":"Delete","response_set_to":request_data['request_src'],"response_data": {"message":"Error in Request"}}
        return  respfail 
    
# PREFERRED LOCATION
def preferredLocation_create(request_data):
    if isinstance(request_data, dict):
        data_to_insert = request_data['request_data']
        final_data_to_insert=convert_data_types_for_insert('ta_application', 'preferred_location', data_to_insert)
        print(final_data_to_insert,"==========FINAL DATA to insert")
        keys = list(data_to_insert.keys())
        columns_output = ",".join([f"`{key}`" for key in keys])
        sta=dbilayer.insert_into_table('preferred_location', columns_output, final_data_to_insert)
        if(sta is not None):
            if ('message' in sta):
                if (sta['message'] == 'Success'):
                    respsucc={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Created Successfully","status_code":200, "last_id": sta["last_insert_id"]}}
                    return respsucc
                else:
                    respfail={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request"}}
                    return respfail
            else:
                respfail={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request"}}
                return respfail
        else:
            respfail={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request"}}
            return respfail
    else:
        respfail={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Error Encountered"}}
        return respfail
    
def preferredLocation_readAll(request_data):
    if isinstance(request_data, dict):
        data=request_data['request_data']
        condition_dict = {}
        condition_dict["status"] = 1
        condition_data = convert_data_types_for_conditions('ta_application', 'preferred_location', condition_dict)
        sta=dbilayer.read_with_condition('preferred_location', '*', condition_data)
        print("sta in bll engine---->", sta)
        if ((sta is not None) and (isinstance(sta, list))):
            if (len(sta) > 0):
                respsucc={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "Success", "status_code":200,"data":sta}}
                return respsucc
            else:
                respfail={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "No Results Found"}}
                return respfail
        else:
            respfail={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request or Requested Items All Are Inactive"}}
            return respfail
    else:
        respfail={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "Error Encountered"}}
        return respfail
    
def preferredLocation_update(request_data):
    if request_data['request_data']['id']:
        data=request_data['request_data']
        id_dict={}
        id_dict['id']=data['id']
        id_dict['status']=1
        condition_data = convert_data_types_for_conditions('ta_application', 'preferred_location', id_dict)
        del data['id']
        to_be_updated_data=convert_data_types_for_update('ta_application', 'preferred_location', data)
        sta = dbilayer.update_table("preferred_location", to_be_updated_data, condition_data)
        print(sta)
        if((sta is not None) and (sta == "Success")):
            respsucc = {"response_id": request_data['request_id'], "response_for":"Update","response_set_to":request_data['request_src'],"response_data": {"message":"Updated Successfully","status_code":200}}
            return  respsucc
        elif(sta == 'Failed'):
            respfail = {"response_id": request_data['request_id'], "response_for":"Update","response_set_to":request_data['request_src'],"response_data": {"message":"Update request Failed"}}
            return  respfail
    else:
        respfail = {"response_id": request_data['request_id'], "response_for":"Update","response_set_to":request_data['request_src'],"response_data": {"message":"Error in Request"}}
        return  respfail 
    
def preferredLocation_delete(request_data):
    if request_data['request_data']['id']:
        data = request_data['request_data']
        id_dict={}
        id_dict['id']=data['id']
        to_be_updated_data=convert_data_types_for_update('ta_application', 'preferred_location', {"status":9})
        condition_data = convert_data_types_for_conditions('ta_application', 'preferred_location', id_dict)
        sta = dbilayer.update_table("preferred_location", to_be_updated_data, condition_data)
        print(sta)
        if((sta is not None) and (sta == "Success")):
            respsucc = {"response_id": request_data['request_id'], "response_for":"Delete","response_set_to":request_data['request_src'],"response_data": {"message":"Deleted Successfully","status_code":200}}
            return  respsucc
        elif(sta == 'Failed'):
            respfail = {"response_id": request_data['request_id'], "response_for":"Delete","response_set_to":request_data['request_src'],"response_data": {"message":"Delete request Failed"}}
            return  respfail
    
    else:
        respfail = {"response_id": request_data['request_id'], "response_for":"Delete","response_set_to":request_data['request_src'],"response_data": {"message":"Error in Request"}}
        return  respfail 

# NOTICE PERIOD
def noticePeriod_create(request_data):
    if isinstance(request_data, dict):
        data_to_insert = request_data['request_data']
        final_data_to_insert=convert_data_types_for_insert('ta_application', 'notice_period', data_to_insert)
        print(final_data_to_insert,"==========FINAL DATA to insert")
        keys = list(data_to_insert.keys())
        columns_output = ",".join([f"`{key}`" for key in keys])
        sta=dbilayer.insert_into_table('notice_period', columns_output, final_data_to_insert)
        if(sta is not None):
            if ('message' in sta):
                if (sta['message'] == 'Success'):
                    respsucc={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Created Successfully","status_code":200, "last_id": sta["last_insert_id"]}}
                    return respsucc
                else:
                    respfail={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request"}}
                    return respfail
            else:
                respfail={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request"}}
                return respfail
        else:
            respfail={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request"}}
            return respfail
    else:
        respfail={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Error Encountered"}}
        return respfail
    
def noticePeriod_readAll(request_data):
    if isinstance(request_data, dict):
        data=request_data['request_data']
        condition_dict = {}
        condition_dict["status"] = 1
        condition_data = convert_data_types_for_conditions('ta_application', 'notice_period', condition_dict)
        sta=dbilayer.read_with_condition('notice_period', '*', condition_data)
        print("sta in bll engine---->", sta)
        if ((sta is not None) and (isinstance(sta, list))):
            if (len(sta) > 0):
                respsucc={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "Success", "status_code":200,"data":sta}}
                return respsucc
            else:
                respfail={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "No Results Found"}}
                return respfail
        else:
            respfail={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request or Requested Items All Are Inactive"}}
            return respfail
    else:
        respfail={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "Error Encountered"}}
        return respfail
    
def noticePeriod_update(request_data):
    if request_data['request_data']['id']:
        data=request_data['request_data']
        id_dict={}
        id_dict['id']=data['id']
        id_dict['status']=1
        condition_data = convert_data_types_for_conditions('ta_application', 'notice_period', id_dict)
        del data['id']
        to_be_updated_data=convert_data_types_for_update('ta_application', 'notice_period', data)
        sta = dbilayer.update_table("notice_period", to_be_updated_data, condition_data)
        print(sta)
        if((sta is not None) and (sta == "Success")):
            respsucc = {"response_id": request_data['request_id'], "response_for":"Update","response_set_to":request_data['request_src'],"response_data": {"message":"Updated Successfully","status_code":200}}
            return  respsucc
        elif(sta == 'Failed'):
            respfail = {"response_id": request_data['request_id'], "response_for":"Update","response_set_to":request_data['request_src'],"response_data": {"message":"Update request Failed"}}
            return  respfail
    else:
        respfail = {"response_id": request_data['request_id'], "response_for":"Update","response_set_to":request_data['request_src'],"response_data": {"message":"Error in Request"}}
        return  respfail 
    
def noticePeriod_delete(request_data):
    if request_data['request_data']['id']:
        data = request_data['request_data']
        id_dict={}
        id_dict['id']=data['id']
        to_be_updated_data=convert_data_types_for_update('ta_application', 'notice_period', {"status":9})
        condition_data = convert_data_types_for_conditions('ta_application', 'notice_period', id_dict)
        sta = dbilayer.update_table("notice_period", to_be_updated_data, condition_data)
        print(sta)
        if((sta is not None) and (sta == "Success")):
            respsucc = {"response_id": request_data['request_id'], "response_for":"Delete","response_set_to":request_data['request_src'],"response_data": {"message":"Deleted Successfully","status_code":200}}
            return  respsucc
        elif(sta == 'Failed'):
            respfail = {"response_id": request_data['request_id'], "response_for":"Delete","response_set_to":request_data['request_src'],"response_data": {"message":"Delete request Failed"}}
            return  respfail
    
    else:
        respfail = {"response_id": request_data['request_id'], "response_for":"Delete","response_set_to":request_data['request_src'],"response_data": {"message":"Error in Request"}}
        return  respfail 


# ROUND TYPE
def roundType_create(request_data):
    if isinstance(request_data, dict):
        data_to_insert = request_data['request_data']
        final_data_to_insert=convert_data_types_for_insert('ta_application', 'round_type', data_to_insert)
        print(final_data_to_insert,"==========FINAL DATA to insert")
        keys = list(data_to_insert.keys())
        columns_output = ",".join([f"`{key}`" for key in keys])
        sta=dbilayer.insert_into_table('round_type', columns_output, final_data_to_insert)
        if(sta is not None):
            if ('message' in sta):
                if (sta['message'] == 'Success'):
                    respsucc={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Created Successfully","status_code":200, "last_id": sta["last_insert_id"]}}
                    return respsucc
                else:
                    respfail={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request"}}
                    return respfail
            else:
                respfail={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request"}}
                return respfail
        else:
            respfail={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request"}}
            return respfail
    else:
        respfail={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Error Encountered"}}
        return respfail
    
def roundType_readAll(request_data):
    if isinstance(request_data, dict):
        data=request_data['request_data']
        condition_dict = {}
        condition_dict["status"] = 1
        condition_data = convert_data_types_for_conditions('ta_application', 'round_type', condition_dict)
        sta=dbilayer.read_with_condition('round_type', '*', condition_data)
        print("sta in bll engine---->", sta)
        if ((sta is not None) and (isinstance(sta, list))):
            if (len(sta) > 0):
                respsucc={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "Success", "status_code":200,"data":sta}}
                return respsucc
            else:
                respfail={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "No Results Found"}}
                return respfail
        else:
            respfail={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request or Requested Items All Are Inactive"}}
            return respfail
    else:
        respfail={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "Error Encountered"}}
        return respfail
    
def roundType_update(request_data):
    if request_data['request_data']['id']:
        data=request_data['request_data']
        id_dict={}
        id_dict['id']=data['id']
        id_dict['status']=1
        condition_data = convert_data_types_for_conditions('ta_application', 'round_type', id_dict)
        del data['id']
        to_be_updated_data=convert_data_types_for_update('ta_application', 'round_type', data)
        sta = dbilayer.update_table("round_type", to_be_updated_data, condition_data)
        print(sta)
        if((sta is not None) and (sta == "Success")):
            respsucc = {"response_id": request_data['request_id'], "response_for":"Update","response_set_to":request_data['request_src'],"response_data": {"message":"Updated Successfully","status_code":200}}
            return  respsucc
        elif(sta == 'Failed'):
            respfail = {"response_id": request_data['request_id'], "response_for":"Update","response_set_to":request_data['request_src'],"response_data": {"message":"Update request Failed"}}
            return  respfail
    else:
        respfail = {"response_id": request_data['request_id'], "response_for":"Update","response_set_to":request_data['request_src'],"response_data": {"message":"Error in Request"}}
        return  respfail 
    
def roundType_delete(request_data):
    if request_data['request_data']['id']:
        data = request_data['request_data']
        id_dict={}
        id_dict['id']=data['id']
        to_be_updated_data=convert_data_types_for_update('ta_application', 'round_type', {"status":9})
        condition_data = convert_data_types_for_conditions('ta_application', 'round_type', id_dict)
        sta = dbilayer.update_table("round_type", to_be_updated_data, condition_data)
        print(sta)
        if((sta is not None) and (sta == "Success")):
            respsucc = {"response_id": request_data['request_id'], "response_for":"Delete","response_set_to":request_data['request_src'],"response_data": {"message":"Deleted Successfully","status_code":200}}
            return  respsucc
        elif(sta == 'Failed'):
            respfail = {"response_id": request_data['request_id'], "response_for":"Delete","response_set_to":request_data['request_src'],"response_data": {"message":"Delete request Failed"}}
            return  respfail
    
    else:
        respfail = {"response_id": request_data['request_id'], "response_for":"Delete","response_set_to":request_data['request_src'],"response_data": {"message":"Error in Request"}}
        return  respfail 
    
# TEMPLATE JOB
def templateJob_create(request_data):
    if isinstance(request_data, dict):
        data_to_insert = request_data['request_data']
        final_data_to_insert=convert_data_types_for_insert('ta_application', 'template_job', data_to_insert)
        print(final_data_to_insert,"==========FINAL DATA to insert")
        keys = list(data_to_insert.keys())
        columns_output = ",".join([f"`{key}`" for key in keys])
        sta=dbilayer.insert_into_table('template_job', columns_output, final_data_to_insert)
        if(sta is not None):
            if ('message' in sta):
                if (sta['message'] == 'Success'):
                    respsucc={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Created Successfully","status_code":200, "last_id": sta["last_insert_id"]}}
                    return respsucc
                else:
                    respfail={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request"}}
                    return respfail
            else:
                respfail={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request"}}
                return respfail
        else:
            respfail={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request"}}
            return respfail
    else:
        respfail={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Error Encountered"}}
        return respfail
    
def templateJob_readAll(request_data):
    if isinstance(request_data, dict):
        data=request_data['request_data']
        condition_dict = {}
        condition_dict["status"] = 1
        condition_data = convert_data_types_for_conditions('ta_application', 'template_job', condition_dict)
        sta=dbilayer.read_with_condition('template_job', '*', condition_data)
        print("sta in bll engine---->", sta)
        if ((sta is not None) and (isinstance(sta, list))):
            if (len(sta) > 0):
                respsucc={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "Success", "status_code":200,"data":sta}}
                return respsucc
            else:
                respfail={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "No Results Found"}}
                return respfail
        else:
            respfail={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request or Requested Items All Are Inactive"}}
            return respfail
    else:
        respfail={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "Error Encountered"}}
        return respfail
    
def templateJob_update(request_data):
    if request_data['request_data']['id']:
        data=request_data['request_data']
        id_dict={}
        id_dict['id']=data['id']
        id_dict['status']=1
        condition_data = convert_data_types_for_conditions('ta_application', 'template_job', id_dict)
        del data['id']
        to_be_updated_data=convert_data_types_for_update('ta_application', 'template_job', data)
        sta = dbilayer.update_table("template_job", to_be_updated_data, condition_data)
        print(sta)
        if((sta is not None) and (sta == "Success")):
            respsucc = {"response_id": request_data['request_id'], "response_for":"Update","response_set_to":request_data['request_src'],"response_data": {"message":"Updated Successfully","status_code":200}}
            return  respsucc
        elif(sta == 'Failed'):
            respfail = {"response_id": request_data['request_id'], "response_for":"Update","response_set_to":request_data['request_src'],"response_data": {"message":"Update request Failed"}}
            return  respfail
    else:
        respfail = {"response_id": request_data['request_id'], "response_for":"Update","response_set_to":request_data['request_src'],"response_data": {"message":"Error in Request"}}
        return  respfail 
    
def templateJob_delete(request_data):
    if request_data['request_data']['id']:
        data = request_data['request_data']
        id_dict={}
        id_dict['id']=data['id']
        to_be_updated_data=convert_data_types_for_update('ta_application', 'template_job', {"status":9})
        condition_data = convert_data_types_for_conditions('ta_application', 'template_job', id_dict)
        sta = dbilayer.update_table("template_job", to_be_updated_data, condition_data)
        print(sta)
        if((sta is not None) and (sta == "Success")):
            respsucc = {"response_id": request_data['request_id'], "response_for":"Delete","response_set_to":request_data['request_src'],"response_data": {"message":"Deleted Successfully","status_code":200}}
            return  respsucc
        elif(sta == 'Failed'):
            respfail = {"response_id": request_data['request_id'], "response_for":"Delete","response_set_to":request_data['request_src'],"response_data": {"message":"Delete request Failed"}}
            return  respfail
    
    else:
        respfail = {"response_id": request_data['request_id'], "response_for":"Delete","response_set_to":request_data['request_src'],"response_data": {"message":"Error in Request"}}
        return  respfail 
    

# TEMPLATE QUESTIONS
def templateQuestion_create(request_data):
    if isinstance(request_data, dict):
        data_to_insert = request_data['request_data']
        final_data_to_insert=convert_data_types_for_insert('ta_application', 'template_question', data_to_insert)
        print(final_data_to_insert,"==========FINAL DATA to insert")
        keys = list(data_to_insert.keys())
        columns_output = ",".join([f"`{key}`" for key in keys])
        sta=dbilayer.insert_into_table('template_question', columns_output, final_data_to_insert)
        if(sta is not None):
            if ('message' in sta):
                if (sta['message'] == 'Success'):
                    respsucc={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Created Successfully","status_code":200, "last_id": sta["last_insert_id"]}}
                    return respsucc
                else:
                    respfail={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request"}}
                    return respfail
            else:
                respfail={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request"}}
                return respfail
        else:
            respfail={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request"}}
            return respfail
    else:
        respfail={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Error Encountered"}}
        return respfail
    
def templateQuestion_readAll(request_data):
    if isinstance(request_data, dict):
        data=request_data['request_data']
        condition_dict = {}
        condition_dict["status"] = 1
        condition_data = convert_data_types_for_conditions('ta_application', 'template_question', condition_dict)
        sta=dbilayer.read_with_condition('template_question', '*', condition_data)
        print("sta in bll engine---->", sta)
        if ((sta is not None) and (isinstance(sta, list))):
            if (len(sta) > 0):
                respsucc={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "Success", "status_code":200,"data":sta}}
                return respsucc
            else:
                respfail={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "No Results Found"}}
                return respfail
        else:
            respfail={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request or Requested Items All Are Inactive"}}
            return respfail
    else:
        respfail={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "Error Encountered"}}
        return respfail
    
def templateQuestion_update(request_data):
    if request_data['request_data']['id']:
        data=request_data['request_data']
        id_dict={}
        id_dict['id']=data['id']
        id_dict['status']=1
        condition_data = convert_data_types_for_conditions('ta_application', 'template_question', id_dict)
        del data['id']
        to_be_updated_data=convert_data_types_for_update('ta_application', 'template_question', data)
        sta = dbilayer.update_table("template_question", to_be_updated_data, condition_data)
        print(sta)
        if((sta is not None) and (sta == "Success")):
            respsucc = {"response_id": request_data['request_id'], "response_for":"Update","response_set_to":request_data['request_src'],"response_data": {"message":"Updated Successfully","status_code":200}}
            return  respsucc
        elif(sta == 'Failed'):
            respfail = {"response_id": request_data['request_id'], "response_for":"Update","response_set_to":request_data['request_src'],"response_data": {"message":"Update request Failed"}}
            return  respfail
    else:
        respfail = {"response_id": request_data['request_id'], "response_for":"Update","response_set_to":request_data['request_src'],"response_data": {"message":"Error in Request"}}
        return  respfail 
    
def templateQuestion_delete(request_data):
    if request_data['request_data']['id']:
        data = request_data['request_data']
        id_dict={}
        id_dict['id']=data['id']
        to_be_updated_data=convert_data_types_for_update('ta_application', 'template_question', {"status":9})
        condition_data = convert_data_types_for_conditions('ta_application', 'template_question', id_dict)
        sta = dbilayer.update_table("template_question", to_be_updated_data, condition_data)
        print(sta)
        if((sta is not None) and (sta == "Success")):
            respsucc = {"response_id": request_data['request_id'], "response_for":"Delete","response_set_to":request_data['request_src'],"response_data": {"message":"Deleted Successfully","status_code":200}}
            return  respsucc
        elif(sta == 'Failed'):
            respfail = {"response_id": request_data['request_id'], "response_for":"Delete","response_set_to":request_data['request_src'],"response_data": {"message":"Delete request Failed"}}
            return  respfail
    
    else:
        respfail = {"response_id": request_data['request_id'], "response_for":"Delete","response_set_to":request_data['request_src'],"response_data": {"message":"Error in Request"}}
        return  respfail 
  


# INTERVIEW STATUS
def interviewStatus_create(request_data):
    if isinstance(request_data, dict):
        data_to_insert = request_data['request_data']
        final_data_to_insert=convert_data_types_for_insert('ta_application', 'interview_status', data_to_insert)
        print(final_data_to_insert,"==========FINAL DATA to insert")
        keys = list(data_to_insert.keys())
        columns_output = ",".join([f"`{key}`" for key in keys])
        sta=dbilayer.insert_into_table('interview_status', columns_output, final_data_to_insert)
        if(sta is not None):
            if ('message' in sta):
                if (sta['message'] == 'Success'):
                    respsucc={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Created Successfully","status_code":200, "last_id": sta["last_insert_id"]}}
                    return respsucc
                else:
                    respfail={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request"}}
                    return respfail
            else:
                respfail={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request"}}
                return respfail
        else:
            respfail={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request"}}
            return respfail
    else:
        respfail={"response_id": request_data['request_id'], "response_for": "Create", "response_set_to": request_data['request_src'], "response": {"message": "Error Encountered"}}
        return respfail
    
def interviewStatus_readAll(request_data):
    if isinstance(request_data, dict):
        data=request_data['request_data']
        condition_dict = {}
        condition_dict["status"] = 1
        condition_data = convert_data_types_for_conditions('ta_application', 'interview_status', condition_dict)
        sta=dbilayer.read_with_condition('interview_status', '*', condition_data)
        print("sta in bll engine---->", sta)
        if ((sta is not None) and (isinstance(sta, list))):
            if (len(sta) > 0):
                respsucc={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "Success", "status_code":200,"data":sta}}
                return respsucc
            else:
                respfail={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "No Results Found"}}
                return respfail
        else:
            respfail={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request or Requested Items All Are Inactive"}}
            return respfail
    else:
        respfail={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "Error Encountered"}}
        return respfail
    
def interviewStatus_update(request_data):
    if request_data['request_data']['id']:
        data=request_data['request_data']
        id_dict={}
        id_dict['id']=data['id']
        id_dict['status']=1
        condition_data = convert_data_types_for_conditions('ta_application', 'interview_status', id_dict)
        del data['id']
        to_be_updated_data=convert_data_types_for_update('ta_application', 'interview_status', data)
        sta = dbilayer.update_table("interview_status", to_be_updated_data, condition_data)
        print(sta)
        if((sta is not None) and (sta == "Success")):
            respsucc = {"response_id": request_data['request_id'], "response_for":"Update","response_set_to":request_data['request_src'],"response_data": {"message":"Updated Successfully","status_code":200}}
            return  respsucc
        elif(sta == 'Failed'):
            respfail = {"response_id": request_data['request_id'], "response_for":"Update","response_set_to":request_data['request_src'],"response_data": {"message":"Update request Failed"}}
            return  respfail
    else:
        respfail = {"response_id": request_data['request_id'], "response_for":"Update","response_set_to":request_data['request_src'],"response_data": {"message":"Error in Request"}}
        return  respfail 
    
def interviewStatus_delete(request_data):
    if request_data['request_data']['id']:
        data = request_data['request_data']
        id_dict={}
        id_dict['id']=data['id']
        to_be_updated_data=convert_data_types_for_update('ta_application', 'interview_status', {"status":9})
        condition_data = convert_data_types_for_conditions('ta_application', 'interview_status', id_dict)
        sta = dbilayer.update_table("interview_status", to_be_updated_data, condition_data)
        print(sta)
        if((sta is not None) and (sta == "Success")):
            respsucc = {"response_id": request_data['request_id'], "response_for":"Delete","response_set_to":request_data['request_src'],"response_data": {"message":"Deleted Successfully","status_code":200}}
            return  respsucc
        elif(sta == 'Failed'):
            respfail = {"response_id": request_data['request_id'], "response_for":"Delete","response_set_to":request_data['request_src'],"response_data": {"message":"Delete request Failed"}}
            return  respfail
    else:
        respfail = {"response_id": request_data['request_id'], "response_for":"Delete","response_set_to":request_data['request_src'],"response_data": {"message":"Error in Request"}}
        return  respfail 
    
    
    
def countryAndNationality_readAll(request_data):
    if isinstance(request_data, dict):
        data=request_data['request_data']
        url = "https://en.wikipedia.org/wiki/List_of_adjectival_and_demonymic_forms_of_place_names"

        # Send a GET request to the URL
        response = requests.get(url)

        # Parse the HTML content of the page
        soup = BeautifulSoup(response.content, 'html.parser')

        # Find all tables containing the data
        tables = soup.find_all('table', {'class': 'wikitable'})

        # Extract country names and nationalities from the table
        countries = []
        nationalities = []

        for table in tables:
            for row in table.find_all('tr')[1:]:  # Skip the header row
                cells = row.find_all('td')
                if len(cells) >= 2:
                    country = cells[0].text.strip()
                    nationality = cells[1].text.strip()
                    countries.append(country)
                    nationalities.append(nationality)

        # Create a list of dictionaries
        output = []
        for i in range(len(countries)):
            output.append({"country" + str(i+1): countries[i], "nationality" + str(i+1): nationalities[i]})
        sta = output
        print("sta in bll engine---->", sta)
        if ((sta is not None) and (isinstance(sta, list))):
            if (len(sta) > 0):
                respsucc={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "Success", "status_code":200,"data":sta}}
                return respsucc
            else:
                respfail={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "No Results Found"}}
                return respfail
        else:
            respfail={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "Some Error in Request or Requested Items All Are Inactive"}}
            return respfail
    else:
        respfail={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "Error Encountered"}}
        return respfail
    
def stateCity_readAll(request_data):
    try:
        static_list = indian_states_and_cities
        state_city_list = [{"state": state, "cities": cities} for state, cities in indian_states_and_cities.items()]
        respsucc={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "Success", "status_code":200,"data":state_city_list}}
        return respsucc
    except:
        respfail={"response_id": request_data['request_id'], "response_for": "Read Many With Condition", "response_set_to": request_data['request_src'], "response": {"message": "No Results Found"}}
        return respfail
    
# resume_parsing 
# Read skills from a text file
async def read_skills_from_file(file_path):
    try:
        async with aiofiles.open(file_path, mode='r', encoding='utf-8') as file:
            skills = await file.read()
        return skills.splitlines()
    except Exception as e:
        print(f"Error reading skills file: {e}")
        return []
    
# Read education from a text file
async def read_education_details_from_file(file_path):
    try:
        async with aiofiles.open(file_path, mode='r', encoding='utf-8') as file:
            education_details = await file.readlines()
        unique_education_details = set()
        for detail in education_details:
            detail = detail.strip()
            if detail not in unique_education_details:
                unique_education_details.add(detail)
        return list(unique_education_details)
    except Exception as e:
        print(f"Error reading education details file: {e}")
        return []

# Clean phone number
def clean_phone_number(phone):
    return phone.replace("\n", "").strip()

# Deduplicate skills
def deduplicate_skills(skills):
    return list(set(skills))

# Extract contact number from resume text
async def extract_contact_number_from_resume(text):
    try:
        pattern = r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"
        match = re.search(pattern, text)
        if match:
            return clean_phone_number(match.group())
        return ''
    except Exception as e:
        print(f"Error extracting contact number: {e}")
        return ''

# Extract email from resume text
async def extract_email_from_resume(text):
    try:
        pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
        match = re.search(pattern, text)
        if match:
            return match.group()
        return ''
    except Exception as e:
        print(f"Error extracting email: {e}")
        return ''

# Extract Education_details  from education.txt file(which matches the resume)
async def extract_education_from_resume(text, education_file_path):
    try:
        education_patterns = await read_skills_from_file(education_file_path)

        education_found = []
        for skill in education_patterns:
            # Use word boundaries to ensure skill matches whole words
            if re.search(r'\b' + re.escape(skill) + r'\b', text, re.IGNORECASE):
                education_found.append(skill)

        return deduplicate_skills(education_found)
    except Exception as e:
        print(f"Error extracting skills: {e}")
        return []
# Extract the candidate skill from the skill.txt(which are present in the resume)
async def extract_skills_from_resume(text, skills_file_path):
    try:
        skills_patterns = await read_skills_from_file(skills_file_path)

        skills_found = []
        for skill in skills_patterns:
            # Use word boundaries to ensure skill matches whole words
            if re.search(r'\b' + re.escape(skill) + r'\b', text, re.IGNORECASE):
                skills_found.append(skill)

        return deduplicate_skills(skills_found)
    except Exception as e:
        print(f"Error extracting skills: {e}")
        return []
    
# Extract candidate_Name from the resume
async def extract_name(text):
    try:
        pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
        match = re.search(pattern, text)
        
        # If email address is found, extract the name from it
        if match:
            email = match.group()
            name = email.split('@')[0]  # Extract name before '@'
            # Remove numbers and symbols from the name
            name = re.sub(r'[^A-Za-z\s]', '', name)
            return name.strip()
        else:
            return ''
    except Exception as e:
        print(f"Error extracting name: {e}")
        return ''

# Extract phone number from resume text
async def extract_phone_from_resume(text):
    try:
        pattern = r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"
        match = re.search(pattern, text)
        if match:
            return clean_phone_number(match.group())
        return ''
    except Exception as e:
        print(f"Error extracting phone: {e}")
        return ''

# Extract links to Git and LinkedIn profiles from resume text
async def extract_social_links_from_resume(text):
    try:
        pattern_git = r"github.com/([A-Za-z0-9_-]+)"
        match_git = re.search(pattern_git, text)
        git_link = f"https://github.com/{match_git.group(1)}" if match_git else ''

        pattern_linkedin = r"linkedin.com/in/([A-Za-z0-9_-]+)"
        match_linkedin = re.search(pattern_linkedin, text)
        linkedin_link = f"https://linkedin.com/in/{match_linkedin.group(1)}" if match_linkedin else ''

        return {'git_link': git_link, 'linkedin_link': linkedin_link}
    except Exception as e:
        print(f"Error extracting social links: {e}")
        return {'git_link': '', 'linkedin_link': ''}

async def extract_text_from_pdf(file_content):
    try:
        # Open the PDF from the bytes content
        pdf_document = fitz.open(stream=file_content, filetype="pdf")
        text = ""
        for page_num in range(len(pdf_document)):
            page = pdf_document.load_page(page_num)
            text += page.get_text()
        return text
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return ''

async def resume_parser_function(request_data):
    try:
        file_content = request_data['file_content']
        skills_file_path = request_data['skills_file_path']
        education_file_path = request_data['education_file_path']
        request_id = request_data.get('request_id', '')
        request_src = request_data.get('request_src', '')

        # Ensure file_content is a string
        if isinstance(file_content, bytes):
            try:
                # Attempt to decode as text
                file_content = file_content.decode('utf-8')
            except UnicodeDecodeError:
                # If it's a PDF, extract the text from the PDF
                file_content = await extract_text_from_pdf(file_content)

#print the content for debugging perpose.
        # Print the file content for debugging
        # print("File Content:", file_content)
        # print("Skills File Path:", skills_file_path)
        # print("Education File Path:", education_file_path)

        name = await extract_name(file_content)
        email = await extract_email_from_resume(file_content)
        phone = await extract_phone_from_resume(file_content)
        skills = await extract_skills_from_resume(file_content, skills_file_path)
        social_link = await extract_social_links_from_resume(file_content)
        education = await extract_education_from_resume(file_content, education_file_path)

        response_success = {
            "response_id": request_id,
            "response_for": "Resume_Parser",
            "response_set_to": request_src,
            "response": {
                "message": "Fetched the data successfully!",
                "data": {
                    "name": name,
                    "email": email,
                    "phone": phone,
                    "skills": skills,
                    "Education": education,
                    "social_media_links":social_link
                }
            }
        }
        return response_success
    except Exception as e:
        print(f"Error in resume_parser_function: {e}")
        return {"error": f"An error occurred: {str(e)}"}
