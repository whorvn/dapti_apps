from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_file
import os
import sys  # Add this import
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import matplotlib.dates as mdates
import io
import base64
from werkzeug.utils import secure_filename
import uuid
import json
from datetime import datetime, timedelta
import traceback

app = Flask(__name__)
app.secret_key = 'student_analysis_app_secret_key'  # Change this in production

# Configure upload folder
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
ALLOWED_EXTENSIONS = {'xlsx', 'xls', 'csv'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Create upload folder if it doesn't exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Helper function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Helper function to parse success rate values
def parse_rate(rate_value):
    """Helper method to parse success rate values in various formats"""
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

# Helper function to calculate max streak
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

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
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
        user_dir = os.path.join(app.config['UPLOAD_FOLDER'], user_id)
        if not os.path.exists(user_dir):
            os.makedirs(user_dir)
            
        # Save file with secure filename
        filename = secure_filename(file.filename)
        file_path = os.path.join(user_dir, filename)
        file.save(file_path)
        
        # Process the file
        try:
            # Check file type
            if filename.endswith('.csv'):
                df = pd.read_csv(file_path)
            else:
                df = pd.read_excel(file_path, engine='openpyxl')
            
            # Process the multi-subject format (similar to original code)
            transformed_data = []
            
            # Identify diagnostic columns
            diagnostic_cols = [col for col in df.columns if 'Diagnostic' in str(col) and 'Accuracy' in str(col)]
            
            # Define main task column groups - match exactly provided format
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
                        continue
                    
                    # Skip if no task or "Not Started"
                    if pd.isna(row.get(task_col)) or row.get(task_col) == "Not Started":
                        continue
                    
                    # Create a record for this task
                    task_record = {
                        **student_data,  # Include all student data
                        "Subject": subject,
                        "Task": row.get(task_col, ""),
                        "Completion_Date": row.get(date_col),
                        "Status": row.get(status_col, ""),
                        "Success_Rate": parse_rate(row.get(rate_col)),
                        "Diagnostics": diagnostics
                    }
                    
                    transformed_data.append(task_record)
            
            # Convert the transformed data to a DataFrame
            if transformed_data:
                df = pd.DataFrame(transformed_data)
                
                # Convert Success_Rate to numeric, handling all possible formats
                if "Success_Rate" in df.columns and df["Success_Rate"].dtype == object:
                    df["Success_Rate"] = df["Success_Rate"].astype(str).replace('Not Started', '0')
                    df["Success_Rate"] = df["Success_Rate"].astype(str).replace('', '0')
                    df["Success_Rate"] = df["Success_Rate"].astype(str).str.rstrip("%")
                    df["Success_Rate"] = pd.to_numeric(df["Success_Rate"], errors='coerce')
                
                # Fill any NaN values with 0
                if "Success_Rate" in df.columns:
                    df["Success_Rate"].fillna(0, inplace=True)
                
                # Convert dates to datetime with explicit format
                if "Completion_Date" in df.columns:
                    df["Completion_Date"] = pd.to_datetime(df["Completion_Date"], errors='coerce')
                
                # Create full name column
                df["Full_Name"] = df["Name"] + " " + df["Surname"]
                
                # Save processed data to user session file
                processed_file = os.path.join(user_dir, 'processed_data.pkl')
                df.to_pickle(processed_file)
                
                # Get available subjects for filter
                subjects = df["Subject"].unique().tolist()
                
                # Store subjects in session
                session['subjects'] = subjects
                
                flash('File uploaded and processed successfully!', 'success')
                return redirect(url_for('analyze'))
            else:
                flash('No task data found in the file. Check the format.', 'error')
                return redirect(url_for('index'))
                
        except Exception as e:
            flash(f'Error processing file: {str(e)}', 'error')
            traceback.print_exc()
            return redirect(url_for('index'))
    else:
        flash('Invalid file type. Please upload an Excel (.xlsx, .xls) or CSV file.', 'error')
        return redirect(url_for('index'))

# Create a custom JSON encoder to handle NumPy data types
class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (np.integer, np.int64)):
            return int(obj)
        elif isinstance(obj, (np.floating, np.float64)):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        return super(NumpyEncoder, self).default(obj)

