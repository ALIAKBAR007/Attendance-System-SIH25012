import sqlite3
import datetime
import os
import pickle
from typing import List, Dict, Tuple, Optional

class AttendanceDatabase:
    def get_teacher_login_logout_counts(self) -> List[Dict]:
        """Get login/logout counts for each teacher"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT teacher_name,
                        SUM(activity_type = 'LOGIN') as login_count,
                        SUM(activity_type = 'LOGOUT') as logout_count
                    FROM teacher_activity
                    GROUP BY teacher_name
                    ORDER BY teacher_name
                """)
                data = []
                for row in cursor.fetchall():
                    data.append({
                        'teacher_name': row[0],
                        'login_count': row[1] or 0,
                        'logout_count': row[2] or 0
                    })
                return data
        except Exception as e:
            print(f"Error getting teacher login/logout counts: {e}")
            return []
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
            
            # Comprehensive attendance table (student_id, name, class_teacher, date, status)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS attendance_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id INTEGER NOT NULL,
                    student_name TEXT NOT NULL,
                    class_teacher TEXT NOT NULL,
                    date TEXT NOT NULL,
                    status TEXT DEFAULT 'ABSENT' CHECK(status IN ('PRESENT', 'ABSENT')),
                    marked_time TIMESTAMP NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(student_id, date),
                    FOREIGN KEY (student_name, class_teacher) REFERENCES students(name, teacher_name)
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
    
    # Attendance Management Methods
    
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
            
    # Attendance Management Methods  
    def mark_student_present(self, student_name: str, teacher_name: str) -> bool:
        """Mark a student as present for today"""
        try:
            today = datetime.date.today().isoformat()
            current_time = datetime.datetime.now()
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get student ID
                cursor.execute("""
                    SELECT id FROM students 
                    WHERE name = ? AND teacher_name = ?
                """, (student_name, teacher_name))
                
                student_result = cursor.fetchone()
                if not student_result:
                    print(f"Student {student_name} not found in {teacher_name}'s class")
                    return False
                    
                student_id = student_result[0]
                
                # Insert or update attendance record
                cursor.execute("""
                    INSERT OR REPLACE INTO attendance_records
                    (student_id, student_name, class_teacher, date, status, marked_time)
                    VALUES (?, ?, ?, ?, 'PRESENT', ?)
                """, (student_id, student_name, teacher_name, today, current_time))
                
                conn.commit()
                return True
                
        except Exception as e:
            print(f"Error marking student present: {e}")
            return False
            
    def is_student_present_today(self, student_name: str, teacher_name: str) -> bool:
        """Check if student is already marked present today"""
        try:
            today = datetime.date.today().isoformat()
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT status FROM attendance_records
                    WHERE student_name = ? AND class_teacher = ? AND date = ?
                """, (student_name, teacher_name, today))
                
                result = cursor.fetchone()
                return result and result[0] == 'PRESENT'
                
        except Exception as e:
            print(f"Error checking if student present: {e}")
            return False
    
    def get_attendance_for_teacher(self, teacher_name: str, date: Optional[str] = None) -> List[Dict]:
        """Get attendance data for a specific teacher's class (dynamic filtering)"""
        try:
            if date is None:
                date = datetime.date.today().isoformat()
                
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get all students in this teacher's class with their attendance status
                cursor.execute("""
                    SELECT 
                        s.id as student_id,
                        s.name as student_name,
                        s.teacher_name as class_teacher,
                        COALESCE(a.status, 'ABSENT') as status,
                        a.marked_time,
                        ? as date
                    FROM students s
                    LEFT JOIN attendance_records a ON (
                        s.id = a.student_id AND 
                        a.date = ?
                    )
                    WHERE s.teacher_name = ?
                    ORDER BY s.name
                """, (date, date, teacher_name))
                
                attendance_data = []
                for row in cursor.fetchall():
                    attendance_data.append({
                        'student_id': row[0],
                        'student_name': row[1], 
                        'class_teacher': row[2],
                        'status': row[3],
                        'marked_time': row[4],
                        'date': row[5]
                    })
                
                return attendance_data
                
        except Exception as e:
            print(f"Error getting attendance for teacher: {e}")
            return []
            
    def get_attendance_summary(self, teacher_name: str, date: Optional[str] = None) -> Dict:
        """Get attendance summary with present/absent counts for a teacher's class"""
        try:
            attendance_data = self.get_attendance_for_teacher(teacher_name, date)
            
            total_students = len(attendance_data)
            present_students = len([student for student in attendance_data if student['status'] == 'PRESENT'])
            absent_students = total_students - present_students
            attendance_percentage = (present_students / total_students * 100) if total_students > 0 else 0
            
            return {
                'total_students': total_students,
                'present_students': present_students,
                'absent_students': absent_students,
                'attendance_percentage': attendance_percentage,
                'date': date or datetime.date.today().isoformat()
            }
                
        except Exception as e:
            print(f"Error getting attendance summary: {e}")
            return {
                'total_students': 0,
                'present_students': 0,
                'absent_students': 0,
                'attendance_percentage': 0,
                'date': date or datetime.date.today().isoformat()
            }
            
    def get_student_attendance_history(self, student_name: str, teacher_name: str, days: int = 30) -> List[Dict]:
        """Get attendance history for a specific student over the last N days"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT date, status, marked_time
                    FROM attendance_records
                    WHERE student_name = ? AND class_teacher = ?
                    ORDER BY date DESC
                    LIMIT ?
                """, (student_name, teacher_name, days))
                
                history = []
                for row in cursor.fetchall():
                    history.append({
                        'date': row[0],
                        'status': row[1],
                        'marked_time': row[2]
                    })
                
                return history
                
        except Exception as e:
            print(f"Error getting student attendance history: {e}")
            return []
            return {'total_students': 0, 'present_students': 0, 'absent_students': 0, 'attendance_percentage': 0}
            
    def get_daily_attendance_list(self, teacher_name: str, date: Optional[str] = None) -> List[Dict]:
        """Get list of all students with their daily attendance status"""
        try:
            if date is None:
                date = datetime.date.today().isoformat()
                
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT 
                        s.name as student_name,
                        COALESCE(a.status, 'ABSENT') as status,
                        a.marked_time,
                        ? as date
                    FROM students s
                    LEFT JOIN attendance_records a ON (
                        s.id = a.student_id AND 
                        a.date = ?
                    )
                    WHERE s.teacher_name = ?
                    ORDER BY s.name
                """, (date, date, teacher_name))
                
                attendance_list = []
                for row in cursor.fetchall():
                    attendance_list.append({
                        'student_name': row[0],
                        'status': row[1],
                        'marked_time': row[2],
                        'date': row[3]
                    })
                
                return attendance_list
                
        except Exception as e:
            print(f"Error getting daily attendance list: {e}")
            return []
            
    # Admin Panel Methods
    def get_teacher_attendance_data(self, teacher_name: str, start_date: str, end_date: str) -> List[Dict]:
        """Get attendance data for a teacher within date range"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT 
                        a.date,
                        a.student_name,
                        a.status,
                        a.marked_time,
                        s.name as student_full_name
                    FROM attendance_records a
                    JOIN students s ON a.student_id = s.id
                    WHERE a.class_teacher = ? 
                    AND a.date BETWEEN ? AND ?
                    ORDER BY a.date DESC, a.student_name
                """, (teacher_name, start_date, end_date))
                
                data = []
                for row in cursor.fetchall():
                    data.append({
                        'date': row[0],
                        'student_name': row[1],
                        'status': row[2],
                        'marked_time': row[3],
                        'teacher_name': teacher_name
                    })
                
                return data
                
        except Exception as e:
            print(f"Error getting teacher attendance data: {e}")
            return []
    
    def get_student_attendance_data(self, teacher_name: str, start_date: str, end_date: str) -> List[Dict]:
        """Get all students' attendance data for a teacher within date range (fixed logic)"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                # Get all students for this teacher
                cursor.execute("""
                    SELECT id, name FROM students WHERE teacher_name = ?
                """, (teacher_name,))
                students = cursor.fetchall()
                data = []
                for student_id, student_name in students:
                    # Get attendance records for this student in range
                    cursor.execute("""
                        SELECT status FROM attendance_records
                        WHERE student_id = ? AND date BETWEEN ? AND ?
                    """, (student_id, start_date, end_date))
                    records = cursor.fetchall()
                    total_days = len(records)
                    present_count = sum(1 for r in records if r[0] == 'PRESENT')
                    absent_count = total_days - present_count
                    attendance_percentage = (present_count / total_days * 100) if total_days > 0 else 0.0
                    data.append({
                        'student_name': student_name,
                        'teacher_name': teacher_name,
                        'present_count': present_count,
                        'total_days': total_days,
                        'attendance_percentage': attendance_percentage,
                        'absent_count': absent_count
                    })
                return data
        except Exception as e:
            print(f"Error getting student attendance data: {e}")
            return []
    
    def get_teacher_summary_stats(self, teacher_name: str, start_date: str, end_date: str) -> Dict:
        """Get summary statistics for a teacher within date range"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get total students
                cursor.execute("""
                    SELECT COUNT(*) FROM students WHERE teacher_name = ?
                """, (teacher_name,))
                total_students = cursor.fetchone()[0]
                
                # Get attendance statistics
                cursor.execute("""
                    SELECT 
                        COUNT(CASE WHEN status = 'PRESENT' THEN 1 END) as total_present,
                        COUNT(*) as total_records,
                        COUNT(DISTINCT date) as days_with_records
                    FROM attendance_records
                    WHERE class_teacher = ? AND date BETWEEN ? AND ?
                """, (teacher_name, start_date, end_date))
                
                stats = cursor.fetchone()
                total_present = stats[0] or 0
                total_records = stats[1] or 0
                days_with_records = stats[2] or 0
                
                avg_attendance = (total_present / total_records * 100) if total_records > 0 else 0
                
                return {
                    'teacher_name': teacher_name,
                    'total_students': total_students,
                    'total_present': total_present,
                    'total_records': total_records,
                    'days_with_records': days_with_records,
                    'avg_attendance_percentage': avg_attendance,
                    'date_range': f"{start_date} to {end_date}"
                }
                
        except Exception as e:
            print(f"Error getting teacher summary stats: {e}")
            return {
                'teacher_name': teacher_name,
                'total_students': 0,
                'total_present': 0,
                'total_records': 0,
                'days_with_records': 0,
                'avg_attendance_percentage': 0,
                'date_range': f"{start_date} to {end_date}"
            }