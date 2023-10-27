"""User Authentication Web Service with Flask Restful Extension and SQLite Database
Basic CRUD Operations - Add, Get, Update and Delete User Information."""

from flask import Flask, make_response, abort
from flask_restful import Api, Resource, reqparse

import os

from sqlite_db import UserDB

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
api = Api(app)
user_db = UserDB('database.db', basedir)


user_post_args = reqparse.RequestParser()
user_post_args.add_argument("username", type=str, help="Field cannot be empty", required=True)
user_post_args.add_argument("email", type=str, help="Field cannot be empty", required=True)
user_post_args.add_argument("password", type=str, help="Field cannot be empty", required=True)
user_post_args.add_argument("joined", type=str, help="Field cannot be empty", required=True)

def json_this_tuple(user_tuple: tuple):
    if user_tuple:
        keys = ('id', 'username', 'email', 'password', 'joined')
        json_output = dict(zip(keys, user_tuple))
        return json_output
    return {}

def make_public_user(user: dict) -> dict:
    new_user = {}

    for key in user:
        if key == 'id':
            new_user['uri'] = api.url_for(User, user_id=user[key], _external=True)
        elif key == 'password':
            new_user[key] = '*' * len(user[key])
        else:
            new_user[key] = user[key]
    return new_user

class User(Resource):
    """ User API Resource """

    def get(self, user_id=None):
        with user_db:
            if not user_id:
                result = user_db.get_users()
                json_users = [json_this_tuple(user) for user in result]
                return {"users": [make_public_user(user) for user in json_users]}
            result = user_db.get_user_by_id(user_id)
        return {'user': make_public_user(json_this_tuple(result))}
    
    def post(self):
        args = user_post_args.parse_args()

        with user_db:
            user_db.add_user(args)
            user = user_db.get_user_by_email(args['email'])
            json_user = json_this_tuple(user)
            return {'user': make_public_user(json_user)}, 201

    def delete(self, user_id=None):
        if not user_id:
            abort(404, "Specify ID of user to be deleted")

        with user_db:
            user_db.delete_user(user_id)
            return '', 204


api.add_resource(User, '/users/api/v1.0/user', '/users/api/v1.0/user/<int:user_id>')

if __name__ == "__main__":
    app.run(debug=True)