# Enhanced function to handle all non-serializable types including timestamps
def convert_to_serializable(obj):
    """Convert non-serializable objects to serializable format."""
    if isinstance(obj, (np.integer, np.int64)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float64)):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, pd.Timestamp):
        return obj.strftime('%Y-%m-%d %H:%M:%S')
    elif isinstance(obj, datetime):
        return obj.strftime('%Y-%m-%d %H:%M:%S')
    else:
        # Don't try to check with pd.api.types.is_datetime64_any_dtype
        # Just return the object as is
        return obj

# Bug fix: Make sure the custom NumpyEncoder is actually used
@app.route('/analyze', methods=['GET', 'POST'])
def analyze():
    if 'user_id' not in session:
        flash('Please upload a file first', 'warning')
        return redirect(url_for('index'))
    
    user_id = session['user_id']
    user_dir = os.path.join(app.config['UPLOAD_FOLDER'], user_id)
    processed_file = os.path.join(user_dir, 'processed_data.pkl')
    
    if not os.path.exists(processed_file):
        flash('No processed data found. Please upload a file first.', 'warning')
        return redirect(url_for('index'))
    
    # Load the processed data
    df = pd.read_pickle(processed_file)
    
    # Default filter values or get from form
    if request.method == 'POST':
        start_date = pd.to_datetime(request.form.get('start_date'))
        end_date = pd.to_datetime(request.form.get('end_date'))
        min_success_rate = float(request.form.get('min_success_rate', 0))
        min_days = int(request.form.get('min_days', 7))
        selected_subject = request.form.get('subject', 'All')
    else:
        # Default values
        start_date = pd.to_datetime('2025-02-19')
        end_date = pd.to_datetime('2025-02-27')
        min_success_rate = 0
        min_days = 7
        selected_subject = 'All'
    
    # Store current filter values in session for displaying in template
    session['filter_values'] = {
        'start_date': start_date.strftime('%Y-%m-%d'),
        'end_date': end_date.strftime('%Y-%m-%d'),
        'min_success_rate': min_success_rate,
        'min_days': min_days,
        'subject': selected_subject
    }
    
    # Apply subject filter if needed
    filtered_df = df.copy()
    if selected_subject != "All":
        filtered_df = filtered_df[filtered_df["Subject"] == selected_subject]
    
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
    student_full_data = {}  # Store full student data
    
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
                "Avg_Success": avg_success,
                "Subjects": subjects_str
            })
            
            # Store full student data
            student_full_data[student_name] = group
    
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
                except Exception as e:
                    # If there's any error, just use the original value
                    # and convert it to a string if it's not a basic type
                    if isinstance(value, (str, int, float, bool, type(None))):
                        clean_record[key] = value
                    else:
                        clean_record[key] = str(value)
            clean_records.append(clean_record)
        clean_full_data[name] = clean_records
    
    # Save as JSON files with standard JSON encoder (no custom encoder needed now)
    with open(summary_file, 'w') as f:
        json.dump(clean_summaries, f)
    
    with open(full_data_file, 'w') as f:
        json.dump(clean_full_data, f)
    
    # Generate summary chart if there are results
    chart_url = None
    if student_summaries:
        chart_url = generate_summary_chart(student_summaries, user_id)
    
    return render_template('analyze.html', 
                           students=student_summaries, 
                           chart_url=chart_url, 
                           subjects=session.get('subjects', []))

