import os
import datetime
import customtkinter as ctk
from CTkTable import CTkTable
import cv2
from PIL import Image, ImageTk
import face_recognition
import threading
from tkinter import messagebox
import sys

import util
from test import test
from database import AttendanceDatabase

# Set the theme and color theme
ctk.set_appearance_mode("dark")  # Modes: "System" (standard), "Dark", "Light"
ctk.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"


class IntegratedAttendanceSystem:
    def __init__(self):
        self.main_window = ctk.CTk()
        self.main_window.geometry("1600x900+100+50")
        self.main_window.title("Integrated Teacher-Student Attendance System")
        
        # Database setup
        self.db = AttendanceDatabase()
        
        # Face recognition setup
        self.db_dir = './db'
        if not os.path.exists(self.db_dir):
            os.mkdir(self.db_dir)
            
        self.model_dir = './Silent-Face-Anti-Spoofing'
        
        # Current logged-in teacher
        self.current_teacher = None
        
        # Camera setup
        self.camera = None
        self.webcam_label = None
        self.most_recent_capture_arr = None
        self.camera_active = False
        
        # UI state
        self.mode = "teacher_login"  # "teacher_login" or "student_attendance"
        
        # Admin settings
        self.admin_password = "admin123"
        
        # Build initial UI
        self.build_ui()
        self.start_camera()
        
    def build_ui(self):
        """Build the main UI structure"""
        # Main container
        self.main_container = ctk.CTkFrame(self.main_window)
        self.main_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Header frame
        self.header_frame = ctk.CTkFrame(self.main_container)
        self.header_frame.pack(fill="x", padx=5, pady=5)
        
        # Title
        self.title_label = ctk.CTkLabel(
            self.header_frame,
            text="Teacher Login - Face Recognition System",
            font=ctk.CTkFont(size=28, weight="bold")
        )
        self.title_label.pack(side="left", padx=20, pady=15)
        
        # Admin button (top right)
        self.admin_btn = ctk.CTkButton(
            self.header_frame,
            text="Admin",
            font=ctk.CTkFont(size=14),
            width=80,
            height=30,
            command=self.show_admin_panel
        )
        self.admin_btn.pack(side="right", padx=20, pady=15)
        
        # Status frame
        self.status_frame = ctk.CTkFrame(self.main_container)
        self.status_frame.pack(fill="x", padx=5, pady=5)
        
        self.status_label = ctk.CTkLabel(
            self.status_frame,
            text="Ready for teacher login...",
            font=ctk.CTkFont(size=16),
            text_color="green"
        )
        self.status_label.pack(pady=10)
        
        # Content frame (will hold different modes)
        self.content_frame = ctk.CTkFrame(self.main_container)
        self.content_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Build teacher login interface
        self.build_teacher_login_ui()
        
    def build_teacher_login_ui(self):
        """Build teacher login interface"""
        # Clear content frame
        for widget in self.content_frame.winfo_children():
            widget.destroy()
            
        # Two-column layout
        # Left side - Camera
        self.camera_frame = ctk.CTkFrame(self.content_frame)
        self.camera_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        
        camera_title = ctk.CTkLabel(
            self.camera_frame,
            text="Face Recognition Camera",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        camera_title.pack(pady=15)
        
        # Webcam display
        self.webcam_label = ctk.CTkLabel(self.camera_frame, text="")
        self.webcam_label.pack(pady=10)
        
        # Right side - Controls
        self.controls_frame = ctk.CTkFrame(self.content_frame)
        self.controls_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        
        controls_title = ctk.CTkLabel(
            self.controls_frame,
            text="Teacher Authentication",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        controls_title.pack(pady=20)
        
        # Teacher login button
        self.teacher_login_btn = ctk.CTkButton(
            self.controls_frame,
            text="Teacher Login",
            font=ctk.CTkFont(size=18, weight="bold"),
            width=250,
            height=60,
            command=self.teacher_login
        )
        self.teacher_login_btn.pack(pady=15)
        
        # Register teacher button
        self.register_teacher_btn = ctk.CTkButton(
            self.controls_frame,
            text="Register New Teacher",
            font=ctk.CTkFont(size=16),
            width=200,
            height=45,
            command=self.register_new_teacher
        )
        self.register_teacher_btn.pack(pady=10)
        
        # Teacher list
        list_title = ctk.CTkLabel(
            self.controls_frame,
            text="Registered Teachers:",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        list_title.pack(pady=(30, 10))
        
        # Teachers list box
        self.teachers_textbox = ctk.CTkTextbox(
            self.controls_frame,
            width=300,
            height=200
        )
        self.teachers_textbox.pack(pady=10)
        
        # Load and display teachers
        self.update_teachers_list()
        
        # Configure grid weights
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_columnconfigure(1, weight=1)
        self.content_frame.grid_rowconfigure(0, weight=1)
        
    def build_student_attendance_ui(self):
        """Build student attendance interface"""
        # Clear content frame
        for widget in self.content_frame.winfo_children():
            widget.destroy()
            
        # Update title
        self.title_label.configure(
            text=f"Student Attendance - {self.current_teacher}'s Class"
        )
        
        # Three-section layout
        # Top section - Camera and controls
        self.top_section = ctk.CTkFrame(self.content_frame)
        self.top_section.pack(fill="x", padx=5, pady=5)
        
        # Left - Camera
        self.camera_frame = ctk.CTkFrame(self.top_section)
        self.camera_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        
        camera_title = ctk.CTkLabel(
            self.camera_frame,
            text="Student Face Recognition",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        camera_title.pack(pady=10)
        
        # Webcam display
        self.webcam_label = ctk.CTkLabel(self.camera_frame, text="")
        self.webcam_label.pack(pady=5)
        
        # Middle - Student controls
        self.student_controls_frame = ctk.CTkFrame(self.top_section)
        self.student_controls_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        
        student_title = ctk.CTkLabel(
            self.student_controls_frame,
            text="Student Operations",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        student_title.pack(pady=15)
        
        # Student login/logout buttons
        self.student_login_btn = ctk.CTkButton(
            self.student_controls_frame,
            text="Student Check-In",
            font=ctk.CTkFont(size=16, weight="bold"),
            width=200,
            height=50,
            command=self.student_checkin
        )
        self.student_login_btn.pack(pady=10)
        
        self.student_logout_btn = ctk.CTkButton(
            self.student_controls_frame,
            text="Student Check-Out",
            font=ctk.CTkFont(size=16),
            width=200,
            height=45,
            command=self.student_checkout
        )
        self.student_logout_btn.pack(pady=10)
        
        # Register student button
        self.register_student_btn = ctk.CTkButton(
            self.student_controls_frame,
            text="Register New Student",
            font=ctk.CTkFont(size=14),
            width=180,
            height=40,
            command=self.register_new_student
        )
        self.register_student_btn.pack(pady=10)
        
        # Right - Summary and logout
        self.summary_frame = ctk.CTkFrame(self.top_section)
        self.summary_frame.grid(row=0, column=2, padx=10, pady=10, sticky="nsew")
        
        summary_title = ctk.CTkLabel(
            self.summary_frame,
            text="Class Summary",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        summary_title.pack(pady=15)
        
        # Attendance summary
        self.summary_textbox = ctk.CTkTextbox(
            self.summary_frame,
            width=250,
            height=150
        )
        self.summary_textbox.pack(pady=10)
        
        # Teacher logout button
        self.teacher_logout_btn = ctk.CTkButton(
            self.summary_frame,
            text="Teacher Logout",
            font=ctk.CTkFont(size=16),
            width=180,
            height=45,
            command=self.teacher_logout
        )
        self.teacher_logout_btn.pack(pady=20)
        
        # Bottom section - Attendance table
        self.table_frame = ctk.CTkFrame(self.content_frame)
        self.table_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        table_title = ctk.CTkLabel(
            self.table_frame,
            text="Today's Attendance Log",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        table_title.pack(pady=10)
        
        # Initialize attendance table
        self.setup_attendance_table()
        
        # Configure grid weights for top section
        self.top_section.grid_columnconfigure(0, weight=1)
        self.top_section.grid_columnconfigure(1, weight=1)
        self.top_section.grid_columnconfigure(2, weight=1)
        
        # Update summary
        self.update_attendance_summary()
        
    def start_camera(self):
        """Initialize and start camera feed"""
        try:
            self.camera = cv2.VideoCapture(0)
            if not self.camera.isOpened():
                self.update_status("Error: Could not open camera", "red")
                return
                
            self.camera_active = True
            self.update_camera_feed()
            
        except Exception as e:
            self.update_status(f"Camera error: {e}", "red")
            
    def update_camera_feed(self):
        """Update camera feed continuously"""
        if self.camera_active and self.camera is not None and self.camera.isOpened():
            ret, frame = self.camera.read()
            if ret:
                # Store the most recent frame
                self.most_recent_capture_arr = frame.copy()
                
                # Convert and resize for display
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame = cv2.resize(frame, (480, 360))
                
                # Convert to CTk image
                image = Image.fromarray(frame)
                photo = ctk.CTkImage(light_image=image, dark_image=image, size=(480, 360))
                
                if self.webcam_label and self.webcam_label.winfo_exists():
                    self.webcam_label.configure(image=photo)
                    
        # Schedule next update
        if self.camera_active:
            self.main_window.after(20, self.update_camera_feed)
            
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
                
            # Anti-spoofing check
            label = test(
                image=self.most_recent_capture_arr,
                model_dir=self.model_dir,
                device_id=0
            )
            
            if label == 1:  # Real face detected
                teacher_name = self.recognize_teacher(self.most_recent_capture_arr)
                
                if teacher_name in ['unknown_person', 'no_persons_found']:
                    util.msg_box('Access Denied', 'Teacher not recognized. Please register first or try again.')
                    self.update_status("Login failed - Teacher not recognized", "red")
                else:
                    # Successful teacher login
                    if self.db.teacher_login(teacher_name):
                        self.current_teacher = teacher_name
                        util.msg_box('Welcome!', f'Welcome, {teacher_name}!')
                        self.update_status(f"Logged in: {teacher_name}", "green")
                        
                        # Switch to student attendance mode
                        self.mode = "student_attendance"
                        self.build_student_attendance_ui()
                    else:
                        util.msg_box('Error', 'Login failed. Please try again.')
                        self.update_status("Login failed - Database error", "red")
                        
            else:  # Spoofing detected
                util.msg_box('Security Alert!', 'Spoofing detected! Please use real face.')
                self.update_status("Login failed - Spoofing detected", "red")
                
        except Exception as e:
            util.msg_box('Error', f'Login error: {str(e)}')
            self.update_status(f"Login error: {e}", "red")
            
    def recognize_teacher(self, image):
        """Recognize teacher using face recognition and database"""
        try:
            # Get face encodings from the image
            face_encodings = face_recognition.face_encodings(image)
            
            if len(face_encodings) == 0:
                return 'no_persons_found'
                
            # Get known teacher encodings from database
            teacher_encodings = self.db.get_teacher_face_encodings()
            
            if len(teacher_encodings) == 0:
                return 'unknown_person'
                
            # Compare faces
            face_encoding = face_encodings[0]
            known_encodings = list(teacher_encodings.values())
            known_names = list(teacher_encodings.keys())
            
            matches = face_recognition.compare_faces(known_encodings, face_encoding)
            
            if True in matches:
                match_index = matches.index(True)
                return known_names[match_index]
            else:
                return 'unknown_person'
                
        except Exception as e:
            print(f"Teacher recognition error: {e}")
            return 'unknown_person'
            
    def teacher_logout(self):
        """Handle teacher logout"""
        try:
            if self.current_teacher:
                if self.db.teacher_logout(self.current_teacher):
                    util.msg_box('Goodbye!', f'Goodbye, {self.current_teacher}!')
                    self.current_teacher = None
                    self.mode = "teacher_login"
                    
                    # Return to teacher login interface
                    self.title_label.configure(text="Teacher Login - Face Recognition System")
                    self.build_teacher_login_ui()
                    self.update_status("Ready for teacher login...", "green")
                else:
                    util.msg_box('Error', 'Logout failed. Please try again.')
                    
        except Exception as e:
            util.msg_box('Error', f'Logout error: {str(e)}')
            
    def student_checkin(self):
        """Handle student check-in"""
        try:
            if not self.current_teacher:
                util.msg_box('Error', 'No teacher logged in.')
                return
                
            self.update_status("Processing student check-in...", "orange")
            
            if self.most_recent_capture_arr is None:
                util.msg_box('Error', 'No camera feed detected.')
                self.update_status("Check-in failed - No camera", "red")
                return
                
            # Anti-spoofing check
            label = test(
                image=self.most_recent_capture_arr,
                model_dir=self.model_dir,
                device_id=0
            )
            
            if label == 1:  # Real face detected
                student_name = self.recognize_student(self.most_recent_capture_arr)
                
                if student_name in ['unknown_person', 'no_persons_found']:
                    util.msg_box('Student Not Found', 'Student not recognized. Please register first or try again.')
                    self.update_status("Check-in failed - Student not recognized", "red")
                else:
                    # Mark attendance
                    if self.db.mark_attendance(student_name, self.current_teacher, "IN"):
                        util.msg_box('Welcome!', f'Welcome, {student_name}!')
                        self.update_status(f"Checked in: {student_name}", "green")
                        self.update_attendance_table()
                        self.update_attendance_summary()
                    else:
                        util.msg_box('Error', 'Check-in failed. Please try again.')
                        self.update_status("Check-in failed - Database error", "red")
                        
            else:  # Spoofing detected
                util.msg_box('Security Alert!', 'Spoofing detected! Please use real face.')
                self.update_status("Check-in failed - Spoofing detected", "red")
                
        except Exception as e:
            util.msg_box('Error', f'Check-in error: {str(e)}')
            self.update_status(f"Check-in error: {e}", "red")
            
    def student_checkout(self):
        """Handle student check-out"""
        try:
            if not self.current_teacher:
                util.msg_box('Error', 'No teacher logged in.')
                return
                
            self.update_status("Processing student check-out...", "orange")
            
            if self.most_recent_capture_arr is None:
                util.msg_box('Error', 'No camera feed detected.')
                self.update_status("Check-out failed - No camera", "red")
                return
                
            # Anti-spoofing check
            label = test(
                image=self.most_recent_capture_arr,
                model_dir=self.model_dir,
                device_id=0
            )
            
            if label == 1:  # Real face detected
                student_name = self.recognize_student(self.most_recent_capture_arr)
                
                if student_name in ['unknown_person', 'no_persons_found']:
                    util.msg_box('Student Not Found', 'Student not recognized. Please register first or try again.')
                    self.update_status("Check-out failed - Student not recognized", "red")
                else:
                    # Mark attendance
                    if self.db.mark_attendance(student_name, self.current_teacher, "OUT"):
                        util.msg_box('Goodbye!', f'Goodbye, {student_name}!')
                        self.update_status(f"Checked out: {student_name}", "green")
                        self.update_attendance_table()
                        self.update_attendance_summary()
                    else:
                        util.msg_box('Error', 'Check-out failed. Please try again.')
                        self.update_status("Check-out failed - Database error", "red")
                        
            else:  # Spoofing detected
                util.msg_box('Security Alert!', 'Spoofing detected! Please use real face.')
                self.update_status("Check-out failed - Spoofing detected", "red")
                
        except Exception as e:
            util.msg_box('Error', f'Check-out error: {str(e)}')
            self.update_status(f"Check-out error: {e}", "red")
            
    def recognize_student(self, image):
        """Recognize student using face recognition and database"""
        try:
            if not self.current_teacher:
                return 'unknown_person'
                
            # Get face encodings from the image
            face_encodings = face_recognition.face_encodings(image)
            
            if len(face_encodings) == 0:
                return 'no_persons_found'
                
            # Get known student encodings for current teacher
            student_encodings = self.db.get_student_face_encodings(self.current_teacher)
            
            if len(student_encodings) == 0:
                return 'unknown_person'
                
            # Compare faces
            face_encoding = face_encodings[0]
            known_encodings = list(student_encodings.values())
            known_names = list(student_encodings.keys())
            
            matches = face_recognition.compare_faces(known_encodings, face_encoding)
            
            if True in matches:
                match_index = matches.index(True)
                return known_names[match_index]
            else:
                return 'unknown_person'
                
        except Exception as e:
            print(f"Student recognition error: {e}")
            return 'unknown_person'
            
    def register_new_teacher(self):
        """Open teacher registration window"""
        self.register_window = ctk.CTkToplevel(self.main_window)
        self.register_window.geometry("600x500+400+200")
        self.register_window.title("Register New Teacher")
        self.register_window.grab_set()
        
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
        
        self.register_teacher_name_entry = ctk.CTkEntry(
            self.register_window,
            placeholder_text="Enter teacher name",
            width=300,
            height=35
        )
        self.register_teacher_name_entry.pack(pady=10)
        
        # Instructions
        instructions = ctk.CTkLabel(
            self.register_window,
            text="Position your face clearly in the camera and click 'Capture Face'",
            font=ctk.CTkFont(size=14),
            wraplength=450
        )
        instructions.pack(pady=20)
        
        # Buttons frame
        buttons_frame = ctk.CTkFrame(self.register_window)
        buttons_frame.pack(pady=20)
        
        capture_btn = ctk.CTkButton(
            buttons_frame,
            text="Capture Face",
            font=ctk.CTkFont(size=16),
            width=150,
            height=45,
            command=self.capture_teacher_face
        )
        capture_btn.pack(side="left", padx=10)
        
        cancel_btn = ctk.CTkButton(
            buttons_frame,
            text="Cancel",
            font=ctk.CTkFont(size=16),
            width=100,
            height=40,
            command=self.register_window.destroy
        )
        cancel_btn.pack(side="left", padx=10)
        
    def capture_teacher_face(self):
        """Capture and register teacher's face"""
        try:
            name = self.register_teacher_name_entry.get().strip()
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
                
            # Register teacher in database
            face_encoding = face_encodings[0]
            
            if self.db.register_teacher(name, face_encoding):
                util.msg_box('Success!', f'Teacher {name} registered successfully!')
                self.register_window.destroy()
                self.update_teachers_list()
            else:
                util.msg_box('Error', f'Teacher {name} already exists or registration failed.')
                
        except Exception as e:
            util.msg_box('Error', f'Registration failed: {str(e)}')
            
    def register_new_student(self):
        """Open student registration window"""
        if not self.current_teacher:
            util.msg_box('Error', 'No teacher logged in.')
            return
            
        self.register_student_window = ctk.CTkToplevel(self.main_window)
        self.register_student_window.geometry("600x500+400+200")
        self.register_student_window.title(f"Register New Student - {self.current_teacher}'s Class")
        self.register_student_window.grab_set()
        
        # Title
        title_label = ctk.CTkLabel(
            self.register_student_window,
            text=f"Register New Student\n{self.current_teacher}'s Class",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.pack(pady=20)
        
        # Name entry
        name_label = ctk.CTkLabel(
            self.register_student_window,
            text="Student Name:",
            font=ctk.CTkFont(size=16)
        )
        name_label.pack(pady=5)
        
        self.register_student_name_entry = ctk.CTkEntry(
            self.register_student_window,
            placeholder_text="Enter student name",
            width=300,
            height=35
        )
        self.register_student_name_entry.pack(pady=10)
        
        # Instructions
        instructions = ctk.CTkLabel(
            self.register_student_window,
            text="Position student's face clearly in the camera and click 'Capture Face'",
            font=ctk.CTkFont(size=14),
            wraplength=450
        )
        instructions.pack(pady=20)
        
        # Buttons frame
        buttons_frame = ctk.CTkFrame(self.register_student_window)
        buttons_frame.pack(pady=20)
        
        capture_btn = ctk.CTkButton(
            buttons_frame,
            text="Capture Face",
            font=ctk.CTkFont(size=16),
            width=150,
            height=45,
            command=self.capture_student_face
        )
        capture_btn.pack(side="left", padx=10)
        
        cancel_btn = ctk.CTkButton(
            buttons_frame,
            text="Cancel",
            font=ctk.CTkFont(size=16),
            width=100,
            height=40,
            command=self.register_student_window.destroy
        )
        cancel_btn.pack(side="left", padx=10)
        
    def capture_student_face(self):
        """Capture and register student's face"""
        try:
            name = self.register_student_name_entry.get().strip()
            if not name:
                util.msg_box('Error', 'Please enter student name.')
                return
                
            if self.most_recent_capture_arr is None:
                util.msg_box('Error', 'No camera feed detected.')
                return
                
            # Get face encoding
            face_encodings = face_recognition.face_encodings(self.most_recent_capture_arr)
            
            if len(face_encodings) == 0:
                util.msg_box('Error', 'No face detected. Please position face clearly in the camera.')
                return
                
            # Register student in database
            face_encoding = face_encodings[0]
            
            if self.current_teacher and self.db.register_student(name, self.current_teacher, face_encoding):
                util.msg_box('Success!', f'Student {name} registered successfully in {self.current_teacher}\'s class!')
                self.register_student_window.destroy()
                self.update_attendance_summary()
            else:
                util.msg_box('Error', f'Student {name} already exists in class or registration failed.')
                
        except Exception as e:
            util.msg_box('Error', f'Student registration failed: {str(e)}')
            
    def update_teachers_list(self):
        """Update the teachers list display"""
        try:
            teachers = self.db.get_all_teachers()
            
            self.teachers_textbox.delete("1.0", "end")
            
            if teachers:
                text = "Registered Teachers:\n\n"
                for teacher in teachers:
                    text += f"• {teacher['name']}\n"
                    text += f"  Registered: {teacher['created_at'][:10]}\n\n"
            else:
                text = "No teachers registered yet.\nClick 'Register New Teacher' to add one."
                
            self.teachers_textbox.insert("1.0", text)
            
        except Exception as e:
            print(f"Error updating teachers list: {e}")
            
    def setup_attendance_table(self):
        """Set up the attendance table"""
        try:
            # Table headers
            headers = ["Student Name", "Time", "Action"]
            
            # Get today's attendance
            today = datetime.date.today().isoformat()
            attendance_data = []
            if self.current_teacher:
                attendance_data = self.db.get_attendance_for_teacher(self.current_teacher, today)
            
            # Prepare table data
            table_data = [headers]
            for record in attendance_data:
                # Parse timestamp
                timestamp = record['timestamp']
                if isinstance(timestamp, str):
                    try:
                        dt = datetime.datetime.fromisoformat(timestamp.replace('T', ' '))
                        time_str = dt.strftime('%H:%M:%S')
                    except:
                        time_str = timestamp
                else:
                    time_str = str(timestamp)
                    
                table_data.append([
                    record['student_name'],
                    time_str,
                    record['attendance_type']
                ])
            
            # Create table
            self.attendance_table = CTkTable(
                self.table_frame,
                values=table_data,
                width=120,
                height=30
            )
            self.attendance_table.pack(pady=10, fill="both", expand=True)
            
        except Exception as e:
            print(f"Error setting up attendance table: {e}")
            
    def update_attendance_table(self):
        """Update the attendance table with latest data"""
        try:
            if hasattr(self, 'attendance_table'):
                self.attendance_table.destroy()
            self.setup_attendance_table()
            
        except Exception as e:
            print(f"Error updating attendance table: {e}")
            
    def update_attendance_summary(self):
        """Update attendance summary display"""
        try:
            if not self.current_teacher:
                return
                
            summary = self.db.get_todays_attendance_summary(self.current_teacher)
            
            text = f"""Today's Class Summary:

Total Students: {summary['total_students']}
Present Today: {summary['present_students']}
Absent Today: {summary['absent_students']}
Attendance: {summary['attendance_percentage']:.1f}%

Class: {self.current_teacher}
Date: {datetime.date.today()}"""

            if hasattr(self, 'summary_textbox') and self.summary_textbox.winfo_exists():
                self.summary_textbox.delete("1.0", "end")
                self.summary_textbox.insert("1.0", text)
                
        except Exception as e:
            print(f"Error updating attendance summary: {e}")
            
    def show_admin_panel(self):
        """Show admin login and panel"""
        # Create admin login dialog
        admin_dialog = ctk.CTkInputDialog(
            title="Admin Login",
            text="Enter admin password:"
        )
        
        password = admin_dialog.get_input()
        
        if password == self.admin_password:
            self.open_admin_panel()
        elif password is not None:  # User didn't cancel
            util.msg_box('Access Denied', 'Incorrect admin password.')
            
    def open_admin_panel(self):
        """Open admin panel window"""
        admin_window = ctk.CTkToplevel(self.main_window)
        admin_window.geometry("800x600+300+100")
        admin_window.title("Admin Panel")
        admin_window.grab_set()
        
        # Title
        title_label = ctk.CTkLabel(
            admin_window,
            text="Administrator Panel",
            font=ctk.CTkFont(size=28, weight="bold")
        )
        title_label.pack(pady=30)
        
        # Placeholder content
        content_frame = ctk.CTkFrame(admin_window)
        content_frame.pack(fill="both", expand=True, padx=40, pady=20)
        
        placeholder_label = ctk.CTkLabel(
            content_frame,
            text="Admin Panel Features\n(To be implemented)\n\n• Manage Teachers\n• Manage Students\n• View Reports\n• System Settings\n• Export Data",
            font=ctk.CTkFont(size=18),
            justify="left"
        )
        placeholder_label.pack(pady=100)
        
        # Close button
        close_btn = ctk.CTkButton(
            admin_window,
            text="Close",
            font=ctk.CTkFont(size=16),
            width=100,
            height=40,
            command=admin_window.destroy
        )
        close_btn.pack(pady=20)
        
    def on_closing(self):
        """Handle application closing"""
        try:
            # Logout current teacher if any
            if self.current_teacher:
                self.db.teacher_logout(self.current_teacher)
                
            # Release camera
            self.camera_active = False
            if self.camera:
                self.camera.release()
                
            # Close main window
            self.main_window.destroy()
            
        except Exception as e:
            print(f"Error during closing: {e}")
            
    def run(self):
        """Start the application"""
        self.main_window.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.main_window.mainloop()


if __name__ == "__main__":
    app = IntegratedAttendanceSystem()
    app.run()