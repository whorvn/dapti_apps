from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_session import Session
import pandas as pd
import os
import uuid
import logging
import traceback
from werkzeug.utils import secure_filename
from config import configure_app
from utils import schedule_cleanup  # Import the cleanup utility

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Initialize app with configuration
app = Flask(__name__)
app = configure_app(app)

# Schedule automatic cleanup of uploaded files (5 minute interval, 5 minute max age)
schedule_cleanup(app.config['UPLOAD_FOLDER'], interval_minutes=5, max_age_minutes=5)

def wrap_in_latex(text):
    """Wrap text in LaTeX delimiters if it contains LaTeX commands but isn't already wrapped."""
    if not text:
        return text
        
    # Check if the text contains LaTeX commands but isn't already wrapped in delimiters
    tex_commands = ['\\text', '\\frac', '\\mathbb', '\\int', '\\sum', '\\prod', '\\lim', '\\infty']
    has_tex = any(cmd in text for cmd in tex_commands)
    already_wrapped = (text.strip().startswith('$') and text.strip().endswith('$')) or \
                       (text.strip().startswith('$$') and text.strip().endswith('$$'))
    
    if has_tex and not already_wrapped:
        # Check if it's a display math (on its own line) or inline math
        if '\n' in text or len(text) > 50:  # Longer expressions or multiline as display math
            return f"$${text}$$"
        else:  # Shorter expressions as inline math
            return f"${text}$"
    return text

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
def index():
    # Debug current session
    logger.debug(f"Session at index route: {list(session.keys()) if session else 'No session'}")
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    # Log request information
    logger.debug("Upload request received")
    logger.debug(f"Request method: {request.method}")
    logger.debug(f"Files in request: {list(request.files.keys())}")
    
    if 'file' not in request.files:
        logger.warning("No file part in the request")
        flash('No file part in the request', 'error')
        return redirect(url_for('index'))
    
    file = request.files['file']
    logger.debug(f"File received: {file.filename}")
    
    if file.filename == '':
        logger.warning("No selected file")
        flash('No selected file', 'error')
        return redirect(url_for('index'))
    
    if not file or not allowed_file(file.filename):
        logger.warning(f"File type not allowed: {file.filename}")
        flash('File type not allowed. Please upload an Excel file (.xlsx or .xls)', 'error')
        return redirect(url_for('index'))
        
    try:
        # Generate unique filename with secure filename
        original_filename = secure_filename(file.filename)
        filename = f"{str(uuid.uuid4())}_{original_filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        # Save file
        logger.debug(f"Saving file to {filepath}")
        file.save(filepath)
        logger.debug(f"File saved successfully: {os.path.exists(filepath)}")
        
        # Process Excel file
        logger.debug(f"Processing Excel file: {filepath}")
        try:
            # Try different engines in case one fails
            try:
                df = pd.read_excel(filepath, engine='openpyxl')
            except Exception as openpyxl_error:
                logger.warning(f"Failed with openpyxl engine: {str(openpyxl_error)}")
                df = pd.read_excel(filepath, engine='xlrd')
                
            logger.debug(f"Excel file loaded successfully with {len(df)} rows")
            logger.debug(f"Columns found: {list(df.columns)}")
        except Exception as e:
            logger.error(f"Failed to load Excel file: {str(e)}")
            logger.error(traceback.format_exc())
            flash(f"Failed to process Excel file: {str(e)}", 'error')
            if os.path.exists(filepath):
                os.remove(filepath)
            return redirect(url_for('index'))
        
        # Check essential columns - be case insensitive
        essential_columns = ['topic', 'class', 'question', 'option a', 'option b', 'correct option']
        df.columns = [col.lower() for col in df.columns]  # Convert all column names to lowercase
        missing_columns = [col for col in essential_columns if col not in df.columns]
        
        if missing_columns:
            logger.warning(f"Missing essential columns: {missing_columns}")
            flash(f"Missing essential columns: {', '.join(missing_columns)}", 'error')
            os.remove(filepath)
            return redirect(url_for('index'))
        
        # Detailed examination of DataFrame contents
        logger.debug(f"DataFrame shape: {df.shape}")
        logger.debug(f"DataFrame columns: {df.columns.tolist()}")
        logger.debug(f"First row: {df.iloc[0].to_dict() if len(df) > 0 else 'No rows'}")
        
        # Process questions
        logger.debug("Processing questions")
        questions = []
        for idx, row in df.iterrows():
            try:
                # Log each row being processed
                logger.debug(f"Processing row {idx}...")
                
                # Process question text to ensure proper LaTeX rendering
                question_text = str(row.get('question', '')) if pd.notna(row.get('question', '')) else ''
                formula_text = str(row.get('formula', '')) if pd.notna(row.get('formula', '')) else ''
                translation_text = str(row.get('translation', '')) if pd.notna(row.get('translation', '')) else ''
                
                # Wrap in LaTeX delimiters if needed
                question_text = wrap_in_latex(question_text)
                formula_text = wrap_in_latex(formula_text)
                translation_text = wrap_in_latex(translation_text)
                
                # Create question dict with all available columns
                question = {
                    'category': str(row.get('category', '')) if pd.notna(row.get('category', '')) else '',
                    'chapter': str(row.get('chapter', '')) if pd.notna(row.get('chapter', '')) else '',
                    'topic': str(row.get('topic', '')),
                    'class': str(row.get('class', '')),
                    'level': str(row.get('level', '')) if pd.notna(row.get('level', '')) else '',
                    'translation': translation_text,
                    'question': question_text,
                    'formula': formula_text,
                    'options': {},
                    'image': str(row.get('image', '')) if pd.notna(row.get('image', '')) else ''
                }
                
                # Add options dynamically - be case insensitive
                option_count = 0
                for col in df.columns:
                    if col.startswith('option '):
                        option_key = col.split(' ')[1].upper()  # Convert to uppercase for consistency
                        if pd.notna(row[col]):
                            option_text = str(row[col])
                            # Ensure option text is properly formatted for LaTeX
                            option_text = wrap_in_latex(option_text)
                            question['options'][option_key] = option_text
                            option_count += 1
                
                # Add correct option - convert to uppercase for consistency
                if pd.notna(row.get('correct option', '')):
                    question['correct_option'] = str(row['correct option']).upper()
                else:
                    question['correct_option'] = ''
                
                # Log question info
                logger.debug(f"Processed question {idx+1}: '{question_text[:30]}...' with {option_count} options")
                if option_count == 0:
                    logger.warning(f"No options found for question {idx+1}")
                
                # Only add if we have valid question text and at least one option
                if question_text.strip() and option_count > 0:
                    questions.append(question)
                else:
                    logger.warning(f"Skipping row {idx}: Empty question text or no options")
                
            except Exception as e:
                logger.error(f"Error processing row {idx}: {str(e)}")
                logger.error(traceback.format_exc())
                continue
        
        if not questions:
            logger.warning("No valid questions found in the Excel file")
            # Log more details to help diagnose the issue
            logger.debug(f"DataFrame had {len(df)} rows but no valid questions extracted")
            flash("No valid questions found in the Excel file. Please check your Excel format.", 'error')
            os.remove(filepath)
            return redirect(url_for('index'))
            
        # Save to session
        logger.debug(f"Saving {len(questions)} questions to session")
        session['questions'] = questions
        logger.debug(f"Session keys after saving: {list(session.keys())}")
        flash(f"Successfully processed {len(questions)} questions", 'success')
        
        # Note: We don't manually delete the file anymore since the cleanup utility will handle it
        # This ensures the file is available for debugging for a few minutes if needed
        
        return redirect(url_for('view_quiz'))
        
    except Exception as e:
        logger.error(f"Error processing file: {str(e)}")
        logger.error(traceback.format_exc())
        flash(f"Error processing file: {str(e)}", 'error')
        # Remove the file in case of error
        if 'filepath' in locals() and os.path.exists(filepath):
            os.remove(filepath)
        return redirect(url_for('index'))

