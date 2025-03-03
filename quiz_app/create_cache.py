import os

# Create directory for Flask session files
os.makedirs('flask_session', exist_ok=True)
print("Created flask_session directory for session cache")
