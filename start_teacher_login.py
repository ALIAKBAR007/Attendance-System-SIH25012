"""
Teacher Login System Launcher
Run this file to start the teacher login interface
"""
import sys
import os

# Add the current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

try:
    from teacher_login import TeacherLoginApp
    
    if __name__ == "__main__":
        print("Starting Teacher Login System...")
        app = TeacherLoginApp()
        app.run()
        
except ImportError as e:
    print(f"Import error: {e}")
    print("Please make sure all required modules are installed:")
    print("pip install customtkinter opencv-python pillow face-recognition")
    
except Exception as e:
    print(f"Error starting application: {e}")