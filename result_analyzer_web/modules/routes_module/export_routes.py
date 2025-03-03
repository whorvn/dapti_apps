"""Routes for exporting data."""

from flask import redirect, url_for, flash, session, send_file
import os
import io
import pandas as pd
from datetime import datetime
import sys

def export_data():
    """Export student data to Excel or CSV."""
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
    import json
    with open(summary_file, 'r') as f:
        student_summaries = json.load(f)
    
    # Check if xlsxwriter is available for Excel export
    excel_export_available = check_xlsxwriter_availability()
    
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

def check_xlsxwriter_availability():
    """Check if xlsxwriter is available for Excel export."""
    try:
        import xlsxwriter
        return True
    except ImportError:
        # Try to install xlsxwriter
        try:
            import subprocess
            subprocess.check_call([sys.executable, "-m", "pip", "install", "xlsxwriter"])
            import xlsxwriter
            return True
        except Exception:
            flash('The xlsxwriter package is required for Excel export. Falling back to CSV format.', 'warning')
            return False
