"""Routes for comparing students."""

from flask import render_template, request, redirect, url_for, flash, session
import os
import json

from modules.charts.chart_generator import generate_comparison_chart

def compare_students():
    """Compare selected students based on various metrics."""
    if 'user_id' not in session:
        flash('Please upload a file first', 'warning')
        return redirect(url_for('index'))
    
    from flask import current_app
    user_id = session['user_id']
    user_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], user_id)
    summary_file = os.path.join(user_dir, 'student_summaries.json')
    
    if not os.path.exists(summary_file):
        flash('No student data found. Please analyze data first.', 'warning')
        return redirect(url_for('analyze'))
    
    # Load student summaries
    with open(summary_file, 'r') as f:
        student_summaries = json.load(f)
    
    if request.method == 'POST':
        # Get selected students and comparison type
        selected_students = request.form.getlist('students')
        comparison_type = request.form.get('comparison_type', 'Success Rate')
        
        if len(selected_students) < 2:
            flash('Please select at least 2 students to compare', 'warning')
            return render_template('compare.html', students=student_summaries)
        
        # Filter student summaries to just the selected ones
        selected_data = []
        for s in student_summaries:
            if s["Full_Name"] in selected_students:
                # Create a copy of the student data with formatted Avg_Success
                student_copy = s.copy()
                if isinstance(s["Avg_Success"], (int, float)):
                    student_copy["Avg_Success"] = f"{float(s['Avg_Success']):.2f}%"
                selected_data.append(student_copy)
        
        # Generate chart data for interactive Chart.js
        comparison_data_obj = create_comparison_data_object(selected_data, comparison_type)
        
        # Generate static chart for backward compatibility
        chart_url = generate_comparison_chart(selected_data, comparison_type, user_id)
        
        # Store data in session for any print functions
        session['comparison_data'] = selected_data
        session['comparison_type'] = comparison_type
        session['comparison_chart_url'] = chart_url
        
        return render_template(
            'compare.html', 
            students=student_summaries,
            selected_students=selected_students,
            comparison_type=comparison_type,
            chart_url=chart_url,
            comparison_data=selected_data,
            comparison_data_obj=comparison_data_obj
        )
    
    return render_template('compare.html', students=student_summaries)

def create_comparison_data_object(selected_data, comparison_type):
    """Create data object for Chart.js visualization."""
    comparison_data_obj = {
        'names': [student["Full_Name"] for student in selected_data],
        'values': []
    }
    
    if comparison_type == "Success Rate":
        comparison_data_obj['values'] = [
            float(student["Avg_Success"].replace('%', '')) 
            if isinstance(student["Avg_Success"], str) 
            else float(student["Avg_Success"]) 
            for student in selected_data
        ]
        
    elif comparison_type == "Tasks Completed":
        comparison_data_obj['values'] = [int(student["Total_Tasks"]) for student in selected_data]
        
    elif comparison_type == "Days Worked":
        comparison_data_obj['values'] = [int(student["Days_Worked"]) for student in selected_data]
        
    elif comparison_type == "Max Streak":
        comparison_data_obj['values'] = [int(student["Max_Streak"]) for student in selected_data]
        
    else:  # "Diagnostics"
        comparison_data_obj['values'] = [int(student.get("Diagnostics_Count", 0)) for student in selected_data]
    
    return comparison_data_obj
