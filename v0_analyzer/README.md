# Excel Task Analysis Tool

This application analyzes Excel data to identify users who completed tasks over a specified period with success rates above a threshold.

## Features

- Load and analyze Excel files containing task completion data
- Filter by date range, task type, and success rate
- Identify users who worked on tasks for a minimum number of days
- Analyze streaks and consistency in task completion
- Visualize results with charts
- Export filtered results to Excel

## Installation

1. Make sure you have Python 3.7+ installed
2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

1. Run the application:

```bash
python excel_analyzer.py
```

2. Use the GUI to:
   - Load your Excel file
   - Set the date range (default is Feb 19-27, 2025)
   - Adjust the success rate threshold
   - Specify the required number of days (default is 7)
   - Filter by specific task or use "All"
   - Click "Analyze Data" to process the file

3. View the results in the table showing:
   - User information
   - Days worked
   - Average success rate
   - Streak information
   - Details about consistent periods

4. Export the results or view visualizations using the corresponding buttons

## Expected Excel Format

The application expects an Excel file with the following columns:
- Name
- Surname
- Phone Number
- Registration Date
- Practice Day (task name)
- Completion Practice Status (date)
- Done/Not Done status
- Success/Progress Rate (percentage)

## Examples

The tool can answer questions such as:
- Which users worked on at least one Task X for 7 days between Feb 19-27?
- Which users maintained a success rate above a certain threshold?
- Did users work consistently or with breaks between task completions?
