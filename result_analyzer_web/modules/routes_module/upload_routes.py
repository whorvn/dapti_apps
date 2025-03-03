"""File upload route handlers."""

from flask import request, redirect, url_for, flash, session
from werkzeug.utils import secure_filename
import os
import uuid
import pandas as pd
import traceback

from modules.data_processing.file_processor import process_excel_file
from modules.utils.file_helpers import allowed_file

def upload_file():
    """Handle file upload and initial processing."""
    if 'file' not in request.files:
        flash('No file part')
        return redirect(request.url)
    
    file = request.files['file']
    
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)
        
    if file and allowed_file(file.filename):
        # Generate unique session ID if not present
        if 'user_id' not in session:
            session['user_id'] = str(uuid.uuid4())
            
        user_id = session['user_id']
        
        # Create user directory
        from flask import current_app
        user_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], user_id)
        if not os.path.exists(user_dir):
            os.makedirs(user_dir)
            
        # Save file with secure filename
        filename = secure_filename(file.filename)
        file_path = os.path.join(user_dir, filename)
        file.save(file_path)
        
        # Process the file
        try:
            # Process the uploaded file
            df, subjects = process_excel_file(file_path, filename)
            
            # Save processed data to user session file
            processed_file = os.path.join(user_dir, 'processed_data.pkl')
            df.to_pickle(processed_file)
            
            # Store subjects in session
            session['subjects'] = subjects
            
            flash('File uploaded and processed successfully!', 'success')
            return redirect(url_for('analyze'))

        except Exception as e:
            flash(f'Error processing file: {str(e)}', 'error')
            traceback.print_exc()
            return redirect(url_for('index'))
    else:
        flash('Invalid file type. Please upload an Excel (.xlsx, .xls) or CSV file.', 'error')
        return redirect(url_for('index'))
