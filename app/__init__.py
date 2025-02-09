import os
from flask import Flask
from flask_login import LoginManager
import logging
from .config import Config
from .database import db, migrate
from .scheduler import init_scheduler
from .utils import get_image_url

logging.basicConfig(level=logging.INFO)
login_manager = LoginManager()


basedir = os.path.abspath(os.path.dirname(__file__))

def create_app():
    basedir = os.path.abspath(os.path.dirname(__file__))
    template_dir = os.path.abspath(os.path.join(basedir, 'View', 'templates'))
    static_dir = os.path.abspath(os.path.join(basedir, 'View', 'static'))

    app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
    app.config.from_object(Config)

    app.config['ENV'] = 'development'
    app.config['DEBUG'] = True

    logging.debug(f"CLOUD_STORAGE_BUCKET: {os.getenv('CLOUD_STORAGE_BUCKET')}")
    logging.debug(f"GOOGLE_APPLICATION_CREDENTIALS: {os.getenv('GOOGLE_APPLICATION_CREDENTIALS')}")

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    @app.context_processor
    def utility_processor():
        return dict(get_image_url=get_image_url)

    with app.app_context():
        from app.Controller.routes import register_routes
        register_routes(app)
        from app.Model.models import User, Event, EventForm, Settings
        db.create_all()

        init_scheduler(app)

    return app

flask_app = create_app()
