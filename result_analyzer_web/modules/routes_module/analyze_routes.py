"""Routes for data analysis functionality."""

from flask import render_template, request, redirect, url_for, flash, session
import os
import pandas as pd
import json

from modules.data_processing.analysis import analyze_student_data
from modules.utils.serialization import convert_to_serializable

def analyze():
    """Analyze student data based on filters."""
    if 'user_id' not in session:
        flash('Please upload a file first', 'warning')
        return redirect(url_for('index'))
    
    from flask import current_app
    user_id = session['user_id']
    user_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], user_id)
    processed_file = os.path.join(user_dir, 'processed_data.pkl')
    
    if not os.path.exists(processed_file):
        flash('No processed data found. Please upload a file first.', 'warning')
        return redirect(url_for('index'))
    
    # Load the processed data
    df = pd.read_pickle(processed_file)
    
    # Process filter values
    filter_values = get_filter_values(request)
    
    # Apply filters and get student summaries
    student_summaries, student_full_data = analyze_student_data(
        df, 
        filter_values['start_date'],
        filter_values['end_date'],
        filter_values['min_success_rate'],
        filter_values['min_days'],
        filter_values['subject']
    )
    
    # Save processed data
    save_processed_data(user_dir, student_summaries, student_full_data)
    
    # Generate summary data for charts
    summary_data = generate_summary_data(student_summaries)
    
    return render_template('analyze.html', 
                           students=student_summaries, 
                           summary_data=summary_data, 
                           subjects=session.get('subjects', []))

def get_filter_values(request):
    """Get filter values from request or session."""
    if request.method == 'POST':
        # Form submission - update filters
        start_date = pd.to_datetime(request.form.get('start_date'))
        end_date = pd.to_datetime(request.form.get('end_date'))
        min_success_rate = float(request.form.get('min_success_rate', 0))
        min_days = int(request.form.get('min_days', 7))
        selected_subject = request.form.get('subject', 'All')
        
        # Store the filter values in session
        session['filter_values'] = {
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d'),
            'min_success_rate': min_success_rate,
            'min_days': min_days,
            'subject': selected_subject
        }
    else:
        # GET request - use stored filters or defaults
        if 'filter_values' in session:
            # Use stored filters
            filter_values = session['filter_values']
            start_date = pd.to_datetime(filter_values['start_date'])
            end_date = pd.to_datetime(filter_values['end_date'])
            min_success_rate = float(filter_values['min_success_rate'])
            min_days = int(filter_values['min_days'])
            selected_subject = filter_values['subject']
        else:
            # First time visit - use defaults
            start_date = pd.to_datetime('2025-02-19')
            end_date = pd.to_datetime('2025-02-27')
            min_success_rate = 0
            min_days = 7
            selected_subject = 'All'
            
            # Store default values in session
            session['filter_values'] = {
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d'),
                'min_success_rate': min_success_rate,
                'min_days': min_days,
                'subject': selected_subject
            }
    
    return {
        'start_date': start_date,
        'end_date': end_date,
        'min_success_rate': min_success_rate,
        'min_days': min_days,
        'subject': selected_subject
    }

def save_processed_data(user_dir, student_summaries, student_full_data):
    """Save processed student data to disk."""
    # Convert DataFrame in student_full_data to dict for serialization
    serializable_full_data = {name: df.to_dict('records') for name, df in student_full_data.items()}
    
    # Save student data for later use
    summary_file = os.path.join(user_dir, 'student_summaries.json')
    full_data_file = os.path.join(user_dir, 'student_full_data.json')
    
    # Convert NumPy types to native Python types before serialization
    clean_summaries = []
    for student in student_summaries:
        clean_student = {}
        for key, value in student.items():
            clean_student[key] = convert_to_serializable(value)
        clean_summaries.append(clean_student)
    
    # Process the full data similarly
    clean_full_data = {}
    for name, df_dict_list in serializable_full_data.items():
        clean_records = []
        for record in df_dict_list:
            clean_record = {}
            for key, value in record.items():
                try:
                    clean_record[key] = convert_to_serializable(value)
                except Exception:
                    # If there's any error, just use the original value
                    # and convert it to a string if it's not a basic type
                    if isinstance(value, (str, int, float, bool, type(None))):
                        clean_record[key] = value
                    else:
                        clean_record[key] = str(value)
            clean_records.append(clean_record)
        clean_full_data[name] = clean_records
    
    # Save as JSON files
    with open(summary_file, 'w') as f:
        json.dump(clean_summaries, f)
    
    with open(full_data_file, 'w') as f:
        json.dump(clean_full_data, f)

def generate_summary_data(student_summaries):
    """Generate chart data for the top students."""
    summary_data = None
    
    if student_summaries:
        # Sort by days worked
        results_sorted = sorted(student_summaries, key=lambda x: x["Days_Worked"], reverse=True)
        
        # Limit to top 10 students for readability
        top_students = results_sorted[:10]
        
        # Prepare data for interactive charts
        summary_data = {
            'names': [student["Full_Name"] for student in top_students],
            'days_worked': [student["Days_Worked"] for student in top_students],
            'tasks_completed': [student["Total_Tasks"] for student in top_students],
            'max_streaks': [student["Max_Streak"] for student in top_students]
        }
    
    return summary_data

def reset_filters():
    """Reset filter values to defaults."""
    if 'filter_values' in session:
        # Reset to default values
        session['filter_values'] = {
            'start_date': '2025-02-19',
            'end_date': '2025-02-27',
            'min_success_rate': 0,
            'min_days': 7,
            'subject': 'All'
        }
    return redirect(url_for('analyze'))
