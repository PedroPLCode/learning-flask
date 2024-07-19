from app import GOOGLE_CLIENT_ID, GOOGLE_SECRET_KEY, app, db, mail
from app.utils import *
from flask import jsonify, request
from flask_mail import Message
from datetime import datetime as dt
from flask_cors import cross_origin
from datetime import datetime, timedelta, timezone
from app.models import User
from flask_jwt_extended import create_access_token,get_jwt,get_jwt_identity, \
                               unset_jwt_cookies, jwt_required
import json
import requests
from dotenv import load_dotenv

@app.after_request
def refresh_expiring_jwts(response):
    try:
        exp_timestamp = get_jwt()["exp"]
        now = datetime.now(timezone.utc)
        target_timestamp = datetime.timestamp(now + timedelta(minutes=30))
        if target_timestamp > exp_timestamp:
            access_token = create_access_token(identity=get_jwt_identity())
            data = response.get_json()
            if type(data) is dict:
                data["access_token"] = access_token 
                response.data = json.dumps(data)
        return response
    except (RuntimeError, KeyError):
        return response

    
@app.route('/token', methods=["POST"])
@cross_origin()
def create_token():
    login = request.json.get("login", None)
    password = request.json.get("password", None)
    user = User.query.filter_by(login = login).first_or_404()
    
    if user and user.verify_password(password):
        access_token = create_access_token(identity=login)
        response = {"access_token": access_token}
        user.last_login = dt.utcnow()
        db.session.commit()
        return response
    else:
        return {"msg": "Wrong email or password"}, 401


@app.route('/google_token', methods=['POST'])
@cross_origin()
def create_google_token():
    auth_code = request.get_json().get('code')
    
    if not auth_code:
        return jsonify({"msg": "Authorization code is missing"}), 400

    data = {
        'code': auth_code,
        'client_id': GOOGLE_CLIENT_ID, 
        'client_secret': GOOGLE_SECRET_KEY,
        'redirect_uri': 'postmessage',
        'grant_type': 'authorization_code'
    }

    try:
        response = requests.post('https://oauth2.googleapis.com/token', data=data)
        response.raise_for_status()  # Raise HTTPError for bad responses
        response_data = response.json()
    except requests.exceptions.RequestException as e:
        return jsonify({"msg": str(e)}), 500

    headers = {
        'Authorization': f'Bearer {response_data["access_token"]}'
    }

    try:
        google_user_info = requests.get('https://www.googleapis.com/oauth2/v3/userinfo', headers=headers).json()
    except requests.exceptions.RequestException as e:
        return jsonify({"msg": str(e)}), 500

    user = User.query.filter_by(email=google_user_info['email'], google_user=True).first()
    
    if not user:
        try:
            new_google_user = User(
                login=google_user_info.get('email'),
                google_user=True,
                email=google_user_info.get('email'),
                name=google_user_info.get('given_name', ''),
                about=google_user_info.get('name', ''),
                last_login=dt.utcnow(),
                picture=google_user_info.get('picture', ''),
            )
            db.session.add(new_google_user)
            db.session.commit()
            user = new_google_user
            
            email_subject = 'Welcome in FoodApp test'
            email_body = f'Hello {new_google_user.name.title()}'
            send_email(new_google_user.email, email_subject, email_body)
    
        except Exception as e:
            return jsonify({"msg": str(e)}), 500
    else:
        user.last_login = dt.utcnow()
        db.session.commit()

    access_token = create_access_token(identity=google_user_info['email'])
    response = {"access_token": access_token}
    
    return jsonify(response), 200


@app.route("/logout", methods=["POST"])
@cross_origin()
def logout():
    response = jsonify({"msg": "logout successful"})
    unset_jwt_cookies(response)
    return response