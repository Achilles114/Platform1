from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# Create Flask app instance
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///db.sqlite3"
app.config['SECRET_KEY'] = "your_secret_key"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['DEBUG'] = True  


# Initialize SQLAlchemy
db = SQLAlchemy(app)

import routes
import models


