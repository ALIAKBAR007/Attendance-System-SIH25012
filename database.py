import sqlite3
import datetime
import os
import pickle
from typing import List, Dict, Tuple, Optional

class AttendanceDatabase:
    """Handles all SQLite database operations for the attendance system"""
    
    def __init__(self, db_path: str = "attendance_system.db"):
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_path)
    
    def init_database(self):
        """Initialize all required tables"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Teachers table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS teachers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    face_encoding BLOB NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Logged in teachers table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS logged_in_teachers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    teacher_name TEXT UNIQUE NOT NULL,
                    login_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (teacher_name) REFERENCES teachers(name)
                )
            """)
            
            # Teacher activity log
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS teacher_activity (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    teacher_name TEXT NOT NULL,
                    activity_type TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (teacher_name) REFERENCES teachers(name)
                )
            """)
            
            # Students table (per teacher/class)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS students (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    teacher_name TEXT NOT NULL,
                    face_encoding BLOB NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(name, teacher_name),
                    FOREIGN KEY (teacher_name) REFERENCES teachers(name)
                )
            """)
            
            # Class attendance table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS class_attendance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_name TEXT NOT NULL,
                    teacher_name TEXT NOT NULL,
                    attendance_type TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (student_name, teacher_name) REFERENCES students(name, teacher_name)
                )
            """)
            
            conn.commit()
    
    # Teacher management methods
    def register_teacher(self, name: str, face_encoding) -> bool:
        """Register a new teacher with face encoding"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Convert face encoding to blob
                face_blob = pickle.dumps(face_encoding)
                
                cursor.execute("""
                    INSERT INTO teachers (name, face_encoding)
                    VALUES (?, ?)
                """, (name, face_blob))
                
                conn.commit()
                return True
                
        except sqlite3.IntegrityError:
            print(f"Teacher {name} already exists")
            return False
        except Exception as e:
            print(f"Error registering teacher: {e}")
            return False
    
    def get_all_teachers(self) -> List[Dict]:
        """Get all registered teachers"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT name, created_at FROM teachers ORDER BY name
                """)
                
                teachers = []
                for row in cursor.fetchall():
                    teachers.append({
                        'name': row[0],
                        'created_at': row[1]
                    })
                
                return teachers
                
        except Exception as e:
            print(f"Error getting teachers: {e}")
            return []
    
    def get_teacher_face_encodings(self) -> Dict[str, object]:
        """Get all teacher face encodings for recognition"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name, face_encoding FROM teachers")
                
                encodings = {}
                for row in cursor.fetchall():
                    name = row[0]
                    face_blob = row[1]
                    face_encoding = pickle.loads(face_blob)
                    encodings[name] = face_encoding
                
                return encodings
                
        except Exception as e:
            print(f"Error getting teacher face encodings: {e}")
            return {}
    
    def teacher_login(self, teacher_name: str) -> bool:
        """Log in a teacher"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Check if teacher exists
                cursor.execute("SELECT name FROM teachers WHERE name = ?", (teacher_name,))
                if not cursor.fetchone():
                    return False
                
                # Add to logged in teachers (replace if exists)
                cursor.execute("""
                    INSERT OR REPLACE INTO logged_in_teachers (teacher_name, login_time)
                    VALUES (?, ?)
                """, (teacher_name, datetime.datetime.now()))
                
                # Log activity
                cursor.execute("""
                    INSERT INTO teacher_activity (teacher_name, activity_type)
                    VALUES (?, ?)
                """, (teacher_name, "LOGIN"))
                
                conn.commit()
                return True
                
        except Exception as e:
            print(f"Error during teacher login: {e}")
            return False
    
    def teacher_logout(self, teacher_name: str) -> bool:
        """Log out a teacher"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Remove from logged in teachers
                cursor.execute("""
                    DELETE FROM logged_in_teachers WHERE teacher_name = ?
                """, (teacher_name,))
                
                # Log activity
                cursor.execute("""
                    INSERT INTO teacher_activity (teacher_name, activity_type)
                    VALUES (?, ?)
                """, (teacher_name, "LOGOUT"))
                
                conn.commit()
                return True
                
        except Exception as e:
            print(f"Error during teacher logout: {e}")
            return False
    
    def get_logged_in_teacher(self) -> Optional[str]:
        """Get currently logged in teacher (assuming single session)"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT teacher_name FROM logged_in_teachers 
                    ORDER BY login_time DESC LIMIT 1
                """)
                
                result = cursor.fetchone()
                return result[0] if result else None
                
        except Exception as e:
            print(f"Error getting logged in teacher: {e}")
            return None
    
    def is_teacher_logged_in(self, teacher_name: str) -> bool:
        """Check if a specific teacher is logged in"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT 1 FROM logged_in_teachers WHERE teacher_name = ?
                """, (teacher_name,))
                
                return cursor.fetchone() is not None
                
        except Exception as e:
            print(f"Error checking teacher login status: {e}")
            return False
    
    # Student management methods
    def register_student(self, name: str, teacher_name: str, face_encoding) -> bool:
        """Register a new student for a specific teacher's class"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Convert face encoding to blob
                face_blob = pickle.dumps(face_encoding)
                
                cursor.execute("""
                    INSERT INTO students (name, teacher_name, face_encoding)
                    VALUES (?, ?, ?)
                """, (name, teacher_name, face_blob))
                
                conn.commit()
                return True
                
        except sqlite3.IntegrityError:
            print(f"Student {name} already exists in {teacher_name}'s class")
            return False
        except Exception as e:
            print(f"Error registering student: {e}")
            return False
    
    def get_students_for_teacher(self, teacher_name: str) -> List[Dict]:
        """Get all students for a specific teacher"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT name, created_at FROM students 
                    WHERE teacher_name = ? ORDER BY name
                """, (teacher_name,))
                
                students = []
                for row in cursor.fetchall():
                    students.append({
                        'name': row[0],
                        'created_at': row[1]
                    })
                
                return students
                
        except Exception as e:
            print(f"Error getting students for teacher: {e}")
            return []
    
    def get_student_face_encodings(self, teacher_name: str) -> Dict[str, object]:
        """Get all student face encodings for a specific teacher's class"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT name, face_encoding FROM students WHERE teacher_name = ?
                """, (teacher_name,))
                
                encodings = {}
                for row in cursor.fetchall():
                    name = row[0]
                    face_blob = row[1]
                    face_encoding = pickle.loads(face_blob)
                    encodings[name] = face_encoding
                
                return encodings
                
        except Exception as e:
            print(f"Error getting student face encodings: {e}")
            return {}
    
    # Attendance management methods
    def mark_attendance(self, student_name: str, teacher_name: str, attendance_type: str) -> bool:
        """Mark attendance for a student"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO class_attendance (student_name, teacher_name, attendance_type)
                    VALUES (?, ?, ?)
                """, (student_name, teacher_name, attendance_type))
                
                conn.commit()
                return True
                
        except Exception as e:
            print(f"Error marking attendance: {e}")
            return False
    
    def get_attendance_for_teacher(self, teacher_name: str, date_filter: Optional[str] = None) -> List[Dict]:
        """Get attendance records for a teacher's class"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                if date_filter:
                    cursor.execute("""
                        SELECT student_name, attendance_type, timestamp
                        FROM class_attendance
                        WHERE teacher_name = ? AND date(timestamp) = ?
                        ORDER BY timestamp DESC
                    """, (teacher_name, date_filter))
                else:
                    cursor.execute("""
                        SELECT student_name, attendance_type, timestamp
                        FROM class_attendance
                        WHERE teacher_name = ?
                        ORDER BY timestamp DESC
                    """, (teacher_name,))
                
                attendance = []
                for row in cursor.fetchall():
                    attendance.append({
                        'student_name': row[0],
                        'attendance_type': row[1],
                        'timestamp': row[2]
                    })
                
                return attendance
                
        except Exception as e:
            print(f"Error getting attendance: {e}")
            return []
    
    def get_todays_attendance_summary(self, teacher_name: str) -> Dict:
        """Get today's attendance summary for a teacher's class"""
        try:
            today = datetime.date.today().isoformat()
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get total students in class
                cursor.execute("""
                    SELECT COUNT(*) FROM students WHERE teacher_name = ?
                """, (teacher_name,))
                total_students = cursor.fetchone()[0]
                
                # Get students present today
                cursor.execute("""
                    SELECT COUNT(DISTINCT student_name) 
                    FROM class_attendance 
                    WHERE teacher_name = ? AND date(timestamp) = ? AND attendance_type = 'IN'
                """, (teacher_name, today))
                present_students = cursor.fetchone()[0]
                
                return {
                    'total_students': total_students,
                    'present_students': present_students,
                    'absent_students': total_students - present_students,
                    'attendance_percentage': (present_students / total_students * 100) if total_students > 0 else 0
                }
                
        except Exception as e:
            print(f"Error getting attendance summary: {e}")
            return {'total_students': 0, 'present_students': 0, 'absent_students': 0, 'attendance_percentage': 0}
    
    def cleanup_old_logins(self):
        """Clean up old login sessions (optional maintenance)"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Remove login sessions older than 24 hours
                cursor.execute("""
                    DELETE FROM logged_in_teachers 
                    WHERE login_time < datetime('now', '-1 day')
                """)
                
                conn.commit()
                
        except Exception as e:
            print(f"Error cleaning up old logins: {e}")