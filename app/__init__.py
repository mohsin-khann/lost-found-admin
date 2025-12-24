from flask import Flask, render_template
from flask_login import LoginManager
from config import Config
from .firebase_service import initialize_firebase
from .models import User
from flask_wtf import CSRFProtect

login_manager = LoginManager()
csrf = CSRFProtect()


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    csrf.init_app(app)

    # Initialize Firebase
    initialize_firebase()

    # Flask-Login setup
    login_manager.init_app(app)
    login_manager.login_view = "routes.login"
    login_manager.login_message = "Please log in to access this page."
    login_manager.login_message_category = "success"

    # User loader
    @login_manager.user_loader
    def load_user(user_email):
        return User(user_email)

    # Register blueprints
    from .routes import bp, admin
    app.register_blueprint(bp)
    app.register_blueprint(admin)

    # 404 handler
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template("404.html"), 404

    return app
