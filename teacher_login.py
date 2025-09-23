import csv
import os
import datetime
import pickle
import customtkinter as ctk
import cv2
from PIL import Image, ImageTk
import face_recognition
import subprocess
import sys

import util
from test import test

# Set the theme and color theme
ctk.set_appearance_mode("dark")  # Modes: "System" (standard), "Dark", "Light"
ctk.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"


class TeacherLoginApp:
    def __init__(self):
        self.main_window = ctk.CTk()
        self.main_window.geometry("1000x700+250+50")
        self.main_window.title("Teacher Login System")
        
        # Database and paths setup
        self.db_dir = './db'
        if not os.path.exists(self.db_dir):
            os.mkdir(self.db_dir)
            
        self.teacher_db_dir = './teacher_db'
        if not os.path.exists(self.teacher_db_dir):
            os.mkdir(self.teacher_db_dir)
            
        self.model_dir = './Silent-Face-Anti-Spoofing'
        
        # Admin password (in production, this should be hashed and stored securely)
        self.admin_password = "admin123"
        
        # Camera setup
        self.camera = None
        self.webcam_label = None
        self.most_recent_capture_arr = None
        
        self.build_ui()
        self.start_camera()
        
    def build_ui(self):
        """Build the teacher login interface"""
        # Title
        title_label = ctk.CTkLabel(
            self.main_window, 
            text="Teacher Login System",
            font=ctk.CTkFont(size=32, weight="bold")
        )
        title_label.pack(pady=30)
        
        # Main container frame
        main_frame = ctk.CTkFrame(self.main_window)
        main_frame.pack(pady=20, padx=40, fill="both", expand=True)
        
        # Left side - Camera feed
        camera_frame = ctk.CTkFrame(main_frame)
        camera_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        
        camera_title = ctk.CTkLabel(
            camera_frame,
            text="Face Recognition Camera",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        camera_title.pack(pady=10)
        
        # Webcam label
        self.webcam_label = ctk.CTkLabel(camera_frame, text="")
        self.webcam_label.pack(pady=10)
        
        # Right side - Login controls
        control_frame = ctk.CTkFrame(main_frame)
        control_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        
        control_title = ctk.CTkLabel(
            control_frame,
            text="Login Controls",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        control_title.pack(pady=20)
        
        # Teacher login button
        self.teacher_login_btn = ctk.CTkButton(
            control_frame,
            text="Teacher Login",
            font=ctk.CTkFont(size=18, weight="bold"),
            width=200,
            height=50,
            command=self.teacher_login
        )
        self.teacher_login_btn.pack(pady=15)
        
        # Register new teacher button
        self.register_teacher_btn = ctk.CTkButton(
            control_frame,
            text="Register New Teacher",
            font=ctk.CTkFont(size=16),
            width=200,
            height=40,
            command=self.register_teacher
        )
        self.register_teacher_btn.pack(pady=10)
        
        # Admin section
        admin_frame = ctk.CTkFrame(control_frame)
        admin_frame.pack(pady=30, padx=20, fill="x")
        
        admin_title = ctk.CTkLabel(
            admin_frame,
            text="Administrator Access",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        admin_title.pack(pady=10)
        
        # Admin password entry
        self.admin_password_entry = ctk.CTkEntry(
            admin_frame,
            placeholder_text="Enter admin password",
            show="*",
            width=180,
            height=35
        )
        self.admin_password_entry.pack(pady=5)
        
        # Admin login button
        self.admin_btn = ctk.CTkButton(
            admin_frame,
            text="Admin Login",
            font=ctk.CTkFont(size=14),
            width=120,
            height=35,
            command=self.admin_login
        )
        self.admin_btn.pack(pady=10)
        
        # Status label
        self.status_label = ctk.CTkLabel(
            control_frame,
            text="Ready for teacher login...",
            font=ctk.CTkFont(size=14),
            text_color="green"
        )
        self.status_label.pack(pady=20)
        
        # Configure grid weights
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_columnconfigure(1, weight=1)
        main_frame.grid_rowconfigure(0, weight=1)
        
    def start_camera(self):
        """Initialize and start camera feed"""
        try:
            self.camera = cv2.VideoCapture(0)
            if not self.camera.isOpened():
                self.update_status("Error: Could not open camera", "red")
                return
            self.update_camera_feed()
        except Exception as e:
            self.update_status(f"Camera error: {e}", "red")
            
    def update_camera_feed(self):
        """Update camera feed continuously"""
        if self.camera is not None and self.camera.isOpened():
            ret, frame = self.camera.read()
            if ret:
                # Store the most recent frame for face recognition
                self.most_recent_capture_arr = frame
                
                # Convert frame for display
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame = cv2.resize(frame, (400, 300))
                
                # Convert to CTk image
                image = Image.fromarray(frame)
                photo = ctk.CTkImage(light_image=image, dark_image=image, size=(400, 300))
                
                if self.webcam_label:
                    self.webcam_label.configure(image=photo)
                    
        # Schedule next update
        self.main_window.after(10, self.update_camera_feed)
        
    def update_status(self, message, color="white"):
        """Update status message"""
        if self.status_label:
            self.status_label.configure(text=message, text_color=color)
            
    def teacher_login(self):
        """Handle teacher login with face recognition"""
        try:
            self.update_status("Processing teacher login...", "orange")
            
            if self.most_recent_capture_arr is None:
                util.msg_box('Error', 'No camera feed detected. Please check camera.')
                self.update_status("Login failed - No camera", "red")
                return
                
            # Check for spoofing
            label = test(
                image=self.most_recent_capture_arr,
                model_dir=self.model_dir,
                device_id=0
            )
            
            if label == 1:  # Real face detected
                # Try to recognize the teacher
                teacher_name = self.recognize_teacher(self.most_recent_capture_arr)
                
                if teacher_name in ['unknown_person', 'no_persons_found']:
                    util.msg_box('Access Denied', 'Teacher not recognized. Please register first or try again.')
                    self.update_status("Login failed - Teacher not recognized", "red")
                else:
                    # Successful teacher login
                    util.msg_box('Welcome!', f'Welcome, {teacher_name}!')
                    self.update_status(f"Login successful: {teacher_name}", "green")
                    self.log_teacher_activity(teacher_name, "LOGIN")
                    
                    # Open student attendance system
                    self.open_student_attendance_system()
                    
            else:  # Spoofing detected
                util.msg_box('Security Alert!', 'Spoofing detected! Please use real face.')
                self.update_status("Login failed - Spoofing detected", "red")
                
        except Exception as e:
            util.msg_box('Error', f'Login error: {str(e)}')
            self.update_status(f"Login error: {e}", "red")
            
    def recognize_teacher(self, image):
        """Recognize teacher using face recognition"""
        try:
            # Get face encodings from the image
            face_encodings = face_recognition.face_encodings(image)
            
            if len(face_encodings) == 0:
                return 'no_persons_found'
                
            # Load known teacher faces
            known_face_encodings = []
            known_face_names = []
            
            for file in os.listdir(self.teacher_db_dir):
                if file.endswith('.pickle'):
                    with open(os.path.join(self.teacher_db_dir, file), 'rb') as f:
                        known_face_encodings.append(pickle.load(f))
                        known_face_names.append(file[:-7])  # Remove .pickle extension
                        
            if len(known_face_encodings) == 0:
                return 'unknown_person'
                
            # Compare faces
            face_encoding = face_encodings[0]
            matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
            
            if True in matches:
                match_index = matches.index(True)
                return known_face_names[match_index]
            else:
                return 'unknown_person'
                
        except Exception as e:
            print(f"Teacher recognition error: {e}")
            return 'unknown_person'
            
    def log_teacher_activity(self, teacher_name, activity):
        """Log teacher login activity to CSV"""
        try:
            log_path = "./teacher_activity.csv"
            current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            with open(log_path, 'a', newline='', encoding='utf-8') as f:
                csv_writer = csv.writer(f)
                csv_writer.writerow([teacher_name, current_time, activity])
                
        except Exception as e:
            print(f"Error logging teacher activity: {e}")
            
    def register_teacher(self):
        """Open teacher registration window"""
        self.register_window = ctk.CTkToplevel(self.main_window)
        self.register_window.geometry("600x400+400+200")
        self.register_window.title("Register New Teacher")
        
        # Title
        title_label = ctk.CTkLabel(
            self.register_window,
            text="Register New Teacher",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(pady=20)
        
        # Name entry
        name_label = ctk.CTkLabel(
            self.register_window,
            text="Teacher Name:",
            font=ctk.CTkFont(size=16)
        )
        name_label.pack(pady=5)
        
        self.register_name_entry = ctk.CTkEntry(
            self.register_window,
            placeholder_text="Enter teacher name",
            width=250,
            height=35
        )
        self.register_name_entry.pack(pady=10)
        
        # Instructions
        instructions = ctk.CTkLabel(
            self.register_window,
            text="Position your face in the camera and click 'Capture Face'",
            font=ctk.CTkFont(size=14),
            wraplength=400
        )
        instructions.pack(pady=20)
        
        # Buttons
        capture_btn = ctk.CTkButton(
            self.register_window,
            text="Capture Face",
            font=ctk.CTkFont(size=16),
            width=150,
            height=40,
            command=self.capture_teacher_face
        )
        capture_btn.pack(pady=10)
        
        cancel_btn = ctk.CTkButton(
            self.register_window,
            text="Cancel",
            font=ctk.CTkFont(size=16),
            width=100,
            height=35,
            command=self.register_window.destroy
        )
        cancel_btn.pack(pady=10)
        
    def capture_teacher_face(self):
        """Capture and save teacher's face"""
        try:
            name = self.register_name_entry.get().strip()
            if not name:
                util.msg_box('Error', 'Please enter teacher name.')
                return
                
            if self.most_recent_capture_arr is None:
                util.msg_box('Error', 'No camera feed detected.')
                return
                
            # Get face encoding
            face_encodings = face_recognition.face_encodings(self.most_recent_capture_arr)
            
            if len(face_encodings) == 0:
                util.msg_box('Error', 'No face detected. Please position your face clearly in the camera.')
                return
                
            # Save face encoding
            face_encoding = face_encodings[0]
            file_path = os.path.join(self.teacher_db_dir, f'{name}.pickle')
            
            with open(file_path, 'wb') as f:
                pickle.dump(face_encoding, f)
                
            util.msg_box('Success!', f'Teacher {name} registered successfully!')
            self.register_window.destroy()
            
        except Exception as e:
            util.msg_box('Error', f'Registration failed: {str(e)}')
            
    def admin_login(self):
        """Handle admin login"""
        entered_password = self.admin_password_entry.get()
        
        if entered_password == self.admin_password:
            util.msg_box('Admin Access', 'Admin login successful!\nAdmin panel will be implemented soon.')
            self.update_status("Admin login successful", "green")
            self.admin_password_entry.delete(0, 'end')  # Clear password field
            
            # TODO: Open admin panel here
            # self.open_admin_panel()
            
        else:
            util.msg_box('Access Denied', 'Incorrect admin password.')
            self.update_status("Admin login failed", "red")
            self.admin_password_entry.delete(0, 'end')  # Clear password field
            
    def open_student_attendance_system(self):
        """Open the main student attendance system"""
        try:
            # Close current window
            if self.camera:
                self.camera.release()
            self.main_window.destroy()
            
            # Launch the main attendance system
            subprocess.Popen([sys.executable, "main_gui_ctk.py"])
            
        except Exception as e:
            util.msg_box('Error', f'Failed to open attendance system: {str(e)}')
            
    def on_closing(self):
        """Handle window closing"""
        if self.camera:
            self.camera.release()
        self.main_window.destroy()
        
    def run(self):
        """Start the application"""
        self.main_window.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.main_window.mainloop()


if __name__ == "__main__":
    app = TeacherLoginApp()
    app.run()