from flask import Flask, render_template, request
import subprocess
import threading
import os
import signal

app = Flask(__name__)

# Global variable to hold the subprocess
current_process = None

# Function to run subprocess in a separate thread
def run_subprocess(script_name):
    global current_process
    current_process = subprocess.Popen(['python', script_name])

# Route to show the main page with buttons
@app.route('/')
def index():
    return render_template('index.html')

# Route to trigger the Age Prediction
@app.route('/age_prediction', methods=['POST'])
def age_prediction():
    # Run the age analysis script in a separate thread
    threading.Thread(target=run_subprocess, args=('age_analysis.py',)).start()
    return "Age Prediction started..."

# Route to trigger Emergency Vehicle Detection
@app.route('/emergency_vehicle', methods=['POST'])
def emergency_vehicle():
    # Run the vehicle detection script in a separate thread
    threading.Thread(target=run_subprocess, args=('detect_webcam.py',)).start()
    return "Emergency Vehicle Detection started..."

# Route to stop the running subprocess
@app.route('/stop', methods=['POST'])
def stop():
    global current_process
    if current_process:
        # Terminate the process
        current_process.terminate()
        current_process = None
        return "Process stopped!"
    else:
        return "No process to stop."

if __name__ == '__main__':
    app.run(debug=True)