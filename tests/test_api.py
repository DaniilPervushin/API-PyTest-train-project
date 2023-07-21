import pytest
import requests
from assertpy.assertpy import assert_that

from config import BASE_URL
from json import dumps
from uuid import uuid4
from helpers.user_auth import UserAuthentication

login_params = {
    ("daniilpervushin.pl@gmail.com", "qwer1234", 200, "You've been successfully logged in!"),
    ("daniilpervushin.pl@gmail.com", "qwer1234!", 401, "Please check your email and password and try again."),
    ("daniilpervushin.pl@gmaill.com", "qwer1234", 401, "Please check your email and password and try again.")
}

registration_params = {
    (f"{str(uuid4()).replace('-', '_')}@test.com", "qwer12", 200, "You have successfully registered. " \
                                                                  "Now you can use your email and password " \
                                                                  "to log in to the app."),
    (f"daniilpervushin.pl@gmail.com", "qwer1234", 400, "User with this email already exist."),
    (f"{str(uuid4()).replace('-', '_')}@test.com", "qwer1", 400, "Password must be at least 6 symbols."),
    (f"{str(uuid4()).replace('-', '_')}test.com", "qwer12", 400, "Your e-mail is not valid.")
}

view_profile_params = {
    ("daniilpervushin.pl@gmail.com", "qwer1234", 200, None, None, None)
}


@pytest.mark.smoke
def test_check_server_is_up():
    response = requests.get(BASE_URL)
    response_text = response.json()

    assert_that(response.status_code).is_equal_to(200)
    assert_that(response_text['message']).is_equal_to("What's up?:)")


@pytest.mark.parametrize('email, password, status_code, message', login_params)
def test_login_existing_user(email, password, status_code, message):
    headers = {
        'Content-Type': 'application/json'
    }
    payload = dumps({"email": email, "password": password})
    response = requests.post(f'{BASE_URL}/login', data=payload, headers=headers)
    response_text = response.json()
    assert_that(response.status_code).is_equal_to(status_code)
    assert_that(response_text['message']).is_equal_to(message)


@pytest.mark.parametrize('email, password, status_code, message', registration_params)
def test_registration(email, password, status_code, message):
    headers = {
        'Content-Type': 'application/json'
    }
    payload = dumps({"email": email, "password": password})
    response = requests.post(f'{BASE_URL}/register', data=payload, headers=headers)
    response_text = response.json()
    assert_that(response.status_code).is_equal_to(status_code)
    assert_that(response_text['message']).is_equal_to(message)


@pytest.mark.parametrize('email, password, status_code, name, phone, username', view_profile_params)
def test_view_user_profile(email, password, status_code, name, phone, username):
    access_token = UserAuthentication(email, password)
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {access_token.user_authentication(email, password)}'
    }

    response = requests.get(f'{BASE_URL}/profile', headers=headers)
    response_text = response.json()
    print(response_text)
    assert_that(response.status_code).is_equal_to(status_code)
    assert_that(response_text[0]['email']).is_equal_to(email)
    assert_that(response_text[0]['name']).is_equal_to(name)
    assert_that(response_text[0]['phone']).is_equal_to(phone)
    assert_that(response_text[0]['username']).is_equal_to(username)


def test_user_profile_update(email, password, status_code, name, phone, username):
    access_token = UserAuthentication(email, password)
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {access_token.user_authentication(email, password)}'
    }
    payload = dumps({"email": email, "password": password, "phone": phone, })
    response =