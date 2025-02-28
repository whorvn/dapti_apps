from flask import Flask, render_template, request, redirect, url_for, jsonify, session, flash
import pandas as pd
import numpy as np
import os
import json
import tempfile
from datetime import datetime, timedelta
import uuid
import plotly
import plotly.express as px
import plotly.graph_objects as go
import sys

# Add the parent directory to the path so we can import from the background_system
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import analyzer logic from the background system
from background_system.student_analysis import StudentAnalysisApp

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['UPLOAD_FOLDER'] = os.path.join(tempfile.gettempdir(), 'dapti_uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max upload

# Create upload folder if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Store data in session
class WebDataStore:
    def __init__(self):
        self.data_by_session = {}
    
    def store_data(self, session_id, df, results_data, student_full_data):
        self.data_by_session[session_id] = {
            'df': df,
            'results_data': results_data,
            'student_full_data': student_full_data,
        }
    
    def get_data(self, session_id):
        return self.data_by_session.get(session_id, {})
    
    def clear_old_sessions(self, max_age_hours=24):
        # Cleanup old sessions (not implemented for simplicity)
        pass

data_store = WebDataStore()

@app.route('/')
def index():
    """Home page with file upload form"""
    # Generate a unique session ID if not already present
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
    
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload and process the Excel data"""
    if 'excel_file' not in request.files:
        flash('No file part')
        return redirect(request.url)
    
    file = request.files['excel_file']
    
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)
    
    if file and '.' in file.filename and file.filename.rsplit('.', 1)[1].lower() in ['xlsx', 'xls']:
        # Save the file temporarily
        temp_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{session['session_id']}_{file.filename}")
        file.save(temp_path)
        
        try:
            # Process the file similar to the desktop app's load_data method
            df = pd.read_excel(temp_path, engine='openpyxl')
            
            # Process data using adapted methods from StudentAnalysisApp
            transformed_data = process_excel_data(df)
            
            if transformed_data.empty:
                flash("No usable data found in the Excel file")
                return redirect(url_for('index'))
            
            # Store the processed data
            session_id = session['session_id']
            data_store.store_data(
                session_id=session_id, 
                df=transformed_data,
                results_data=[],  # Will be populated after analysis
                student_full_data={}  # Will be populated after analysis
            )
            
            # Set default filter values in session
            session['start_date'] = '2025-02-19'
            session['end_date'] = '2025-02-27'
            session['min_success_rate'] = '0'
            session['min_days'] = '7'
            session['subject'] = 'All'
            
            # Identify unique subjects for the filter dropdown
            subjects = transformed_data['Subject'].unique().tolist()
            session['available_subjects'] = ['All'] + sorted(subjects)
            
            flash(f"Data loaded successfully: {len(transformed_data)} records found")
            return redirect(url_for('analyze'))
            
        except Exception as e:
            flash(f"Error processing file: {str(e)}")
            import traceback
            traceback.print_exc()
            return redirect(url_for('index'))
        finally:
            # Clean up the temporary file
            if os.path.exists(temp_path):
                os.remove(temp_path)
    else:
        flash('Invalid file type. Please upload an Excel file (.xlsx, .xls)')
        return redirect(url_for('index'))

@app.route('/analyze', methods=['GET', 'POST'])
def analyze():
    """Display analysis form and results"""
    if 'session_id' not in session:
        flash('No data session found. Please upload a file first.')
        return redirect(url_for('index'))
    
    # Get stored data
    session_data = data_store.get_data(session['session_id'])
    
    if not session_data or 'df' not in session_data:
        flash('Session data not found. Please upload a file again.')
        return redirect(url_for('index'))
    
    # Handle filter form submission
    if request.method == 'POST':
        # Update session filter values
        session['start_date'] = request.form.get('start_date', session.get('start_date', '2025-02-19'))
        session['end_date'] = request.form.get('end_date', session.get('end_date', '2025-02-27'))
        session['min_success_rate'] = request.form.get('min_success_rate', session.get('min_success_rate', '0'))
        session['min_days'] = request.form.get('min_days', session.get('min_days', '7'))
        session['subject'] = request.form.get('subject', session.get('subject', 'All'))
    
    # Run the analysis with current filters
    result_data, filtered_df = analyze_student_data(
        session_data['df'],
        start_date=session.get('start_date', '2025-02-19'),
        end_date=session.get('end_date', '2025-02-27'),
        min_success_rate=float(session.get('min_success_rate', '0')),
        min_days=int(session.get('min_days', '7')),
        subject_filter=session.get('subject', 'All')
    )
    
    # Update stored results data
    session_data['results_data'] = result_data
    
    # Create student_full_data from filtered_df
    student_full_data = {}
    for name, group in filtered_df.groupby('Full_Name'):
        student_full_data[name] = group
    
    session_data['student_full_data'] = student_full_data
    
    # Create visualization for top students
    if result_data:
        # Sort results by days worked for chart
        sorted_results = sorted(result_data, key=lambda x: x['Days_Worked'], reverse=True)
        top_results = sorted_results[:10]  # Top 10 students
        
        # Create JSON for charts
        chart_data = create_chart_data_json(top_results)
    else:
        chart_data = None
    
    return render_template(
        'analyze.html',
        results=result_data,
        chart_data=chart_data,
        filters={
            'start_date': session.get('start_date'),
            'end_date': session.get('end_date'),
            'min_success_rate': session.get('min_success_rate'),
            'min_days': session.get('min_days'),
            'subject': session.get('subject'),
            'available_subjects': session.get('available_subjects', ['All'])
        }
    )

@app.route('/student/<student_name>')
def student_details(student_name):
    """Show detailed student information"""
    if 'session_id' not in session:
        flash('No data session found. Please upload a file first.')
        return redirect(url_for('index'))
    
    # Get stored data
    session_data = data_store.get_data(session['session_id'])
    
    if not session_data or 'student_full_data' not in session_data:
        flash('Student data not found. Please analyze data first.')
        return redirect(url_for('analyze'))
    
    # URL decode the student name
    student_name = student_name.replace('_', ' ')
    
    if student_name not in session_data['student_full_data']:
        flash(f'Student "{student_name}" not found in results')
        return redirect(url_for('analyze'))
    
    # Get student data
    student_data = session_data['student_full_data'][student_name]
    
    # Create profile data
    profile_data = create_student_profile_data(student_data)
    
    # Create charts for student data
    progress_chart = create_progress_chart(student_data)
    diagnostic_chart = create_diagnostic_chart(student_data)
    subjects_chart = create_subjects_chart(student_data)
    
    # Create timeline data
    timeline_data = create_timeline_data(student_data)
    
    # Create task list data
    task_data = create_task_data(student_data)
    
    return render_template(
        'student_details.html',
        student_name=student_name,
        profile=profile_data,
        progress_chart=progress_chart,
        diagnostic_chart=diagnostic_chart,
        subjects_chart=subjects_chart,
        timeline_data=timeline_data,
        task_data=task_data
    )

@app.route('/compare', methods=['GET', 'POST'])
def compare_students():
    """Compare multiple students"""
    if 'session_id' not in session:
        flash('No data session found. Please upload a file first.')
        return redirect(url_for('index'))
    
    # Get stored data
    session_data = data_store.get_data(session['session_id'])
    
    if not session_data or 'results_data' not in session_data:
        flash('Results data not found. Please analyze data first.')
        return redirect(url_for('analyze'))
    
    all_students = [student['Full_Name'] for student in session_data['results_data']]
    
    if request.method == 'POST':
        # Process comparison request
        selected_students = request.form.getlist('students')
        compare_by = request.form.get('compare_by', 'Success Rate')
        subject = request.form.get('subject', 'All')
        
        if len(selected_students) < 2:
            flash('Please select at least 2 students to compare')
            return render_template(
                'compare.html',
                students=all_students,
                comparison_data=None,
                available_subjects=session.get('available_subjects', ['All'])
            )
        
        # Create comparison data
        comparison_data = create_comparison_data(
            session_data,
            selected_students,
            compare_by,
            subject
        )
        
        return render_template(
            'compare.html',
            students=all_students,
            selected_students=selected_students,
            comparison_data=comparison_data,
            compare_by=compare_by,
            subject=subject,
            available_subjects=session.get('available_subjects', ['All'])
        )
    
    # Just show the selection form
    return render_template(
        'compare.html',
        students=all_students,
        comparison_data=None,
        available_subjects=session.get('available_subjects', ['All'])
    )

@app.route('/export', methods=['POST'])
def export_results():
    """Export results as JSON"""
    if 'session_id' not in session:
        return jsonify({'error': 'No session found'})
    
    # Get stored data
    session_data = data_store.get_data(session['session_id'])
    
    if not session_data or 'results_data' not in session_data:
        return jsonify({'error': 'No results data found'})
    
    # Convert data to JSON
    return jsonify({
        'results': session_data['results_data'],
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })

# Helper functions adapted from the original StudentAnalysisApp
def process_excel_data(df):
    """Process the Excel data into a transformed format"""
    transformed_data = []
    
    # Identify diagnostic columns
    diagnostic_cols = [col for col in df.columns if 'Diagnostic' in str(col) and 'Accuracy' in str(col)]
    
    # Define main task column groups
    task_columns = {
        "Math": {
            "Practice Task": "Practice Task",
            "Completion Date": "Completion Date",
            "Practice Status": "Practice Status",
            "Success/Progress Rate": "Success/Progress Rate"
        },
        "English": {
            "Practice Task": "Practice Task (English)",
            "Completion Date": "Completion Date (English)",
            "Practice Status": "Practice Status (English)",
            "Success/Progress Rate": "Success/Progress Rate (English)"
        }
    }
    
    # Process each row in the DataFrame
    for idx, row in df.iterrows():
        student_data = {
            "Name": row.get("Name", ""),
            "Surname": row.get("Surname", ""),
            "Phone": row.get("Phone Number", ""),
            "Grade": row.get("Grade", ""),
            "Parent_Number": row.get("Parent Number", ""),
            "School": row.get("School", ""),
            "Registration_Date": row.get("Registration Date")
        }
        
        # Extract diagnostic values
        diagnostics = {}
        for col in diagnostic_cols:
            if pd.notna(row.get(col)):
                diag_name = str(col).replace(" - Accuracy", "").strip()
                diag_value = row.get(col)
                if isinstance(diag_value, (int, float)) or (isinstance(diag_value, str) and diag_value.strip()):
                    diagnostics[diag_name] = diag_value
        
        # Process each subject
        for subject, columns in task_columns.items():
            task_col = columns["Practice Task"]
            date_col = columns["Completion Date"]
            status_col = columns["Practice Status"]
            rate_col = columns["Success/Progress Rate"]
            
            # Check if the subject columns exist in the dataframe
            if not all(col in df.columns for col in columns.values()):
                print(f"Skipping subject {subject}, missing required columns")
                continue
            
            # Skip if no task or "Not Started"
            if pd.isna(row.get(task_col)) or row.get(task_col) == "Not Started":
                continue
            
            # Parse success rate
            success_rate = parse_rate(row.get(rate_col))
            
            # Create a record for this task
            task_record = {
                **student_data,  # Include all student data
                "Subject": subject,
                "Task": row.get(task_col, ""),
                "Completion_Date": row.get(date_col),
                "Status": row.get(status_col, ""),
                "Success_Rate": success_rate,
                "Diagnostics": diagnostics
            }
            
            transformed_data.append(task_record)
    
    # Convert to DataFrame
    if transformed_data:
        transformed_df = pd.DataFrame(transformed_data)
        
        # Convert dates to datetime
        transformed_df["Completion_Date"] = pd.to_datetime(transformed_df["Completion_Date"], errors='coerce')
        
        # Create full name column
        transformed_df["Full_Name"] = transformed_df["Name"] + " " + transformed_df["Surname"]
        
        return transformed_df
    
    return pd.DataFrame()

def parse_rate(rate_value):
    """Parse success rate values in various formats"""
    if pd.isna(rate_value) or rate_value == "Not Started":
        return 0
    
    if isinstance(rate_value, (int, float)):
        return float(rate_value)
        
    # Handle string values
    if isinstance(rate_value, str):
        # Remove % sign if present
        rate_str = rate_value.replace("%", "").strip()
        try:
            return float(rate_str)
        except ValueError:
            return 0
    
    return 0

def analyze_student_data(df, start_date, end_date, min_success_rate, min_days, subject_filter):
    """Analyze student data based on filters"""
    try:
        # Convert dates to datetime objects
        start_date = pd.to_datetime(start_date)
        end_date = pd.to_datetime(end_date)
        
        # Create a copy of the DataFrame for filtering
        filtered_df = df.copy()
        
        # Apply subject filter if not "All"
        if subject_filter != "All":
            filtered_df = filtered_df[filtered_df["Subject"] == subject_filter]
        
        # Filter by date range, success rate, and status
        filtered_df = filtered_df[
            (filtered_df["Completion_Date"] >= start_date) &
            (filtered_df["Completion_Date"] <= end_date) &
            (filtered_df["Success_Rate"] > min_success_rate) &
            (filtered_df["Status"] == "Done")
        ]
        
        # Group by student name
        student_groups = filtered_df.groupby("Full_Name")
        
        # Store student summary data
        student_summaries = []
        
        # Process each student's data
        for student_name, group in student_groups:
            # Get the unique dates where the student completed at least one task
            completion_dates = sorted(group["Completion_Date"].dt.date.unique())
            days_worked = len(completion_dates)
            
            # Count total tasks completed
            total_tasks = len(group)
            
            # Only include students who worked on at least min_days
            if days_worked >= min_days:
                # Calculate average success rate
                avg_success = group["Success_Rate"].mean()
                
                # Calculate max streak (consecutive days)
                max_streak = calculate_max_streak(completion_dates)
                
                # Get first record for student info
                first_record = group.iloc[0]
                
                # Count diagnostic tests completed
                diagnostics_count = 0
                if 'Diagnostics' in group.columns and len(group) > 0:
                    # Get the first record's diagnostics dict
                    if isinstance(first_record['Diagnostics'], dict):
                        diagnostics_count = len(first_record['Diagnostics'])
                
                # Get unique subjects for this student
                subjects = sorted(group["Subject"].unique())
                subjects_str = ", ".join(subjects)
                
                student_summaries.append({
                    "Full_Name": student_name,
                    "Phone": first_record.get("Phone", ""),
                    "Grade": first_record.get("Grade", ""),
                    "Days_Worked": days_worked,
                    "Total_Tasks": total_tasks,
                    "Diagnostics_Count": diagnostics_count,
                    "Max_Streak": max_streak,
                    "Avg_Success": float(avg_success),
                    "Subjects": subjects_str
                })
        
        return student_summaries, filtered_df
        
    except Exception as e:
        print(f"Error during analysis: {str(e)}")
        import traceback
        traceback.print_exc()
        return [], df

def calculate_max_streak(dates):
    """Calculate the maximum number of consecutive days in the list of dates"""
    if len(dates) <= 1:
        return len(dates)
        
    streak_count = 1
    max_streak = 1
    
    for i in range(1, len(dates)):
        # Calculate difference with previous date
        date_diff = (dates[i] - dates[i-1]).days
        
        if date_diff == 1:  # Consecutive day
            streak_count += 1
            max_streak = max(max_streak, streak_count)
        else:
            streak_count = 1  # Reset streak counter
    
    return max_streak

def create_chart_data_json(top_students):
    """Create JSON data for the charts"""
    # Extract data for charts
    names = [r["Full_Name"] for r in top_students]
    days = [r["Days_Worked"] for r in top_students]
    tasks = [r["Total_Tasks"] for r in top_students]
    success_rates = [r["Avg_Success"] for r in top_students]
    max_streaks = [r["Max_Streak"] for r in top_students]
    
    # Create chart objects
    days_chart = {
        'x': days,
        'y': names,
        'type': 'bar',
        'orientation': 'h',
        'marker': {'color': 'rgba(58, 130, 246, 0.7)'}
    }
    
    tasks_chart = {
        'x': tasks,
        'y': names,
        'type': 'bar',
        'orientation': 'h',
        'marker': {'color': 'rgba(72, 187, 120, 0.7)'}
    }
    
    streaks_chart = {
        'x': max_streaks,
        'y': names,
        'type': 'bar',
        'orientation': 'h',
        'marker': {'color': 'rgba(237, 100, 166, 0.7)'}
    }
    
    return {
        'names': names,
        'days': days_chart,
        'tasks': tasks_chart,
        'streaks': streaks_chart
    }

def create_student_profile_data(student_data):
    """Create student profile data for the template"""
    student_info = student_data.iloc[0]
    
    # Calculate performance metrics
    completion_dates = sorted(student_data["Completion_Date"].dt.date.unique())
    days_worked = len(completion_dates)
    total_tasks = len(student_data)
    avg_success = student_data["Success_Rate"].mean()
    max_streak = calculate_max_streak(completion_dates)
    
    # Count diagnostic tests
    diagnostics_count = 0
    if 'Diagnostics' in student_data.columns and len(student_data) > 0:
        # Get the first record's diagnostics dict
        if isinstance(student_info.get('Diagnostics'), dict):
            diagnostics_count = len(student_info.get('Diagnostics', {}))
    
    # Get registration date as string
    reg_date = student_info.get("Registration_Date", "")
    if hasattr(reg_date, 'strftime'):
        reg_date = reg_date.strftime("%Y-%m-%d")
    
    # Get recent activity
    recent_activity = []
    recent_tasks = student_data.sort_values("Completion_Date", ascending=False).head(5)
    for _, row in recent_tasks.iterrows():
        recent_activity.append({
            'date': row["Completion_Date"].strftime("%Y-%m-%d"),
            'subject': row["Subject"],
            'task': row["Task"],
            'success_rate': f"{row['Success_Rate']:.2f}%"
        })
    
    return {
        'personal': {
            'name': student_info.get("Name", ""),
            'surname': student_info.get("Surname", ""),
            'phone': student_info.get("Phone", ""),
            'grade': student_info.get("Grade", ""),
            'parent_number': student_info.get("Parent_Number", ""),
        },
        'academic': {
            'school': student_info.get("School", ""),
            'registration_date': reg_date,
            'subjects': ", ".join(sorted(student_data["Subject"].unique())),
        },
        'performance': {
            'days_worked': days_worked,
            'total_tasks': total_tasks,
            'diagnostics_count': diagnostics_count,
            'max_streak': max_streak,
            'avg_success': f"{avg_success:.2f}%",
        },
        'recent_activity': recent_activity
    }

def create_progress_chart(student_data):
    """Create progress chart data"""
    # Daily success rate data
    daily_data = student_data.groupby(student_data["Completion_Date"].dt.date).agg({
        "Success_Rate": "mean"
    }).reset_index()
    
    # Sort by date
    daily_data = daily_data.sort_values("Completion_Date")
    
    # Convert to lists for the chart
    dates = [d.strftime("%Y-%m-%d") for d in daily_data["Completion_Date"]]
    rates = [float(r) for r in daily_data["Success_Rate"]]
    
    # Create chart with Plotly
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=dates,
        y=rates,
        mode='lines+markers',
        name='Success Rate',
        line=dict(color='royalblue', width=2),
        marker=dict(size=8)
    ))
    
    fig.update_layout(
        title='Daily Average Success Rate',
        xaxis_title='Date',
        yaxis_title='Success Rate (%)',
        yaxis=dict(range=[0, 100]),
        height=500
    )
    
    # Convert to JSON for the template
    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

def create_diagnostic_chart(student_data):
    """Create diagnostic chart data"""
    # Extract diagnostic data
    diagnostics = student_data.iloc[0].get("Diagnostics", {})
    
    if not diagnostics:
        return None
    
    # Create scores for chart visualization
    chart_data = {}
    
    for test, score in diagnostics.items():
        try:
            if isinstance(score, (int, float)):
                chart_data[test] = float(score)
            elif isinstance(score, str) and score.replace('.', '', 1).isdigit():
                chart_data[test] = float(score)
        except:
            # Skip items that can't be converted to float
            pass
    
    if not chart_data:
        return None
    
    # Sort by diagnostic number
    sorted_chart_data = {}
    
    # Extract diagnostic numbers for proper sorting
    diag_numbers = []
    for key in chart_data.keys():
        if "Diagnostic" in key:
            try:
                # Extract numbers from diagnostic names (e.g., "Diagnostic 5" -> 5)
                number = int(''.join(filter(str.isdigit, key)))
                diag_numbers.append((number, key))
            except:
                diag_numbers.append((999, key))  # Use high number for non-standard naming
        else:
            diag_numbers.append((999, key))
    
    # Sort by diagnostic number
    diag_numbers.sort()
    
    # Create ordered data
    for _, key in diag_numbers:
        sorted_chart_data[key] = chart_data[key]
    
    # Calculate average diagnostic score
    avg_score = sum(sorted_chart_data.values()) / len(sorted_chart_data) if sorted_chart_data else 0
    
    # Shorten test names for display
    short_names = []
    for test in sorted_chart_data.keys():
        if "Diagnostic" in test:
            parts = test.split()
            short_names.append(f"{parts[0]} {parts[1]}" if len(parts) > 1 else test)
        else:
            short_names.append(test[:15] + "..." if len(test) > 18 else test)
    
    # Create line chart
    fig = go.Figure()
    
    # Add line for diagnostics
    fig.add_trace(go.Scatter(
        x=list(range(len(sorted_chart_data))),
        y=list(sorted_chart_data.values()),
        mode='lines+markers',
        name='Diagnostic Scores',
        line=dict(color='blue', width=2),
        marker=dict(size=10)
    ))
    
    # Add horizontal line for average
    fig.add_shape(
        type="line",
        x0=-0.5,
        x1=len(sorted_chart_data) - 0.5,
        y0=avg_score,
        y1=avg_score,
        line=dict(
            color="red",
            width=2,
            dash="dash",
        )
    )
    
    # Add annotation for average
    fig.add_annotation(
        x=len(sorted_chart_data) - 1,
        y=avg_score,
        text=f"Average: {avg_score:.1f}%",
        showarrow=False,
        yshift=10,
        font=dict(color="red")
    )
    
    # Add value labels above each point
    for i, score in enumerate(sorted_chart_data.values()):
        fig.add_annotation(
            x=i,
            y=score,
            text=f"{score:.1f}%",
            showarrow=False,
            yshift=10
        )
    
    # Update layout
    fig.update_layout(
        title='Diagnostic Test Scores Progress',
        xaxis=dict(
            title='Diagnostic Test',
            tickmode='array',
            tickvals=list(range(len(short_names))),
            ticktext=short_names,
            tickangle=45
        ),
        yaxis=dict(
            title='Score (%)',
            range=[0, 105]
        ),
        height=500
    )
    
    # Convert to JSON for the template
    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

def create_subjects_chart(student_data):
    """Create chart comparing different subjects"""
    # Group by subject
    subjects = sorted(student_data["Subject"].unique())
    
    if len(subjects) <= 1:
        return None
        
    # Calculate subject metrics
    subject_metrics = []
    
    for subject in subjects:
        subject_data = student_data[student_data["Subject"] == subject]
        
        # Calculate metrics
        task_count = len(subject_data)
        avg_success = subject_data["Success_Rate"].mean()
        days_worked = len(subject_data["Completion_Date"].dt.date.unique())
        
        subject_metrics.append({
            "Subject": subject,
            "Tasks": task_count,
            "Success": avg_success,
            "Days": days_worked
        })
    
    # Create bar chart
    fig = go.Figure()
    
    # Extract data for plotting
    x_subjects = [m["Subject"] for m in subject_metrics]
    tasks = [m["Tasks"] for m in subject_metrics]
    success = [m["Success"] for m in subject_metrics]
    days = [m["Days"] for m in subject_metrics]
    
    # Add traces for each metric
    fig.add_trace(go.Bar(
        x=x_subjects,
        y=tasks,
        name='Tasks Completed',
        marker_color='green'
    ))
    
    fig.add_trace(go.Bar(
        x=x_subjects,
        y=success,
        name='Avg Success Rate (%)',
        marker_color='blue'
    ))
    
    fig.add_trace(go.Bar(
        x=x_subjects,
        y=days,
        name='Days Worked',
        marker_color='purple'
    ))
    
    # Update layout
    fig.update_layout(
        title='Subject Performance Comparison',
        xaxis_title='Subject',
        yaxis_title='Value',
        barmode='group',
        height=500
    )
    
    # Convert to JSON for the template
    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

def create_timeline_data(student_data):
    """Create timeline data for the template"""
    # Get date range from first task to today
    first_date = student_data["Completion_Date"].min().date()
    last_date = max(datetime.now().date(), student_data["Completion_Date"].max().date())
    
    # Create a date range
    date_range = pd.date_range(start=first_date, end=last_date)
    
    # Group by date
    date_groups = student_data.groupby(student_data["Completion_Date"].dt.date)
    
    # Create timeline data
    timeline_data = []
    
    for date in date_range:
        date_only = date.date()
        date_str = date_only.strftime("%Y-%m-%d")
        
        # Check if any tasks were completed on this date
        if date_only in date_groups.groups:
            day_data = date_groups.get_group(date_only)
            tasks_count = len(day_data)
            avg_success = day_data["Success_Rate"].mean()
            
            # Tasks completed with their success rates
            task_details = ", ".join([f"{row['Task']}: {row['Success_Rate']:.1f}%" 
                                     for _, row in day_data.iterrows()])
            
            timeline_data.append({
                'date': date_str,
                'subjects': ", ".join(day_data["Subject"].unique()),
                'tasks_info': f"{tasks_count} tasks ({task_details})",
                'avg_success': f"{avg_success:.2f}%",
                'has_tasks': True
            })
        else:
            timeline_data.append({
                'date': date_str,
                'subjects': "",
                'tasks_info': "",
                'avg_success': "",
                'has_tasks': False
            })
    
    return timeline_data

def create_task_data(student_data):
    """Create task data for the template"""
    # Sort data by date
    sorted_data = student_data.sort_values(by=["Completion_Date", "Subject"])
    
    # Create task data
    task_data = []
    
    for _, row in sorted_data.iterrows():
        task_data.append({
            'date': row["Completion_Date"].strftime("%Y-%m-%d"),
            'subject': row["Subject"],
            'task': row["Task"],
            'success_rate': f"{row['Success_Rate']:.2f}%",
            'status': row["Status"],
            'success_rate_number': float(row["Success_Rate"])  # For color coding
        })
    
    return task_data

def create_comparison_data(session_data, selected_students, compare_by, subject_filter):
    """Create comparison data for the template"""
    if not selected_students or len(selected_students) < 2:
        return None
    
    comparison_data = []
    
    for student_name in selected_students:
        # Find student in results data
        student = next((s for s in session_data['results_data'] if s["Full_Name"] == student_name), None)
        if not student:
            continue
            
        # Get the student's detailed data
        if student_name not in session_data['student_full_data']:
            continue
            
        student_data = session_data['student_full_data'][student_name]
        
        # Filter by subject if needed
        if subject_filter != "All":
            student_data = student_data[student_data["Subject"] == subject_filter]
            if len(student_data) == 0:
                continue
        
        # Get comparison value based on selected criteria
        if compare_by == "Success Rate":
            value = student["Avg_Success"]
            display_value = f"{value:.2f}%"
        elif compare_by == "Tasks Completed":
            value = student["Total_Tasks"]
            display_value = str(value)
        elif compare_by == "Days Worked":
            value = student["Days_Worked"]
            display_value = str(value)
        elif compare_by == "Max Streak":
            value = student["Max_Streak"]
            display_value = str(value)
        elif compare_by == "Diagnostics":
            value = student.get("Diagnostics_Count", 0)
            display_value = str(value)
        
        # Add to comparison data
        comparison_data.append({
            'name': student_name,
            'value': value,
            'display_value': display_value,
            'grade': student["Grade"],
            'days_worked': student["Days_Worked"],
            'total_tasks': student["Total_Tasks"],
            'subjects': student["Subjects"]
        })
    
    # Sort by the comparison value (descending)
    comparison_data = sorted(comparison_data, key=lambda x: x['value'], reverse=True)
    
    return comparison_data

if __name__ == "__main__":
    # Create necessary dirs
    os.makedirs('static', exist_ok=True)
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)
    
    app.run(debug=True)
