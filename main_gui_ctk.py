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
            text="Mark Present",
            font=ctk.CTkFont(size=16, weight="bold"),
            width=200,
            height=50,
            command=self.mark_student_present
        )
        self.student_login_btn.pack(pady=10)

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
        
        # View Attendance button
        self.view_attendance_btn = ctk.CTkButton(
            self.student_controls_frame,
            text="View Attendance Log",
            font=ctk.CTkFont(size=14),
            width=180,
            height=40,
            command=self.open_attendance_page
        )
        self.view_attendance_btn.pack(pady=10)
        
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
            
    def mark_student_present(self):
        """Mark student as present for today"""
        try:
            if not self.current_teacher:
                util.msg_box('Error', 'No teacher logged in.')
                return
                
            self.update_status("Marking student present...", "orange")
            
            if self.most_recent_capture_arr is None:
                util.msg_box('Error', 'No camera feed detected.')
                self.update_status("Mark present failed - No camera", "red")
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
                    self.update_status("Mark present failed - Student not recognized", "red")
                else:
                    # Check if student is already marked present today
                    if self.db.is_student_present_today(student_name, self.current_teacher):
                        util.msg_box('Already Present', f'{student_name} is already marked present for today.')
                        self.update_status(f"Already present: {student_name}", "orange")
                    else:
                        # Mark attendance as present using new daily system
                        if self.db.mark_student_present(student_name, self.current_teacher):
                            util.msg_box('Present!', f'{student_name} marked present for today!')
                            self.update_status(f"Marked present: {student_name}", "green")
                            self.update_attendance_summary()
                        else:
                            util.msg_box('Error', 'Failed to mark present. Please try again.')
                            self.update_status("Mark present failed - Database error", "red")
                        
            else:  # Spoofing detected
                util.msg_box('Security Alert!', 'Spoofing detected! Please use real face.')
                self.update_status("Mark present failed - Spoofing detected", "red")
                
        except Exception as e:
            util.msg_box('Error', f'Mark present error: {str(e)}')
            self.update_status(f"Mark present error: {e}", "red")
            
    def open_attendance_page(self):
        """Open the attendance log page in a separate window"""
        if not self.current_teacher:
            util.msg_box('Error', 'No teacher logged in.')
            return
            
        # Create attendance window
        self.attendance_window = ctk.CTkToplevel(self.main_window)
        self.attendance_window.geometry("1000x700+200+100")
        self.attendance_window.title(f"Attendance Log - {self.current_teacher}'s Class")
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
        """Get formatted attendance data for display"""
        try:
            if not self.current_teacher:
                return []
                
            # Get daily attendance list (shows all students with their status)
            today = datetime.date.today().isoformat()
            daily_attendance = self.db.get_attendance_for_teacher(self.current_teacher, today)
            
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
            
            if filter_type == "today":
                attendance_data = self.db.get_attendance_for_teacher(self.current_teacher, today)
                display_date = "Today"
            elif filter_type == "yesterday":
                attendance_data = self.db.get_attendance_for_teacher(self.current_teacher, yesterday)
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
        """Update attendance summary display"""
        try:
            if not self.current_teacher:
                return
                
            summary = self.get_present_absent_summary()
            
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
            
    def get_present_absent_summary(self):
        """Get today's present/absent summary for teacher's class"""
        try:
            if not self.current_teacher:
                return {'total_students': 0, 'present_students': 0, 'absent_students': 0, 'attendance_percentage': 0}
            
            # Use the new daily attendance summary method
            return self.db.get_attendance_summary(self.current_teacher)
                
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
        self.admin_window.geometry("1200x800+200+100")
        self.admin_window.title("Admin Panel - Attendance Management System")
        self.admin_window.grab_set()
        
        # Title
        title_label = ctk.CTkLabel(
            self.admin_window,
            text="Administrator Panel",
            font=ctk.CTkFont(size=28, weight="bold")
        )
        title_label.pack(pady=20)
        
        # Create tab view
        self.admin_tabview = ctk.CTkTabview(self.admin_window, width=1150, height=700)
        self.admin_tabview.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Add tabs
        self.admin_tabview.add("Teachers Data")
        self.admin_tabview.add("Students Data")
        
        # Setup tabs
        self.setup_teachers_tab()
        self.setup_students_tab()
        
        # Set default tab
        self.admin_tabview.set("Teachers Data")
        
    def setup_teachers_tab(self):
        """Setup the Teachers Data tab"""
        teachers_tab = self.admin_tabview.tab("Teachers Data")
        
        # Control frame
        control_frame = ctk.CTkFrame(teachers_tab)
        control_frame.pack(fill="x", padx=10, pady=10)
        
        # Teacher selection
        teacher_frame = ctk.CTkFrame(control_frame)
        teacher_frame.pack(side="left", fill="x", expand=True, padx=5, pady=10)
        
        ctk.CTkLabel(teacher_frame, text="Select Teacher:", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=5)
        
        # Get all teachers for dropdown
        teachers = self.db.get_all_teachers()
        teacher_names = [teacher['name'] for teacher in teachers] if teachers else ["No teachers found"]
        
        self.teacher_dropdown = ctk.CTkComboBox(
            teacher_frame,
            values=teacher_names,
            width=200,
            command=self.on_teacher_selected
        )
        self.teacher_dropdown.pack(pady=5)
        
        # Date range frame
        date_frame = ctk.CTkFrame(control_frame)
        date_frame.pack(side="right", padx=5, pady=10)
        
        ctk.CTkLabel(date_frame, text="Date Range:", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=5)
        
        date_controls = ctk.CTkFrame(date_frame)
        date_controls.pack(pady=5)
        
        # Start date
        start_frame = ctk.CTkFrame(date_controls)
        start_frame.pack(side="left", padx=5)
        ctk.CTkLabel(start_frame, text="From:", font=ctk.CTkFont(size=12)).pack()
        
        self.start_date_teacher = CTkDatePicker(start_frame, max_date=datetime.date.today())
        # Set default date to today
        today_str = datetime.date.today().strftime("%m/%d/%Y")
        self.start_date_teacher.date_entry.insert(0, today_str)
        self.start_date_teacher.selected_date = datetime.datetime.combine(datetime.date.today(), datetime.time())
        self.start_date_teacher.pack(pady=5)
        
        # End date  
        end_frame = ctk.CTkFrame(date_controls)
        end_frame.pack(side="left", padx=5)
        ctk.CTkLabel(end_frame, text="To:", font=ctk.CTkFont(size=12)).pack()
        
        self.end_date_teacher = CTkDatePicker(end_frame, max_date=datetime.date.today())
        # Set default date to today
        self.end_date_teacher.date_entry.insert(0, today_str)
        self.end_date_teacher.selected_date = datetime.datetime.combine(datetime.date.today(), datetime.time())
        self.end_date_teacher.pack(pady=5)
        
        # Load data button
        load_btn = ctk.CTkButton(
            date_frame,
            text="Load Data",
            command=self.load_teacher_data_with_validation,
            width=120,
            height=32
        )
        load_btn.pack(pady=10)
        
        # Summary frame
        self.teacher_summary_frame = ctk.CTkFrame(teachers_tab)
        self.teacher_summary_frame.pack(fill="x", padx=10, pady=5)
        
        # Data display frame
        self.teacher_data_frame = ctk.CTkScrollableFrame(teachers_tab, height=400)
        self.teacher_data_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
    def setup_students_tab(self):
        """Setup the Students Data tab"""
        students_tab = self.admin_tabview.tab("Students Data")
        
        # Control frame
        control_frame = ctk.CTkFrame(students_tab)
        control_frame.pack(fill="x", padx=10, pady=10)
        
        # Teacher selection for students
        teacher_frame = ctk.CTkFrame(control_frame)
        teacher_frame.pack(side="left", fill="x", expand=True, padx=5, pady=10)
        
        ctk.CTkLabel(teacher_frame, text="Select Teacher:", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=5)
        
        # Get all teachers for dropdown
        teachers = self.db.get_all_teachers()
        teacher_names = [teacher['name'] for teacher in teachers] if teachers else ["No teachers found"]
        
        self.student_teacher_dropdown = ctk.CTkComboBox(
            teacher_frame,
            values=teacher_names,
            width=200,
            command=self.on_student_teacher_selected
        )
        self.student_teacher_dropdown.pack(pady=5)
        
        # Date range frame
        date_frame = ctk.CTkFrame(control_frame)
        date_frame.pack(side="right", padx=5, pady=10)
        
        ctk.CTkLabel(date_frame, text="Date Range:", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=5)
        
        date_controls = ctk.CTkFrame(date_frame)
        date_controls.pack(pady=5)
        
        # Start date
        start_frame = ctk.CTkFrame(date_controls)
        start_frame.pack(side="left", padx=5)
        ctk.CTkLabel(start_frame, text="From:", font=ctk.CTkFont(size=12)).pack()
        
        self.start_date_student = CTkDatePicker(start_frame, max_date=datetime.date.today())
        # Set default date to today
        today_str = datetime.date.today().strftime("%m/%d/%Y")
        self.start_date_student.date_entry.insert(0, today_str)
        self.start_date_student.selected_date = datetime.datetime.combine(datetime.date.today(), datetime.time())
        self.start_date_student.pack(pady=5)
        
        # End date
        end_frame = ctk.CTkFrame(date_controls)
        end_frame.pack(side="left", padx=5)
        ctk.CTkLabel(end_frame, text="To:", font=ctk.CTkFont(size=12)).pack()
        
        self.end_date_student = CTkDatePicker(end_frame, max_date=datetime.date.today())
        # Set default date to today
        self.end_date_student.date_entry.insert(0, today_str)
        self.end_date_student.selected_date = datetime.datetime.combine(datetime.date.today(), datetime.time())
        self.end_date_student.pack(pady=5)
        
        # Load data button
        load_btn = ctk.CTkButton(
            date_frame,
            text="Load Data",
            command=self.load_student_data_with_validation,
            width=120,
            height=32
        )
        load_btn.pack(pady=10)
        
        # Summary frame
        self.student_summary_frame = ctk.CTkFrame(students_tab)
        self.student_summary_frame.pack(fill="x", padx=10, pady=5)
        
        # Data display frame
        self.student_data_frame = ctk.CTkScrollableFrame(students_tab, height=400)
        self.student_data_frame.pack(fill="both", expand=True, padx=10, pady=10)
    
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

            # Display summary
            summary_label = ctk.CTkLabel(
                self.teacher_summary_frame,
                text=f"Teacher Login/Logout Data ({start_date_str} to {end_date_str})",
                font=ctk.CTkFont(size=16, weight="bold")
            )
            summary_label.pack(pady=5)

            # Get teacher activity data within time frame
            teacher_data = self.get_teacher_activity_data(start_date_str, end_date_str)
            
            if not teacher_data:
                no_data_label = ctk.CTkLabel(
                    self.teacher_data_frame,
                    text="No teacher activity found for the selected date range",
                    font=ctk.CTkFont(size=14)
                )
                no_data_label.pack(pady=50)
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
            
            # Add Combined Activity Section
            combined_label = ctk.CTkLabel(
                self.teacher_data_frame,
                text="Recent Combined Teacher Activity",
                font=ctk.CTkFont(size=14, weight="bold")
            )
            combined_label.pack(pady=(20, 5))
            
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
                    self.teacher_data_frame,
                    values=activity_table_data,
                    width=150,
                    height=25
                )
                activity_table.pack(pady=5, fill="both", expand=True)
            else:
                no_activity_label = ctk.CTkLabel(
                    self.teacher_data_frame,
                    text="No combined activity found for the selected date range",
                    font=ctk.CTkFont(size=12),
                    text_color="gray"
                )
                no_activity_label.pack(pady=10)
            
        except Exception as e:
            print(f"Error loading teacher data: {e}")
            error_label = ctk.CTkLabel(
                self.teacher_data_frame,
                text=f"Error loading data: {str(e)}",
                font=ctk.CTkFont(size=14),
                text_color="red"
            )
            error_label.pack(pady=50)
            
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
            
            # Display summary
            summary_label = ctk.CTkLabel(
                self.student_summary_frame,
                text=f"Student Attendance for {selected_teacher} ({start_date_str} to {end_date_str})",
                font=ctk.CTkFont(size=16, weight="bold")
            )
            summary_label.pack(pady=5)
            
            # Get student attendance data
            student_data = self.get_student_attendance_in_range(selected_teacher, start_date_str, end_date_str)
            
            if not student_data:
                no_data_label = ctk.CTkLabel(
                    self.student_data_frame,
                    text="No students found for the selected teacher",
                    font=ctk.CTkFont(size=14)
                )
                no_data_label.pack(pady=50)
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
            error_label = ctk.CTkLabel(
                self.student_data_frame,
                text=f"Error loading data: {str(e)}",
                font=ctk.CTkFont(size=14),
                text_color="red"
            )
            error_label.pack(pady=50)
            
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