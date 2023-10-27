from flask import Flask, abort, make_response, request, url_for
from flask_httpauth import HTTPBasicAuth
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
# from flask_bcrypt import Bcrypt

import os

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
auth = HTTPBasicAuth()
# bcrypt = Bcrypt(app)

app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(basedir, 'database.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class TaskDB(db.Model):
    __tablename__ = 'tasks'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.String)
    done = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    def to_json(self):
        json_task = {
            'title': self.title,
            'description': self.description,
            'done': self.done,
            'uri': url_for('get_task', task_id=self.id, _external=True),
            'author': UserDB.query.get(self.user_id).username
        }
        return json_task
    
    def __repr__(self):
        return f"<TaskDB(title={self.title})"


class UserDB(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), nullable=True, unique=True)
    password = db.Column(db.String(60), nullable=True)
    tasks = db.relationship('TaskDB', backref='user', lazy='dynamic')

    # Add to json method for both db models

    def to_json(self):
        json_user = {
            'uri': url_for('get_user', _external=True),
            'username': self.username,
            'tasks_uri': url_for('get_user_tasks', user_id=self.id, _external=True)
        }
        return json_user
    
    def __repr__(self):
        return f"<UserDB(username={self.username})"


def make_public_task(task: object) -> dict:
    public_task = {
        'title': task.title,
        'description': task.description,
        'done': task.done,
        'uri': url_for('get_task', task_id=task.id, _external=True)
    }
    return public_task
# User Authentication

@auth.verify_password
def verify_password(username, password):
    user = UserDB.query.filter_by(username=username.lower()).first()
    if user and check_password_hash(user.password, password):
        # user [auth.current_user() to get return value]
        return user


@auth.error_handler
def unauthorized():
    return make_response({'error': 'Unauthorized access'}, 403)

# End of User Authentication

@app.errorhandler(405)
def not_found(error):
    return make_response({'error': 'Not Allowed'}, 405)

@app.errorhandler(422)
def wrong_param(error):
    return make_response({'error': "User with that name already exists!. Choose a another username"}, 422)

@app.errorhandler(404)
def not_found(error):
    return make_response({'error': 'Not Found'}, 404)

# API VIEW FUNCTIONS

@app.route('/todo/api/v1.0/user', methods=['GET'])
@auth.login_required
def get_user():
    """Return the user json user try get user info when 
    login successful don't use id, because the user might not know the id"""

    user = auth.current_user()
    print(user.username)

    return {"user": user.to_json() if user else None}

@app.route('/todo/api/v1.0/user/<string:username>/delete', methods=['DELETE'])
@auth.login_required
def delete_user(username):
    user = UserDB.query.filter_by(username=username).first()

    if not user or user.username != auth.current_user().username:
        print('Aborting')
        abort(405)

    db.session.delete(user)
    db.session.commit()
    return '', 204
    

@app.route('/todo/api/v1.0/users', methods=['POST'])
def create_user():
    if not request.json or not 'username' in request.json \
        or not 'password' in request.json:
        abort(404)

    if 'username' in request.json and type(request.json['username']) != str:
        abort(400)

    if 'password' in request.json and type(request.json['password']) != str:
        abort(400)

    if 'username' in request.json:
        user = UserDB.query.filter_by(username=request.json['username']).first()
        if user:
            abort(422)
    

    hashed_password = generate_password_hash(request.json['password'])
    user = UserDB(username=request.json['username'.lower()], password=hashed_password)

    db.session.add(user)
    db.session.commit()

    # return {'done': True}, 201 
    return user.to_json(), 201

@app.route('/todo/api/v1.0/user/<int:user_id>', methods=['GET'])
@auth.login_required
def get_user_tasks(user_id):
    user = UserDB.query.get(user_id)

    if not user:
        abort(404)

    user_tasks_json = [task.to_json() for task in user.tasks.all()]
    return user_tasks_json


@app.route('/todo/api/v1.0/tasks', methods=['GET'])
@auth.login_required
def get_tasks():
    tasks = auth.current_user().tasks

    if not tasks:
        abort(404)
    # return {'tasks': tasks}
    # return {"tasks": [make_public_task(task) for task in tasks]}
    return {"tasks": [task.to_json() for task in tasks]}

@app.route('/todo/api/v1.0/task/<int:task_id>', methods=['GET'])
@auth.login_required
def get_task(task_id):
    task = TaskDB.query.get(task_id)

    if not task:
        abort(404)
    
    # return {'task': make_public_task(task)}
    return {'task': task.to_json()}

@app.route('/todo/api/v1.0/tasks', methods=['POST'])
@auth.login_required
def create_task():
    print('got in tasker')
    if not request.json or not 'title' in request.json:
        abort(404)

    task = TaskDB(
        title=request.json.get('title'),
        description=request.json.get('description', ''),
        user=auth.current_user()
    )

    db.session.add(task)
    db.session.commit()
    return {"task": make_public_task(task)}, 201

@app.route('/todo/api/v1.0/tasks/<int:task_id>', methods=['PUT'])
@auth.login_required
def update_task(task_id): # Add make public to this
    task = TaskDB.query.get(task_id)

    if not task:
        abort(404)

    if not request.json:
        abort(400)
    
    if 'title' in request.json and type(request.json['title']) != str:
        abort(400)

    if 'description' in request.json and type(request.json['description']) != str:
        abort(400)
    
    if 'done' in request.json and type(request.json['done']) != bool:
        abort(400)

    task.title = request.json.get('title', task.title)
    task.description = request.json.get('description', task.description)
    task.done = request.json.get('done', task.done)

    db.session.commit()

    return {'task': make_public_task(task)}

@app.route('/todo/api/v1.0/tasks/<int:task_id>', methods=['DELETE'])
@auth.login_required
def delete_task(task_id):
    task = TaskDB.query.get(task_id)

    if not task:
        abort(404)
    
    db.session.delete(task)
    db.session.commit()

    return {'deleted': True}, 204

# Search Filter endpoints 

@app.route('/todo/api/v1.0/tasks/search', methods=['GET', 'POST'])
def search_filter():
    filter_options = ['task_status', 'first_letter']

    result = {'args-in': None}
    args = request.args
    for key in args:
        if key in filter_options:
            result = {'args-in': key}
            break
    # data = request.json
    print(args)

    return {'arg': f'args-{args}', 'result': result}
    # return {'arg': f'args-{args}', 'json': f'json data-{data}'}

if __name__ == '__main__':
    app.run(debug=True)

# Now Add Improvements like
#1 Real Database(Done)

#2 Multiple user handling service. 
#   if the system supports multiple users the authentication sent by the 
#   client could be used to obtain user specific todo lists. 
#   You'll have to create a second resource which will be the user. 
#   POST request would represent registering new user. A GET would return
#   the user information back to the client.

#3 Search filter with pagination option or get my completed task or 
# uncompleted tasks, search by first letter, sort to by letter / completed down, 
# if you like you can add time created and time completed but its not necessary