def generate_summary_chart(results, user_id):
    """Generate summary charts for all qualifying students"""
    if not results:
        return None
        
    # Sort by days worked
    results_sorted = sorted(results, key=lambda x: x["Days_Worked"], reverse=True)
    
    # Limit to top 10 students for readability
    top_students = results_sorted[:10]
    
    # Extract data for charts
    names = [r["Full_Name"] for r in top_students]
    days = [r["Days_Worked"] for r in top_students]
    tasks = [r["Total_Tasks"] for r in top_students]
    max_streaks = [r["Max_Streak"] for r in top_students]
    
    # Create a figure with student analysis - with 3 subplots
    fig = Figure(figsize=(10, 12))
    
    # Days worked chart
    ax1 = fig.add_subplot(311)
    y_pos = np.arange(len(names))
    ax1.barh(y_pos, days, color="skyblue")
    ax1.set_yticks(y_pos)
    ax1.set_yticklabels(names)
    ax1.set_xlabel("Days Worked")
    ax1.set_title("Top Students by Days Worked")
    
    # Total tasks chart
    ax2 = fig.add_subplot(312)
    ax2.barh(y_pos, tasks, color="lightgreen")
    ax2.set_yticks(y_pos)
    ax2.set_yticklabels(names)
    ax2.set_xlabel("Total Tasks Completed")
    ax2.set_title("Tasks Completed by Top Students")
    
    # Max streak chart
    ax3 = fig.add_subplot(313)
    ax3.barh(y_pos, max_streaks, color="salmon")
    ax3.set_yticks(y_pos)
    ax3.set_yticklabels(names)
    ax3.set_xlabel("Maximum Consecutive Days Streak")
    ax3.set_title("Max Streaks by Top Students")
    
    # Adjust layout
    fig.tight_layout()
    
    # Save the figure
    chart_filename = f'summary_chart_{user_id}.png'
    chart_path = os.path.join('static', 'charts', chart_filename)
    
    # Ensure directory exists
    os.makedirs(os.path.join('static', 'charts'), exist_ok=True)
    
    # Save figure
    fig.savefig(chart_path)
    
    return url_for('static', filename=f'charts/{chart_filename}')

@app.route('/student/<name>')
def student_detail(name):
    if 'user_id' not in session:
        flash('Session expired. Please upload file again.', 'warning')
        return redirect(url_for('index'))
    
    user_id = session['user_id']
    user_dir = os.path.join(app.config['UPLOAD_FOLDER'], user_id)
    
    # Load student summaries
    summary_file = os.path.join(user_dir, 'student_summaries.json')  # Changed extension
    full_data_file = os.path.join(user_dir, 'student_full_data.json')  # Changed extension
    
    if not os.path.exists(summary_file) or not os.path.exists(full_data_file):
        flash('Student data not found. Please analyze data first.', 'warning')
        return redirect(url_for('analyze'))
    
    # Load student data
    with open(summary_file, 'r') as f:
        student_summaries = json.load(f)
    
    with open(full_data_file, 'r') as f:
        student_full_data_json = json.load(f)
    
    # Find student in summaries
    student_summary = next((s for s in student_summaries if s["Full_Name"] == name), None)
    
    if not student_summary:
        flash(f'Student {name} not found', 'error')
        return redirect(url_for('analyze'))
    
    # Convert JSON data back to DataFrame
    if name in student_full_data_json:
        student_data = pd.DataFrame(student_full_data_json[name])
        
        # Convert dates back to datetime
        if "Completion_Date" in student_data.columns:
            student_data["Completion_Date"] = pd.to_datetime(student_data["Completion_Date"])
    else:
        flash(f'Detailed data for student {name} not found', 'error')
        return redirect(url_for('analyze'))
    
    # Generate charts
    profile_info = get_student_profile_info(student_data)
    timeline_data = get_student_timeline_data(student_data)
    tasks_data = get_student_tasks_data(student_data)
    progress_charts = generate_progress_charts(student_data, user_id, name)
    diagnostics_data = get_diagnostics_data(student_data)
    subject_comparison = generate_subject_comparison(student_data, user_id, name)
    
    return render_template('student_detail.html',
                          student=student_summary,
                          profile=profile_info,
                          timeline_data=timeline_data,
                          tasks_data=tasks_data,
                          progress_charts=progress_charts,
                          diagnostics_data=diagnostics_data,
                          subject_comparison=subject_comparison)

