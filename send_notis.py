#send_notis.py
import http.client, urllib
from config import Pushover
#import pushover
#import requests

APP_TOKEN = Pushover.APP_TOKEN
USER_KEY = Pushover.USER_KEY


def send_noti(MESSAGE, username):
    exceptions = ("alex","admin")

    if username not in exceptions:
        conn = http.client.HTTPSConnection("api.pushover.net:443")

        conn.request("POST", "/1/messages.json",
            urllib.parse.urlencode({
            "token": APP_TOKEN,
            "user": USER_KEY,
            "message": MESSAGE,
        }), { "Content-type": "application/x-www-form-urlencoded" })

        conn.getresponse()


# En deshuso, no funciona correctamente
def send_noti___(MESSAGE, username, image_path=None):
    exceptions = ("alex")

    if username not in exceptions:
        conn = http.client.HTTPSConnection("api.pushover.net:443")

        if image_path:
            with open(image_path, 'rb') as image_file:
                image_data = image_file.read()

            boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
            headers = {
                'Content-type': f'multipart/form-data; boundary={boundary}',
            }

            body = (
                f'--{boundary}\r\n'
                f'Content-Disposition: form-data; name="token"\r\n\r\n{APP_TOKEN}\r\n'
                f'--{boundary}\r\n'
                f'Content-Disposition: form-data; name="user"\r\n\r\n{USER_KEY}\r\n'
                f'--{boundary}\r\n'
                f'Content-Disposition: form-data; name="message"\r\n\r\n{MESSAGE}\r\n'
                f'--{boundary}\r\n'
                f'Content-Disposition: form-data; name="attachment"; filename="image.png"\r\n'
                f'Content-Type: image/png\r\n\r\n'
                f'{image_data}\r\n'
                f'--{boundary}--\r\n'
            )

            conn.request("POST", "/1/messages.json", body, headers)
        else:
            conn.request("POST", "/1/messages.json",
                         urllib.parse.urlencode({
                             "token": APP_TOKEN,
                             "user": USER_KEY,
                             "message": MESSAGE,
                         }), { "Content-type": "application/x-www-form-urlencoded" })

        response = conn.getresponse()
        return response.status, response.reason
