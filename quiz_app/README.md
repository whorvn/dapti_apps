# Excel Quiz Web App

An interactive Flask web application that allows users to upload Excel files containing quiz questions and displays them in an organized, visually appealing manner.

## Features

- Easy Excel file upload with drag-and-drop functionality
- Interactive quiz display with automatic correct answer highlighting
- Support for various question components (text, translations, formulas, etc.)
- Responsive design for desktop and mobile devices
- Print functionality for quiz sheets
- Error handling for improper file formats

## Installation

1. Clone this repository or download the code
2. Create a virtual environment and activate it:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install the required packages:
   ```
   pip install -r requirements.txt
   ```
4. Run the application:
   ```
   python app.py
   ```
5. Open your browser and navigate to http://127.0.0.1:5000/

## Excel File Format

Your Excel file should contain columns with the following headers:

- **Required columns**:
  - Topic
  - Class
  - Question
  - Option A, Option B (at minimum)
  - Correct option

- **Optional columns**:
  - Category
  - Chapter
  - Translation
  - Formula
  - Image (URL to image)
  - Option C, Option D, Option E (depending on how many options you need)
  - Level

## Usage

1. Upload your Excel file through the web interface
2. The application will process the file and display all quiz questions
3. Correct answers are automatically highlighted
4. Use the "Print Quiz" button to get a printable version
5. Use "Upload New File" to start over

## License

This project is licensed under the MIT License.
