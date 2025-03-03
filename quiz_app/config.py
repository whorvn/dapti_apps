import os
import tempfile
from flask_session import Session

def configure_app(app):
    """Configure the Flask application."""
    # Get the absolute path to this file's directory
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Basic configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', os.urandom(24).hex())
    
    # Upload configuration
    app.config['UPLOAD_FOLDER'] = os.path.join(base_dir, 'static', 'uploads')
    app.config['ALLOWED_EXTENSIONS'] = {'xlsx', 'xls'}
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload
    
    # Session configuration
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['SESSION_FILE_DIR'] = os.path.join(base_dir, 'flask_session')
    app.config['SESSION_PERMANENT'] = True
    app.config['SESSION_USE_SIGNER'] = True
    app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 hour
    
    # Create necessary directories
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['SESSION_FILE_DIR'], exist_ok=True)
    
    # Initialize the Flask-Session extension
    Session(app)
    
    return app
