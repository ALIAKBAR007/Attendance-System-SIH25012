
import os
import datetime
import pickle
import customtkinter as ctk
from tkinter import ttk
from CTkTable import CTkTable
import cv2
from PIL import Image, ImageTk
import face_recognition
import csv

import util
from test import test


# Set the theme and color theme
ctk.set_appearance_mode("dark")  # Modes: "System" (standard), "Dark", "Light"
ctk.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"


class AttendanceApp:
    def load_log_data(self):
        # Reset table data to just headers
        self.table_data = [
            ["Name", "Date", "Time", "Action"]
        ]
        # Read log file if it exists
        if os.path.exists(self.log_path):
            try:
                with open(self.log_path, 'r', newline='') as f:
                    reader = csv.reader(f)
                    for row in reader:
                        if len(row) >= 3:
                            name = row[0]
                            datetime_str = row[1]
                            action = row[2]
                            # Parse datetime
                            try:
                                dt = datetime.datetime.fromisoformat(datetime_str.replace('T', ' '))
                                date_str = dt.strftime('%Y-%m-%d')
                                time_str = dt.strftime('%H:%M:%S')
                            except Exception:
                                date_str = datetime_str.split()[0] if ' ' in datetime_str else datetime_str
                                time_str = datetime_str.split()[1] if ' ' in datetime_str else ''
                            self.table_data.append([name, date_str, time_str, action])
            except Exception as e:
                print(f"Error reading log file: {e}")
        # Update the table with new data
        self.table.destroy()
        self.table = CTkTable(
            master=self.table_scrollable_frame,
            row=len(self.table_data),
            column=4,
            values=self.table_data,
            colors=["#202027", "#41464C"],  # Dark theme colors
            header_color="#2F323A",  # Header color
            hover_color="#494A53"  # Hover color
        )
        self.table.pack(fill="both", expand=True, padx=10, pady=10)
    def refresh_log_table(self):
        """Switch to table page and refresh the data"""
        self.tabview.set("Log Table")
        self.load_log_data()
    def __init__(self):
        self.main_window = ctk.CTk()
        self.main_window.geometry("1400x650+200+50")
        self.main_window.title("Attendance System")
        
        # Database and log setup - MUST be defined first
        self.db_dir = './db'
        if not os.path.exists(self.db_dir):
            os.mkdir(self.db_dir)

        self.log_path = "./log.csv"
        self.logged_in_path = "./logged_in.csv"

        # Anti-spoofing model path
        self.model_dir = os.path.join("Silent-Face-Anti-Spoofing", "resources", "anti_spoof_models")
        
        # Create tabview for tabs
        self.tabview = ctk.CTkTabview(self.main_window, width=1380, height=620)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create tabs
        self.tabview.add("Main Page")
        self.tabview.add("Log Table")
        
        # Initialize pages
        self.setup_main_page()
        self.setup_table_page()
    
    def setup_main_page(self):
        """Setup the main page with camera and buttons"""
        main_tab = self.tabview.tab("Main Page")
        
        # Create main frame
        main_frame = ctk.CTkFrame(main_tab)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Camera frame
        camera_frame = ctk.CTkFrame(main_frame)
        camera_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        # Camera label
        self.webcam_label = ctk.CTkLabel(camera_frame, text="Camera Loading...", width=700, height=500)
        self.webcam_label.pack(padx=10, pady=10)
        
        # Control panel frame
        control_frame = ctk.CTkFrame(main_frame, width=300)
        control_frame.pack(side="right", fill="y", padx=(10, 0))
        control_frame.pack_propagate(False)
        
        # Title for control panel
        title_label = ctk.CTkLabel(control_frame, text="Control Panel", 
                                  font=ctk.CTkFont(size=20, weight="bold"))
        title_label.pack(pady=(20, 30))
        
        # Login button
        self.login_button = ctk.CTkButton(
            control_frame, 
            text="Login", 
            command=self.login,
            width=200,
            height=50,
            font=ctk.CTkFont(size=16),
            fg_color="green",
            hover_color="darkgreen"
        )
        self.login_button.pack(pady=15)
        
        # Logout button
        self.logout_button = ctk.CTkButton(
            control_frame, 
            text="Logout", 
            command=self.logout,
            width=200,
            height=50,
            font=ctk.CTkFont(size=16),
            fg_color="red",
            hover_color="darkred"
        )
        self.logout_button.pack(pady=15)
        
        # Register new user button
        self.register_button = ctk.CTkButton(
            control_frame, 
            text="Register New User", 
            command=self.register_new_user,
            width=200,
            height=50,
            font=ctk.CTkFont(size=16),
            fg_color="gray",
            hover_color="darkgray"
        )
        self.register_button.pack(pady=15)
        
        # Refresh log button
        self.refresh_button = ctk.CTkButton(
            control_frame, 
            text="Refresh Log Table", 
            command=self.refresh_log_table,
            width=200,
            height=50,
            font=ctk.CTkFont(size=16),
            fg_color="blue",
            hover_color="darkblue"
        )
        self.refresh_button.pack(pady=15)
        
        # Status label
        self.status_label = ctk.CTkLabel(control_frame, text="Ready", 
                                        font=ctk.CTkFont(size=14))
        self.status_label.pack(pady=(30, 10))
        
        # Initialize camera
        self.add_webcam(self.webcam_label)
    
    def setup_table_page(self):
        """Setup the table page to display log.txt"""
        table_tab = self.tabview.tab("Log Table")
        
        # Create main frame for table tab
        table_main_frame = ctk.CTkFrame(table_tab)
        table_main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Title
        title_label = ctk.CTkLabel(table_main_frame, text="Attendance Log", 
                                  font=ctk.CTkFont(size=24, weight="bold"))
        title_label.pack(pady=(10, 20))
        
        # Create scrollable frame for the table
        self.table_scrollable_frame = ctk.CTkScrollableFrame(
            table_main_frame,
            width=800,
            height=400
        )
        self.table_scrollable_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        # Initialize table data with headers
        self.table_data = [
            ["Name", "Date", "Time", "Action"]
        ]
        
        # Create CTkTable inside the scrollable frame
        self.table = CTkTable(
            master=self.table_scrollable_frame,
            row=1,
            column=4,
            values=self.table_data,
            colors=["#202027", "#41464C"],  # Dark theme colors
            header_color="#2F323A",  # Header color
            hover_color="#494A53"  # Hover color
        )
        self.table.pack(fill="both", expand=True, padx=10, pady=10)
        refresh_table_button = ctk.CTkButton(
            table_main_frame, 
            text="Refresh Table", 
            command=self.load_log_data,
            width=200,
            height=40,
            font=ctk.CTkFont(size=16),
            fg_color="lightblue",
            text_color="black",
            hover_color="skyblue"
        )
        refresh_table_button.pack(pady=10)
        # Load initial data
        self.load_log_data()
    
    def add_webcam(self, label):
        """Initialize and start webcam"""
        if 'cap' not in self.__dict__:
            self.cap = cv2.VideoCapture(0)
        
        self._label = label
        self.process_webcam()
    
    def process_webcam(self):
        """Process webcam frames"""
        ret, frame = self.cap.read()
        if not ret:
            self._label.after(20, self.process_webcam)
            return
        
        self.most_recent_capture_arr = frame
        img_ = cv2.cvtColor(self.most_recent_capture_arr, cv2.COLOR_BGR2RGB)
        self.most_recent_capture_pil = Image.fromarray(img_)
        
        # Resize image to fit the label
        img_resized = self.most_recent_capture_pil.resize((680, 480), Image.Resampling.LANCZOS)
        imgtk = ImageTk.PhotoImage(image=img_resized)
        
        
        self._label.after(20, self.process_webcam)
    
    def update_status(self, message):
        """Update status label"""
        self.status_label.configure(text=message)
    
    def get_logged_in_users(self):
        """Get list of currently logged in users"""
        if os.path.exists(self.logged_in_path):
            try:
                with open(self.logged_in_path, 'r') as f:
                    users = [line.strip() for line in f.readlines() if line.strip()]
                return users
            except Exception as e:
                print(f"Error reading logged_in file: {e}")
                return []
        return []
    
    def add_logged_in_user(self, username):
        """Add user to logged in list"""
        try:
            with open(self.logged_in_path, 'a') as f:
                f.write(f'{username}\n')
        except Exception as e:
            print(f"Error adding user to logged_in file: {e}")
    
    def remove_logged_in_user(self, username):
        """Remove user from logged in list"""
        try:
            logged_in_users = self.get_logged_in_users()
            if username in logged_in_users:
                logged_in_users.remove(username)
                with open(self.logged_in_path, 'w', newline='') as f:
                    writer = csv.writer(f)
                    for user in logged_in_users:
                        writer.writerow([user])
        except Exception as e:
            print(f"Error removing user from logged_in file: {e}")
    
    def is_user_logged_in(self, username):
        """Check if user is currently logged in"""
        return username in self.get_logged_in_users()
    
    def login(self):
        """Handle login functionality"""
        self.update_status("Processing login...")
        
        label = test(
            image=self.most_recent_capture_arr,
            model_dir=self.model_dir,
            device_id=0
        )
        
        if label == 1:
            name = util.recognize(self.most_recent_capture_arr, self.db_dir)
            
            if name in ['unknown_person', 'no_persons_found']:
                util.msg_box('Ups...', 'Unknown user. Please register new user or try again.')
                self.update_status("Login failed - Unknown user")
            else:
                # Check if user is already logged in
                if self.is_user_logged_in(name):
                    util.msg_box('Already Logged In!', f'{name} is already logged in. Please log out first.')
                    self.update_status(f"Login failed - {name} already logged in")
                else:
                    # User is not logged in, proceed with login
                    util.msg_box('Welcome back!', f'Welcome, {name}.')
                    with open(self.log_path, 'a') as f:
                        f.write(f'{name},{datetime.datetime.now()},in\n')
                    self.add_logged_in_user(name)
                    self.update_status(f"Logged in: {name}")
        else:
            util.msg_box('Hey, you are a spoofer!', 'You are fake!')
            self.update_status("Login failed - Spoofing detected")
    
    def logout(self):
        """Handle logout functionality"""
        self.update_status("Processing logout...")
        
        label = test(
            image=self.most_recent_capture_arr,
            model_dir=self.model_dir,
            device_id=0
        )
        
        if label == 1:
            name = util.recognize(self.most_recent_capture_arr, self.db_dir)
            
            if name in ['unknown_person', 'no_persons_found']:
                util.msg_box('Ups...', 'Unknown user. Please register new user or try again.')
                self.update_status("Logout failed - Unknown user")
            else:
                # Check if user is actually logged in
                if not self.is_user_logged_in(name):
                    util.msg_box('Already Logged Out!', f'{name} is already logged out. Please log in first.')
                    self.update_status(f"Logout failed - {name} already logged out")
                else:
                    # User is logged in, proceed with logout
                    util.msg_box('Hasta la vista!', f'Goodbye, {name}.')
                    with open(self.log_path, 'a') as f:
                        f.write(f'{name},{datetime.datetime.now()},out\n')
                    self.remove_logged_in_user(name)
                    self.update_status(f"Logged out: {name}")
        else:
            util.msg_box('Hey, you are a spoofer!', 'You are fake!')
            self.update_status("Logout failed - Spoofing detected")
    
    def register_new_user(self):
        """Open registration window"""
        self.register_window = ctk.CTkToplevel(self.main_window)
        self.register_window.geometry("1200x600+370+120")
        self.register_window.title("Register New User")
        
        # Make window modal
        self.register_window.transient(self.main_window)
        self.register_window.grab_set()
        
        # Main frame
        main_frame = ctk.CTkFrame(self.register_window)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Camera frame
        camera_frame = ctk.CTkFrame(main_frame)
        camera_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        # Capture label
        self.capture_label = ctk.CTkLabel(camera_frame, text="Captured Image", width=700, height=500)
        self.capture_label.pack(padx=10, pady=10)
        
        # Control frame
        control_frame = ctk.CTkFrame(main_frame, width=300)
        control_frame.pack(side="right", fill="y")
        control_frame.pack_propagate(False)
        
        # Title
        title_label = ctk.CTkLabel(control_frame, text="User Registration", 
                                  font=ctk.CTkFont(size=18, weight="bold"))
        title_label.pack(pady=(20, 30))
        
        # Username label
        username_label = ctk.CTkLabel(control_frame, text="Enter Username:", 
                                     font=ctk.CTkFont(size=14))
        username_label.pack(pady=(0, 10))
        
        # Username entry
        self.username_entry = ctk.CTkEntry(control_frame, width=250, height=40,
                                          font=ctk.CTkFont(size=14))
        self.username_entry.pack(pady=(0, 30))
        
        # Accept button
        accept_button = ctk.CTkButton(
            control_frame, 
            text="Accept", 
            command=self.accept_register_new_user,
            width=200,
            height=50,
            font=ctk.CTkFont(size=16),
            fg_color="green",
            hover_color="darkgreen"
        )
        accept_button.pack(pady=15)
        
        # Try again button
        try_again_button = ctk.CTkButton(
            control_frame, 
            text="Cancel", 
            command=self.try_again_register_new_user,
            width=200,
            height=50,
            font=ctk.CTkFont(size=16),
            fg_color="red",
            hover_color="darkred"
        )
        try_again_button.pack(pady=15)
        
        # Add current image to capture label
        self.add_img_to_label(self.capture_label)
    
    def try_again_register_new_user(self):
        """Close registration window"""
        self.register_window.destroy()
    
    def add_img_to_label(self, label):
        """Add current camera frame to registration window"""
        if hasattr(self, 'most_recent_capture_pil'):
            img_resized = self.most_recent_capture_pil.resize((680, 480), Image.Resampling.LANCZOS)
            imgtk = ImageTk.PhotoImage(image=img_resized)
            label.configure(image=imgtk, text="")
            label.image = imgtk  # Keep a reference
            self.register_new_user_capture = self.most_recent_capture_arr.copy()
    
    def accept_register_new_user(self):
        """Accept new user registration"""
        name = self.username_entry.get().strip()
        
        if not name:
            util.msg_box('Error', 'Please enter a username!')
            return
        
        try:
            embeddings = face_recognition.face_encodings(self.register_new_user_capture)[0]
            
            file = open(os.path.join(self.db_dir, f'{name}.pickle'), 'wb')
            pickle.dump(embeddings, file)
            file.close()
            
            util.msg_box('Success!', 'User was registered successfully!')
            self.update_status(f"User registered: {name}")
            self.register_window.destroy()
        except IndexError:
            util.msg_box('Error', 'No face detected! Please try again.')
        except Exception as e:
            util.msg_box('Error', f'Registration failed: {str(e)}')
    
    def start(self):
        """Start the application"""
        self.main_window.mainloop()
    
    def __del__(self):
        """Cleanup when app closes"""
        if hasattr(self, 'cap'):
            self.cap.release()


if __name__ == "__main__":
    app = AttendanceApp()
    app.start()
