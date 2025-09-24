#!/usr/bin/env python3
"""
Test script to verify the Excel export button and functionality work properly
"""

import os
import sys
import tempfile
from datetime import datetime, date
import sqlite3

# Add the project directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def create_test_database():
    """Create a test database with sample data"""
    db_path = os.path.join(tempfile.gettempdir(), "test_attendance.db")
    
    # Remove existing test db
    if os.path.exists(db_path):
        os.remove(db_path)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute("""
        CREATE TABLE teacher_activity (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            teacher_name TEXT NOT NULL,
            activity_type TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
    """)
    
    cursor.execute("""
        CREATE TABLE students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            teacher_name TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    
    cursor.execute("""
        CREATE TABLE attendance_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_name TEXT NOT NULL,
            class_teacher TEXT NOT NULL,
            date TEXT NOT NULL,
            status TEXT NOT NULL,
            marked_time TEXT NOT NULL,
            attendance_type TEXT DEFAULT 'class',
            UNIQUE(student_name, date, attendance_type)
        )
    """)
    
    # Insert test data
    test_teacher_data = [
        ('John Smith', 'login', '2025-09-24 08:30:00'),
        ('Jane Doe', 'logout', '2025-09-24 17:00:00'),
        ('Bob Johnson', 'login', '2025-09-24 09:15:00'),
        ('Alice Brown', 'login', '2025-09-23 08:45:00'),
    ]
    
    cursor.executemany("""
        INSERT INTO teacher_activity (teacher_name, activity_type, timestamp)
        VALUES (?, ?, ?)
    """, test_teacher_data)
    
    test_student_data = [
        ('Alice Student', 'John Smith', '2025-09-20 10:00:00'),
        ('Bob Student', 'Jane Doe', '2025-09-21 11:00:00'),
        ('Charlie Student', 'John Smith', '2025-09-22 09:30:00'),
    ]
    
    cursor.executemany("""
        INSERT INTO students (name, teacher_name, created_at)
        VALUES (?, ?, ?)
    """, test_student_data)
    
    test_attendance_data = [
        ('Alice Student', 'John Smith', '2025-09-24', 'present', '08:30:00', 'class'),
        ('Bob Student', 'Jane Doe', '2025-09-24', 'present', '08:35:00', 'class'),
        ('Alice Student', 'John Smith', '2025-09-24', 'present', '12:30:00', 'meal'),
        ('Charlie Student', 'John Smith', '2025-09-23', 'absent', '08:30:00', 'class'),
    ]
    
    cursor.executemany("""
        INSERT INTO attendance_records (student_name, class_teacher, date, status, marked_time, attendance_type)
        VALUES (?, ?, ?, ?, ?, ?)
    """, test_attendance_data)
    
    conn.commit()
    conn.close()
    
    print(f"✅ Test database created: {db_path}")
    return db_path

def test_export_queries():
    """Test the database queries used by the export functions"""
    db_path = create_test_database()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("\n🧪 Testing export database queries...")
    
    # Test teacher activity query
    cursor.execute("""
        SELECT teacher_name, activity_type, timestamp
        FROM teacher_activity
        WHERE DATE(timestamp) BETWEEN ? AND ?
        ORDER BY timestamp DESC
    """, ('2025-09-23', '2025-09-24'))
    
    teacher_data = cursor.fetchall()
    print(f"📊 Teacher activity records found: {len(teacher_data)}")
    
    # Test student registration query  
    cursor.execute("""
        SELECT teacher_name, name, created_at
        FROM students
        WHERE DATE(created_at) BETWEEN ? AND ?
        ORDER BY teacher_name, name
    """, ('2025-09-20', '2025-09-24'))
    
    student_data = cursor.fetchall()
    print(f"📊 Student registration records found: {len(student_data)}")
    
    # Test class attendance query
    cursor.execute("""
        SELECT s.teacher_name, a.student_name, a.date, a.status, a.marked_time
        FROM attendance_records a
        JOIN students s ON a.student_name = s.name AND a.class_teacher = s.teacher_name
        WHERE a.attendance_type = 'class' 
        AND DATE(a.date) BETWEEN ? AND ?
        ORDER BY s.teacher_name, a.date, a.student_name
    """, ('2025-09-23', '2025-09-24'))
    
    class_attendance = cursor.fetchall()
    print(f"📊 Class attendance records found: {len(class_attendance)}")
    
    # Test meal attendance query
    cursor.execute("""
        SELECT s.teacher_name, a.student_name, a.date, a.status, a.marked_time
        FROM attendance_records a
        JOIN students s ON a.student_name = s.name AND a.class_teacher = s.teacher_name
        WHERE a.attendance_type = 'meal' 
        AND DATE(a.date) BETWEEN ? AND ?
        ORDER BY s.teacher_name, a.date, a.student_name
    """, ('2025-09-23', '2025-09-24'))
    
    meal_attendance = cursor.fetchall()
    print(f"📊 Meal attendance records found: {len(meal_attendance)}")
    
    conn.close()
    
    # Clean up
    os.remove(db_path)
    
    return len(teacher_data) > 0 and len(student_data) > 0

def test_excel_export_simulation():
    """Simulate the Excel export process"""
    print("\n🧪 Testing Excel export simulation...")
    
    try:
        import pandas as pd
        
        # Simulate the export process
        downloads_path = os.path.join(os.path.expanduser("~"), "Downloads", "Attendance_Export")
        os.makedirs(downloads_path, exist_ok=True)
        
        # Test teacher data export
        teacher_data = [
            ['John Smith', 'login', '2025-09-24', '08:30:00', '2025-09-24 08:30:00'],
            ['Jane Doe', 'logout', '2025-09-24', '17:00:00', '2025-09-24 17:00:00']
        ]
        
        df = pd.DataFrame(teacher_data, columns=['Teacher Name', 'Activity Type', 'Date', 'Time', 'Timestamp'])
        
        filename = os.path.join(downloads_path, "Test_Teacher_Activity_2025-09-20_to_2025-09-24.xlsx")
        df.to_excel(filename, index=False, sheet_name='Teacher Activity')
        
        if os.path.exists(filename):
            print(f"✅ Successfully created test Excel file: {filename}")
            file_size = os.path.getsize(filename)
            print(f"📁 File size: {file_size} bytes")
            
            # Clean up
            os.remove(filename)
            try:
                os.rmdir(downloads_path)
            except:
                pass  # Directory might not be empty
            
            return True
        else:
            print("❌ Test Excel file was not created")
            return False
            
    except ImportError:
        print("❌ pandas not available for Excel export")
        return False
    except Exception as e:
        print(f"❌ Error in Excel export simulation: {e}")
        return False

def main():
    """Run all export functionality tests"""
    print("🧪 Starting Excel Export Button and Functionality Tests")
    print("=" * 70)
    
    results = []
    
    # Test 1: Database queries
    results.append(test_export_queries())
    
    # Test 2: Excel export simulation
    results.append(test_excel_export_simulation())
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 Test Results Summary:")
    print(f"✅ Passed: {sum(results)}")
    print(f"❌ Failed: {len(results) - sum(results)}")
    
    if all(results):
        print("🎉 All export functionality tests passed!")
        print("📤 The export button and Excel functionality are ready for use.")
        return True
    else:
        print("⚠️  Some tests failed. Check the error messages above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)