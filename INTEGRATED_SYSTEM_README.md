# Integrated Teacher-Student Attendance System

A complete face recognition-based attendance management system with integrated teacher login and student attendance tracking, powered by SQLite database.

## 🌟 Features

### Teacher Authentication
- **Face Recognition Login**: Teachers authenticate using face recognition
- **Anti-Spoofing Protection**: Advanced spoofing detection prevents fake face attacks
- **Secure Registration**: Easy teacher registration with face encoding storage
- **Session Management**: Automatic login/logout tracking

### Student Attendance Management
- **Class-Specific Access**: Each teacher manages only their own class students
- **Real-time Face Recognition**: Students check-in/out using face recognition
- **Live Attendance Tracking**: Real-time attendance table updates
- **Attendance Statistics**: Daily summary with percentages and counts

### Administrative Features
- **Admin Panel**: Password-protected admin access (expandable)
- **SQLite Database**: Serverless, efficient data management
- **Activity Logging**: Complete audit trail of all system activities
- **Data Integrity**: Normalized database structure with foreign keys

## 🗃️ Database Structure

### Tables Overview
- **`teachers`**: Teacher profiles with face encodings
- **`logged_in_teachers`**: Current login sessions
- **`teacher_activity`**: Login/logout activity log
- **`students`**: Student profiles per teacher/class
- **`class_attendance`**: Student check-in/out records

### Database Schema

```sql
-- Teachers table
CREATE TABLE teachers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    face_encoding BLOB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Teacher sessions
CREATE TABLE logged_in_teachers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    teacher_name TEXT UNIQUE NOT NULL,
    login_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (teacher_name) REFERENCES teachers(name)
);

-- Activity logging
CREATE TABLE teacher_activity (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    teacher_name TEXT NOT NULL,
    activity_type TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (teacher_name) REFERENCES teachers(name)
);

-- Students per class
CREATE TABLE students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    teacher_name TEXT NOT NULL,
    face_encoding BLOB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(name, teacher_name),
    FOREIGN KEY (teacher_name) REFERENCES teachers(name)
);

-- Attendance records
CREATE TABLE class_attendance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_name TEXT NOT NULL,
    teacher_name TEXT NOT NULL,
    attendance_type TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_name, teacher_name) REFERENCES students(name, teacher_name)
);
```

## 🚀 How to Use

### 1. Starting the System
```bash
python main_gui_ctk.py
```

### 2. Teacher Registration (First Time)
1. Click **"Register New Teacher"**
2. Enter teacher name
3. Position face in camera
4. Click **"Capture Face"**
5. Face encoding is stored in database

### 3. Teacher Login Process
1. **Position face** in front of camera
2. Click **"Teacher Login"**
3. System performs:
   - Anti-spoofing detection
   - Face recognition against teacher database
   - Session login in database
4. **Successful login** → Switch to student attendance mode

### 4. Student Management
Once teacher is logged in:

#### Register Students
1. Click **"Register New Student"**
2. Enter student name
3. Capture student's face
4. Student added to teacher's class

#### Student Check-In/Out
1. Student positions face in camera
2. Click **"Student Check-In"** or **"Student Check-Out"**
3. System recognizes student and marks attendance
4. Table updates automatically

### 5. Teacher Logout
1. Click **"Teacher Logout"**
2. Session ends and system returns to teacher login mode

### 6. Admin Access
1. Click **"Admin"** button (top-right corner)
2. Enter admin password (default: `admin123`)
3. Access admin panel (expandable for future features)

## 🎛️ Interface Layout

### Teacher Login Mode
```
┌─────────────────────────────────────────┐
│ Teacher Login - Face Recognition System │ [Admin]
├─────────────────────────────────────────┤
│              Status Messages            │
├──────────────────┬──────────────────────┤
│   Camera Feed    │   Login Controls     │
│                  │                      │
│  [Live Video]    │  [Teacher Login]     │
│                  │  [Register Teacher]  │
│                  │                      │
│                  │  Registered Teachers │
│                  │  [List Display]      │
└──────────────────┴──────────────────────┘
```

### Student Attendance Mode
```
┌─────────────────────────────────────────┐
│ Student Attendance - [Teacher]'s Class │ [Admin]
├─────────────────────────────────────────┤
│              Status Messages            │
├──────────┬─────────────┬────────────────┤
│  Camera  │   Student   │    Summary     │
│          │  Controls   │                │
│ [Video]  │ [Check-In]  │  Class Stats   │
│          │ [Check-Out] │                │
│          │ [Register]  │ [Logout]       │
├─────────────────────────────────────────┤
│          Today's Attendance Table       │
│ [Student Name] [Time] [Action]          │
└─────────────────────────────────────────┘
```

