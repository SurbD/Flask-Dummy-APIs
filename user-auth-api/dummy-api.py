from flask import Flask, request, make_response
from flask_restful import Api, Resource


app = Flask(__name__)
api = Api(app)

tasks = [
    {
        'id': 1,
        'title': 'Read Think and Grow Rich',
        'done': False
    },
    {
        'id': 2,
        'title': 'Read Flask Restful Docs',
        'done': False
    }
]

def public_task(task: dict) -> dict:
    new_task = {}
    for field in task:
        if field == 'id':
            new_task['uri'] = api.url_for(Todo, task_id=task['id'], _external=True)
        else:
            new_task[field] = task[field]
    return new_task

@app.errorhandler(404)
def not_found(error):
    return make_response({'error': 'Not Found'}, 404)

class Todo(Resource):
    """Task API Resource"""

    def get(self, task_id=None):
        if not task_id:
            return {"task": [public_task(task) for task in tasks]}
        
        task = [task for task in tasks if (task['id'] == task_id)]

        if task:
            return {"task": public_task(task[0])}
        
        return {"task": None}
    
        
    
api.add_resource(Todo, "/todo/api/v1.0/tasks/<int:task_id>", "/todo/api/v1.0/tasks")
# api.add_resource(Todo, "/todo/api/v1.0/tasks/<int:task_id>")

if __name__ == "__main__":
    app.run(debug=True)

# I think building APIs without flask-restful has 
# it's advantages like customizable uris but i'm still 
# looking lets see which one is better with or without the extension.