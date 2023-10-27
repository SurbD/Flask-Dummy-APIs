from flask import Flask, abort, make_response
from flask_restful import Api, Resource, reqparse, fields, marshal
from flask_httpauth import HTTPBasicAuth


app = Flask(__name__)
api = Api(app)
auth = HTTPBasicAuth()

@auth.get_password
def get_password(username):
    if username == 'admin':
        return 'python'
    return None

@auth.error_handler
def unauthorized():
    return make_response({'errors': 'Unauthorized Access!'}, 403)

@app.errorhandler(500)
def server_error(error):
    return make_response({'error': 'Internal Server Error!'}, 500)


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

task_fields = {
    'title': fields.String,
    'description': fields.String,
    'done': fields.Boolean,
    'uri': fields.Url('task')
}   

class UserAPI(Resource):

    def get(self, id): pass
    def put(self, id): pass
    def delete(self, id): pass

# api.add_resource(UserAPI, '/users/<int:id>', endpoint='user')

# Since the TODO resource defines two URLs: /todo/api/v1.0/tasks for 
# the list of tasks, and /todo/api/v1.0/tasks/<int:id> for an individual tasks. 
# There two ways to make it accept the request sent to the Resource with the url. 
# One way is to -> create two resources, the Second ways is to add the url as path 
# of the single resource and Set the id in the routing each HTTP method to a 
# default of None then use and if-else condition to respond differently if the id 
# value is not added to the url.

class TaskListAPI(Resource):
    decorators = [auth.login_required]

    def __init__(self):
        self.regparse = reqparse.RequestParser()
        self.regparse.add_argument('title', type=str, required=True,
                                   help='No task title provided', location='json')
        self.regparse.add_argument('description', type=str, default="", location='json')
        super(TaskListAPI, self).__init__()

    def get(self):
        return {'task': [marshal(task, task_fields) for task in tasks]}

    def post(self):
        args = self.regparse.parse_args()

        task = {
            'id': tasks[-1]['id'] + 1 if len(tasks) > 0 else 1,
            'title': args['title'],
            'description': args['description'],
            'done': False
        }

        tasks.append(task)
        return {'task': marshal(task, task_fields)}, 201


class TaskAPI(Resource):
    decorators = [auth.login_required]

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('title', type=str, location='json')
        self.reqparse.add_argument('description', type=str, location='json')
        self.reqparse.add_argument('done', type=bool, location='json')
        super(TaskAPI, self).__init__()

    def get(self, id):
        task = [task for task in tasks if task['id'] == id]

        if len(task) == 0:
            abort(404)

        return {'task': marshal(task[0], task_fields)}

    def put(self, id):
        task = list(filter(lambda t: t['id'] == id, tasks))

        if len(task) == 0:
            abort(404)
        task = task[0]
        args = self.reqparse.parse_args()
        for k, v in args.items():
            if v != None:
                task[k] = v
        return {'task': marshal(task, task_fields)}

    def delete(self, id):
        task = [task for task in tasks if task['id'] == id]

        if len(task) == 0:
            abort(404)

        tasks.remove(task[0])
        return {'result': True}, 204


api.add_resource(TaskListAPI, '/todo/api/v1.0/tasks', endpoint='tasks')
api.add_resource(TaskAPI, '/todo/api/v1.0/tasks/<int:id>', endpoint='task')

if __name__ == "__main__":
    app.run(debug=True)