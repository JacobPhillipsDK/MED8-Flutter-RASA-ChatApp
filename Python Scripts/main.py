import json

import firebase_admin
import requests
from firebase_admin import credentials
from firebase_admin import db
import datetime
import time
from colorama import Fore, Back, Style
from sendNotificationsPOST_REQUEST import SendNotificationPOSTRequest


class FirebaseConnection:
    def __init__(self, jsonPath: str, debug=False):

        self.notification_setup = None
        self.jsonreader = None
        self.debug = debug
        if self.debug:
            print(Fore.CYAN + 'DEBUG MODE IS ENABLED', Style.RESET_ALL)

        self.jsonPath = jsonPath
        self.fcmToken = ""
        self.listener = None
        self.cred = " "
        self.database_url = ""
        self.username = ""
        self.rasa_url = "http://localhost:5005/webhooks/rest/webhook"
        self.firstname = " "
        self.lastname = " "
        self.fullname = " "
        self.sessionID = ''
        self.directReplyCounter = 0

        self.initialize_app_to_firebase()
        self.ref = db.reference('session/user')
        self.refDirectReply = db.reference('session/user/DirectReplyResponse')

        self.keep_reading_for_new_data = True

    def initialize_app_to_firebase(self):
        # Use a service account
        self.cred = None  # Place Json file here
        self.database_url = None # Get URL to the Firebase Database

        print(f'cred: {self.cred} database_url: {self.database_url} username: {self.username}')
        cred_obj = credentials.Certificate(self.cred)
        default_app = firebase_admin.initialize_app(cred_obj, {'databaseURL': self.database_url})
        print('######################################')
        print(Fore.RED + 'Rasa Fire connecting initialized', Style.RESET_ALL)

    def create_message(self, content_of_message):
        """
        Crafting message with message,username,timestamp
        """
        now = datetime.datetime.now()
        message = {
            'message': content_of_message,
            'username': "Edit me to change username",
            "timestamp": time.time(),
            "date": now.strftime('%Y-%m-%d %H:%M:%S.%f'),
        }
        return message

    def write_data_to_firebase(self, message, session_id):
        session_ref = self.ref.child(f'{session_id}/message')
        session_ref.push(message)
        # print(f'Message sent to firebase : {message}')
        return None

    def write_data_to_firebase_to_RASA(self, message, session_id):
        session_ref = self.ref.child(f'{session_id}/RASA/message/')
        session_ref.set(message)
        # print(f'Message sent to firebase : {message}')
        return None

    def setupNotification(self):
        self.notification_setup = SendNotificationPOSTRequest(device_token=self.getToken())

    def FirebaseGetToken(self):
        ref = db.reference(f'session/user/{self.sessionID}/FCMTOKEN')
        data = ref.get()
        self.fcmToken = data['FcmToken']

    def getToken(self):
        return self.fcmToken

    def send_message_firebase(self, message: str):

        self.setupNotification()

        message_to_send = self.create_message(content_of_message=message)

        self.write_data_to_firebase(message=message_to_send, session_id=self.sessionID)
        self.write_data_to_firebase_to_RASA(message=message_to_send, session_id=self.sessionID)

        payload = self.notification_setup.create_notificationPayload(title="ChatterBOT", body=message)
        self.notification_setup.send_notification_payload(payload)
        return message_to_send

    def listen_for_new_data(self):
        # Define the function to handle new data events
        print(Fore.CYAN + 'Listening for new session...', Style.RESET_ALL)
        self.ref.listen(self.listen_for_session)

    def get_userinfo(self):
        ref = db.reference(f'session/user/{self.sessionID}/UserInformation')
        data = ref.get()
        try:
            self.firstname = data['firstname']
            self.lastname = data['lastname']
        except (KeyError, TypeError):
            print(f'Userinformation not found in firebase {KeyError} , {TypeError}')
            # if error gets firstname and lastname from username
            ref = db.reference(f'session/user/{self.sessionID}')
            data = ref.get()
            username = data['username']
            firstname = username.split(' ')[0]
            lastname = username.split(' ')[1]
            self.firstname = firstname
            self.lastname = lastname
        # Here we listen for new messages in the session

    def add_sessionID_to_json(self):
        return self.jsonreader.setSessionID(sessionID=self.sessionID)

    def listen_for_session(self, event):
        data = event.data
        if data is not None and 'sessionID' in data and self.keep_reading_for_new_data is True:
            self.fullname = data['username']
            self.sessionID = data['sessionID']
            print('######################################')
            print(f'You are now connected to the session: {self.sessionID}')
            print('--------------------------------------')
            # self.add_sessionID_to_json()
            self.get_userinfo()
            self.FirebaseGetToken()  # Here we request the token from the server, so we can send notifications
            # Greeting message that says hello to the user when they first connect to the session
            greeting = str(f'Hej {self.firstname}, Jeg er {self.username}. Hvad kan jeg hjælpe dig med?😀')
            self.send_message_firebase(message=greeting)
            formatted_data = f"{Back.WHITE + self.username} ({Back.WHITE + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')}):{Style.RESET_ALL} {Fore.GREEN + greeting + Style.RESET_ALL}"
            print(formatted_data)
            ## Send the greeting message to firebase so the user can see it
            self.hook_to_session(session_id=self.sessionID)
            self.keep_reading_for_new_data = False

    def read_firebaseDirectReply(self):
        self.refDirectReply.listen(self.on_session_found_directReply)

    def hook_to_session(self, session_id):
        self.export_sessionID_FCMToken()
        ref = db.reference(f'session/user/{session_id}/message')
        ref.listen(self.on_session_found)

    def on_session_found_directReply(self, event):
        import orjson
        data = event.data
        if not self.keep_reading_for_new_data:
            try:
                json_data = orjson.dumps(data)
                parsed_data = orjson.loads(json_data)
                print(f'json_data: {parsed_data}')
                date = parsed_data['date']
                # Only print data timestamp is close to the time now
                print(f' date from direct reply: {date}')
                # current_time = datetime.datetime.fr
            except Exception as e:
                print(f'Error processing direct reply: {e}')
                print(f' Did not find any data in the direct reply saved in firebase')

    def on_session_found(self, event):
        data = event.data
        if not self.keep_reading_for_new_data:
            if data is not None and 'username' and 'message' in data:
                formatted_data = f"{Back.WHITE + data['username']} ({Back.WHITE + data['date']}):{Style.RESET_ALL} {Fore.GREEN + data['message'] + Style.RESET_ALL}"
                print(formatted_data)
                if self.debug:
                    print(f'self.fullname: {self.fullname}')
                    print(f'self.sessionID: {self.sessionID[:self.sessionID.index("-")]}')
                    print(f'username: {data["username"]}')
                ## This logic is needed so the bot will only answer back if the user writes to it. It checks if the username is the same as the sessionID,
                # if we did not do this, the bot would answer back to itself
                # We check if the username is the same as the sessionID, if it is, we know that the message is from the user
                if data['username'] == f'{self.firstname}-{self.lastname}':
                    user_message = data['message']
                    rasa_response = requests.post(url=self.rasa_url, json={"message": user_message}).json()
                    if rasa_response:

                        if self.debug:
                            print(f'{Fore.RED}RASA: {rasa_response}{Style.RESET_ALL}')
                        if 'name' in rasa_response[0]["text"]:
                            data = rasa_response[0]["text"].replace('name', self.firstname)
                            self.send_message_firebase(message=data)
                        else:
                            self.send_message_firebase(message=rasa_response[0]["text"].replace('\\n', '\n'))

                    else:
                        self.send_message_firebase(
                            message='ChatterBot kan desværre ikke forstå dig, skriv venligst noget andet')

    def export_sessionID_FCMToken(self):
        """Exports the sessionID and FCMToken to a json file"""
        try:
            sessionID = self.sessionID
            fcmToken = self.fcmToken
            data = {
                "sessionID": sessionID,
                "fcmToken": fcmToken
            }
            with open('sessionID_FCMToken.json', 'w') as outfile:
                json.dump(data, outfile)
        except Exception as e:
            print(f'Error exporting sessionID and FCMToken: {e}')


def main():
    jsonPath = 'jsonFiles/rasabotInformation.json'
    firebase_obj = FirebaseConnection(jsonPath=jsonPath, debug=False)
    firebase_obj.listen_for_new_data()


if __name__ == '__main__':
    main()
