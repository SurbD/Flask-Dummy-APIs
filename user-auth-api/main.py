"""
User Authentication Web Service with SQLite Database and Flask-HTTPAuth
"""

from flask import Flask


app = Flask(__name__)


if __name__ == "__main__":
    app.run(debug=True)