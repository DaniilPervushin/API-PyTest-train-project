import requests
from json import dumps
from config import BASE_URL
from user_auth import UserAuthentication


class UserProfileUpdate:
    def __init__(self, email, password, name, username, phone):
        # self.access_token = access_token
        self.email = email
        self.password = password
        self.name = name
        self.username = username
        self.phone = phone

    def update_user_profile(self, email, password):
        access_token = UserAuthentication(email, password)
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {access_token.user_authentication(email, password)}'
        }
