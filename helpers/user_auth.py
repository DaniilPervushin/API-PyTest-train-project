import requests
from json import dumps
from config import BASE_URL


class UserAuthentication:
    def __init__(self, email, password):
        self.email = email
        self.password = password

    def user_authentication(self, email, password):
        headers = {
            'Content-Type': 'application/json'
        }
        payload = dumps({"email": email, "password": password})
        response = requests.post(f'{BASE_URL}/login', data=payload, headers=headers)
        response_body = response.json()

        return response_body['access_token']

