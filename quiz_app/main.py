import os
from app import app, logger
import subprocess
from utils import cleanup_old_files

def setup_environment():
    """Set up the environment before running the app."""
    # Create required directories
    os.makedirs('static/uploads', exist_ok=True)
    os.makedirs('flask_session', exist_ok=True)
    
    # Clean up old files on startup
    uploads_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static/uploads')
    cleanup_old_files(uploads_dir)
    
    # Install required packages if needed
    try:
        import flask_session
    except ImportError:
        logger.warning("Flask-Session not installed. Installing now...")
        subprocess.call(['pip', 'install', 'Flask-Session'])

    # Check if the uploads directory is writable
    uploads_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static/uploads')
    if not os.access(uploads_dir, os.W_OK):
        logger.error(f"Upload directory {uploads_dir} is not writable!")
    
    # Check if session directory is writable
    session_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'flask_session')
    if not os.access(session_dir, os.W_OK):
        logger.error(f"Session directory {session_dir} is not writable!")

if __name__ == '__main__':
    # Set up environment
    setup_environment()
    
    # Start the app
    print("\n===== QUIZ APP STARTED =====")
    print("Main app URL: http://127.0.0.1:5000/")
    print("Math Examples: http://127.0.0.1:5000/math-examples")
    print("LaTeX Tester: http://127.0.0.1:5000/prepare-latex")
    print("LaTeX Helper: http://127.0.0.1:5000/latex-helper")
    print("\nUploaded files will be automatically deleted after 5 minutes")
    print("============================\n")
    
    logger.info("Starting the Flask application...")
    app.run(debug=True)
