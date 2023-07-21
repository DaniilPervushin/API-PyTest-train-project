import pymysql
import re
from pymysql import cursors, Error, Warning
from app import app
from config import mysql, jwt
from flask import jsonify, make_response
from flask import flash, request
from flask_login import login_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from functools import wraps
from flask_jwt_extended import create_access_token, jwt_required, create_refresh_token, get_jwt_identity, decode_token

#validation for email
global e_validation
e_validation = re.compile(r'([A-Za-z0-9]+[.-_])*[A-Za-z0-9]+@[A-Za-z0-9-]+(\.[A-Z|a-z]{2,})+')

# Test rout
@app.route('/')
def up():
    return jsonify(message="What's up?:)")


# Registration
@app.route('/register', methods=['POST'])
def user_register():
    _json = request.json
    _email = _json['email']
    _password = generate_password_hash(_json['password'], method='sha256')
    conn = mysql.connect()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    # Email Format Validation
    if not re.fullmatch(e_validation, _email):
        return jsonify(message='Your e-mail is not valid.'), 400
    # Password len check
    if len(_json['password']) < 6:
        return jsonify(message="Password must be at least 6 symbols."), 400
    try:
        sqlQuery = 'INSERT INTO users(email, password) VALUES (%s, %s)'
        bindData = (_email, _password)
        cursor.execute(sqlQuery, bindData)
        conn.commit()
        respone = jsonify(message= 'You have successfully registered. ' \
                                   'Now you can use your email and password to log in to the app.')
        return respone
    except pymysql.Error as e:
        if e.args[0] == 1062:
            return jsonify(message="User with this email already exist."), 400
    finally:
        cursor.close()
        conn.close()


@app.route('/login', methods=['POST'])
def login():
    _json = request.json
    _email = _json['email']
    _password = _json['password']
    conn = mysql.connect()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    user = cursor.execute("SELECT email, password, id, is_admin FROM users WHERE email=%s", _email)
    fetch_user = cursor.fetchall()
    if not user or not check_password_hash(fetch_user[0]['password'], _password):
        return jsonify(message='Please check your email and password and try again.'), 401
    if user and check_password_hash(fetch_user[0]['password'], _password):
        access_token = create_access_token(identity={"id":fetch_user[0]['id'],"is_admin":fetch_user[0]['is_admin']}, expires_delta=timedelta(seconds=900))
        refresh_token = create_refresh_token(identity={"id":fetch_user[0]['id'],"is_admin":fetch_user[0]['is_admin']})
        decode = decode_token(access_token)
        return jsonify(message="You've been successfully logged in!", access_token=access_token, refresh_token=refresh_token), 200

    cursor.close()
    conn.close()


@app.route('/profile', methods=['GET'])
@jwt_required()
def current_user_profile():
    decoded = decode_token(request.headers['Authorization'][7:])
    current_user_id = decoded['sub']['id']
    conn = mysql.connect()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    cursor.execute('SELECT email, name, username, phone FROM users WHERE id=%s', current_user_id)
    user_data = cursor.fetchall()
    return user_data


@app.route('/profile', methods=['PUT'])
@jwt_required()
def current_user_profile_update():
    decoded = decode_token(request.headers['Authorization'][7:])
    current_user_id = decoded['sub']['id']
    _json = request.json
    _email = _json['email']
    _name = _json['name']
    _username = _json['username']
    _phone = _json['phone']
    # Email format validation
    if not re.fullmatch(e_validation, _email):
        return jsonify(message='Your e-mail is not valid.'), 400

    conn = mysql.connect()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    # Is email unique check.
    print([current_user_id, _email])
    cursor.execute('SELECT count(*) as count from users where id != %s and email = %s', [current_user_id, _email])
    if cursor.fetchall()[0]['count'] > 0:
        return jsonify(message='This email address is in use by another user.'), 403
    # Is username unique check.
    print(_username is not None)
    if _username is not None:
        cursor.execute('SELECT count(*) as count from users where id != %s and username = %s', [current_user_id, _username])
        if cursor.fetchall()[0]['count'] > 0:
            return jsonify(message='This username is already taken by another user.'), 403
    sqlQuery = "UPDATE users SET email=%s, username=%s, name=%s, phone=%s WHERE id=%s"
    bindData = (_email, _username, _name, _phone, current_user_id)
    cursor.execute(sqlQuery, bindData)
    conn.commit()
    responce = jsonify(message='Your Profile Was Successfully Updated!')
    return responce, 200