def get_student_profile_info(student_data):
    # Get first row for student info - all records should have same student info
    student_info = student_data.iloc[0].to_dict()
    
    # Calculate performance metrics
    completion_dates = sorted(student_data["Completion_Date"].dt.date.unique())
    days_worked = len(completion_dates)
    total_tasks = len(student_data)
    avg_success = student_data["Success_Rate"].mean()
    max_streak = calculate_max_streak(completion_dates)
    
    # Count diagnostic tests
    diagnostics_count = 0
    if 'Diagnostics' in student_data.columns and len(student_data) > 0:
        if isinstance(student_info.get('Diagnostics'), dict):
            diagnostics_count = len(student_info.get('Diagnostics', {}))
    
    # Get recent activities
    recent_tasks = student_data.sort_values("Completion_Date", ascending=False).head(5)
    recent_activities = []
    
    for _, row in recent_tasks.iterrows():
        date_str = row["Completion_Date"].strftime("%Y-%m-%d")
        recent_activities.append({
            "date": date_str,
            "subject": row["Subject"],
            "task": row["Task"],
            "success_rate": f"{row['Success_Rate']:.2f}%"
        })
    
    return {
        "personal_info": {
            "first_name": student_info.get("Name", ""),
            "last_name": student_info.get("Surname", ""),
            "phone": student_info.get("Phone", ""),
            "grade": student_info.get("Grade", "")
        },
        "academic_info": {
            "school": student_info.get("School", ""),
            "registration_date": student_info.get("Registration_Date", ""),
            "subjects": ", ".join(sorted(student_data["Subject"].unique()))
        },
        "contact_info": {
            "parent_number": student_info.get("Parent_Number", "")
        },
        "performance": {
            "days_worked": days_worked,
            "total_tasks": total_tasks,
            "diagnostics_count": diagnostics_count,
            "max_streak": max_streak,
            "avg_success": f"{avg_success:.2f}%"
        },
        "recent_activity": recent_activities
    }

def get_student_timeline_data(student_data):
    # Create a date range that spans from first task to today
    first_date = student_data["Completion_Date"].min().date()
    last_date = max(datetime.now().date(), student_data["Completion_Date"].max().date())
    
    # Group data by date
    date_groups = student_data.groupby(student_data["Completion_Date"].dt.date)
    
    # Create a date range from first task to today
    date_range = pd.date_range(start=first_date, end=last_date)
    
    timeline_data = []
    
    # Populate the timeline with all dates
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
                "date": date_str,
                "subjects": ", ".join(day_data["Subject"].unique()),
                "tasks_count": tasks_count,
                "task_details": task_details,
                "avg_success": f"{avg_success:.2f}%",
                "has_task": True
            })
        else:
            # No tasks on this day
            timeline_data.append({
                "date": date_str,
                "subjects": "-",
                "tasks_count": 0,
                "task_details": "No tasks",
                "avg_success": "-",
                "has_task": False
            })
    
    return timeline_data

def get_student_tasks_data(student_data):
    # Sort student data by completion date
    sorted_data = student_data.sort_values(by=["Completion_Date", "Task"])
    
    tasks_data = []
    
    # Prepare tasks data
    for _, row in sorted_data.iterrows():
        date_str = row["Completion_Date"].strftime("%Y-%m-%d")
        
        success_rate = row["Success_Rate"]
        success_class = ""
        if success_rate >= 80:
            success_class = "high-success"
        elif success_rate >= 50:
            success_class = "medium-success"
        else:
            success_class = "low-success"
        
        tasks_data.append({
            "date": date_str,
            "subject": row["Subject"],
            "task": row["Task"],
            "success_rate": f"{row['Success_Rate']:.2f}%",
            "status": row["Status"],
            "success_class": success_class
        })
    
    return tasks_data

