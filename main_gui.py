import os
import datetime
import pickle
import tkinter as tk
from tkinter import ttk
import cv2
from PIL import Image, ImageTk
import face_recognition

import util
from test import test


class AttendanceApp:
    def __init__(self):
        self.main_window = tk.Tk()
        self.main_window.geometry("1400x600+200+50")
        self.main_window.title("Attendance System")
        
        # Database and log setup - MUST be defined first
        self.db_dir = './db'
        if not os.path.exists(self.db_dir):
            os.mkdir(self.db_dir)

        self.log_path = "./log.txt"

        # Anti-spoofing model path
        self.model_dir = os.path.join("Silent-Face-Anti-Spoofing", "resources", "anti_spoof_models")
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.main_window)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create frames for each page
        self.main_frame = ttk.Frame(self.notebook)
        self.table_frame = ttk.Frame(self.notebook)
        
        # Add tabs to notebook
        self.notebook.add(self.main_frame, text="Main Page")
        self.notebook.add(self.table_frame, text="Log Table")
        
        # Initialize main page
        self.setup_main_page()
        
        # Initialize table page
        self.setup_table_page()
    
    def setup_main_page(self):
        """Setup the main page with camera and buttons"""
        # Camera display
        self.webcam_label = util.get_img_label(self.main_frame)
        self.webcam_label.place(x=10, y=10, width=700, height=500)
        
        # Control buttons frame
        button_frame = tk.Frame(self.main_frame)
        button_frame.place(x=730, y=50, width=200, height=400)
        
        # Login button
        self.login_button = util.get_button(button_frame, 'Login', 'green', self.login)
        self.login_button.pack(pady=20, fill='x')
        
        # Logout button
        self.logout_button = util.get_button(button_frame, 'Logout', 'red', self.logout)
        self.logout_button.pack(pady=20, fill='x')
        
        # Register new user button
        self.register_button = util.get_button(
            button_frame, 'Register New User', 'gray', self.register_new_user, fg='black'
        )
        self.register_button.pack(pady=20, fill='x')
        
        # Refresh log button
        self.refresh_button = util.get_button(
            button_frame, 'Refresh Log Table', 'blue', self.refresh_log_table, fg='white'
        )
        self.refresh_button.pack(pady=20, fill='x')
        
        # Initialize camera
        self.add_webcam(self.webcam_label)
    
    def setup_table_page(self):
        """Setup the table page to display log.txt"""
        # Title
        title_label = tk.Label(self.table_frame, text="Attendance Log", 
                              font=('Arial', 16, 'bold'))
        title_label.pack(pady=10)
        
        # Create treeview for table
        columns = ('Name', 'Date', 'Time', 'Action')
        self.tree = ttk.Treeview(self.table_frame, columns=columns, show='headings')
        
        # Define column headings
        self.tree.heading('Name', text='Name')
        self.tree.heading('Date', text='Date')
        self.tree.heading('Time', text='Time')
        self.tree.heading('Action', text='Action (In/Out)')
        
        # Configure column widths
        self.tree.column('Name', width=200)
        self.tree.column('Date', width=150)
        self.tree.column('Time', width=150)
        self.tree.column('Action', width=100)
        
        # Add scrollbars
        v_scrollbar = ttk.Scrollbar(self.table_frame, orient='vertical', command=self.tree.yview)
        h_scrollbar = ttk.Scrollbar(self.table_frame, orient='horizontal', command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Pack the treeview and scrollbars
        self.tree.pack(side='left', fill='both', expand=True, padx=(10, 0), pady=10)
        v_scrollbar.pack(side='right', fill='y', pady=10)
        h_scrollbar.pack(side='bottom', fill='x', padx=10)
        
        # Refresh button for table page
        refresh_frame = tk.Frame(self.table_frame)
        refresh_frame.pack(pady=10)
        
        refresh_table_button = tk.Button(refresh_frame, text="Refresh Table", 
                                       command=self.load_log_data, bg='lightblue')
        refresh_table_button.pack()
        
        # Load initial data
        self.load_log_data()
    
    def load_log_data(self):
        """Load data from log.txt into the table"""
        # Clear existing data
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Read log file if it exists
        if os.path.exists(self.log_path):
            try:
                with open(self.log_path, 'r') as f:
                    lines = f.readlines()
                
                for line in lines:
                    line = line.strip()
                    if line:  # Skip empty lines
                        parts = line.split(',')
                        if len(parts) >= 3:
                            name = parts[0]
                            datetime_str = parts[1]
                            action = parts[2]
                            
                            # Parse datetime
                            try:
                                dt = datetime.datetime.fromisoformat(datetime_str.replace('T', ' '))
                                date_str = dt.strftime('%Y-%m-%d')
                                time_str = dt.strftime('%H:%M:%S')
                            except:
                                # Fallback if datetime parsing fails
                                date_str = datetime_str.split()[0] if ' ' in datetime_str else datetime_str
                                time_str = datetime_str.split()[1] if ' ' in datetime_str else ''
                            
                            self.tree.insert('', 'end', values=(name, date_str, time_str, action))
            except Exception as e:
                print(f"Error reading log file: {e}")
    
    def refresh_log_table(self):
        """Switch to table page and refresh the data"""
        self.notebook.select(1)  # Select table tab
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
        imgtk = ImageTk.PhotoImage(image=self.most_recent_capture_pil)
        self._label.imgtk = imgtk
        self._label.configure(image=imgtk)
        
        self._label.after(20, self.process_webcam)
    
    def login(self):
        """Handle login functionality"""
        label = test(
            image=self.most_recent_capture_arr,
            model_dir=self.model_dir,
            device_id=0
        )
        
        if label == 1:
            name = util.recognize(self.most_recent_capture_arr, self.db_dir)
            
            if name in ['unknown_person', 'no_persons_found']:
                util.msg_box('Ups...', 'Unknown user. Please register new user or try again.')
            else:
                util.msg_box('Welcome back!', f'Welcome, {name}.')
                with open(self.log_path, 'a') as f:
                    f.write(f'{name},{datetime.datetime.now()},in\n')
        else:
            util.msg_box('Hey, you are a spoofer!', 'You are fake!')
    
    def logout(self):
        """Handle logout functionality"""
        label = test(
            image=self.most_recent_capture_arr,
            model_dir=self.model_dir,
            device_id=0
        )
        
        if label == 1:
            name = util.recognize(self.most_recent_capture_arr, self.db_dir)
            
            if name in ['unknown_person', 'no_persons_found']:
                util.msg_box('Ups...', 'Unknown user. Please register new user or try again.')
            else:
                util.msg_box('Hasta la vista!', f'Goodbye, {name}.')
                with open(self.log_path, 'a') as f:
                    f.write(f'{name},{datetime.datetime.now()},out\n')
        else:
            util.msg_box('Hey, you are a spoofer!', 'You are fake!')
    
    def register_new_user(self):
        """Open registration window"""
        self.register_new_user_window = tk.Toplevel(self.main_window)
        self.register_new_user_window.geometry("1200x520+370+120")
        self.register_new_user_window.title("Register New User")
        
        # Accept button
        self.accept_button_register_new_user_window = util.get_button(
            self.register_new_user_window, 'Accept', 'green', self.accept_register_new_user
        )
        self.accept_button_register_new_user_window.place(x=750, y=300)
        
        # Try again button
        self.try_again_button_register_new_user_window = util.get_button(
            self.register_new_user_window, 'Try again', 'red', self.try_again_register_new_user
        )
        self.try_again_button_register_new_user_window.place(x=750, y=400)
        
        # Capture label
        self.capture_label = util.get_img_label(self.register_new_user_window)
        self.capture_label.place(x=10, y=0, width=700, height=500)
        
        self.add_img_to_label(self.capture_label)
        
        # Username entry
        self.entry_text_register_new_user = util.get_entry_text(self.register_new_user_window)
        self.entry_text_register_new_user.place(x=750, y=150)
        
        # Text label
        self.text_label_register_new_user = util.get_text_label(
            self.register_new_user_window, 'Please,\ninput username:'
        )
        self.text_label_register_new_user.place(x=750, y=70)
    
    def try_again_register_new_user(self):
        """Close registration window"""
        self.register_new_user_window.destroy()
    
    def add_img_to_label(self, label):
        """Add current camera frame to registration window"""
        imgtk = ImageTk.PhotoImage(image=self.most_recent_capture_pil)
        label.imgtk = imgtk
        label.configure(image=imgtk)
        self.register_new_user_capture = self.most_recent_capture_arr.copy()
    
    def accept_register_new_user(self):
        """Accept new user registration"""
        name = self.entry_text_register_new_user.get(1.0, "end-1c")
        
        if not name.strip():
            util.msg_box('Error', 'Please enter a username!')
            return
        
        try:
            embeddings = face_recognition.face_encodings(self.register_new_user_capture)[0]
            
            file = open(os.path.join(self.db_dir, f'{name}.pickle'), 'wb')
            pickle.dump(embeddings, file)
            file.close()
            
            util.msg_box('Success!', 'User was registered successfully!')
            self.register_new_user_window.destroy()
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
