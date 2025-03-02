#!/usr/bin/env python
"""
Standalone script for cleaning up old data.
Can be used as a cron job or scheduled task if APScheduler isn't suitable.
"""

import os
import shutil
import logging
from datetime import datetime, timedelta
import argparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='cleanup.log',
    filemode='a'
)
logger = logging.getLogger('manual_cleanup')

def cleanup_old_data(upload_folder, days=7):
    """Remove user uploaded files and folders older than specified days"""
    logger.info(f"Starting manual data cleanup for folders older than {days} days")
    
    # Set cleanup threshold
    cleanup_threshold = datetime.now() - timedelta(days=days)
    
    # Ensure upload folder exists
    if not os.path.exists(upload_folder):
        logger.error(f"Upload folder does not exist: {upload_folder}")
        return
    
    try:
        # List all user folders
        user_folders = [f for f in os.listdir(upload_folder) 
                       if os.path.isdir(os.path.join(upload_folder, f))]
        
        cleaned_count = 0
        for user_id in user_folders:
            user_dir = os.path.join(upload_folder, user_id)
            
            # Get folder modification time
            mod_time = datetime.fromtimestamp(os.path.getmtime(user_dir))
            
            # If folder is older than threshold, delete it
            if mod_time < cleanup_threshold:
                logger.info(f"Removing old data for user_id: {user_id}, last modified: {mod_time}")
                shutil.rmtree(user_dir, ignore_errors=True)
                cleaned_count += 1
        
        logger.info(f"Manual data cleanup complete. Removed {cleaned_count} old user folders")
        print(f"Cleanup complete. Removed {cleaned_count} old user folders.")
    except Exception as e:
        logger.error(f"Error during manual data cleanup: {str(e)}")
        print(f"Error during cleanup: {str(e)}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Clean up old uploaded data files.')
    parser.add_argument('--days', type=int, default=7, 
                        help='Remove files older than this many days (default: 7)')
    parser.add_argument('--folder', type=str, default='uploads', 
                        help='Path to the uploads folder (default: uploads)')
    
    args = parser.parse_args()
    
    # Get the absolute path of the uploads folder
    script_dir = os.path.dirname(os.path.abspath(__file__))
    upload_folder = os.path.join(script_dir, args.folder)
    
    cleanup_old_data(upload_folder, args.days)
