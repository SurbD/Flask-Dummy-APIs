from flask import Flask, abort, make_response, request, url_for
from flask_httpauth import HTTPBasicAuth

app = Flask(__name__)
auth = HTTPBasicAuth()

tasks = [
    {
        'id': 1,
        'title': 'Buy Groceries',
        'description': 'Milk, Cheese, Pizza, Fruit, Peanut Butter',
        'done': False
    },
    {
        'id': 2,
        'title': 'Learn Django',
        'description': "You need to read the docs, and follow Corey Schafer's Youtube Playlist",
        'done': False
    }
]

def make_public_task(task: dict) -> dict:
    new_task = {}
    for field in task:
        if field == 'id':
            new_task['uri'] = url_for('get_task', task_id=task['id'], _external=True)
        else:
            new_task[field] = task[field]
    return new_task

# User Authentication

@auth.get_password
def get_password(username):
    if username == 'admin':
        return 'python'
    return None

@auth.error_handler
def unauthorized():
    return make_response({'error': 'Unauthorized access'}, 401)

# End of User Authentication

@app.route('/todo/api/v1.0/tasks', methods=['GET'])
@auth.login_required
def get_tasks():
    # return {'tasks': tasks}
    return {"tasks": [make_public_task(task) for task in tasks]}

@app.route('/todo/api/v1.0/tasks/<int:task_id>', methods=['GET'])
def get_task(task_id):
    task = [task for task in tasks if task['id'] == task_id]
    # print(task)
    if len(task) == 0:
        abort(404)
    return {'task': make_public_task(task[0])}

@app.errorhandler(405)
def not_found(error):
    return make_response({'error': 'Not Allowed'}, 405)

@app.errorhandler(404)
def not_found(error):
    return make_response({'error': 'Not Found'}, 404)

@app.route('/todo/api/v1.0/tasks', methods=['POST'])
def create_task():
    if not request.json or not 'title' in request.json:
        abort(404)
    print(request.json)

    task = {
        'id': tasks[-1]['id'] + 1,
        'title': request.json['title'],
        'description': request.json.get('description', ""),
        'done': False
    }

    tasks.append(task)
    return {"task": make_public_task(task)}, 201

@app.route('/todo/api/v1.0/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id): # Add make public to this
    task = [task for task in tasks if task['id'] == task_id]

    if len(task) == 0:
        abort(404)

    if not request.json:
        abort(400)
    
    if 'title' in request.json and type(request.json['title']) != str:
        abort(400)

    if 'description' in request.json and type(request.json['description']) != str:
        abort(400)
    
    if 'done' in request.json and type(request.json['done']) != bool:
        abort(400)

    task[0]['title'] = request.json.get('title', task[0]['title'])
    task[0]['description'] = request.json.get('description', task[0]['description'])
    task[0]['done'] = request.json.get('done', task[0]['done'])

    return {'task': task[0]}

@app.route('/todo/api/v1.0/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    task = [task for task in tasks if task['id'] == task_id]

    if len(task) == 0:
        abort(404)
    
    tasks.remove(task[0])
    return {'deleted': True}, 204

if __name__ == '__main__':
    app.run(debug=True)

# Now Add Improvements like
#1 Real Database

#2 Multiple user handling service. 
#   if the system supports multiple users the authentication sent by the 
#   client could be used to obtain user specific todo lists. 
#   You'll have to create a second resource which will be the user. 
#   POST request would represent registering new user. A GET would return
#   the user information back to the client.

#3 Search filter with pagination option or get my completed task or 
# uncompleted tasks, search by first letter, sort to by letter / completed down, 
# if you like you can add time created and time completed but its not necessary
