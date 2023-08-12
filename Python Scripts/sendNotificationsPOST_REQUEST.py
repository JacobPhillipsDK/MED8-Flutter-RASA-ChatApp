import google.auth
import json
import requests
import google.auth.transport.requests
from google.oauth2 import service_account


device_token = "000000000"


# Some of this code take inspiration from :
# https://github.com/firebase/quickstart-python/blob/2c68e7c5020f4dbb072cca4da03dba389fbbe4ec/messaging/messaging.py#L26-L35
# https://firebase.google.com/docs/cloud-messaging/migrate-v1

class SendNotificationPOSTRequest:
    def __init__(self, device_token: str, debug=False):

        self.device_token = device_token
        self.body = ''
        self.debug = debug
        self.ProjectID = 'Project id fro the Firebase Project'

        # Copied from
        self.PROJECT_ID = f'{self.ProjectID}'
        self.BASE_URL = 'https://fcm.googleapis.com'
        self.FCM_ENDPOINT = 'v1/projects/' + self.PROJECT_ID + '/messages:send'
        self.FCM_URL = self.BASE_URL + '/' + self.FCM_ENDPOINT
        self.SCOPES = ['https://www.googleapis.com/auth/firebase.messaging']

    def request_access_token(self):
        """Retrieve a valid access token that can be used to authorize requests.
        :return: Access token.
        """
        credentials = service_account.Credentials.from_service_account_file(
            'service_account_you_get_from_firebase.json', scopes=self.SCOPES)
        request = google.auth.transport.requests.Request()
        credentials.refresh(request)
        return credentials.token

    def create_notificationPayload(self, body, title):
        # Define the notification payload
        payload = {
            "message": {
                "token": f"{self.device_token}",
                "android": {
                    "priority": "high"
                },
                "apns": {
                    "payload": {
                        "aps": {
                            "content-available": 1 # 0 or 1 dictates if the  notifications will be seen
                            # silently or not | 1 means silent
                        }
                    }
                },
                "data": {
                    "reply": "reply_direct",
                    "title": title,
                    "body": body,
                }
            }
        }

        return payload

    def send_notification_payload(self, payload):
        # Send the notification using the FCM API
        headers = {
            'Authorization': 'Bearer ' + self.request_access_token(),
            'Content-Type': 'application/json; UTF-8'
        }
        response = requests.post(url=self.FCM_URL, data=json.dumps(payload), headers=headers)

        # Check the response
        if self.debug:
            if response.status_code == 200:
                print(f"Notification sent successfully. With status code: {response.status_code}")
                print(json.decoder.JSONDecoder().decode(response.text))
                print(f'response code {response.status_code} : {response.reason}')
            else:
                print("Error sending notification: ", response.text)
                print(f'response code {response.status_code} : {response.reason}')



def main():
    notification_setup = SendNotificationPOSTRequest(device_token=device_token, debug=False)
    print(notification_setup.FCM_URL)

    payload = notification_setup.create_notificationPayload(title="This is the title of the notification", body="This is the body of the notification,")
    notification_setup.send_notification_payload(payload)
 

if __name__ == '__main__':
    main()
