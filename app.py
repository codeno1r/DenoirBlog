# Import OS and DotEnv
import os
# Import Flask, Bootstrap, SQLAlchemy, DeclarativeBase, LoginManager, Bcrypt and Migrate
from flask import Flask
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate


db = SQLAlchemy()


def create_app():
    # init App
    app = Flask(__name__)
    app.secret_key = os.environ.get('SECRET_KEY')

    # init Bootstrap5
    bootstrap = Bootstrap5(app)

    # init DB
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DB_URI')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)

    # Import routes here later
    from routes import register_routes
    register_routes(app, db)

    # init Migrate
    migrate = Migrate(app, db)
    return app
