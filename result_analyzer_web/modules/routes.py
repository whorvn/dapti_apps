"""Application routes module."""

from flask import render_template, request, redirect, url_for, flash, session, jsonify, send_file
from functools import wraps
from datetime import datetime

from modules.routes_module.upload_routes import upload_file
from modules.routes_module.analyze_routes import analyze, reset_filters
from modules.routes_module.student_routes import student_detail
from modules.routes_module.compare_routes import compare_students
from modules.routes_module.export_routes import export_data
from modules.routes_module.session_routes import check_session, extend_session

def session_required(f):
    """Decorator to check if user session is valid."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Your session has expired. Please upload your file again.', 'warning')
            return redirect(url_for('index'))
        
        # Check session age if needed
        if 'last_activity' in session:
            last_activity = datetime.fromisoformat(session['last_activity'])
            if datetime.now() - last_activity > app.config['PERMANENT_SESSION_LIFETIME']:
                session.clear()
                flash('Your session has expired due to inactivity. Please upload your file again.', 'warning')
                return redirect(url_for('index'))
                
        # Update last activity timestamp
        session['last_activity'] = datetime.now().isoformat()
        return f(*args, **kwargs)
    return decorated_function

def register_routes(app):
    """Register all route functions with the Flask app."""
    
    # Simple routes
    @app.route('/')
    def index():
        return render_template('index.html')
    
    # Error handlers
    @app.errorhandler(500)
    def server_error(e):
        app.logger.error(f"Server error: {e}")
        return render_template('error.html', error=str(e)), 500

    @app.errorhandler(404)
    def not_found(e):
        return render_template('error.html', error="The requested page was not found."), 404
    
    # Register blueprint routes
    app.route('/upload', methods=['POST'])(upload_file)
    
    app.route('/analyze', methods=['GET', 'POST'])(session_required(analyze))
    app.route('/reset_filters', methods=['POST'])(reset_filters)
    
    app.route('/student/<name>')(session_required(student_detail))
    
    app.route('/compare', methods=['GET', 'POST'])(session_required(compare_students))
    
    app.route('/export')(export_data)
    
    app.route('/check_session')(check_session)
    app.route('/extend_session', methods=['POST'])(extend_session)