@app.route('/quiz')
def view_quiz():
    logger.debug(f"Session keys at quiz route: {list(session.keys())}")
    if 'questions' not in session or not session['questions']:
        logger.warning("No questions found in session")
        flash('Please upload an Excel file first', 'error')
        return redirect(url_for('index'))
    
    questions = session['questions']
    logger.debug(f"Retrieved {len(questions)} questions from session")
    return render_template('quiz.html', questions=questions)

@app.route('/clear')
def clear_session():
    logger.debug("Clearing session")
    session.clear()
    flash('Session cleared. You can upload a new file.', 'success')
    return redirect(url_for('index'))

# Add a simple route to check session
@app.route('/debug')
def debug_session():
    questions_count = len(session.get('questions', [])) if 'questions' in session else 0
    return {
        'session': {key: str(session[key])[:100] + '...' if len(str(session[key])) > 100 else str(session[key]) for key in session.keys()} if session else {},
        'has_questions': 'questions' in session,
        'question_count': questions_count,
        'session_keys': list(session.keys()) if session else []
    }

# Add a route to show math examples
@app.route('/math-examples')
def math_examples():
    return render_template('math_example.html')

# Add a route to handle LaTeX preparation
@app.route('/prepare-latex')
def prepare_latex():
    sample_text = request.args.get('text', '\\frac{1}{2}+\\frac{1}{3}=\\frac{5}{6}')
    return render_template('latex_viewer.html', latex=sample_text)

# Add a LaTeX helper route
@app.route('/latex-helper')
def latex_helper():
    return render_template('latex_helper.html')

# Don't run directly from this file
if __name__ == '__main__':
    logger.warning("This file should be imported, not run directly. Use main.py instead.")
