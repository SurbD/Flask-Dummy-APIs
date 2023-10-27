from flask import Flask, make_response, url_for, abort
from flask_restful import Api, Resource, reqparse, marshal, fields
from flask_httpauth import HTTPBasicAuth
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

import os

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
api = Api(app)
auth = HTTPBasicAuth()

app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(basedir, 'todo_database.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


class UsersDB(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    tasks = db.relationship('TasksDB', backref='author', lazy='dynamic')

    def __repr__(self):
        return f"<UsersDB(username={self.username})>"

class TasksDB(db.Model):
    __tablename__ = 'tasks'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.String)
    done = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    def to_json(self):
        json_tasks = {
            'title': self.title,
            'description': self.description, # f"{self.description[:30]}..."
            'done': self.done,
            'author': self.author.username,
            'uri': url_for('task', id=self.id, _external=True)
        }
        return json_tasks

    def __repr__(self):
        return f"<TasksDB(title={self.title}, user_id={self.user_id})>"
    

# API Authentication

@auth.verify_password
def verify_password(username, password):
    # Query database to confirm user exists
    user = UsersDB.query.filter_by(username=username.lower()).first()

    if user and check_password_hash(user.password, password):
        return user

@auth.error_handler
def unauthorized():
    return make_response({"error": "Unauthorized Access"}, 403)

# End of API Authentication

@app.errorhandler(403)
def forbidden(error):
    return make_response({'error': 'Sorry, you cannot do that it is Forbidden'})

@app.errorhandler(405)
def not_allowed(error):
    return make_response({'error': 'Not Allowed'}, 405)

@app.errorhandler(404)
def not_found(error):
    return make_response({'error': 'Not Found'}, 404)

@app.errorhandler(422)
def wrong_param(error):
    return make_response({'error': "User with that name already exists!. Choose a another username"}, 422)

user_fields = {
    'uri': fields.Url('user'),
    'username': fields.String,
    'tasks': fields.Url('tasks')
}

# Task Resources

class User(Resource):
    # decorators = [auth.login_required]

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument("username", type=str, required=True, 
                                   help="Username field empty or invalid", location="json")
        self.reqparse.add_argument("password", type=str, required=True, 
                                   help="User password field empty or invalid", location="json")
        super().__init__()

    @auth.login_required
    def get(self):
        user = auth.current_user()
        return {"user": marshal(user, user_fields)}

    def post(self):
        args = self.reqparse.parse_args()

        check_user = UsersDB.query.filter_by(username=args['username'].lower()).first()
        if check_user:
            abort(422)

        hashed_password = generate_password_hash(args['password'])
        user = UsersDB(username=args['username'].lower(), password=hashed_password)

        db.session.add(user)
        db.session.commit()

        return {'user': marshal(user, user_fields)}, 201
    
    @auth.login_required
    def delete(self):
        user = auth.current_user()
        username = user.username

        db.session.delete(user)
        db.session.commit()

        return {'message': f'User "{username}" has been deleted and no longer exists'}, 204
    
    # Add PUT for updating and deleting user later


class TaskListAPI(Resource):
    decorators = [auth.login_required]

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('title', type=str, required=True,
                                   help='No task title provided', location='json')
        self.reqparse.add_argument('description', type=str, default="", location='json')
        super().__init__()

    def get(self):
        tasks = auth.current_user().tasks

        if not tasks:
            abort(404)
        return {"tasks": [task.to_json() for task in tasks]}
    
    def post(self):
        args = self.reqparse.parse_args()

        task = TasksDB(title=args['title'],
                         description=args.get('description', ''), author=auth.current_user())
        
        db.session.add(task)
        db.session.commit()

        return {'task': task.to_json()}, 201


class TaskAPI(Resource):
    decorators = [auth.login_required]

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('title', type=str, location='json')
        self.reqparse.add_argument('description', type=str, location='json')
        self.reqparse.add_argument('done', type=bool, location='json')
        super().__init__()

    def get(self, id):
        task = TasksDB.query.get(id)
        user = auth.current_user()

        if not task:
            abort(404)

        if task.author != user:
            abort(405)

        return {'task': task.to_json()}
    
    def put(self, id):
        task = TasksDB.query.get(id)

        if not task:
            abort(404)
        if task.author != auth.current_user():
            abort(405)

        put_actions = {
            'title': task.title,
            'description': task.description,
            'done': task.done
        }
        args = self.reqparse.parse_args()
        
        for key, value in args.items():
            if value != None:
                put_actions[key] = value

        db.session.commit()

        return {'task': task.to_json()}
    
    def delete(self):
        task = TasksDB.query.get(id)
        user = auth.current_user()

        if not task:
            abort(404)

        if task.author != user:
            abort(405)

        db.session.delete(task)
        db.session.commit()

        return {'message': f'Task "Id-{task.id}" has been deleted and no longer exists'}, 204

api.add_resource(User, "/todo/api/v2/user", endpoint="user")
api.add_resource(TaskListAPI, "/todo/api/v2/tasks", endpoint="tasks")
api.add_resource(TaskAPI, "/todo/api/v2/tasks/<int:id>", endpoint="task")

if __name__ == "__main__":
    app.run(debug=True)

# Search Filters