def generate_progress_charts(student_data, user_id, student_name):
    # Daily success rate chart
    daily_data = student_data.groupby(student_data["Completion_Date"].dt.date).agg({
        "Success_Rate": "mean"
    }).reset_index()
    
    # Sort by date
    daily_data = daily_data.sort_values("Completion_Date")
    
    # Create the figure with multiple subplots
    fig = Figure(figsize=(10, 12))
    
    # Daily success rate chart
    ax1 = fig.add_subplot(311)
    ax1.plot(daily_data["Completion_Date"], daily_data["Success_Rate"], 
             marker='o', linestyle='-', color='blue')
    ax1.set_title('Daily Average Success Rate')
    ax1.set_ylabel('Success Rate (%)')
    ax1.set_xlabel('Date')
    ax1.grid(True, linestyle='--', alpha=0.7)
    
    # Format dates on x-axis
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    fig.autofmt_xdate()
    
    # Task completion chart - count tasks per day
    task_counts = student_data.groupby(student_data["Completion_Date"].dt.date).size().reset_index()
    task_counts.columns = ["Completion_Date", "Task_Count"]
    
    # Create the second subplot (tasks completed per day)
    ax2 = fig.add_subplot(312)
    ax2.bar(task_counts["Completion_Date"], task_counts["Task_Count"], color='green', alpha=0.7)
    ax2.set_title('Tasks Completed Per Day')
    ax2.set_ylabel('Number of Tasks')
    ax2.set_xlabel('Date')
    ax2.grid(True, linestyle='--', alpha=0.7, axis='y')
    
    # Format dates on x-axis
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    
    # Subject performance chart
    ax3 = fig.add_subplot(313)
    
    # Group by subject
    subject_data = student_data.groupby("Subject").agg({
        "Success_Rate": "mean",
        "Task": "count"
    }).reset_index()
    
    # Sort by number of tasks
    subject_data = subject_data.sort_values("Task", ascending=False)
    
    # Bar chart for subjects
    bars = ax3.bar(subject_data["Subject"], subject_data["Success_Rate"], color='purple', alpha=0.7)
    
    # Add task count as text above bars
    for bar, count in zip(bars, subject_data["Task"]):
        height = bar.get_height()
        ax3.text(bar.get_x() + bar.get_width()/2., height + 2,
                f'{count} tasks', ha='center', va='bottom', rotation=0)
    
    ax3.set_title('Average Success Rate by Subject')
    ax3.set_ylabel('Success Rate (%)')
    ax3.set_ylim(0, 105)  # Set y limit to accommodate annotations
    ax3.grid(True, linestyle='--', alpha=0.7, axis='y')
    
    # Rotate x-axis labels for better readability
    plt.setp(ax3.get_xticklabels(), rotation=45, ha='right')
    
    # Adjust layout
    fig.tight_layout()
    
    # Save chart
    chart_filename = f'progress_chart_{user_id}_{student_name.replace(" ", "_")}.png'
    chart_path = os.path.join('static', 'charts', chart_filename)
    
    # Save figure
    fig.savefig(chart_path)
    
    return url_for('static', filename=f'charts/{chart_filename}')

