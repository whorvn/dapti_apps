import pandas as pd
import tkinter as tk
from tkinter import filedialog, ttk
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import os
import numpy as np
import matplotlib.dates as mdates

class StudentAnalysisApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Student Task Analysis")
        self.root.geometry("900x700")
        self.df = None
        
        # Create frames
        self.file_frame = ttk.Frame(root, padding="10")
        self.file_frame.pack(fill="x")
        
        self.filter_frame = ttk.Frame(root, padding="10")
        self.filter_frame.pack(fill="x")
        
        self.result_frame = ttk.Frame(root, padding="10")
        self.result_frame.pack(fill="both", expand=True)
        
        # File selection
        ttk.Label(self.file_frame, text="Excel File:").grid(row=0, column=0, sticky="w")
        self.file_path = tk.StringVar()
        ttk.Entry(self.file_frame, textvariable=self.file_path, width=50).grid(row=0, column=1, padx=5)
        ttk.Button(self.file_frame, text="Browse...", command=self.browse_file).grid(row=0, column=2)
        ttk.Button(self.file_frame, text="Load Data", command=self.load_data).grid(row=0, column=3, padx=5)
        
        # Filter options
        ttk.Label(self.filter_frame, text="Start Date:").grid(row=0, column=0, sticky="w")
        self.start_date = tk.StringVar(value="2025-02-19")
        ttk.Entry(self.filter_frame, textvariable=self.start_date, width=12).grid(row=0, column=1, padx=5)
        
        ttk.Label(self.filter_frame, text="End Date:").grid(row=0, column=2, sticky="w")
        self.end_date = tk.StringVar(value="2025-02-27")
        ttk.Entry(self.filter_frame, textvariable=self.end_date, width=12).grid(row=0, column=3, padx=5)
        
        ttk.Label(self.filter_frame, text="Min Success Rate (%):").grid(row=0, column=4, sticky="w")
        self.min_success_rate = tk.StringVar(value="0")
        ttk.Entry(self.filter_frame, textvariable=self.min_success_rate, width=5).grid(row=0, column=5, padx=5)
        
        ttk.Label(self.filter_frame, text="Min Working Days:").grid(row=0, column=6, sticky="w")
        self.min_days = tk.StringVar(value="7")
        ttk.Entry(self.filter_frame, textvariable=self.min_days, width=5).grid(row=0, column=7, padx=5)
        
        ttk.Button(self.filter_frame, text="Apply Filters", command=self.analyze_data).grid(row=0, column=8, padx=10)
        
        # Export button
        ttk.Button(self.filter_frame, text="Export Results", command=self.export_results).grid(row=1, column=8, padx=10, pady=5)
        
        # Results area with tabs
        self.tabs = ttk.Notebook(self.result_frame)
        self.tabs.pack(fill="both", expand=True)
        
        self.results_tab = ttk.Frame(self.tabs)
        self.chart_tab = ttk.Frame(self.tabs)
        self.tabs.add(self.results_tab, text="Results")
        self.tabs.add(self.chart_tab, text="Charts")
        
        # Results table - updated columns to include total tasks
        self.results_tree = ttk.Treeview(self.results_tab, columns=("name", "days_worked", "total_tasks", "max_streak", "avg_success", "completion_dates"))
        self.results_tree.heading("#0", text="ID")
        self.results_tree.heading("name", text="Student Name")
        self.results_tree.heading("days_worked", text="Days Worked")
        self.results_tree.heading("total_tasks", text="Total Tasks")
        self.results_tree.heading("max_streak", text="Max Streak")
        self.results_tree.heading("avg_success", text="Avg Success Rate")
        self.results_tree.heading("completion_dates", text="Completion Dates")
        
        self.results_tree.column("#0", width=40)
        self.results_tree.column("name", width=180)
        self.results_tree.column("days_worked", width=80)
        self.results_tree.column("total_tasks", width=80)
        self.results_tree.column("max_streak", width=80)
        self.results_tree.column("avg_success", width=100)
        self.results_tree.column("completion_dates", width=200)
        
        self.results_tree.pack(fill="both", expand=True)
        
        # Add scrollbar to results tree
        results_scrollbar = ttk.Scrollbar(self.results_tab, orient="vertical", command=self.results_tree.yview)
        results_scrollbar.pack(side="right", fill="y")
        self.results_tree.configure(yscrollcommand=results_scrollbar.set)
        
        # Bind click event to the results tree
        self.results_tree.bind("<Double-1>", self.show_student_details)
        
        # Chart area
        self.chart_frame = ttk.Frame(self.chart_tab)
        self.chart_frame.pack(fill="both", expand=True)
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_bar = ttk.Label(root, textvariable=self.status_var, relief="sunken", anchor="w")
        self.status_bar.pack(side="bottom", fill="x")
        self.status_var.set("Ready")
        
        # Store results for export
        self.results_data = []
        
        # Store full student data for detailed view
        self.student_full_data = {}
        
    def browse_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx *.xls")])
        if file_path:
            self.file_path.set(file_path)
    
    def load_data(self):
        try:
            file_path = self.file_path.get()
            if not file_path:
                self.status_var.set("Error: Please select a file first")
                return
            
            # Try to import openpyxl before loading the Excel file
            try:
                import openpyxl
                print("openpyxl successfully imported")
            except ImportError:
                # If openpyxl is not found, try to install it
                self.status_var.set("Missing openpyxl package. Attempting to install...")
                try:
                    import subprocess
                    # Run pip install in a subprocess
                    subprocess.check_call(["pip", "install", "--no-cache-dir", "openpyxl"])
                    self.status_var.set("openpyxl installed successfully, loading data...")
                    import openpyxl  # Try importing again after installation
                except Exception as e:
                    self.status_var.set(f"Error installing openpyxl: {str(e)}. Please install manually with 'pip install openpyxl'")
                    return
                    
            # Explicitly use openpyxl as the engine
            self.df = pd.read_excel(file_path, engine='openpyxl')
            
            # Print initial column names for debugging
            print("Original columns:", self.df.columns.tolist())
            
            # Process the multi-subject format
            transformed_data = []
            
            # Identify all subject columns in the data
            subject_patterns = {}
            
            # First identify the base columns (without subject)
            base_cols = []
            subject_cols = {}
            diagnostic_cols = []
            
            for col in self.df.columns:
                col_str = str(col).strip()
                
                # Collect diagnostic columns separately
                if "Diagnostic" in col_str:
                    diagnostic_cols.append(col)
                    continue
                    
                # Check if this is a subject-specific column
                subject_match = None
                if "(" in col_str and ")" in col_str:
                    # Extract subject name from parentheses
                    subject_name = col_str[col_str.find("(")+1:col_str.find(")")]
                    base_col_name = col_str[:col_str.find("(")].strip()
                    
                    # Initialize subject pattern if not seen before
                    if subject_name not in subject_patterns:
                        subject_patterns[subject_name] = {}
                    
                    # Store the column mapping
                    subject_patterns[subject_name][base_col_name] = col
                    
                    # Track subject columns
                    if subject_name not in subject_cols:
                        subject_cols[subject_name] = []
                    subject_cols[subject_name].append(col)
                else:
                    # This is a base column
                    base_cols.append(col)
            
            # Add "Math" as default subject if we find Practice Task without parentheses
            default_subject_cols = {}
            for col in base_cols:
                col_str = str(col).strip()
                if col_str in ["Practice Task", "Completion Date", "Practice Status", "Success/Progress Rate"]:
                    if "Math" not in subject_patterns:
                        subject_patterns["Math"] = {}
                    subject_patterns["Math"][col_str] = col
                    default_subject_cols[col_str] = col
                    
            if default_subject_cols:
                subject_cols["Math"] = list(default_subject_cols.values())
            
            print("Detected subjects:", list(subject_patterns.keys()))
            print("Subject columns:", subject_cols)
            
            # Create a base DataFrame with student info - excluding subject columns
            excluded_cols = []
            for subject in subject_cols:
                excluded_cols.extend(subject_cols[subject])
            
            base_df_cols = [col for col in self.df.columns if col not in excluded_cols and "Practice" not in str(col) and "Success" not in str(col) and "Completion" not in str(col)]
            
            # Process each row in the DataFrame
            for idx, row in self.df.iterrows():
                # Process each subject's columns
                for subject, pattern in subject_patterns.items():
                    # Check if we have all necessary columns for this subject
                    if not all(k in pattern for k in ["Practice Task", "Completion Date", "Practice Status", "Success/Progress Rate"]):
                        print(f"Missing required columns for subject {subject}")
                        continue
                        
                    task_col = pattern["Practice Task"]
                    date_col = pattern["Completion Date"]
                    status_col = pattern["Practice Status"]
                    rate_col = pattern["Success/Progress Rate"]
                    
                    # Skip if no task or "Not Started"
                    if pd.isna(row.get(task_col)) or row.get(task_col) == "Not Started":
                        continue
                        
                    # Create a record for this task
                    task_record = {
                        "Name": row.get("Name", ""),
                        "Surname": row.get("Surname", ""),
                        "Phone": row.get("Phone Number", ""),
                        "Registration_Date": row.get("Registration Date"),
                        "Subject": subject,
                        "Task": row.get(task_col, ""),
                        "Completion_Date": row.get(date_col),
                        "Status": row.get(status_col, ""),
                        "Success_Rate": self._parse_rate(row.get(rate_col))
                    }
                    
                    # Add any diagnostic scores if available
                    for diag_col in diagnostic_cols:
                        if not pd.isna(row.get(diag_col)):
                            diag_name = str(diag_col).replace(" - Accuracy", "")
                            task_record[diag_name] = row.get(diag_col)
                    
                    transformed_data.append(task_record)
                    
            # Convert the transformed data to a DataFrame
            if transformed_data:
                self.df = pd.DataFrame(transformed_data)
                print("Transformed columns:", self.df.columns.tolist())
                
                # Add subject filter to the GUI
                self.add_subject_filter(self.df["Subject"].unique())
            else:
                self.status_var.set("No task data found in the file. Check the format.")
                return
            
            # Convert Success_Rate to numeric, handling all possible formats
            if self.df["Success_Rate"].dtype == object:  # If it's a string or mixed type
                # Replace any non-numeric values with '0'
                self.df["Success_Rate"] = self.df["Success_Rate"].astype(str).replace('Not Started', '0')
                self.df["Success_Rate"] = self.df["Success_Rate"].astype(str).replace('', '0')
                # Remove '%' sign if present
                self.df["Success_Rate"] = self.df["Success_Rate"].astype(str).str.rstrip("%")
                # Convert to float
                self.df["Success_Rate"] = pd.to_numeric(self.df["Success_Rate"], errors='coerce')
            
            # Fill any NaN values with 0
            self.df["Success_Rate"].fillna(0, inplace=True)
            
            # Convert dates to datetime with explicit format
            try:
                self.df["Completion_Date"] = pd.to_datetime(self.df["Completion_Date"], errors='coerce')
            except:
                self.status_var.set("Warning: Some dates couldn't be parsed correctly")
            
            # Create full name column
            self.df["Full_Name"] = self.df["Name"] + " " + self.df["Surname"]
            
            self.status_var.set(f"Data loaded successfully. {len(self.df)} records found.")
            # Print column types for debugging
            print("Success_Rate column type:", self.df["Success_Rate"].dtype)
            print("First few values:", self.df["Success_Rate"].head())
            
        except Exception as e:
            self.status_var.set(f"Error loading data: {str(e)}")
            # Print more detailed error information
            import traceback
            traceback.print_exc()
            
            # Check if it's an openpyxl error
            if "openpyxl" in str(e).lower():
                self.status_var.set("Error with openpyxl. Try reopening the application or installing openpyxl manually.")
                
                # Create a popup with instructions
                try:
                    popup = tk.Toplevel(self.root)
                    popup.title("Dependency Error")
                    popup.geometry("500x200")
                    
                    frame = ttk.Frame(popup, padding=20)
                    frame.pack(fill="both", expand=True)
                    
                    ttk.Label(
                        frame, 
                        text="Missing openpyxl Package", 
                        font=("Segoe UI", 12, "bold")
                    ).pack(pady=(0, 10))
                    
                    ttk.Label(
                        frame,
                        text="The application requires the 'openpyxl' package to read Excel files.\n\n"
                            "Please try one of these solutions:",
                        justify="left"
                    ).pack(fill="x", pady=(0, 10))
                    
                    ttk.Label(
                        frame,
                        text="1. Close and reopen the application\n"
                            "2. Run this command in a terminal: pip install openpyxl\n"
                            "3. Reinstall the application",
                        justify="left"
                    ).pack(fill="x")
                    
                    ttk.Button(
                        frame, 
                        text="OK", 
                        command=popup.destroy
                    ).pack(pady=10)
                    
                except:
                    pass  # If popup creation fails, just show the status message
    
    def _parse_rate(self, rate_value):
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
    
    def analyze_data(self):
        if self.df is None:
            self.status_var.set("Error: No data loaded")
            return
        
        try:
            # Get filter values
            start_date = pd.to_datetime(self.start_date.get())
            end_date = pd.to_datetime(self.end_date.get())
            min_success_rate = float(self.min_success_rate.get())
            min_days = int(self.min_days.get())
            
            # Apply subject filter if available
            filtered_df = self.df.copy()
            if hasattr(self, 'subject_var') and self.subject_var.get() != "All":
                selected_subject = self.subject_var.get()
                filtered_df = filtered_df[filtered_df["Subject"] == selected_subject]
                print(f"Filtered for subject: {selected_subject}, records: {len(filtered_df)}")
            
            # Ensure Success_Rate is numeric
            if not pd.api.types.is_numeric_dtype(filtered_df["Success_Rate"]):
                filtered_df["Success_Rate"] = pd.to_numeric(filtered_df["Success_Rate"], errors='coerce')
                filtered_df["Success_Rate"].fillna(0, inplace=True)
            
            # Filter by date range, success rate, and status
            filtered_df = filtered_df[
                (filtered_df["Completion_Date"] >= start_date) &
                (filtered_df["Completion_Date"] <= end_date) &
                (filtered_df["Success_Rate"] > min_success_rate) &
                (filtered_df["Status"] == "Done")
            ]
            
            # Print debug information
            print(f"Records after filtering: {len(filtered_df)}")
            
            # Group by student name
            student_groups = filtered_df.groupby("Full_Name")
            
            # Store student summary data
            student_summaries = []
            self.student_full_data = {}  # Clear previous data
            
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
                    max_streak = self.calculate_max_streak(completion_dates)
                    
                    # Format dates for display
                    dates_str = ", ".join([date.strftime("%Y-%m-%d") for date in completion_dates])
                    
                    # Get unique subjects for this student
                    subjects = sorted(group["Subject"].unique())
                    subjects_str = ", ".join(subjects)
                    
                    student_summaries.append({
                        "Full_Name": student_name,
                        "Days_Worked": days_worked,
                        "Total_Tasks": total_tasks,
                        "Max_Streak": max_streak,
                        "Avg_Success": avg_success,
                        "Subjects": subjects_str,
                        "Completion_Dates": dates_str
                    })
                    
                    # Store full student data for detailed view
                    self.student_full_data[student_name] = group
            
            # Store results for export
            self.results_data = student_summaries
            
            # Clear existing results
            for item in self.results_tree.get_children():
                self.results_tree.delete(item)
            
            # Display results
            if student_summaries:
                for idx, student in enumerate(student_summaries):
                    self.results_tree.insert("", "end", text=str(idx+1), 
                                           values=(student["Full_Name"], 
                                                  student["Days_Worked"],
                                                  student["Total_Tasks"],
                                                  student["Max_Streak"],
                                                  f"{student['Avg_Success']:.2f}%",
                                                  student["Completion_Dates"]))
                
                # Create chart with the results
                self.create_chart(student_summaries)
                
                self.status_var.set(f"Analysis complete. Found {len(student_summaries)} qualifying students.")
            else:
                self.status_var.set("No students match the criteria.")
                
        except Exception as e:
            self.status_var.set(f"Error during analysis: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def calculate_max_streak(self, dates):
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
    
    def check_for_streak(self, dates):
        """Check if there are min_days consecutive dates in the list"""
        min_days = int(self.min_days.get())
        max_streak = self.calculate_max_streak(dates)
        return max_streak >= min_days
    
    def show_student_details(self, event):
        """Show detailed view of a student when their name is clicked"""
        # Get the selected item
        item = self.results_tree.selection()[0]
        student_name = self.results_tree.item(item, "values")[0]
        
        if student_name not in self.student_full_data:
            self.status_var.set(f"No detailed data available for {student_name}")
            return
            
        # Create new window for student details
        detail_window = tk.Toplevel(self.root)
        detail_window.title(f"Student Details: {student_name}")
        detail_window.geometry("1000x700")
        
        # Create notebook for tabs in detail window
        detail_tabs = ttk.Notebook(detail_window)
        detail_tabs.pack(fill="both", expand=True)
        
        # Create tabs
        timeline_tab = ttk.Frame(detail_tabs)
        tasks_tab = ttk.Frame(detail_tabs)
        progress_tab = ttk.Frame(detail_tabs)
        
        detail_tabs.add(timeline_tab, text="Timeline")
        detail_tabs.add(tasks_tab, text="Tasks")
        detail_tabs.add(progress_tab, text="Progress")
        
        # Get student data
        student_data = self.student_full_data[student_name]
        
        # Create timeline view showing all days from first task to today
        self.create_timeline_view(timeline_tab, student_data)
        
        # Create tasks view showing all tasks completed
        self.create_tasks_view(tasks_tab, student_data)
        
        # Create progress charts
        self.create_progress_charts(progress_tab, student_data)
    
    def create_timeline_view(self, parent, student_data):
        """Create a timeline view showing all dates and tasks completed on each date"""
        # Frame for filter and controls
        control_frame = ttk.Frame(parent, padding="5")
        control_frame.pack(fill="x")
        
        # Create a date range that spans from first task to today
        first_date = student_data["Completion_Date"].min().date()
        last_date = max(datetime.now().date(), student_data["Completion_Date"].max().date())
        
        # Show date range
        ttk.Label(control_frame, text=f"Date Range: {first_date} to {last_date}").pack(side="left", padx=5)
        
        # Subject filter for timeline
        ttk.Label(control_frame, text="Filter Subject:").pack(side="left", padx=(20, 5))
        timeline_subject_var = tk.StringVar(value="All")
        timeline_subject_dropdown = ttk.Combobox(control_frame, textvariable=timeline_subject_var, width=10)
        timeline_subject_dropdown.pack(side="left", padx=5)
        
        # Get unique subjects
        subjects = ["All"] + sorted(student_data["Subject"].unique().tolist())
        timeline_subject_dropdown['values'] = subjects
        
        # Create a frame for the timeline table
        table_frame = ttk.Frame(parent, padding="5")
        table_frame.pack(fill="both", expand=True)
        
        # Create timeline treeview
        columns = ("date", "subjects", "tasks_completed", "avg_success")
        timeline_tree = ttk.Treeview(table_frame, columns=columns)
        timeline_tree.heading("#0", text="")
        timeline_tree.heading("date", text="Date")
        timeline_tree.heading("subjects", text="Subjects")
        timeline_tree.heading("tasks_completed", text="Tasks Completed")
        timeline_tree.heading("avg_success", text="Avg Success Rate")
        
        timeline_tree.column("#0", width=0, stretch=tk.NO)
        timeline_tree.column("date", width=120)
        timeline_tree.column("subjects", width=120)
        timeline_tree.column("tasks_completed", width=150)
        timeline_tree.column("avg_success", width=120)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=timeline_tree.yview)
        scrollbar.pack(side="right", fill="y")
        timeline_tree.configure(yscrollcommand=scrollbar.set)
        timeline_tree.pack(fill="both", expand=True)
        
        # Function to update timeline with selected subject
        def update_timeline(*args):
            # Clear existing items
            for item in timeline_tree.get_children():
                timeline_tree.delete(item)
                
            # Filter based on selected subject
            if timeline_subject_var.get() == "All":
                filtered_data = student_data
            else:
                filtered_data = student_data[student_data["Subject"] == timeline_subject_var.get()]
            
            # Group data by date
            date_groups = filtered_data.groupby(filtered_data["Completion_Date"].dt.date)
            
            # Create a date range from first task to today
            date_range = pd.date_range(start=first_date, end=last_date)
            
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
                    
                    timeline_tree.insert("", "end", text="", values=(
                        date_str, 
                        ", ".join(day_data["Subject"].unique()),
                        f"{tasks_count} ({task_details})", 
                        f"{avg_success:.2f}%"
                    ))
                    
                    # Apply a background color for days with tasks
                    last_item = timeline_tree.get_children()[-1]
                    timeline_tree.item(last_item, tags=("has_task",))
                else:
                    # No tasks on this day
                    timeline_tree.insert("", "end", text="", values=(date_str, "-", "No tasks", "-"))
            
            # Define tags for coloring
            timeline_tree.tag_configure('has_task', background='#e6f2ff')
        
        # Bind the update function to the subject dropdown
        timeline_subject_dropdown.bind("<<ComboboxSelected>>", update_timeline)
        
        # Initial update
        update_timeline()
    
    def create_tasks_view(self, parent, student_data):
        """Create a detailed view of all tasks completed by the student"""
        # Sort student data by completion date
        sorted_data = student_data.sort_values(by=["Completion_Date", "Task"])
        
        # Create a frame for the tasks table
        table_frame = ttk.Frame(parent, padding="5")
        table_frame.pack(fill="both", expand=True)
        
        # Create tasks treeview
        columns = ("date", "subject", "task", "success_rate", "status")
        tasks_tree = ttk.Treeview(table_frame, columns=columns)
        tasks_tree.heading("#0", text="")
        tasks_tree.heading("date", text="Completion Date")
        tasks_tree.heading("subject", text="Subject")
        tasks_tree.heading("task", text="Task")
        tasks_tree.heading("success_rate", text="Success Rate")
        tasks_tree.heading("status", text="Status")
        
        tasks_tree.column("#0", width=0, stretch=tk.NO)
        tasks_tree.column("date", width=120)
        tasks_tree.column("subject", width=100)
        tasks_tree.column("task", width=150)
        tasks_tree.column("success_rate", width=100)
        tasks_tree.column("status", width=100)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tasks_tree.yview)
        scrollbar.pack(side="right", fill="y")
        tasks_tree.configure(yscrollcommand=scrollbar.set)
        tasks_tree.pack(fill="both", expand=True)
        
        # Populate the tasks table
        for _, row in sorted_data.iterrows():
            date_str = row["Completion_Date"].strftime("%Y-%m-%d")
            
            tasks_tree.insert("", "end", text="", values=(
                date_str,
                row["Subject"],
                row["Task"],
                f"{row['Success_Rate']:.2f}%",
                row["Status"]
            ))
            
            # Apply color based on success rate
            last_item = tasks_tree.get_children()[-1]
            if row["Success_Rate"] >= 80:
                tasks_tree.item(last_item, tags=("high_success",))
            elif row["Success_Rate"] >= 50:
                tasks_tree.item(last_item, tags=("medium_success",))
            else:
                tasks_tree.item(last_item, tags=("low_success",))
        
        # Define tags for coloring
        tasks_tree.tag_configure('high_success', background='#d4edda')
        tasks_tree.tag_configure('medium_success', background='#fff3cd')
        tasks_tree.tag_configure('low_success', background='#f8d7da')
    
    def create_progress_charts(self, parent, student_data):
        """Create progress charts showing the student's performance over time"""
        # Create a figure with multiple subplots - one more for subjects
        fig = plt.Figure(figsize=(10, 12))
        
        # Daily success rate chart
        daily_data = student_data.groupby(student_data["Completion_Date"].dt.date).agg({
            "Success_Rate": "mean"
        }).reset_index()
        
        # Sort by date
        daily_data = daily_data.sort_values("Completion_Date")
        
        # Create the first subplot (daily success rate)
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
        
        # NEW: Subject performance chart
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
        
        # Create canvas
        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
    
    def create_chart(self, results):
        """Create summary charts for all qualifying students"""
        # Clear previous chart
        for widget in self.chart_frame.winfo_children():
            widget.destroy()
            
        if not results:
            return
            
        # Create a figure with student analysis - now with 3 subplots
        fig = plt.Figure(figsize=(8, 10))
        
        # Sort by days worked
        results_sorted = sorted(results, key=lambda x: x["Days_Worked"], reverse=True)
        
        # Limit to top 10 students for readability
        top_students = results_sorted[:10]
        
        # Extract data for charts
        names = [r["Full_Name"] for r in top_students]
        days = [r["Days_Worked"] for r in top_students]
        tasks = [r["Total_Tasks"] for r in top_students]
        success_rates = [r["Avg_Success"] for r in top_students]
        max_streaks = [r["Max_Streak"] for r in top_students]
        
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
        
        # Embed the chart in the tkinter window
        canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
    
    def export_results(self):
        if not self.results_data:
            self.status_var.set("No results to export")
            return
            
        try:
            # Ask for save location
            file_path = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx")]
            )
            
            if not file_path:
                return
                
            # Convert results to DataFrame and export
            results_df = pd.DataFrame(self.results_data)
            results_df.to_excel(file_path, index=False)
            
            self.status_var.set(f"Results exported successfully to {file_path}")
            
        except Exception as e:
            self.status_var.set(f"Error exporting results: {str(e)}")

    def add_subject_filter(self, subjects):
        """Add a subject filter dropdown to the filter frame"""
        # Only add if it doesn't already exist
        if not hasattr(self, 'subject_var'):
            ttk.Label(self.filter_frame, text="Subject:").grid(row=1, column=0, sticky="w")
            self.subject_var = tk.StringVar(value="All")
            self.subject_dropdown = ttk.Combobox(self.filter_frame, textvariable=self.subject_var, width=15)
            self.subject_dropdown.grid(row=1, column=1, padx=5, pady=5)
        
        # Update the values
        subjects_list = ["All"] + sorted(list(subjects))
        self.subject_dropdown['values'] = subjects_list

if __name__ == "__main__":
    root = tk.Tk()
    app = StudentAnalysisApp(root)
    root.mainloop()
