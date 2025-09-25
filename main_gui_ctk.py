import os
import datetime
import customtkinter as ctk
from CTkTable import CTkTable
import cv2
from PIL import Image, ImageTk
import face_recognition
import threading
from tkinter import messagebox
import tkinter as tk
from CTkDatePicker.CTkDatePicker import CTkDatePicker
import sys

import util
# import test
from database import AttendanceDatabase

# Simple anti-spoofing function
def simple_anti_spoof_test(image, model_dir=None, device_id=0):
    """Simple anti-spoofing test - always returns 1 (real face)"""
    return 1

# Set the theme and color theme
ctk.set_appearance_mode("dark")  # Modes: "System" (standard), "Dark", "Light"
ctk.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"


class IntegratedAttendanceSystem:
    def __init__(self):
        self.main_window = ctk.CTk()
        self.main_window.geometry("1080x1920")
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
        """Build student attendance interface with tabview as main interface"""
        # Clear content frame
        for widget in self.content_frame.winfo_children():
            widget.destroy()
            
        # Update title
        self.title_label.configure(
            text=f"Student Attendance - {self.current_teacher}'s Class"
        )
        
        # Main TabView takes up entire content area
        self.attendance_tabview = ctk.CTkTabview(
            self.content_frame,
            width=1050,
            height=650
        )
        self.attendance_tabview.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create tabs
        self.attendance_tabview.add("Class Attendance")
        self.attendance_tabview.add("Midday Meal Attendance")
        
        # Setup comprehensive Class Attendance tab
        self.setup_class_attendance_tab()
        
        # Setup comprehensive Midday Meal Attendance tab  
        self.setup_meal_attendance_tab()
        
        # Set default tab
        self.attendance_tabview.set("Class Attendance")
        
        # Update summaries
        self.update_class_summary()
        self.update_meal_summary()
        
    def setup_class_attendance_tab(self):
        """Setup comprehensive Class Attendance tab with full functionality"""
        class_tab = self.attendance_tabview.tab("Class Attendance")
        
        # Main container for the tab
        main_container = ctk.CTkFrame(class_tab)
        main_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Top section - Three column layout
        top_section = ctk.CTkFrame(main_container)
        top_section.pack(fill="x", padx=5, pady=5)
        
        # Left - Camera
        camera_frame = ctk.CTkFrame(top_section)
        camera_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")

        camera_title = ctk.CTkLabel(
            camera_frame,
            text="Student Face Recognition",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        camera_title.pack(pady=10)

        # Webcam display
        self.class_webcam_label = ctk.CTkLabel(camera_frame, text="")
        self.class_webcam_label.pack(pady=5)

        # Right - Expanded Controls, Buttons and Summary
        controls_summary_frame = ctk.CTkFrame(top_section)
        controls_summary_frame.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")

        # Controls section
        controls_title = ctk.CTkLabel(
            controls_summary_frame,
            text="Class Attendance Controls",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        controls_title.pack(pady=10)

        # Horizontal layout for buttons and summary
        content_frame = ctk.CTkFrame(controls_summary_frame)
        content_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Left side - Buttons
        buttons_frame = ctk.CTkFrame(content_frame)
        buttons_frame.grid(row=0, column=0, padx=10, pady=5, sticky="nsew")

        # Mark Present button
        self.class_mark_present_btn = ctk.CTkButton(
            buttons_frame,
            text="Mark Present",
            font=ctk.CTkFont(size=14, weight="bold"),
            width=180,
            height=50,
            command=lambda: self._mark_regular_attendance("present"),
            fg_color=("#1f6aa5", "#1f6aa5")
        )
        self.class_mark_present_btn.pack(pady=8)

        # Register student button
        self.class_register_student_btn = ctk.CTkButton(
            buttons_frame,
            text="Register New Student",
            font=ctk.CTkFont(size=12),
            width=180,
            height=40,
            command=self.register_new_student,
            fg_color=("#388e3c", "#388e3c")
        )
        self.class_register_student_btn.pack(pady=5)

        # View Attendance button
        self.class_view_attendance_btn = ctk.CTkButton(
            buttons_frame,
            text="View Attendance Log",
            font=ctk.CTkFont(size=12),
            width=180,
            height=40,
            command=lambda: self.open_attendance_page("regular"),
            fg_color=("#d32f2f", "#d32f2f")
        )
        self.class_view_attendance_btn.pack(pady=5)

        # Teacher logout button (moved from summary section)
        self.teacher_logout_btn = ctk.CTkButton(
            buttons_frame,
            text="Teacher Logout",
            font=ctk.CTkFont(size=14),
            width=180,
            height=45,
            command=self.teacher_logout,
            fg_color=("#d32f2f", "#d32f2f")
        )
        self.teacher_logout_btn.pack(pady=10)

        # Right side - Summary and logout
        summary_section = ctk.CTkFrame(content_frame)
        summary_section.grid(row=0, column=1, padx=10, pady=5, sticky="nsew")

        summary_title = ctk.CTkLabel(
            summary_section,
            text="Today's Summary",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        summary_title.pack(pady=5)

        # Overall attendance summary
        self.class_overall_summary = ctk.CTkTextbox(
            summary_section,
            width=280,
            height=200
        )
        self.class_overall_summary.pack(pady=10)

        # Configure grid weights
        content_frame.grid_columnconfigure(0, weight=1)
        content_frame.grid_columnconfigure(1, weight=1)
        
        # Configure top section weights - give more space to right column
        top_section.grid_columnconfigure(0, weight=1)
        top_section.grid_columnconfigure(1, weight=2)
        
    def setup_meal_attendance_tab(self):
        """Setup comprehensive Midday Meal Attendance tab with full functionality"""
        meal_tab = self.attendance_tabview.tab("Midday Meal Attendance")
        
        # Main container for the tab
        main_container = ctk.CTkFrame(meal_tab)
        main_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Top section - Three column layout
        top_section = ctk.CTkFrame(main_container)
        top_section.pack(fill="x", padx=5, pady=5)
        
        # Left - Camera
        camera_frame = ctk.CTkFrame(top_section)
        camera_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")

        camera_title = ctk.CTkLabel(
            camera_frame,
            text="Student Face Recognition",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        camera_title.pack(pady=10)

        # Webcam display (shared with class tab)
        self.meal_webcam_label = ctk.CTkLabel(camera_frame, text="")
        self.meal_webcam_label.pack(pady=5)

        # Right - Expanded Controls, Buttons and Summary
        controls_summary_frame = ctk.CTkFrame(top_section)
        controls_summary_frame.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")

        # Controls section
        controls_title = ctk.CTkLabel(
            controls_summary_frame,
            text="Meal Attendance Controls",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        controls_title.pack(pady=10)

        # Horizontal layout for buttons and summary
        content_frame = ctk.CTkFrame(controls_summary_frame)
        content_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Left side - Buttons
        buttons_frame = ctk.CTkFrame(content_frame)
        buttons_frame.grid(row=0, column=0, padx=10, pady=5, sticky="nsew")

        # Mark Meal Present button
        self.meal_mark_present_btn = ctk.CTkButton(
            buttons_frame,
            text="Mark Meal Present",
            font=ctk.CTkFont(size=14, weight="bold"),
            width=180,
            height=50,
            command=lambda: self._mark_meal_attendance("present"),
            fg_color=("#1f6aa5", "#1f6aa5")
        )
        self.meal_mark_present_btn.pack(pady=8)

        # Register student button (same functionality)
        self.meal_register_student_btn = ctk.CTkButton(
            buttons_frame,
            text="Register New Student",
            font=ctk.CTkFont(size=12),
            width=180,
            height=40,
            command=self.register_new_student,
            fg_color=("#388e3c", "#388e3c")
        )
        self.meal_register_student_btn.pack(pady=5)

        # View Meal Log button
        self.meal_view_attendance_btn = ctk.CTkButton(
            buttons_frame,
            text="View Meal Log",
            font=ctk.CTkFont(size=12),
            width=180,
            height=40,
            command=lambda: self.open_attendance_page("meal"),
            fg_color=("#d32f2f", "#d32f2f")
        )
        self.meal_view_attendance_btn.pack(pady=5)

        # Right side - Summary and info
        summary_section = ctk.CTkFrame(content_frame)
        summary_section.grid(row=0, column=1, padx=10, pady=5, sticky="nsew")

        summary_title = ctk.CTkLabel(
            summary_section,
            text="Meal Program Summary",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        summary_title.pack(pady=5)

        # Overall meal summary
        self.meal_overall_summary = ctk.CTkTextbox(
            summary_section,
            width=280,
            height=120
        )
        self.meal_overall_summary.pack(pady=10)

        # Additional meal program info
        info_label = ctk.CTkLabel(
            summary_section,
            text="Midday Meal Program\nGovernment Tracking System\nNutritional Support Initiative",
            font=ctk.CTkFont(size=12),
            justify="center"
        )
        info_label.pack(pady=15)

        # Configure grid weights
        content_frame.grid_columnconfigure(0, weight=1)
        content_frame.grid_columnconfigure(1, weight=1)
        
        # Configure top section weights - give more space to right column
        top_section.grid_columnconfigure(0, weight=1)
        top_section.grid_columnconfigure(1, weight=2)        # Bottom section - Detailed summary
        bottom_section = ctk.CTkFrame(main_container)
        bottom_section.pack(fill="x", padx=5, pady=(10, 5))
        
        detailed_title = ctk.CTkLabel(
            bottom_section,
            text="Today's Meal Attendance Summary",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        detailed_title.pack(pady=10)
        
        self.meal_summary_textbox = ctk.CTkTextbox(
            bottom_section,
            width=900,
            height=120
        )
        self.meal_summary_textbox.pack(pady=10)
        
    def start_camera(self):
        """Initialize and start camera feed"""
        try:
            # Built-in camera (uncomment to use):
            # self.camera = cv2.VideoCapture(0)
            
            # USB camera (currently active):
            self.camera = cv2.VideoCapture(1)
            
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
                frame = cv2.resize(frame, (350, 280))
                
                # Convert to CTk image
                image = Image.fromarray(frame)
                photo = ctk.CTkImage(light_image=image, dark_image=image, size=(350, 280))
                
                # Update all camera labels
                if hasattr(self, 'webcam_label') and self.webcam_label and self.webcam_label.winfo_exists():
                    self.webcam_label.configure(image=photo)
                    
                if hasattr(self, 'class_webcam_label') and self.class_webcam_label and self.class_webcam_label.winfo_exists():
                    self.class_webcam_label.configure(image=photo)
                    
                if hasattr(self, 'meal_webcam_label') and self.meal_webcam_label and self.meal_webcam_label.winfo_exists():
                    self.meal_webcam_label.configure(image=photo)
                    
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
            label = simple_anti_spoof_test(
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
            

    
    def _mark_regular_attendance(self, status):
        """Mark regular class attendance"""
        try:
            self.update_status(f"Marking student {status}...", "orange")
            
            if self.most_recent_capture_arr is None:
                util.msg_box('Error', 'No camera feed detected.')
                self.update_status(f"Mark {status} failed - No camera", "red")
                return
                
            # Anti-spoofing check
            label = simple_anti_spoof_test(
                image=self.most_recent_capture_arr,
                model_dir=self.model_dir,
                device_id=0
            )
            
            if label == 1:  # Real face detected
                student_name = self.recognize_student(self.most_recent_capture_arr)
                
                if student_name in ['unknown_person', 'no_persons_found']:
                    util.msg_box('Student Not Found', 'Student not recognized. Please register first or try again.')
                    self.update_status(f"Mark {status} failed - Student not recognized", "red")
                else:
                    if status == "present" and self.current_teacher:
                        # Check if student is already marked present today
                        if self.db.is_student_present_today(student_name, self.current_teacher):
                            util.msg_box('Already Present', f'{student_name} is already marked present for today.')
                            self.update_status(f"Already present: {student_name}", "orange")
                        else:
                            # Mark attendance as present
                            if self.db.mark_student_present(student_name, self.current_teacher):
                                util.msg_box('Present!', f'{student_name} marked present for today!')
                                self.update_status(f"Marked present: {student_name}", "green")
                                self.update_attendance_summary()
                                self.update_class_summary()
                            else:
                                util.msg_box('Error', 'Failed to mark present. Please try again.')
                                self.update_status("Mark present failed - Database error", "red")
                        
            else:  # Spoofing detected
                util.msg_box('Security Alert!', 'Spoofing detected! Please use real face.')
                self.update_status(f"Mark {status} failed - Spoofing detected", "red")
                
        except Exception as e:
            print(f"Error marking regular attendance: {e}")
            self.update_status(f"Mark {status} error: {e}", "red")
    
    def _mark_meal_attendance(self, status):
        """Mark meal attendance"""
        try:
            self.update_status(f"Marking meal {status}...", "orange")
            
            if self.most_recent_capture_arr is None:
                util.msg_box('Error', 'No camera feed detected.')
                self.update_status(f"Mark meal {status} failed - No camera", "red")
                return
                
            # Anti-spoofing check
            label = simple_anti_spoof_test(
                image=self.most_recent_capture_arr,
                model_dir=self.model_dir,
                device_id=0
            )
            
            if label == 1:  # Real face detected
                student_name = self.recognize_student(self.most_recent_capture_arr)
                
                if student_name in ['unknown_person', 'no_persons_found']:
                    util.msg_box('Student Not Found', 'Student not recognized. Please register first or try again.')
                    self.update_status(f"Mark meal {status} failed - Student not recognized", "red")
                else:
                    if status == "present" and self.current_teacher:
                        # Check if student is already marked present for meal today
                        if self.db.is_student_meal_present_today(student_name, self.current_teacher):
                            util.msg_box('Already Present', f'{student_name} is already marked present for meal today.')
                            self.update_status(f"Already meal present: {student_name}", "orange")
                        else:
                            # Mark meal attendance
                            meal_status = "PRESENT" if status == "present" else "ABSENT"
                            if self.db.mark_student_meal_present(student_name, self.current_teacher, meal_status):
                                util.msg_box('Meal Attendance!', f'{student_name} marked {status} for meal!')
                                self.update_status(f"Meal {status}: {student_name}", "green")
                                self.update_attendance_summary()
                                self.update_meal_summary()
                            else:
                                util.msg_box('Error', f'Failed to mark meal {status}. Please try again.')
                                self.update_status(f"Mark meal {status} failed - Database error", "red")
                        
            else:  # Spoofing detected
                util.msg_box('Security Alert!', 'Spoofing detected! Please use real face.')
                self.update_status(f"Mark meal {status} failed - Spoofing detected", "red")
                
        except Exception as e:
            print(f"Error marking meal attendance: {e}")
            self.update_status(f"Mark meal {status} error: {e}", "red")
            
    def open_attendance_page(self, attendance_type="regular"):
        """Open the attendance log page in a separate window"""
        if not self.current_teacher:
            util.msg_box('Error', 'No teacher logged in.')
            return
            
        # Create attendance window
        self.attendance_window = ctk.CTkToplevel(self.main_window)
        self.attendance_window.geometry("1000x700+200+100")
        
        if attendance_type == "meal":
            self.attendance_window.title(f"Meal Attendance Log - {self.current_teacher}'s Class")
            self.current_attendance_type = "meal"
        else:
            self.attendance_window.title(f"Class Attendance Log - {self.current_teacher}'s Class")
            self.current_attendance_type = "regular"
            
        self.attendance_window.grab_set()
        
        # Header
        header_frame = ctk.CTkFrame(self.attendance_window)
        header_frame.pack(fill="x", padx=10, pady=10)
        
        title_label = ctk.CTkLabel(
            header_frame,
            text=f"Attendance Log - {self.current_teacher}'s Class",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(side="left", padx=20, pady=15)
        
        # Refresh button
        refresh_btn = ctk.CTkButton(
            header_frame,
            text="Refresh",
            font=ctk.CTkFont(size=14),
            width=100,
            height=35,
            command=self.refresh_attendance_table
        )
        refresh_btn.pack(side="right", padx=20, pady=15)
        
        # Date filter frame
        date_frame = ctk.CTkFrame(self.attendance_window)
        date_frame.pack(fill="x", padx=10, pady=5)
        
        date_label = ctk.CTkLabel(
            date_frame,
            text="Date Filter:",
            font=ctk.CTkFont(size=14)
        )
        date_label.pack(side="left", padx=20, pady=10)
        
        # Today button
        today_btn = ctk.CTkButton(
            date_frame,
            text="Today",
            font=ctk.CTkFont(size=12),
            width=80,
            height=30,
            command=lambda: self.filter_attendance_by_date("today")
        )
        today_btn.pack(side="left", padx=5, pady=10)
        
        # Yesterday button
        yesterday_btn = ctk.CTkButton(
            date_frame,
            text="Yesterday",
            font=ctk.CTkFont(size=12),
            width=80,
            height=30,
            command=lambda: self.filter_attendance_by_date("yesterday")
        )
        yesterday_btn.pack(side="left", padx=5, pady=10)
        
        # Scrollable frame for table
        self.attendance_scroll_frame = ctk.CTkScrollableFrame(
            self.attendance_window,
            width=950,
            height=500
        )
        self.attendance_scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Initialize table
        self.setup_scrollable_attendance_table()
        
        # Close button
        close_btn = ctk.CTkButton(
            self.attendance_window,
            text="Close",
            font=ctk.CTkFont(size=16),
            width=120,
            height=40,
            command=self.attendance_window.destroy
        )
        close_btn.pack(pady=10)
        
    def setup_scrollable_attendance_table(self):
        """Set up the scrollable attendance table"""
        try:
            # Clear existing table
            for widget in self.attendance_scroll_frame.winfo_children():
                widget.destroy()
                
            if not self.current_teacher:
                return
                
            # Get attendance data
            attendance_data = self.get_formatted_attendance_data()
            
            if not attendance_data:
                no_data_label = ctk.CTkLabel(
                    self.attendance_scroll_frame,
                    text="No attendance records found",
                    font=ctk.CTkFont(size=16)
                )
                no_data_label.pack(pady=50)
                return
            
            # Create table headers
            headers = ["Student Name", "Date", "Time", "Status"]
            
            # Table data with headers
            table_data = [headers] + attendance_data
            
            # Create scrollable table
            self.attendance_table = CTkTable(
                self.attendance_scroll_frame,
                values=table_data,
                width=200,
                height=40
            )
            self.attendance_table.pack(pady=10, fill="both", expand=True)
            
        except Exception as e:
            print(f"Error setting up scrollable attendance table: {e}")
            
    def get_formatted_attendance_data(self):
        """Get formatted attendance data for display based on current attendance type"""
        try:
            if not self.current_teacher:
                return []
                
            # Get daily attendance list based on current attendance type
            today = datetime.date.today().isoformat()
            attendance_type = getattr(self, 'current_attendance_type', 'regular')
            db_attendance_type = 'class' if attendance_type == 'regular' else 'meal'
            daily_attendance = self.db.get_attendance_for_teacher(self.current_teacher, today, db_attendance_type)
            
            formatted_data = []
            for record in daily_attendance:
                # Parse marked time
                marked_time = record['marked_time']
                if marked_time:
                    if isinstance(marked_time, str):
                        try:
                            dt = datetime.datetime.fromisoformat(marked_time.replace('T', ' '))
                            time_str = dt.strftime('%H:%M:%S')
                        except:
                            time_str = marked_time
                    else:
                        time_str = str(marked_time)
                else:
                    time_str = "Not marked"
                
                formatted_data.append([
                    record['student_name'],
                    record['date'],
                    time_str,
                    record['status']
                ])
            
            return formatted_data
            
        except Exception as e:
            print(f"Error getting formatted attendance data: {e}")
            return []
            
    def refresh_attendance_table(self):
        """Refresh the attendance table"""
        if hasattr(self, 'attendance_scroll_frame'):
            self.setup_scrollable_attendance_table()
            
    def filter_attendance_by_date(self, filter_type):
        """Filter attendance records by date (today or yesterday)"""
        try:
            if not self.current_teacher or not hasattr(self, 'attendance_scroll_frame'):
                return
                
            # Clear existing table
            for widget in self.attendance_scroll_frame.winfo_children():
                widget.destroy()
                
            # Calculate dates
            today = datetime.date.today().isoformat()
            yesterday = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
            
            # Determine attendance type
            attendance_type = getattr(self, 'current_attendance_type', 'regular')
            db_attendance_type = 'class' if attendance_type == 'regular' else 'meal'
            
            if filter_type == "today":
                attendance_data = self.db.get_attendance_for_teacher(self.current_teacher, today, db_attendance_type)
                display_date = "Today"
            elif filter_type == "yesterday":
                attendance_data = self.db.get_attendance_for_teacher(self.current_teacher, yesterday, db_attendance_type)
                display_date = "Yesterday"
            else:
                attendance_data = []
                display_date = "Unknown"
                
            # Format data for display
            formatted_data = []
            for record in attendance_data:
                # Use the correct field names from new database structure
                marked_time = record.get('marked_time', '')
                
                if marked_time:
                    try:
                        # Parse the timestamp
                        if isinstance(marked_time, str):
                            dt = datetime.datetime.fromisoformat(marked_time.replace('T', ' '))
                        else:
                            dt = marked_time
                        time_str = dt.strftime('%H:%M:%S')
                    except:
                        time_str = str(marked_time) if marked_time else 'N/A'
                else:
                    time_str = 'N/A'  # For absent students
                
                # Use correct status field
                status = "Present" if record.get('status') == "PRESENT" else "Absent"
                date_str = record.get('date', display_date)
                
                formatted_data.append([
                    record['student_name'],
                    date_str,
                    time_str,
                    status
                ])
            
            if not formatted_data:
                no_data_label = ctk.CTkLabel(
                    self.attendance_scroll_frame,
                    text=f"No attendance records found for {display_date.lower()}",
                    font=ctk.CTkFont(size=16)
                )
                no_data_label.pack(pady=50)
                return
                
            headers = ["Student Name", "Date", "Time", "Status"]
            table_data = [headers] + formatted_data
            
            # Create filtered table
            filtered_table = CTkTable(
                self.attendance_scroll_frame,
                values=table_data,
                width=200,
                height=40
            )
            filtered_table.pack(pady=10, fill="both", expand=True)
            
        except Exception as e:
            print(f"Error filtering attendance: {e}")
            # Show error message to user as well
            error_label = ctk.CTkLabel(
                self.attendance_scroll_frame,
                text=f"Error loading attendance data: {str(e)}",
                font=ctk.CTkFont(size=16),
                text_color="red"
            )
            error_label.pack(pady=50)
            
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
                self.update_class_summary()
                self.update_meal_summary()
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
            
    def update_attendance_summary(self):
        """Update attendance summary display in overall summaries"""
        try:
            if not self.current_teacher:
                return
                
            summary = self.get_present_absent_summary()
            
            text = f"""Overall Summary:

Total Students: {summary['total_students']}
Present Today: {summary['present_students']}
Absent Today: {summary['absent_students']}
Attendance: {summary['attendance_percentage']:.1f}%

Teacher: {self.current_teacher}
Date: {datetime.date.today().strftime('%Y-%m-%d')}"""

            # Update class tab overall summary
            if hasattr(self, 'class_overall_summary') and self.class_overall_summary.winfo_exists():
                self.class_overall_summary.delete("1.0", "end")
                self.class_overall_summary.insert("1.0", text)
            
            # Update meal tab overall summary with meal-specific data
            meal_summary = self.get_meal_attendance_summary()
            meal_text = f"""Meal Summary:

Total Students: {meal_summary.get('total_students', 0)}
Had Meal: {meal_summary.get('meal_present', 0)}
Missed Meal: {meal_summary.get('meal_absent', 0)}
Participation: {meal_summary.get('meal_percentage', 0):.1f}%

Teacher: {self.current_teacher}
Date: {datetime.date.today().strftime('%Y-%m-%d')}"""
            
            if hasattr(self, 'meal_overall_summary') and self.meal_overall_summary.winfo_exists():
                self.meal_overall_summary.delete("1.0", "end")
                self.meal_overall_summary.insert("1.0", meal_text)
                
        except Exception as e:
            print(f"Error updating attendance summary: {e}")
    
    def update_class_summary(self):
        """Update class attendance summary in the tab"""
        try:
            if not self.current_teacher:
                return
                
            summary = self.get_present_absent_summary()
            
            text = f"""Regular Class Attendance Summary:

Total Students: {summary['total_students']}
Present Today: {summary['present_students']}
Absent Today: {summary['absent_students']}
Attendance Rate: {summary['attendance_percentage']:.1f}%

Teacher: {self.current_teacher}
Date: {datetime.date.today()}"""

            if hasattr(self, 'class_overall_summary') and self.class_overall_summary.winfo_exists():
                self.class_overall_summary.delete("1.0", "end")
                self.class_overall_summary.insert("1.0", text)
                
        except Exception as e:
            print(f"Error updating class summary: {e}")
    
    def update_meal_summary(self):
        """Update meal attendance summary in the tab"""
        try:
            if not self.current_teacher:
                return
                
            # Get meal attendance data (using regular attendance for demo)
            meal_summary = self.get_meal_attendance_summary()
            
            text = f"""Midday Meal Attendance Summary:

Total Students: {meal_summary.get('total_students', 0)}
Had Meal: {meal_summary.get('meal_present', 0)}
Missed Meal: {meal_summary.get('meal_absent', 0)}
Participation: {meal_summary.get('meal_percentage', 0):.1f}%

Teacher: {self.current_teacher}
Date: {datetime.date.today()}"""

            if hasattr(self, 'meal_summary_textbox') and self.meal_summary_textbox.winfo_exists():
                self.meal_summary_textbox.delete("1.0", "end")
                self.meal_summary_textbox.insert("1.0", text)
                
        except Exception as e:
            print(f"Error updating meal summary: {e}")
    
    def get_meal_attendance_summary(self):
        """Get meal attendance summary"""
        try:
            if not self.current_teacher:
                return {'total_students': 0, 'meal_present': 0, 'meal_absent': 0, 'meal_percentage': 0}
            
            # Use the meal attendance summary method
            meal_summary = self.db.get_meal_attendance_summary(self.current_teacher)
            
            return {
                'total_students': meal_summary['total_students'],
                'meal_present': meal_summary['present_students'],
                'meal_absent': meal_summary['absent_students'],
                'meal_percentage': meal_summary['attendance_percentage']
            }
                
        except Exception as e:
            print(f"Error getting meal attendance summary: {e}")
            return {'total_students': 0, 'meal_present': 0, 'meal_absent': 0, 'meal_percentage': 0}
            
    def get_present_absent_summary(self):
        """Get today's present/absent summary for teacher's class (class attendance)"""
        try:
            if not self.current_teacher:
                return {'total_students': 0, 'present_students': 0, 'absent_students': 0, 'attendance_percentage': 0}
            
            # Use the class attendance summary method
            return self.db.get_class_attendance_summary(self.current_teacher)
                
        except Exception as e:
            print(f"Error getting present/absent summary: {e}")
            return {'total_students': 0, 'present_students': 0, 'absent_students': 0, 'attendance_percentage': 0}
            
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
        """Open comprehensive admin panel window with tabbed views"""
        self.admin_window = ctk.CTkToplevel(self.main_window)
        self.admin_window.geometry("1200x800+150+50")
        self.admin_window.title("Admin Panel - Attendance Management System")
        self.admin_window.grab_set()
        
        # Compact header frame
        header_frame = ctk.CTkFrame(
            self.admin_window,
            height=55,
            corner_radius=0,
            fg_color=("gray85", "gray15")
        )
        header_frame.pack(fill="x", padx=0, pady=0)
        header_frame.pack_propagate(False)
        
        # Compact title
        title_label = ctk.CTkLabel(
            header_frame,
            text="📊 Administrator Panel",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=("gray10", "gray90")
        )
        title_label.pack(pady=15)
        
        # Main content container with reduced spacing
        content_frame = ctk.CTkFrame(
            self.admin_window,
            corner_radius=10,
            fg_color="transparent"
        )
        content_frame.pack(fill="both", expand=True, padx=15, pady=10)
        
        # Compact tab view
        self.admin_tabview = ctk.CTkTabview(
            content_frame, 
            width=1070, 
            height=600,
            corner_radius=10,
            border_width=1,
            segmented_button_fg_color=("gray80", "gray20"),
            segmented_button_selected_color=("blue", "blue"),
            segmented_button_selected_hover_color=("dark blue", "dark blue")
        )
        self.admin_tabview.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Add modern tabs with icons
        self.admin_tabview.add("👨‍🏫 Teachers Analytics")
        self.admin_tabview.add("👨‍🎓 Students Analytics")
        self.admin_tabview.add("📊 Data Export")
        
        # Setup tabs
        self.setup_teachers_tab()
        self.setup_students_tab()
        self.setup_export_tab()
        
        # Set default tab
        self.admin_tabview.set("👨‍🏫 Teachers Analytics")
        
    def setup_teachers_tab(self):
        """Setup the Teachers Data tab"""
        teachers_tab = self.admin_tabview.tab("👨‍🏫 Teachers Analytics")
        
        # Compact control panel
        control_panel = ctk.CTkFrame(
            teachers_tab,
            corner_radius=10,
            border_width=1,
            fg_color=("gray95", "gray10")
        )
        control_panel.pack(fill="x", padx=10, pady=10)
        
        # Compact control panel header
        control_header = ctk.CTkLabel(
            control_panel,
            text="🔧 Analytics Controls",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=("blue", "light blue")
        )
        control_header.pack(pady=8)
        
        # Compact controls container
        controls_container = ctk.CTkFrame(control_panel, fg_color="transparent")
        controls_container.pack(fill="x", padx=15, pady=(0, 10))
        
        # Compact teacher selection card
        teacher_card = ctk.CTkFrame(
            controls_container,
            corner_radius=8,
            fg_color=("white", "gray20")
        )
        teacher_card.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        ctk.CTkLabel(
            teacher_card, 
            text="👤 Teacher Selection", 
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=("gray20", "gray80")
        ).pack(pady=(8, 3))
        
        # Get all teachers for dropdown
        teachers = self.db.get_all_teachers()
        teacher_names = [teacher['name'] for teacher in teachers] if teachers else ["No teachers found"]
        
        self.teacher_dropdown = ctk.CTkComboBox(
            teacher_card,
            values=teacher_names,
            width=180,
            height=28,
            corner_radius=6,
            command=self.on_teacher_selected,
            font=ctk.CTkFont(size=11)
        )
        self.teacher_dropdown.pack(pady=(3, 8))
        
        # Date range card
        date_card = ctk.CTkFrame(
            controls_container,
            corner_radius=12,
            fg_color=("white", "gray20")
        )
        date_card.pack(side="right", padx=(15, 0))
        
        ctk.CTkLabel(
            date_card, 
            text="📅 Date Range", 
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=("gray20", "gray80")
        ).pack(pady=(15, 10))
        
        date_controls = ctk.CTkFrame(date_card, fg_color="transparent")
        date_controls.pack(pady=(0, 15), padx=15)
        
        # Compact start date
        start_frame = ctk.CTkFrame(date_controls, fg_color="transparent")
        start_frame.pack(side="left", padx=4)
        ctk.CTkLabel(
            start_frame, 
            text="From:", 
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=("gray40", "gray70")
        ).pack(pady=(0, 2))
        
        self.start_date_teacher = CTkDatePicker(start_frame, max_date=datetime.date.today())
        # Set default date to today
        today_str = datetime.date.today().strftime("%m/%d/%Y")
        self.start_date_teacher.date_entry.insert(0, today_str)
        self.start_date_teacher.selected_date = datetime.datetime.combine(datetime.date.today(), datetime.time())
        self.start_date_teacher.pack(pady=2)
        
        # Compact end date
        end_frame = ctk.CTkFrame(date_controls, fg_color="transparent")
        end_frame.pack(side="left", padx=4)
        ctk.CTkLabel(
            end_frame, 
            text="To:", 
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=("gray40", "gray70")
        ).pack(pady=(0, 2))
        
        self.end_date_teacher = CTkDatePicker(end_frame, max_date=datetime.date.today())
        # Set default date to today
        self.end_date_teacher.date_entry.insert(0, today_str)
        self.end_date_teacher.selected_date = datetime.datetime.combine(datetime.date.today(), datetime.time())
        self.end_date_teacher.pack(pady=2)
        
        # Compact load button
        load_btn = ctk.CTkButton(
            date_card,
            text="📊 Load Analytics",
            command=self.load_teacher_data_with_validation,
            width=120,
            height=32,
            corner_radius=8,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=("blue", "blue"),
            hover_color=("dark blue", "dark blue")
        )
        load_btn.pack(pady=(3, 8))
        
        # Compact summary section
        self.teacher_summary_frame = ctk.CTkFrame(
            teachers_tab,
            corner_radius=8,
            border_width=1,
            fg_color=("gray95", "gray10")
        )
        self.teacher_summary_frame.pack(fill="x", padx=10, pady=5)
        
        # Compact data display section
        data_container = ctk.CTkFrame(
            teachers_tab,
            corner_radius=8,
            border_width=1,
            fg_color=("gray95", "gray10")
        )
        data_container.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        # Compact data section header
        data_header = ctk.CTkLabel(
            data_container,
            text="📈 Teachers Activity Data",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=("blue", "light blue")
        )
        data_header.pack(pady=8)
        
        # Compact scrollable data frame
        self.teacher_data_frame = ctk.CTkScrollableFrame(
            data_container,
            height=320,
            corner_radius=6,
            fg_color=("white", "gray20")
        )
        self.teacher_data_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
    def setup_students_tab(self):
        """Setup the Students Data tab"""
        students_tab = self.admin_tabview.tab("👨‍🎓 Students Analytics")
        
        # Compact control panel
        control_panel = ctk.CTkFrame(
            students_tab,
            corner_radius=10,
            border_width=1,
            fg_color=("gray95", "gray10")
        )
        control_panel.pack(fill="x", padx=10, pady=10)
        
        # Compact control panel header
        control_header = ctk.CTkLabel(
            control_panel,
            text="🔧 Student Analytics Controls",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=("blue", "light blue")
        )
        control_header.pack(pady=8)
        
        # Compact controls container
        controls_container = ctk.CTkFrame(control_panel, fg_color="transparent")
        controls_container.pack(fill="x", padx=15, pady=(0, 10))
        
        # Compact teacher selection card
        teacher_card = ctk.CTkFrame(
            controls_container,
            corner_radius=8,
            fg_color=("white", "gray20")
        )
        teacher_card.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        ctk.CTkLabel(
            teacher_card, 
            text="👤 Select Teacher", 
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=("gray20", "gray80")
        ).pack(pady=(8, 3))
        
        # Get all teachers for dropdown
        teachers = self.db.get_all_teachers()
        teacher_names = [teacher['name'] for teacher in teachers] if teachers else ["No teachers found"]
        
        self.student_teacher_dropdown = ctk.CTkComboBox(
            teacher_card,
            values=teacher_names,
            width=180,
            height=28,
            corner_radius=6,
            command=self.on_student_teacher_selected,
            font=ctk.CTkFont(size=11)
        )
        self.student_teacher_dropdown.pack(pady=(3, 8))
        
        # Date range card
        date_card = ctk.CTkFrame(
            controls_container,
            corner_radius=12,
            fg_color=("white", "gray20")
        )
        date_card.pack(side="right", padx=(15, 0))
        
        ctk.CTkLabel(
            date_card, 
            text="📅 Date Range", 
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=("gray20", "gray80")
        ).pack(pady=(15, 10))
        
        date_controls = ctk.CTkFrame(date_card, fg_color="transparent")
        date_controls.pack(pady=(0, 15), padx=15)
        
        # Compact start date
        start_frame = ctk.CTkFrame(date_controls, fg_color="transparent")
        start_frame.pack(side="left", padx=4)
        ctk.CTkLabel(
            start_frame, 
            text="From:", 
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=("gray40", "gray70")
        ).pack(pady=(0, 2))
        
        self.start_date_student = CTkDatePicker(start_frame, max_date=datetime.date.today())
        # Set default date to today
        today_str = datetime.date.today().strftime("%m/%d/%Y")
        self.start_date_student.date_entry.insert(0, today_str)
        self.start_date_student.selected_date = datetime.datetime.combine(datetime.date.today(), datetime.time())
        self.start_date_student.pack(pady=2)
        
        # Compact end date
        end_frame = ctk.CTkFrame(date_controls, fg_color="transparent")
        end_frame.pack(side="left", padx=4)
        ctk.CTkLabel(
            end_frame, 
            text="To:", 
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=("gray40", "gray70")
        ).pack(pady=(0, 2))
        
        self.end_date_student = CTkDatePicker(end_frame, max_date=datetime.date.today())
        # Set default date to today
        self.end_date_student.date_entry.insert(0, today_str)
        self.end_date_student.selected_date = datetime.datetime.combine(datetime.date.today(), datetime.time())
        self.end_date_student.pack(pady=2)
        
        # Compact load button
        load_btn = ctk.CTkButton(
            date_card,
            text="📊 Load Analytics",
            command=self.load_student_data_with_validation,
            width=120,
            height=32,
            corner_radius=8,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=("blue", "blue"),
            hover_color=("dark blue", "dark blue")
        )
        load_btn.pack(pady=(3, 8))
        
        # Compact summary section
        self.student_summary_frame = ctk.CTkFrame(
            students_tab,
            corner_radius=8,
            border_width=1,
            fg_color=("gray95", "gray10")
        )
        self.student_summary_frame.pack(fill="x", padx=10, pady=5)
        
        # Compact data display section
        data_container = ctk.CTkFrame(
            students_tab,
            corner_radius=8,
            border_width=1,
            fg_color=("gray95", "gray10")
        )
        data_container.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        # Compact data section header
        data_header = ctk.CTkLabel(
            data_container,
            text="📊 Student Attendance Data",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=("blue", "light blue")
        )
        data_header.pack(pady=8)
        
        # Compact scrollable data frame
        self.student_data_frame = ctk.CTkScrollableFrame(
            data_container,
            height=320,
            corner_radius=6,
            fg_color=("white", "gray20")
        )
        self.student_data_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
    
    def setup_export_tab(self):
        """Setup the Data Export tab"""
        export_tab = self.admin_tabview.tab("📊 Data Export")
        
        # Scrollable main container
        main_container = ctk.CTkScrollableFrame(export_tab)
        main_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Header
        header_frame = ctk.CTkFrame(
            main_container,
            corner_radius=10,
            border_width=1,
            fg_color=("gray95", "gray10")
        )
        header_frame.pack(fill="x", padx=5, pady=5)
        
        header_title = ctk.CTkLabel(
            header_frame,
            text="📊 Data Export to Excel",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=("blue", "light blue")
        )
        header_title.pack(pady=15)
        
        # Export controls container
        controls_container = ctk.CTkFrame(main_container)
        controls_container.pack(fill="x", padx=5, pady=10)
        
        # Date range selection
        date_frame = ctk.CTkFrame(
            controls_container,
            corner_radius=8,
            fg_color=("white", "gray20")
        )
        date_frame.pack(fill="x", padx=10, pady=10)
        
        date_title = ctk.CTkLabel(
            date_frame,
            text="📅 Select Date Range",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=("gray20", "gray80")
        )
        date_title.pack(pady=(10, 5))
        
        # Date controls
        date_controls = ctk.CTkFrame(date_frame, fg_color="transparent")
        date_controls.pack(pady=10)
        
        # Start date
        start_frame = ctk.CTkFrame(date_controls, fg_color="transparent")
        start_frame.pack(side="left", padx=10)
        ctk.CTkLabel(
            start_frame,
            text="From:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=("gray40", "gray70")
        ).pack(pady=(0, 5))
        
        self.export_start_date = CTkDatePicker(start_frame, max_date=datetime.date.today())
        today_str = datetime.date.today().strftime("%m/%d/%Y")
        self.export_start_date.date_entry.insert(0, today_str)
        self.export_start_date.selected_date = datetime.datetime.combine(datetime.date.today(), datetime.time())
        self.export_start_date.pack(pady=5)
        
        # End date
        end_frame = ctk.CTkFrame(date_controls, fg_color="transparent")
        end_frame.pack(side="left", padx=10)
        ctk.CTkLabel(
            end_frame,
            text="To:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=("gray40", "gray70")
        ).pack(pady=(0, 5))
        
        self.export_end_date = CTkDatePicker(end_frame, max_date=datetime.date.today())
        self.export_end_date.date_entry.insert(0, today_str)
        self.export_end_date.selected_date = datetime.datetime.combine(datetime.date.today(), datetime.time())
        self.export_end_date.pack(pady=5)
        
        # Data type selection
        checkbox_frame = ctk.CTkFrame(
            controls_container,
            corner_radius=8,
            fg_color=("white", "gray20")
        )
        checkbox_frame.pack(fill="x", padx=10, pady=10)
        
        checkbox_title = ctk.CTkLabel(
            checkbox_frame,
            text="📋 Select Data Types to Export",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=("gray20", "gray80")
        )
        checkbox_title.pack(pady=(10, 5))
        
        # Checkbox container
        checkbox_container = ctk.CTkFrame(checkbox_frame, fg_color="transparent")
        checkbox_container.pack(pady=10)
        
        # Teacher data checkbox
        self.export_teacher_data = ctk.CTkCheckBox(
            checkbox_container,
            text="Teacher Login/Logout Data",
            font=ctk.CTkFont(size=12),
            checkbox_width=20,
            checkbox_height=20
        )
        self.export_teacher_data.pack(anchor="w", padx=20, pady=5)
        
        # Student data checkbox
        self.export_student_data = ctk.CTkCheckBox(
            checkbox_container,
            text="Student Registration Data",
            font=ctk.CTkFont(size=12),
            checkbox_width=20,
            checkbox_height=20
        )
        self.export_student_data.pack(anchor="w", padx=20, pady=5)
        
        # Class attendance checkbox
        self.export_class_attendance = ctk.CTkCheckBox(
            checkbox_container,
            text="Class Attendance Data",
            font=ctk.CTkFont(size=12),
            checkbox_width=20,
            checkbox_height=20
        )
        self.export_class_attendance.pack(anchor="w", padx=20, pady=5)
        
        # Meal attendance checkbox
        self.export_meal_attendance = ctk.CTkCheckBox(
            checkbox_container,
            text="Midday Meal Attendance Data",
            font=ctk.CTkFont(size=12),
            checkbox_width=20,
            checkbox_height=20
        )
        self.export_meal_attendance.pack(anchor="w", padx=20, pady=5)
        
        # Export Actions Section - Make it more prominent
        export_actions_frame = ctk.CTkFrame(
            controls_container,
            corner_radius=8,
            fg_color=("white", "gray20"),
            border_width=2,
            border_color=("#2fa572", "#2fa572")
        )
        export_actions_frame.pack(fill="x", padx=10, pady=20)
        
        # Export button - Make it more visible
        self.export_button = ctk.CTkButton(
            export_actions_frame,
            text="EXPORT TO EXCEL FILES",
            font=ctk.CTkFont(size=18, weight="bold"),
            width=400,
            height=60,
            command=self.export_data_to_excel,
            fg_color=("#2fa572", "#2fa572"),
            hover_color=("#207244", "#207244"),
            corner_radius=10
        )
        self.export_button.pack(pady=20)
        
        # Status label
        self.export_status_label = ctk.CTkLabel(
            export_actions_frame,
            text="Files will be exported to your Downloads folder",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=("#2fa572", "#2fa572")
        )
        self.export_status_label.pack(pady=(0, 15))
    
    def on_teacher_selected(self, choice):
        """Handle teacher selection in teachers tab"""
        # Clear previous data when teacher changes
        for widget in self.teacher_data_frame.winfo_children():
            widget.destroy()
        for widget in self.teacher_summary_frame.winfo_children():
            widget.destroy()
            
    def on_student_teacher_selected(self, choice):
        """Handle teacher selection in students tab"""
        # Clear previous data when teacher changes
        for widget in self.student_data_frame.winfo_children():
            widget.destroy()
        for widget in self.student_summary_frame.winfo_children():
            widget.destroy()
            
    def validate_date_range(self, start_date, end_date):
        """Validate that from date is not higher than to date"""
        try:
            # Convert dates to datetime.date objects
            if isinstance(start_date, str):
                # Try different date formats
                try:
                    start_dt = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
                except ValueError:
                    try:
                        start_dt = datetime.datetime.strptime(start_date, "%m/%d/%Y").date()
                    except ValueError:
                        start_dt = datetime.datetime.strptime(start_date, "%d/%m/%Y").date()
            else:
                start_dt = start_date
                
            if isinstance(end_date, str):
                # Try different date formats
                try:
                    end_dt = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()
                except ValueError:
                    try:
                        end_dt = datetime.datetime.strptime(end_date, "%m/%d/%Y").date()
                    except ValueError:
                        end_dt = datetime.datetime.strptime(end_date, "%d/%m/%Y").date()
            else:
                end_dt = end_date
                
            if start_dt > end_dt:
                util.msg_box('Invalid Date Range', 'From date cannot be later than To date. Please select a valid date range.')
                return False
            return True
        except Exception as e:
            util.msg_box('Date Error', f'Invalid date format: {str(e)}')
            return False
            
    def load_teacher_data_with_validation(self):
        """Load teacher data with date validation"""
        try:
            start_date = self.start_date_teacher.get_date()
            end_date = self.end_date_teacher.get_date()
            
            if self.validate_date_range(start_date, end_date):
                self.load_teacher_data()
        except Exception as e:
            util.msg_box('Error', f'Failed to load teacher data: {str(e)}')
            
    def load_student_data_with_validation(self):
        """Load student data with date validation"""
        try:
            start_date = self.start_date_student.get_date()
            end_date = self.end_date_student.get_date()
            
            if self.validate_date_range(start_date, end_date):
                self.load_student_data()
        except Exception as e:
            util.msg_box('Error', f'Failed to load student data: {str(e)}')
            
    def load_teacher_data(self):
        """Load and display teacher login/logout data within time frame"""
        try:
            # Clear previous data
            for widget in self.teacher_data_frame.winfo_children():
                widget.destroy()
            for widget in self.teacher_summary_frame.winfo_children():
                widget.destroy()

            # Get date range
            start_date = self.start_date_teacher.get_date()
            end_date = self.end_date_teacher.get_date()
            
            # Convert dates to proper format for database query
            try:
                if isinstance(start_date, str):
                    # Parse string date and convert to YYYY-MM-DD format
                    try:
                        parsed_date = datetime.datetime.strptime(start_date, "%m/%d/%Y")
                        start_date_str = parsed_date.strftime('%Y-%m-%d')
                    except ValueError:
                        start_date_str = start_date  # Use as is if already in correct format
                else:
                    start_date_str = start_date.strftime('%Y-%m-%d')
                    
                if isinstance(end_date, str):
                    # Parse string date and convert to YYYY-MM-DD format
                    try:
                        parsed_date = datetime.datetime.strptime(end_date, "%m/%d/%Y")
                        end_date_str = parsed_date.strftime('%Y-%m-%d')
                    except ValueError:
                        end_date_str = end_date  # Use as is if already in correct format
                else:
                    end_date_str = end_date.strftime('%Y-%m-%d')
            except Exception as e:
                print(f"Error parsing dates: {e}")
                start_date_str = str(start_date)
                end_date_str = str(end_date)

            # Display compact summary with icons
            summary_label = ctk.CTkLabel(
                self.teacher_summary_frame,
                text=f"📈 Teacher Activity Summary\n{start_date_str} to {end_date_str}",
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color=("blue", "light blue")
            )
            summary_label.pack(pady=8)

            # Get teacher activity data within time frame
            teacher_data = self.get_teacher_activity_data(start_date_str, end_date_str)
            
            if not teacher_data:
                no_data_frame = ctk.CTkFrame(
                    self.teacher_data_frame,
                    corner_radius=10,
                    fg_color=("gray90", "gray25")
                )
                no_data_frame.pack(pady=30, padx=20, fill="x")
                
                no_data_label = ctk.CTkLabel(
                    no_data_frame,
                    text="📭 No teacher activity found for the selected date range",
                    font=ctk.CTkFont(size=14),
                    text_color=("gray50", "gray70")
                )
                no_data_label.pack(pady=30)
                return

            # Prepare table data
            headers = ["Teacher Name", "Login Count", "Logout Count", "Last Activity"]
            table_data = [headers]
            
            for teacher in teacher_data:
                table_data.append([
                    teacher['teacher_name'],
                    str(teacher['login_count']),
                    str(teacher['logout_count']),
                    teacher['last_activity']
                ])

            # Create table
            table = CTkTable(
                self.teacher_data_frame,
                values=table_data,
                width=150,
                height=30
            )
            table.pack(pady=10, fill="both", expand=True)
            
            # Add Combined Activity Section with modern styling
            activity_section = ctk.CTkFrame(
                self.teacher_data_frame,
                corner_radius=10,
                fg_color=("gray98", "gray15")
            )
            activity_section.pack(pady=10, padx=8, fill="both", expand=True)
            
            combined_label = ctk.CTkLabel(
                activity_section,
                text="🕒 Recent Combined Teacher Activity",
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color=("blue", "light blue")
            )
            combined_label.pack(pady=8)
            
            # Get combined activity data
            combined_activity = self.get_combined_teacher_activity(start_date_str, end_date_str, 15)
            
            if combined_activity:
                # Prepare combined activity table
                activity_headers = ["Teacher Name", "Activity", "Timestamp"]
                activity_table_data = [activity_headers]
                
                for activity in combined_activity:
                    activity_table_data.append([
                        activity['teacher_name'],
                        activity['activity_type'],
                        activity['timestamp']
                    ])
                
                # Create combined activity table
                activity_table = CTkTable(
                    activity_section,
                    values=activity_table_data,
                    width=150,
                    height=25
                )
                activity_table.pack(pady=5, padx=10, fill="both", expand=True)
            else:
                no_activity_label = ctk.CTkLabel(
                    activity_section,
                    text="📭 No combined activity found for the selected date range",
                    font=ctk.CTkFont(size=10),
                    text_color=("gray50", "gray70")
                )
                no_activity_label.pack(pady=10)
            
        except Exception as e:
            print(f"Error loading teacher data: {e}")
            error_frame = ctk.CTkFrame(
                self.teacher_data_frame,
                corner_radius=10,
                fg_color=("red", "dark red"),
                border_width=1
            )
            error_frame.pack(pady=15, padx=15, fill="x")
            
            error_label = ctk.CTkLabel(
                error_frame,
                text=f"⚠️ Error loading data: {str(e)}",
                font=ctk.CTkFont(size=12),
                text_color="white"
            )
            error_label.pack(pady=10)
            
    def get_teacher_activity_data(self, start_date, end_date):
        """Get teacher login/logout activity within date range"""
        try:
            # Get all teachers first
            teachers = self.db.get_all_teachers()
            if not teachers:
                return []
                
            teacher_activity = []
            
            for teacher in teachers:
                teacher_name = teacher['name']
                
                # Count logins within date range using database connection
                with self.db.get_connection() as conn:
                    cursor = conn.cursor()
                    
                    # Count logins
                    cursor.execute("""
                        SELECT COUNT(*) as login_count 
                        FROM teacher_activity 
                        WHERE teacher_name = ? AND activity_type = 'LOGIN' 
                        AND DATE(timestamp) BETWEEN ? AND ?
                    """, (teacher_name, start_date, end_date))
                    login_count = cursor.fetchone()[0]
                    
                    # Count logouts
                    cursor.execute("""
                        SELECT COUNT(*) as logout_count 
                        FROM teacher_activity 
                        WHERE teacher_name = ? AND activity_type = 'LOGOUT' 
                        AND DATE(timestamp) BETWEEN ? AND ?
                    """, (teacher_name, start_date, end_date))
                    logout_count = cursor.fetchone()[0]
                    
                    # Get last activity
                    cursor.execute("""
                        SELECT timestamp, activity_type 
                        FROM teacher_activity 
                        WHERE teacher_name = ? AND DATE(timestamp) BETWEEN ? AND ?
                        ORDER BY timestamp DESC LIMIT 1
                    """, (teacher_name, start_date, end_date))
                    last_activity_row = cursor.fetchone()
                    
                    if last_activity_row:
                        last_activity = f"{last_activity_row[1]} at {last_activity_row[0][:19]}"
                    else:
                        last_activity = "No activity"
                    
                    teacher_activity.append({
                        'teacher_name': teacher_name,
                        'login_count': login_count,
                        'logout_count': logout_count,
                        'last_activity': last_activity
                    })
                    
            return teacher_activity
            
        except Exception as e:
            print(f"Error getting teacher activity data: {e}")
            return []
            
    def get_combined_teacher_activity(self, start_date, end_date, limit=20):
        """Get combined activity log for all teachers within date range"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get all teacher activities within date range, ordered by timestamp
                cursor.execute("""
                    SELECT teacher_name, activity_type, timestamp 
                    FROM teacher_activity 
                    WHERE DATE(timestamp) BETWEEN ? AND ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                """, (start_date, end_date, limit))
                
                activities = cursor.fetchall()
                
                combined_activity = []
                for activity in activities:
                    combined_activity.append({
                        'teacher_name': activity[0],
                        'activity_type': activity[1],
                        'timestamp': activity[2][:19] if activity[2] else "Unknown"
                    })
                    
                return combined_activity
                
        except Exception as e:
            print(f"Error getting combined teacher activity: {e}")
            return []
            
    def load_student_data(self):
        """Load and display student attendance data with missing data as absent"""
        try:
            selected_teacher = self.student_teacher_dropdown.get()
            if selected_teacher == "No teachers found" or not selected_teacher:
                # Show message for no teacher selected
                for widget in self.student_data_frame.winfo_children():
                    widget.destroy()
                for widget in self.student_summary_frame.winfo_children():
                    widget.destroy()
                    
                no_teacher_label = ctk.CTkLabel(
                    self.student_data_frame,
                    text="Please select a teacher first",
                    font=ctk.CTkFont(size=14),
                    text_color="orange"
                )
                no_teacher_label.pack(pady=50)
                return
                
            start_date = self.start_date_student.get_date()
            end_date = self.end_date_student.get_date()
            
            # Convert dates to proper format
            try:
                if isinstance(start_date, str):
                    try:
                        parsed_date = datetime.datetime.strptime(start_date, "%m/%d/%Y")
                        start_date_str = parsed_date.strftime('%Y-%m-%d')
                    except ValueError:
                        start_date_str = start_date
                else:
                    start_date_str = start_date.strftime('%Y-%m-%d')
                    
                if isinstance(end_date, str):
                    try:
                        parsed_date = datetime.datetime.strptime(end_date, "%m/%d/%Y")
                        end_date_str = parsed_date.strftime('%Y-%m-%d')
                    except ValueError:
                        end_date_str = end_date
                else:
                    end_date_str = end_date.strftime('%Y-%m-%d')
            except Exception as e:
                print(f"Error parsing dates: {e}")
                start_date_str = str(start_date)
                end_date_str = str(end_date)
            
            # Clear previous data
            for widget in self.student_data_frame.winfo_children():
                widget.destroy()
            for widget in self.student_summary_frame.winfo_children():
                widget.destroy()
            
            # Display modern summary with icons
            summary_label = ctk.CTkLabel(
                self.student_summary_frame,
                text=f"📊 Student Attendance Report\n{selected_teacher} • {start_date_str} to {end_date_str}",
                font=ctk.CTkFont(size=16, weight="bold"),
                text_color=("blue", "light blue")
            )
            summary_label.pack(pady=15)
            
            # Get student attendance data
            student_data = self.get_student_attendance_in_range(selected_teacher, start_date_str, end_date_str)
            
            if not student_data:
                no_data_frame = ctk.CTkFrame(
                    self.student_data_frame,
                    corner_radius=10,
                    fg_color=("gray90", "gray25")
                )
                no_data_frame.pack(pady=30, padx=20, fill="x")
                
                no_data_label = ctk.CTkLabel(
                    no_data_frame,
                    text="👨‍🎓 No students found for the selected teacher",
                    font=ctk.CTkFont(size=14),
                    text_color=("gray50", "gray70")
                )
                no_data_label.pack(pady=30)
                return
            
            # Prepare table data
            headers = ["Student Name", "Present Days", "Absent Days", "Total Days", "Attendance %"]
            table_data = [headers]
            
            for student in student_data:
                table_data.append([
                    student['student_name'],
                    str(student['present_days']),
                    str(student['absent_days']),
                    str(student['total_days']),
                    f"{student['attendance_percentage']:.1f}%"
                ])
            
            # Create table
            table = CTkTable(
                self.student_data_frame,
                values=table_data,
                width=150,
                height=30
            )
            table.pack(pady=10, fill="both", expand=True)
            
        except Exception as e:
            print(f"Error loading student data: {e}")
            error_frame = ctk.CTkFrame(
                self.student_data_frame,
                corner_radius=10,
                fg_color=("red", "dark red"),
                border_width=1
            )
            error_frame.pack(pady=30, padx=20, fill="x")
            
            error_label = ctk.CTkLabel(
                error_frame,
                text=f"⚠️ Error loading data: {str(e)}",
                font=ctk.CTkFont(size=14),
                text_color="white"
            )
            error_label.pack(pady=20)
            
    def get_student_attendance_in_range(self, teacher_name, start_date, end_date):
        """Get student attendance data with missing data counted as absent"""
        try:
            # Get all students for this teacher
            students = self.db.get_students_for_teacher(teacher_name)
            if not students:
                return []
                
            # Calculate number of days in range
            start_dt = datetime.datetime.strptime(start_date, '%Y-%m-%d').date()
            end_dt = datetime.datetime.strptime(end_date, '%Y-%m-%d').date()
            total_days = (end_dt - start_dt).days + 1
            
            student_attendance = []
            
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                for student in students:
                    student_name = student['name']
                    
                    # Count present days (only count records with status='PRESENT')
                    cursor.execute("""
                        SELECT COUNT(*) as present_count 
                        FROM attendance_records 
                        WHERE student_id = (
                            SELECT id FROM students WHERE name = ? AND teacher_name = ?
                        ) 
                        AND status = 'PRESENT' 
                        AND date BETWEEN ? AND ?
                    """, (student_name, teacher_name, start_date, end_date))
                    
                    present_days = cursor.fetchone()[0]
                    
                    # Absent days = total days - present days
                    # This follows the logic: "take them as absent unless it is written present"
                    absent_days = total_days - present_days
                    
                    # Calculate attendance percentage
                    if total_days > 0:
                        attendance_percentage = (present_days / total_days) * 100
                    else:
                        attendance_percentage = 0.0
                    
                    student_attendance.append({
                        'student_name': student_name,
                        'present_days': present_days,
                        'absent_days': absent_days,
                        'total_days': total_days,
                        'attendance_percentage': attendance_percentage
                    })
                    
            return student_attendance
            
        except Exception as e:
            print(f"Error getting student attendance in range: {e}")
            return []
    
    def export_data_to_excel(self):
        """Export selected data types to Excel files"""
        try:
            # Validate date range
            try:
                if hasattr(self.export_start_date, 'selected_date') and self.export_start_date.selected_date:
                    start_date = self.export_start_date.selected_date.date()
                else:
                    util.msg_box('Error', 'Please select a valid start date.')
                    return
                    
                if hasattr(self.export_end_date, 'selected_date') and self.export_end_date.selected_date:
                    end_date = self.export_end_date.selected_date.date()
                else:
                    util.msg_box('Error', 'Please select a valid end date.')
                    return
            except Exception as e:
                util.msg_box('Error', f'Please select valid start and end dates. Error: {str(e)}')
                return
            
            if not self.validate_date_range(start_date, end_date):
                return
            
            # Check if at least one checkbox is selected
            export_options = {
                'teacher': self.export_teacher_data.get(),
                'student': self.export_student_data.get(),
                'class_attendance': self.export_class_attendance.get(),
                'meal_attendance': self.export_meal_attendance.get()
            }
            
            if not any(export_options.values()):
                util.msg_box('Error', 'Please select at least one data type to export.')
                return
            
            # Update status
            self.export_status_label.configure(text="Exporting data, please wait...")
            self.export_button.configure(state="disabled")
            self.main_window.update()
            
            # Get downloads folder path with date range
            start_date_str = start_date.isoformat()
            end_date_str = end_date.isoformat()
            folder_name = f"Attendance_Export_{start_date_str}_to_{end_date_str}"
            downloads_path = os.path.join(os.path.expanduser("~"), "Downloads", folder_name)
            os.makedirs(downloads_path, exist_ok=True)
            
            exported_files = []
            
            # Export teacher data
            if export_options['teacher']:
                filename = self.export_teacher_data_to_excel(downloads_path, start_date_str, end_date_str)
                if filename:
                    exported_files.append(filename)
            
            # Export student data
            if export_options['student']:
                filename = self.export_student_data_to_excel(downloads_path, start_date_str, end_date_str)
                if filename:
                    exported_files.append(filename)
            
            # Export class attendance data
            if export_options['class_attendance']:
                filename = self.export_class_attendance_to_excel(downloads_path, start_date_str, end_date_str)
                if filename:
                    exported_files.append(filename)
            
            # Export meal attendance data
            if export_options['meal_attendance']:
                filename = self.export_meal_attendance_to_excel(downloads_path, start_date_str, end_date_str)
                if filename:
                    exported_files.append(filename)
            
            # Show success message
            if exported_files:
                files_list = '\n'.join([f"• {os.path.basename(f)}" for f in exported_files])
                util.msg_box('Export Successful!', 
                           f'Data exported successfully!\n\nFiles created:\n{files_list}\n\nLocation: {downloads_path}')
                self.export_status_label.configure(text=f"{len(exported_files)} file(s) exported successfully to Downloads folder")
            else:
                util.msg_box('Export Failed', 'No data was exported. Please check your selections and try again.')
                self.export_status_label.configure(text="Export failed - No data found")
            
        except Exception as e:
            util.msg_box('Export Error', f'An error occurred during export: {str(e)}')
            self.export_status_label.configure(text=f"Export error: {str(e)}")
            print(f"Export error: {e}")
        finally:
            self.export_button.configure(state="normal")
    
    def export_teacher_data_to_excel(self, downloads_path, start_date, end_date):
        """Export teacher login/logout data to Excel"""
        try:
            import pandas as pd
            
            # Get teacher activity data
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT teacher_name, activity_type, timestamp
                    FROM teacher_activity
                    WHERE DATE(timestamp) BETWEEN ? AND ?
                    ORDER BY timestamp DESC
                """, (start_date, end_date))
                
                data = cursor.fetchall()
            
            if not data:
                return None
            
            # Create DataFrame
            df = pd.DataFrame(data, columns=['Teacher Name', 'Activity Type', 'Timestamp'])
            
            # Format timestamp
            df['Date'] = pd.to_datetime(df['Timestamp']).dt.date
            df['Time'] = pd.to_datetime(df['Timestamp']).dt.time
            
            # Reorder columns
            df = df[['Teacher Name', 'Activity Type', 'Date', 'Time', 'Timestamp']]
            
            # Save to Excel
            filename = os.path.join(downloads_path, f"Teacher_Activity_{start_date}_to_{end_date}.xlsx")
            df.to_excel(filename, index=False, sheet_name='Teacher Activity')
            
            return filename
            
        except ImportError:
            util.msg_box('Missing Dependency', 'pandas library is required for Excel export. Please install it using: pip install pandas openpyxl')
            return None
        except Exception as e:
            print(f"Error exporting teacher data: {e}")
            return None
    
    def export_student_data_to_excel(self, downloads_path, start_date, end_date):
        """Export student registration data to Excel (organized by class)"""
        try:
            import pandas as pd
            
            # Get all students with their teachers
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT teacher_name, name, created_at
                    FROM students
                    WHERE DATE(created_at) BETWEEN ? AND ?
                    ORDER BY teacher_name, name
                """, (start_date, end_date))
                
                data = cursor.fetchall()
            
            if not data:
                return None
            
            # Create Excel file with multiple sheets (one per teacher)
            filename = os.path.join(downloads_path, f"Student_Registration_{start_date}_to_{end_date}.xlsx")
            
            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                # Group by teacher
                teacher_groups = {}
                for teacher_name, student_name, created_at in data:
                    if teacher_name not in teacher_groups:
                        teacher_groups[teacher_name] = []
                    teacher_groups[teacher_name].append({
                        'Student Name': student_name,
                        'Registration Date': created_at,
                        'Class Teacher': teacher_name
                    })
                
                # Create sheet for each teacher
                for teacher_name, students in teacher_groups.items():
                    df = pd.DataFrame(students)
                    sheet_name = teacher_name[:30]  # Excel sheet name limit
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
                
                # Create summary sheet
                all_students = []
                for teacher_name, students in teacher_groups.items():
                    all_students.extend(students)
                
                if all_students:
                    summary_df = pd.DataFrame(all_students)
                    summary_df = summary_df.sort_values(['Class Teacher', 'Student Name'])
                    summary_df.to_excel(writer, sheet_name='All Students Summary', index=False)
            
            return filename
            
        except ImportError:
            util.msg_box('Missing Dependency', 'pandas library is required for Excel export. Please install it using: pip install pandas openpyxl')
            return None
        except Exception as e:
            print(f"Error exporting student data: {e}")
            return None
    
    def export_class_attendance_to_excel(self, downloads_path, start_date, end_date):
        """Export comprehensive class attendance data showing all teachers and students"""
        try:
            import pandas as pd
            
            # Get all teachers and their students
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get all teachers
                cursor.execute("SELECT DISTINCT teacher_name FROM students ORDER BY teacher_name")
                teachers = [row[0] for row in cursor.fetchall()]
                
                if not teachers:
                    return None
                
                # Get all unique dates in the range
                cursor.execute("""
                    SELECT DISTINCT date FROM attendance_records 
                    WHERE attendance_type = 'class' AND DATE(date) BETWEEN ? AND ?
                    ORDER BY date
                """, (start_date, end_date))
                dates = [row[0] for row in cursor.fetchall()]
                
                if not dates:
                    return None
                
                # Get all students for each teacher
                teacher_students = {}
                for teacher in teachers:
                    cursor.execute("""
                        SELECT name FROM students 
                        WHERE teacher_name = ? 
                        ORDER BY name
                    """, (teacher,))
                    teacher_students[teacher] = [row[0] for row in cursor.fetchall()]
                
                # Get attendance data
                cursor.execute("""
                    SELECT s.teacher_name, a.student_name, a.date, a.status
                    FROM attendance_records a
                    JOIN students s ON a.student_name = s.name AND a.class_teacher = s.teacher_name
                    WHERE a.attendance_type = 'class' 
                    AND DATE(a.date) BETWEEN ? AND ?
                """, (start_date, end_date))
                
                attendance_data = {}
                for teacher_name, student_name, date, status in cursor.fetchall():
                    key = (teacher_name, student_name, date)
                    attendance_data[key] = status
            
            # Create comprehensive Excel file
            filename = os.path.join(downloads_path, f"Class_Attendance_Comprehensive_{start_date}_to_{end_date}.xlsx")
            
            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                # Create comprehensive attendance sheet
                comprehensive_data = []
                
                # Create header row with teacher sections
                header_row = ['Date']
                for i, teacher in enumerate(teachers):
                    if i > 0:
                        header_row.append('')  # Empty column for spacing
                    # Add columns for this teacher (Student, Present, Absent, Total)
                    header_row.extend([f'{teacher} - Student', f'{teacher} - Present', f'{teacher} - Absent', f'{teacher} - Total'])
                
                comprehensive_data.append(header_row)
                
                # Create data rows for each date
                for date in dates:
                    row = [date]
                    
                    for i, teacher in enumerate(teachers):
                        if i > 0:
                            row.append('')  # Empty column for spacing
                        
                        students = teacher_students.get(teacher, [])
                        present_count = 0
                        absent_count = 0
                        
                        # Count attendance for this teacher on this date
                        for student in students:
                            status = attendance_data.get((teacher, student, date), 'No Record')
                            if status == 'present':
                                present_count += 1
                            elif status == 'absent':
                                absent_count += 1
                        
                        total_students = len(students)
                        
                        row.extend([
                            f'{len(students)} students',
                            str(present_count),
                            str(absent_count),
                            str(total_students)
                        ])
                    
                    comprehensive_data.append(row)
                
                # Convert to DataFrame and save
                df_comprehensive = pd.DataFrame(comprehensive_data[1:], columns=comprehensive_data[0])
                df_comprehensive.to_excel(writer, sheet_name='Comprehensive Attendance', index=False)
                
                # Create detailed student-by-student sheet
                detailed_data = []
                
                # Create detailed header
                detailed_header = ['Date', 'Time']
                for i, teacher in enumerate(teachers):
                    if i > 0:
                        detailed_header.append('')  # Spacing column
                    students = teacher_students.get(teacher, [])
                    for student in students:
                        detailed_header.append(f'{teacher} - {student}')
                
                detailed_data.append(detailed_header)
                
                # Create detailed data rows
                for date in dates:
                    row = [date, '']  # Date and empty time column
                    
                    for i, teacher in enumerate(teachers):
                        if i > 0:
                            row.append('')  # Spacing column
                        
                        students = teacher_students.get(teacher, [])
                        for student in students:
                            status = attendance_data.get((teacher, student, date), 'No Record')
                            # Use simple indicators: P = Present, A = Absent, - = No Record
                            if status == 'present':
                                row.append('P')
                            elif status == 'absent':
                                row.append('A')
                            else:
                                row.append('-')
                    
                    detailed_data.append(row)
                
                # Convert detailed data to DataFrame and save
                df_detailed = pd.DataFrame(detailed_data[1:], columns=detailed_data[0])
                df_detailed.to_excel(writer, sheet_name='Student Details', index=False)
                
                # Create summary sheet for each teacher
                for teacher in teachers:
                    teacher_data = []
                    students = teacher_students.get(teacher, [])
                    
                    # Create teacher-specific data
                    teacher_header = ['Date'] + students
                    teacher_data.append(teacher_header)
                    
                    for date in dates:
                        row = [date]
                        for student in students:
                            status = attendance_data.get((teacher, student, date), 'No Record')
                            if status == 'present':
                                row.append('Present')
                            elif status == 'absent':
                                row.append('Absent')
                            else:
                                row.append('No Record')
                        teacher_data.append(row)
                    
                    if teacher_data and len(teacher_data) > 1:  # Has data besides header
                        df_teacher = pd.DataFrame(teacher_data[1:], columns=teacher_data[0])
                        sheet_name = f"{teacher}"[:30]  # Excel sheet name limit
                        df_teacher.to_excel(writer, sheet_name=sheet_name, index=False)
            
            return filename
            
        except ImportError:
            util.msg_box('Missing Dependency', 'pandas library is required for Excel export. Please install it using: pip install pandas openpyxl')
            return None
        except Exception as e:
            print(f"Error exporting comprehensive class attendance data: {e}")
            return None
    
    def export_meal_attendance_to_excel(self, downloads_path, start_date, end_date):
        """Export comprehensive meal attendance data showing all teachers and students"""
        try:
            import pandas as pd
            
            # Get all teachers and their students
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get all teachers
                cursor.execute("SELECT DISTINCT teacher_name FROM students ORDER BY teacher_name")
                teachers = [row[0] for row in cursor.fetchall()]
                
                if not teachers:
                    return None
                
                # Get all unique dates in the range
                cursor.execute("""
                    SELECT DISTINCT date FROM attendance_records 
                    WHERE attendance_type = 'meal' AND DATE(date) BETWEEN ? AND ?
                    ORDER BY date
                """, (start_date, end_date))
                dates = [row[0] for row in cursor.fetchall()]
                
                if not dates:
                    return None
                
                # Get all students for each teacher
                teacher_students = {}
                for teacher in teachers:
                    cursor.execute("""
                        SELECT name FROM students 
                        WHERE teacher_name = ? 
                        ORDER BY name
                    """, (teacher,))
                    teacher_students[teacher] = [row[0] for row in cursor.fetchall()]
                
                # Get meal attendance data
                cursor.execute("""
                    SELECT s.teacher_name, a.student_name, a.date, a.status
                    FROM attendance_records a
                    JOIN students s ON a.student_name = s.name AND a.class_teacher = s.teacher_name
                    WHERE a.attendance_type = 'meal' 
                    AND DATE(a.date) BETWEEN ? AND ?
                """, (start_date, end_date))
                
                attendance_data = {}
                for teacher_name, student_name, date, status in cursor.fetchall():
                    key = (teacher_name, student_name, date)
                    attendance_data[key] = status
            
            # Create comprehensive Excel file
            filename = os.path.join(downloads_path, f"Meal_Attendance_Comprehensive_{start_date}_to_{end_date}.xlsx")
            
            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                # Create comprehensive attendance sheet
                comprehensive_data = []
                
                # Create header row with teacher sections
                header_row = ['Date']
                for i, teacher in enumerate(teachers):
                    if i > 0:
                        header_row.append('')  # Empty column for spacing
                    # Add columns for this teacher (Student, Present, Absent, Total)
                    header_row.extend([f'{teacher} - Student', f'{teacher} - Present', f'{teacher} - Absent', f'{teacher} - Total'])
                
                comprehensive_data.append(header_row)
                
                # Create data rows for each date
                for date in dates:
                    row = [date]
                    
                    for i, teacher in enumerate(teachers):
                        if i > 0:
                            row.append('')  # Empty column for spacing
                        
                        students = teacher_students.get(teacher, [])
                        present_count = 0
                        absent_count = 0
                        
                        # Count attendance for this teacher on this date
                        for student in students:
                            status = attendance_data.get((teacher, student, date), 'No Record')
                            if status == 'present':
                                present_count += 1
                            elif status == 'absent':
                                absent_count += 1
                        
                        total_students = len(students)
                        
                        row.extend([
                            f'{len(students)} students',
                            str(present_count),
                            str(absent_count),
                            str(total_students)
                        ])
                    
                    comprehensive_data.append(row)
                
                # Convert to DataFrame and save
                df_comprehensive = pd.DataFrame(comprehensive_data[1:], columns=comprehensive_data[0])
                df_comprehensive.to_excel(writer, sheet_name='Comprehensive Meal Attendance', index=False)
                
                # Create detailed student-by-student sheet
                detailed_data = []
                
                # Create detailed header
                detailed_header = ['Date', 'Time']
                for i, teacher in enumerate(teachers):
                    if i > 0:
                        detailed_header.append('')  # Spacing column
                    students = teacher_students.get(teacher, [])
                    for student in students:
                        detailed_header.append(f'{teacher} - {student}')
                
                detailed_data.append(detailed_header)
                
                # Create detailed data rows
                for date in dates:
                    row = [date, '']  # Date and empty time column
                    
                    for i, teacher in enumerate(teachers):
                        if i > 0:
                            row.append('')  # Spacing column
                        
                        students = teacher_students.get(teacher, [])
                        for student in students:
                            status = attendance_data.get((teacher, student, date), 'No Record')
                            # Use simple indicators: P = Present, A = Absent, - = No Record
                            if status == 'present':
                                row.append('P')
                            elif status == 'absent':
                                row.append('A')
                            else:
                                row.append('-')
                    
                    detailed_data.append(row)
                
                # Convert detailed data to DataFrame and save
                df_detailed = pd.DataFrame(detailed_data[1:], columns=detailed_data[0])
                df_detailed.to_excel(writer, sheet_name='Student Details', index=False)
                
                # Create summary sheet for each teacher
                for teacher in teachers:
                    teacher_data = []
                    students = teacher_students.get(teacher, [])
                    
                    # Create teacher-specific data
                    teacher_header = ['Date'] + students
                    teacher_data.append(teacher_header)
                    
                    for date in dates:
                        row = [date]
                        for student in students:
                            status = attendance_data.get((teacher, student, date), 'No Record')
                            if status == 'present':
                                row.append('Present')
                            elif status == 'absent':
                                row.append('Absent')
                            else:
                                row.append('No Record')
                        teacher_data.append(row)
                    
                    if teacher_data and len(teacher_data) > 1:  # Has data besides header
                        df_teacher = pd.DataFrame(teacher_data[1:], columns=teacher_data[0])
                        sheet_name = f"{teacher}"[:30]  # Excel sheet name limit
                        df_teacher.to_excel(writer, sheet_name=sheet_name, index=False)
            
            return filename
            
        except ImportError:
            util.msg_box('Missing Dependency', 'pandas library is required for Excel export. Please install it using: pip install pandas openpyxl')
            return None
        except Exception as e:
            print(f"Error exporting comprehensive meal attendance data: {e}")
            return None
        
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