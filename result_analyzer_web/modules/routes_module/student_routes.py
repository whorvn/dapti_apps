"""Routes for student detail views."""

from flask import render_template, flash, redirect, url_for, session
from urllib.parse import unquote
import os
import json
import pandas as pd
import unicodedata

from modules.data_processing.student_profile import (
    get_student_profile_info, 
    get_student_timeline_data, 
    get_student_tasks_data,
    get_progress_chart_data,
    get_subject_comparison_data,
    get_diagnostics_data
)
from modules.charts.chart_generator import generate_progress_charts, generate_subject_comparison

def student_detail(name):
    """Display detailed information for a specific student."""
    if 'user_id' not in session:
        flash('Session expired. Please upload file again.', 'warning')
        return redirect(url_for('index'))
    
    from flask import current_app
    user_id = session['user_id']
    user_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], user_id)
    
    # Decode the URL-encoded name
    decoded_name = unquote(name)
    
    # Load student summaries
    summary_file = os.path.join(user_dir, 'student_summaries.json')
    full_data_file = os.path.join(user_dir, 'student_full_data.json')
    
    if not os.path.exists(summary_file) or not os.path.exists(full_data_file):
        flash('Student data not found. Please analyze data first.', 'warning')
        return redirect(url_for('analyze'))
    
    # Load student data
    with open(summary_file, 'r') as f:
        student_summaries = json.load(f)
    
    with open(full_data_file, 'r') as f:
        student_full_data_json = json.load(f)
    
    # Find student in summaries
    student_summary = next((s for s in student_summaries if s["Full_Name"] == decoded_name), None)
    
    if not student_summary:
        # Try with normalization
        student_summary = next(
            (s for s in student_summaries if unicodedata.normalize('NFC', s["Full_Name"]) == 
             unicodedata.normalize('NFC', decoded_name)), 
            None
        )
    
    if not student_summary:
        flash(f'Student {decoded_name} not found', 'error')
        return redirect(url_for('analyze'))
    
    # Get the student name as stored in the data
    actual_name = student_summary["Full_Name"]
    
    # Convert JSON data back to DataFrame
    if actual_name in student_full_data_json:
        student_data = pd.DataFrame(student_full_data_json[actual_name])
        
        # Convert dates back to datetime
        if "Completion_Date" in student_data.columns:
            student_data["Completion_Date"] = pd.to_datetime(student_data["Completion_Date"])
    else:
        flash(f'Detailed data for student {decoded_name} not found', 'error')
        return redirect(url_for('analyze'))
    
    # Generate profile data and charts
    profile_info = get_student_profile_info(student_data)
    timeline_data = get_student_timeline_data(student_data)
    tasks_data = get_student_tasks_data(student_data)
    
    # Generate chart data
    progress_data = get_progress_chart_data(student_data)
    subject_data = get_subject_comparison_data(student_data)
    diagnostics_data = get_diagnostics_data(student_data)
    
    # Generate static charts for backward compatibility
    progress_charts = generate_progress_charts(student_data, user_id, name)
    subject_comparison = generate_subject_comparison(student_data, user_id, name)
    
    return render_template(
        'student_detail.html',
        student=student_summary,
        profile=profile_info,
        timeline_data=timeline_data,
        tasks_data=tasks_data,
        progress_charts=progress_charts, 
        progress_data=progress_data,
        subject_comparison=subject_comparison,
        subject_data=subject_data,
        diagnostics_data=diagnostics_data
    )
