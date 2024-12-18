from flask import Flask
from web_app.extensions import db, bcrypt, login_manager
from flask_migrate import Migrate
from web_app.config import Config


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize extensions
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)

    # Initialize Flask-Migrate
    Migrate(app, db)

    # Register Blueprints
    from web_app.routes import app_routes
    app.register_blueprint(app_routes)

    with app.app_context():
        # Import models to register them with SQLAlchemy
        from web_app import models
        db.create_all()  # Ensure all tables are created

    return app


@login_manager.user_loader
def load_user(user_id):
    from web_app.models import User
    return User.query.get(int(user_id))
