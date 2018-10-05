
# coding: utf-8

# In[119]:

from __future__ import print_function
# get_ipython().run_line_magic('config', 'IPCompleter.greedy=True')
from googleapiclient.discovery import build
import googleapiclient.discovery
import google.oauth2.credentials
from httplib2 import Http
from oauth2client import file, client, tools
from receipt_detector import is_receipt
from datetime import datetime,timedelta
from dateutil.parser import parse
import pytz


# In[62]:


# If modifying these scopes, delete the file token.json.
SCOPES = 'https://www.googleapis.com/auth/gmail.readonly'


# In[115]:


# store = file.Storage('token.json')
# creds = store.get()
# if not creds or creds.invalid:
#     flow = client.flow_from_clientsecrets('credentials.json', SCOPES)
#     creds = tools.run_flow(flow, store)
# service = build('gmail', 'v1', http=creds.authorize(Http()))


# In[125]:


user_id =  'me'
label_id_one = 'INBOX'
label_id_two = 'UNREAD'
    
def get_messages(service, date_query):
    
    messages = []
    try:
        response = service.users().messages().list(userId=user_id,labelIds=[label_id_one],q=date_query).execute()
        
        if 'messages' in response:
          messages.extend(response['messages'])

        while 'nextPageToken' in response:
          page_token = response['nextPageToken']
          response = service.users().messages().list(userId=user_id,labelIds=[label_id_one],q=date_query,
                                             pageToken=page_token).execute()
          messages.extend(response['messages'])
          
    except Exception as error:
        print ('An error occurred: %s' % error)
    return messages


# In[111]:


def check_for_receipt(message):
    payld = message['payload'] # get payload of the message 
    headr = payld['headers'] # get header of the payload

    
    for one in headr: # getting the Subject
        if one['name'] == 'Subject':
            msg_subject = one['value']
            if is_receipt(msg_subject.lower()):
                return True,msg_subject,payld
    return False,None,None


# In[112]:


# import base64 
# import email

# def get_message_body(message):
# #     try:
# #     message = service.users().messages().get(userId=user_id, id=msg_id, format='raw').execute()
#     bodies = []
    
#     if message['payload']['body']['size'] > 0:
#         return message['payload']['body']
#     elif 'parts' in message['payload'] and len(message['payload']['parts']) > 0:
#         for part in message['payload']['parts']:
#             bodies.append(part['body']['data'])
            
#     for body in bodies:
#         msg_str = base64.urlsafe_b64decode(body.encode('ASCII')).decode()



# m = service.users().messages().list(userId=user_id,labelIds=[label_id_one]).execute()
# msg = service.users().messages().get(userId=user_id, id=m['messages'][10]['id']).execute()
# # print(msg)
# print (get_message_body(msg)) 
# # check_for_receipt(msg)


# In[126]:


import time


def get_receipts(credentials, date_range):
    
    print(type(credentials))
    creds = google.oauth2.credentials.Credentials(**credentials)
    service = googleapiclient.discovery.build('gmail', 'v1', credentials=creds)
    
    receipts = []
    def on_complete(request_id, response, exception):
        if exception is not None:
            print("error")
            print(exception)
        else:
            got_receipt, subject,payload = check_for_receipt(response)
            
            if got_receipt:
                receipt = {
                    'subject' : subject,
                    # 'payload' : payload
                }
                receipts.append(receipt)
            
    messages = get_messages(service,date_range)
    print(len(messages))
    chunk_size = 250
    start = 0
    while start <= len(messages):

        start_time = time.time()
        batch = service.new_batch_http_request()
        end = start + chunk_size

        if end >= len(messages):
            end = len(messages) - 1

        for i in range(start,end):
            batch.add(service.users().messages().get(userId=user_id, id=messages[i]['id']), callback=on_complete)

        batch.execute()
        end_time = time.time()
        # google only allows 250 calls per second although 500 seems to work
        wait = max(1 - (end_time - start_time),0)

        time.sleep(wait)
        start += chunk_size
    print('done')
    return receipts
        
# get_receipts('after:2018/09/03 before:2018/10/3')

