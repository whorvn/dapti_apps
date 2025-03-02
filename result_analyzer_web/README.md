# Student Result Analyzer

A web application for analyzing and visualizing student performance data.

## Features

- Upload and process student task data
- Filter students by date range, success rate, and working days
- View detailed student profiles with performance metrics
- Generate visual charts and reports
- Compare multiple students
- Export data to Excel or CSV
- Automatic cleanup of old data files

## Installation

1. Clone this repository:

```bash
git clone <repository-url>
cd result_analyzer_web
```

2. Create a virtual environment:

```bash
python -m venv myenv
source myenv/bin/activate  # On Windows: myenv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

## Running the Application

Start the application:

```bash
python app.py
```

By default, the application will run on http://127.0.0.1:5000/

## Data Cleanup

The application includes automatic data cleanup to prevent accumulation of old uploaded files. By default, files older than 7 days are automatically removed. This happens:

1. As a scheduled task when the application is running (using APScheduler)
2. You can manually run the cleanup script:

```bash
python cleanup.py --days 14  # Removes files older than 14 days
```

## Configuration

You can configure the following aspects:

- `UPLOAD_FOLDER`: Where uploaded files are stored
- `PERMANENT_SESSION_LIFETIME`: How long user sessions last before expiring
- Data cleanup threshold: How long to keep uploaded files

## Security Considerations

For production deployment:

1. Change the secret key
2. Enable HTTPS (set `SESSION_COOKIE_SECURE = True`)
3. Configure appropriate file size limits
4. Set up proper authentication if needed

## License

[Specify your license information]
