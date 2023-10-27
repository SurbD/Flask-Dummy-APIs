from flask import Flask, session
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
# app.config['SECRET_KEY'] = 'super secret key'
auth = HTTPBasicAuth()

users = {
        "joan": generate_password_hash("hello"),
        "jason": generate_password_hash("cringe")
    }

@auth.verify_password
def verify_password(username, password):
    if username in users and check_password_hash(users.get(username), password):
        # session['user'] = [(k,v) for k,v in users.items() if k == username]
        return 'Admin shit'

@app.route("/")
@auth.login_required
def index():
    print(session.get('user'))
    return "Hello, {}!".format(auth.current_user().title())

if __name__ == "__main__":
    app.run(debug=True)