def get_diagnostics_data(student_data):
    # Extract diagnostic data
    diagnostics = student_data.iloc[0].get("Diagnostics", {})
    
    if not diagnostics:
        return {
            "has_data": False,
            "tests": []
        }
    
    # Calculate average diagnostic score if possible
    diagnostic_scores = list(diagnostics.values())
    avg_score = None
    
    if diagnostic_scores:
        try:
            # Convert to numeric if they're strings
            numeric_scores = []
            for score in diagnostic_scores:
                if isinstance(score, (int, float)):
                    numeric_scores.append(float(score))
                elif isinstance(score, str) and score.replace('.', '', 1).isdigit():
                    numeric_scores.append(float(score))
            
            if numeric_scores:
                avg_score = sum(numeric_scores) / len(numeric_scores)
        except:
            pass
    
    # Prepare diagnostics data
    tests_data = []
    for test, score in diagnostics.items():
        tests_data.append({
            "test": test,
            "score": score
        })
    
    return {
        "has_data": True,
        "count": len(diagnostics),
        "avg_score": f"{avg_score:.2f}%" if avg_score is not None else "N/A",
        "tests": tests_data
    }

def generate_subject_comparison(student_data, user_id, student_name):
    subjects = sorted(student_data["Subject"].unique())
    
    if len(subjects) <= 1:
        return None
        
    # Create figure for subject comparison
    fig = Figure(figsize=(10, 6))
    ax = fig.add_subplot(111)
    
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
    
    # Create bar chart comparing subjects
    x = np.arange(len(subjects))
    width = 0.25
    
    # Extract metrics for plotting
    tasks = [metric["Tasks"] for metric in subject_metrics]
    success = [metric["Success"] for metric in subject_metrics]
    days = [metric["Days"] for metric in subject_metrics]
    
    # Plot bars
    ax.bar(x - width, tasks, width, label='Tasks Completed')
    ax.bar(x, success, width, label='Avg Success Rate (%)')
    ax.bar(x + width, days, width, label='Days Worked')
    
    # Add labels and legend
    ax.set_xlabel('Subject')
    ax.set_ylabel('Value')
    ax.set_title('Subject Comparison')
    ax.set_xticks(x)
    ax.set_xticklabels(subjects)
    ax.legend()
    
    # Adjust layout
    fig.tight_layout()
    
    # Save chart
    chart_filename = f'subject_chart_{user_id}_{student_name.replace(" ", "_")}.png'
    chart_path = os.path.join('static', 'charts', chart_filename)
    
    # Save figure
    fig.savefig(chart_path)
    
    return url_for('static', filename=f'charts/{chart_filename}')

@app.route('/compare', methods=['GET', 'POST'])
def compare_students():
    if 'user_id' not in session:
        flash('Please upload a file first', 'warning')
        return redirect(url_for('index'))
    
    user_id = session['user_id']
    user_dir = os.path.join(app.config['UPLOAD_FOLDER'], user_id)
    summary_file = os.path.join(user_dir, 'student_summaries.json')  # Changed extension
    
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
        selected_data = [s for s in student_summaries if s["Full_Name"] in selected_students]
        
        # Generate comparison chart
        chart_url = generate_comparison_chart(selected_data, comparison_type, user_id)
        
        return render_template('compare.html', 
                               students=student_summaries,
                               selected_students=selected_students,
                               comparison_type=comparison_type,
                               chart_url=chart_url,
                               comparison_data=selected_data)
    
    return render_template('compare.html', students=student_summaries)

