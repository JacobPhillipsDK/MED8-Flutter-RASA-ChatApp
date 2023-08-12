import firebase_admin
from firebase_admin import credentials, messaging


class FireBaseSendNotification:
    def __init__(self, token_key: str, debug=False):
        self.cred = None  # You need a service account json file to place in here.
        self.debug = debug
        self.FCM_TOKEN_KEY = token_key
        self.initialize_app_to_firebase()

    def initialize_app_to_firebase(self):
        # Use a service account
        cred_obj = credentials.Certificate(self.cred)
        firebase_admin.initialize_app(cred_obj)
        print('######################################')
        print('Rasa Fire connecting initialized')

    def send_notification(self, title, body):
        print('Trying to send notification')
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body,
                image="link_to_image.png",
            ),
            token=self.FCM_TOKEN_KEY,
        )
        response = messaging.send(message, dry_run=False, app=None)
        print('Successfully sent message:', response)
        return response


if __name__ == '__main__':
    #
    firebase_obj = FireBaseSendNotification(token_key="device_token", debug=False)
    firebase_obj.send_notification(title='Random Fact By Jacob ', body=f'😎 😎 😎 😎 😎 😎 😎 😎 😎 😎')