@app.route('/change_password', methods=['PUT'])
@jwt_required()
def current_user_change_password():
    try:
        decoded = decode_token(request.headers['Authorization'][7:])
        current_user_id = decoded['sub']['id']
        _json = request.json
        _old_password = _json['old_password']
        _new_password = _json['new_password']
        # Check password len
        if _new_password is None:
            return  jsonify(message="Password can't be empty.")
        if len(_new_password) < 6:
            return jsonify(message="Password must be at least 6 symbols.")
        conn = mysql.connect()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute("SELECT password FROM users WHERE id=%s", current_user_id)
        fetch_password = cursor.fetchall()
        # check that old password is valid
        if not check_password_hash(fetch_password[0]['password'], _old_password):
            return jsonify(message="Old password is not valid."), 403
        # check that new password is unique
        elif _old_password == _new_password:
            return jsonify(message="You may not reuse the same password again."), 403
        else:
            sqlQuery = "UPDATE users SET password=%s WHERE id=%s"
            bindData = (generate_password_hash(_new_password, method='sha256'), current_user_id)
            cursor.execute(sqlQuery, bindData)
            conn.commit()
            return jsonify(message='You successfully changed your password'), 200
    except Exception as e:
        print(e)
    # finally:
    #     cursor.close()
    #     conn.close()


@app.route('/delete', methods=['DELETE'])
@jwt_required()
def user_profile_delete():
    decoded = decode_token(request.headers['Authorization'][7:])
    current_user_id = decoded['sub']['id']
    current_user_is_admin = decoded['sub']['is_admin']
    print(current_user_is_admin)
    if current_user_is_admin ==1:
        return jsonify(message="Admin can't delete his profile. Please contact the db administrator."), 403
    try:
        conn = mysql.connect()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute("DELETE FROM users WHERE id=%s", current_user_id)
        conn.commit()
        return jsonify(message='Your profile has been deleted. \
You can always register yourself a new one.'), 200
    except Exception as e:
        print(e)
    finally:
        cursor.close()
        conn.close()




@app.route('/users', methods=['GET'])
@jwt_required()
def user_list():
    try:
        conn = mysql.connect()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute("SELECT id, email, name, username, phone FROM users WHERE is_admin != True")
        empRows = cursor.fetchall()
        responce = jsonify({'users' : empRows})
        responce.status_code = 200
        return responce
    except Exception as e:
        print(e)
    finally:
        cursor.close()
        conn.close()


@app.route('/user_update/<user_id>', methods=['PUT'])
@jwt_required()
def user_update(user_id):
    decoded = decode_token(request.headers['Authorization'][7:])
    current_user_is_admin = decoded['sub']['is_admin']
    if current_user_is_admin == 0:
        return jsonify(message="You don't have permission to perform this action."), 403
    try:
        _json = request.json
        _email = _json['email']
        _username = _json['username']
        _name = _json['name']
        _phone = _json['phone']
        conn = mysql.connect()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        # Is email unique check.
        cursor.execute("SELECT count(*) as count from users where id = %s and email != %s", user_id, _email)
        if cursor.fetchall():
            return jsonify(message='This email address is in use by another user.'), 403
        # Is username unique check.
        cursor.execute("SELECT count(*) as count from users where id = %s and username != %s", user_id, _username)
        if cursor.fetchall():
            return jsonify(message='This username is already taken by another user.'), 403
        if _name and _email and _username and _name and _phone and request.method == 'PUT':
            conn = mysql.connect()
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            sqlQuery = "UPDATE users SET email=%s, username=%s, name=%s, phone=%s  WHERE id=%s"
            bindData = (_email, _username, _name, _phone, user_id)
            cursor.execute(sqlQuery, bindData)
            conn.commit()
            responce = jsonify(message='Your profile was successfully updated'),200
            return responce
    except Exception as e:
        print(e)
    finally:
        cursor.close()
        conn.close()


@app.route('/delete/<user_id>', methods=['DELETE'])
@jwt_required()
def delete_user(user_id):
    try:
        conn = mysql.connect()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        decoded = decode_token(request.headers['Authorization'][7:])
        current_user_is_admin = decoded['sub']['is_admin']
        if current_user_is_admin == 0:
            return jsonify(message="You don't have permission to perform this action."), 403
        cursor.execute("SELECT count(*) as count from users where id = %s", user_id)
        if cursor.fetchall()[0]['count'] == 0:
            return jsonify(message='There are no records found in the system with this ID'), 404
        cursor.execute("SELECT is_admin FROM users WHERE id=%s", user_id)
        if cursor.fetchall()[0]['is_admin']:
            return jsonify(message="Admin can't delete admins profile. Please contact the db administrator."), 403
        cursor.execute("DELETE FROM users WHERE id=%s", user_id)
        conn.commit()
        return jsonify(message='The entry was successfully deleted.'), 200
    except Exception as e:
        print(e)
    finally:
        cursor.close()
        conn.close()


@app.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh_user_toke():
    identity = get_jwt_identity()
    new_access_token = create_access_token(identity=identity)
    return jsonify(access_token=new_access_token), 200




if __name__ == "__main__":
    app.run(debug=True)