def generate_comparison_chart(students, comparison_type, user_id):
    """Generate a chart comparing selected students"""
    if not students:
        return None
    
    # Create a figure for comparison
    fig = Figure(figsize=(10, 6))
    ax = fig.add_subplot(111)
    
    # Prepare data based on comparison type
    names = [student["Full_Name"] for student in students]
    
    if comparison_type == "Success Rate":
        values = [float(student["Avg_Success"]) for student in students]  # Convert to native Python float
        ylabel = "Average Success Rate (%)"
        title = "Success Rate Comparison"
        
    elif comparison_type == "Tasks Completed":
        values = [int(student["Total_Tasks"]) for student in students]  # Convert to native Python int
        ylabel = "Total Tasks Completed"
        title = "Tasks Completed Comparison"
        
    elif comparison_type == "Days Worked":
        values = [int(student["Days_Worked"]) for student in students]  # Convert to native Python int
        ylabel = "Days Worked"
        title = "Days Worked Comparison"
        
    elif comparison_type == "Max Streak":
        values = [int(student["Max_Streak"]) for student in students]  # Convert to native Python int
        ylabel = "Maximum Consecutive Days"
        title = "Max Streak Comparison"
        
    else:
        values = [int(student.get("Diagnostics_Count", 0)) for student in students]  # Convert to native Python int
        ylabel = "Diagnostics Completed"
        title = "Diagnostics Comparison"
    
    # Create horizontal bar chart
    y_pos = np.arange(len(names))
    ax.barh(y_pos, values, align='center')
    ax.set_yticks(y_pos)
    ax.set_yticklabels(names)
    ax.invert_yaxis()  # labels read top-to-bottom
    ax.set_xlabel(ylabel)
    ax.set_title(title)
    
    # Add value labels
    for i, v in enumerate(values):
        ax.text(v + 0.1, i, str(v), va='center')
    
    # Adjust layout
    fig.tight_layout()
    
    # Save chart
    chart_filename = f'comparison_chart_{user_id}_{comparison_type.replace(" ", "_")}.png'
    chart_path = os.path.join('static', 'charts', chart_filename)
    
    # Save figure
    fig.savefig(chart_path)
    
    return url_for('static', filename=f'charts/{chart_filename}')

@app.route('/export')
def export_data():
    if 'user_id' not in session:
        flash('Please upload a file first', 'warning')
        return redirect(url_for('index'))
    
    user_id = session['user_id']
    user_dir = os.path.join(app.config['UPLOAD_FOLDER'], user_id)
    summary_file = os.path.join(user_dir, 'student_summaries.json')
    
    if not os.path.exists(summary_file):
        flash('No student data not found. Please analyze data first.', 'warning')
        return redirect(url_for('analyze'))
    
    # Load student summaries
    with open(summary_file, 'r') as f:
        student_summaries = json.load(f)
    
    # Check if xlsxwriter is available
    try:
        import xlsxwriter
        excel_export_available = True
    except ImportError:
        excel_export_available = False
        # Try to install xlsxwriter
        try:
            import subprocess
            subprocess.check_call([sys.executable, "-m", "pip", "install", "xlsxwriter"])
            import xlsxwriter
            excel_export_available = True
        except:
            flash('The xlsxwriter package is required for Excel export. Falling back to CSV format.', 'warning')
    
    # Create file in memory
    output = io.BytesIO()
    
    # Convert to DataFrame
    df = pd.DataFrame(student_summaries)
    
    # Reorder columns for better readability
    if not df.empty:
        column_order = [
            'Full_Name', 'Phone', 'Grade', 'Days_Worked', 'Total_Tasks',
            'Diagnostics_Count', 'Max_Streak', 'Avg_Success', 'Subjects'
        ]
        # Only include columns that exist in the dataframe
        available_columns = [col for col in column_order if col in df.columns]
        df = df[available_columns]
    
    # Generate a filename timestamp
    now = datetime.now()
    timestamp = now.strftime('%Y%m%d_%H%M%S')
    
    # Export based on available packages
    if excel_export_available:
        # Export to Excel
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name='Student Analysis', index=False)
        
        # Seek to beginning of file
        output.seek(0)
        
        filename = f"student_analysis_{timestamp}.xlsx"
        mimetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    else:
        # Fall back to CSV if xlsxwriter is not available
        df.to_csv(output, index=False)
        #
        # Seek to beginning of file
        output.seek(0)
        
        filename = f"student_analysis_{timestamp}.csv"
        mimetype = 'text/csv'
    
    return send_file(
        output,
        mimetype=mimetype,
        as_attachment=True,
        download_name=filename
    )


if __name__ == '__main__':
    app.run(debug=True)