## 📊 Data Flow

### Teacher Login Flow
1. **Face Capture** → Camera feed
2. **Anti-Spoofing** → Real face validation
3. **Face Recognition** → Compare with teacher database
4. **Database Login** → Record session in `logged_in_teachers`
5. **Activity Log** → Record in `teacher_activity`
6. **UI Switch** → Change to student attendance mode

### Student Attendance Flow
1. **Face Capture** → Camera feed
2. **Anti-Spoofing** → Real face validation
3. **Face Recognition** → Compare with class students
4. **Attendance Marking** → Record in `class_attendance`
5. **UI Update** → Refresh table and summary
6. **Activity Log** → Timestamp and action recorded

## 🔧 Technical Architecture

### Core Components
- **`IntegratedAttendanceSystem`**: Main application class
- **`AttendanceDatabase`**: SQLite database manager
- **Face Recognition**: Using `face_recognition` library
- **Anti-Spoofing**: Using custom `test` module
- **UI Framework**: CustomTkinter for modern interface

### File Structure
```
├── main_gui_ctk.py          # Main integrated application
├── database.py              # SQLite database manager
├── util.py                  # UI utility functions
├── test.py                  # Anti-spoofing detection
├── attendance_system.db     # SQLite database (auto-created)
├── db/                      # Face encodings directory
└── requirements.txt         # Python dependencies
```

### Dependencies
- `customtkinter` - Modern UI framework
- `opencv-python` - Camera and image processing
- `face-recognition` - Face detection and recognition
- `Pillow` - Image handling
- `sqlite3` - Database (built-in)

## 🎯 Key Advantages

### Over CSV-Based System
1. **Data Integrity**: Foreign keys and constraints
2. **Concurrent Access**: SQLite handles multiple operations
3. **Query Efficiency**: SQL queries for complex data retrieval
4. **Scalability**: Better performance with large datasets
5. **Backup & Recovery**: Single database file

### Security Features
1. **Anti-Spoofing**: Prevents photo/video attacks
2. **Face Encoding**: Biometric data stored as mathematical encodings
3. **Session Management**: Automatic logout tracking
4. **Admin Protection**: Password-protected administrative access
5. **Activity Audit**: Complete trail of all system activities

## 🛠️ Configuration

### Admin Password
Default: `admin123`
Change in `main_gui_ctk.py`:
```python
self.admin_password = "your_new_password"
```

### Database Location
Default: `attendance_system.db`
Change in `database.py`:
```python
def __init__(self, db_path: str = "your_database.db"):
```

### Camera Settings
- Default camera index: 0
- Display resolution: 480x360
- Update interval: 20ms

## 🔮 Future Enhancements

### Admin Panel Features
- [ ] Teacher management (add/edit/delete)
- [ ] Student management across all classes
- [ ] Attendance reports and analytics
- [ ] Data export (CSV, Excel, PDF)
- [ ] System settings and configuration
- [ ] User role management
- [ ] Backup and restore functionality

### System Improvements
- [ ] Multi-camera support
- [ ] Mobile app integration
- [ ] Cloud database synchronization
- [ ] Email notifications
- [ ] Attendance threshold alerts
- [ ] Photo capture for records
- [ ] Biometric device integration

## 📈 Usage Statistics

The system automatically tracks:
- Teacher login/logout times
- Student attendance patterns
- Daily/weekly/monthly summaries
- System usage analytics
- Face recognition accuracy metrics

## 🆘 Troubleshooting

### Common Issues

**Camera Not Working**
- Ensure camera is connected and not used by another app
- Check camera permissions
- Try different camera index (0, 1, 2...)

**Face Recognition Fails**
- Ensure good lighting conditions
- Position face clearly in frame
- Re-register if consistently failing
- Check camera focus

**Database Errors**
- Verify database file permissions
- Check disk space
- Restart application if corrupted

**UI Issues**
- Update CustomTkinter: `pip install --upgrade customtkinter`
- Check Python version compatibility
- Verify all dependencies installed

## 📝 Support

For technical support:
1. Check error messages in console
2. Verify all dependencies installed
3. Test camera functionality separately
4. Check database file integrity