"""
Web Application Runner for Student Task Analysis.
This script launches the Flask web server for the student analysis application.
"""
import os
import sys
from web_app.app import app

# Check for required packages
try:
    import flask
    import pandas as pd
    import plotly
except ImportError as e:
    print(f"Missing required package: {e.name}")
    print("Please install missing packages with: pip install flask pandas plotly")
    sys.exit(1)

if __name__ == "__main__":
    # Run the Flask application
    port = int(os.environ.get("PORT", 5000))
    
    print("Starting Student Task Analysis Web App...")
    print(f"URL: http://localhost:{port}")
    print("Press Ctrl+C to stop the server")
    
    app.run(host="0.0.0.0", port=port, debug=True)
