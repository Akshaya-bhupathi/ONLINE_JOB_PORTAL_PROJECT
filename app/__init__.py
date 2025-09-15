from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt 
from flask_migrate import Migrate
from flask_mail import Mail
from config import Config
import os
from logging.handlers import RotatingFileHandler
import logging
from flask_wtf.csrf import CSRFProtect


db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()
migrate = Migrate()
mail = Mail()
csrf = CSRFProtect()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    csrf.init_app(app)

    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)

    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'
    login_manager.session_protection = "strong"

    from app.routes import main, auth, jobs, dashboard_bp
    app.register_blueprint(main)
    app.register_blueprint(auth)
    app.register_blueprint(jobs)
    app.register_blueprint(dashboard_bp)
    
    from app.templates.errors.handlers import bp as errors_bp
    app.register_blueprint(errors_bp)

    # Create upload folder if it doesn't exist
    os.makedirs(os.path.join(app.instance_path, 'uploads'), exist_ok=True)

    if not app.debug and not app.testing:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = RotatingFileHandler('logs/jobportal.log', maxBytes=10240, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('Job Portal startup')

    # Shell Context Processor
    @app.shell_context_processor
    def make_shell_context():
        return {
            'db': db,
            'User': User,
            'Job': Job,
            'Application': Application,
            'create_admin': create_admin
        }

    # Import models at the end to avoid circular imports
    from app.models import User, Job, Application
    from app.utils import create_admin
    migrate.init_app(app, db)
    
    
    

    return app

from app import models