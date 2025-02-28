# DaptiFilter - Excel Task Analysis Tool

This application analyzes Excel data to identify users who completed tasks over a specified period with success rates above a threshold. It helps in filtering and analyzing performance data from Excel spreadsheets.

## Features

- Load and analyze Excel files containing task completion data
- Filter by date range, task type, success rate and subject
- Identify users who worked on tasks for a minimum number of days
- Analyze streaks and consistency in task completion
- Visualize results with charts
- Export filtered results to Excel
- Support for multiple subjects (Math, English, etc.)

## Project Structure

The project is organized into multiple components:
- `excel_analyzer.py` - Main application file
- `v0_analyzer/` - Core analysis modules
- `background_system/` - Background processing components

## Installation

1. Make sure you have Python 3.7+ installed
2. Clone the repository:
```bash
git clone https://github.com/yourusername/daptifilter.git
cd daptifilter
```
3. Create a virtual environment:
```bash
python -m venv myenv
source myenv/bin/activate  # On Windows use: myenv\Scripts\activate
```
4. Install the required dependencies:
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
   - Select a subject to filter by or use "All" subjects
   - Adjust the success rate threshold
   - Specify the required number of days (default is 7)
   - Click "Apply Filters" to process the file

3. View the results in the table showing:
   - User information
   - Days worked
   - Total tasks completed
   - Maximum streak information
   - Average success rate
   - Details about completion dates

4. Export the results or view visualizations using the corresponding buttons

## Expected Excel Format

The application supports two Excel formats:

### Standard Format
- Name
- Surname
- Phone Number
- Registration Date
- Practice Task
- Completion Date
- Practice Status
- Success/Progress Rate

### Multi-Subject Format
- Base student information (Name, Surname, etc.)
- Diagnostic columns for assessment scores (optional)
- Subject-specific columns with format:
  - Practice Task (SubjectName)
  - Completion Date (SubjectName)
  - Practice Status (SubjectName)
  - Success/Progress Rate (SubjectName)

For example:
- Practice Task (English)
- Completion Date (English)
- Practice Status (English)
- Success/Progress Rate (English)

## Examples

The tool can answer questions such as:
- Which users worked on at least one Math task for 7 days between Feb 19-27?
- Which users maintained a success rate above a certain threshold in English tasks?
- Did users work consistently or with breaks between task completions?
- How did students perform across different subjects?

## Configuration

The application supports several configuration options:
- Default date ranges can be modified in the settings
- Success rate thresholds can be customized
- Multiple visualization options available
- Subject filtering for detailed analysis

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
