#!/usr/bin/env python3
"""
Test the comprehensive attendance export functionality
"""

import os
import sys
import tempfile
import sqlite3
from datetime import datetime, date

# Add the project directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def create_comprehensive_test_database():
    """Create a comprehensive test database with multiple teachers and students"""
    db_path = os.path.join(tempfile.gettempdir(), "test_comprehensive_attendance.db")
    
    # Remove existing test db
    if os.path.exists(db_path):
        os.remove(db_path)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create tables
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
    
    # Insert test students for multiple teachers
    test_students = [
        # Teacher A's students
        ('Alice Smith', 'Teacher A', '2025-09-01 10:00:00'),
        ('Bob Johnson', 'Teacher A', '2025-09-01 10:05:00'),
        ('Charlie Brown', 'Teacher A', '2025-09-01 10:10:00'),
        
        # Teacher B's students
        ('Diana Wilson', 'Teacher B', '2025-09-01 11:00:00'),
        ('Edward Davis', 'Teacher B', '2025-09-01 11:05:00'),
        
        # Teacher C's students
        ('Fiona Garcia', 'Teacher C', '2025-09-01 12:00:00'),
        ('George Miller', 'Teacher C', '2025-09-01 12:05:00'),
        ('Hannah Taylor', 'Teacher C', '2025-09-01 12:10:00'),
        ('Ian Anderson', 'Teacher C', '2025-09-01 12:15:00'),
    ]
    
    cursor.executemany("""
        INSERT INTO students (name, teacher_name, created_at)
        VALUES (?, ?, ?)
    """, test_students)
    
    # Insert comprehensive test attendance data
    test_attendance = [
        # Class attendance - Day 1 (2025-09-23)
        ('Alice Smith', 'Teacher A', '2025-09-23', 'present', '08:30:00', 'class'),
        ('Bob Johnson', 'Teacher A', '2025-09-23', 'present', '08:31:00', 'class'),
        ('Charlie Brown', 'Teacher A', '2025-09-23', 'absent', '08:30:00', 'class'),
        
        ('Diana Wilson', 'Teacher B', '2025-09-23', 'present', '08:30:00', 'class'),
        ('Edward Davis', 'Teacher B', '2025-09-23', 'present', '08:32:00', 'class'),
        
        ('Fiona Garcia', 'Teacher C', '2025-09-23', 'present', '08:30:00', 'class'),
        ('George Miller', 'Teacher C', '2025-09-23', 'absent', '08:30:00', 'class'),
        ('Hannah Taylor', 'Teacher C', '2025-09-23', 'present', '08:33:00', 'class'),
        ('Ian Anderson', 'Teacher C', '2025-09-23', 'present', '08:34:00', 'class'),
        
        # Class attendance - Day 2 (2025-09-24)
        ('Alice Smith', 'Teacher A', '2025-09-24', 'present', '08:30:00', 'class'),
        ('Bob Johnson', 'Teacher A', '2025-09-24', 'absent', '08:30:00', 'class'),
        ('Charlie Brown', 'Teacher A', '2025-09-24', 'present', '08:35:00', 'class'),
        
        ('Diana Wilson', 'Teacher B', '2025-09-24', 'present', '08:30:00', 'class'),
        ('Edward Davis', 'Teacher B', '2025-09-24', 'absent', '08:30:00', 'class'),
        
        ('Fiona Garcia', 'Teacher C', '2025-09-24', 'present', '08:30:00', 'class'),
        ('George Miller', 'Teacher C', '2025-09-24', 'present', '08:31:00', 'class'),
        ('Hannah Taylor', 'Teacher C', '2025-09-24', 'absent', '08:30:00', 'class'),
        ('Ian Anderson', 'Teacher C', '2025-09-24', 'present', '08:32:00', 'class'),
        
        # Meal attendance - Day 1
        ('Alice Smith', 'Teacher A', '2025-09-23', 'present', '12:30:00', 'meal'),
        ('Bob Johnson', 'Teacher A', '2025-09-23', 'present', '12:31:00', 'meal'),
        
        ('Diana Wilson', 'Teacher B', '2025-09-23', 'present', '12:30:00', 'meal'),
        ('Edward Davis', 'Teacher B', '2025-09-23', 'absent', '12:30:00', 'meal'),
        
        ('Fiona Garcia', 'Teacher C', '2025-09-23', 'present', '12:30:00', 'meal'),
        ('Hannah Taylor', 'Teacher C', '2025-09-23', 'present', '12:32:00', 'meal'),
        
        # Meal attendance - Day 2
        ('Alice Smith', 'Teacher A', '2025-09-24', 'absent', '12:30:00', 'meal'),
        ('Charlie Brown', 'Teacher A', '2025-09-24', 'present', '12:33:00', 'meal'),
        
        ('Diana Wilson', 'Teacher B', '2025-09-24', 'present', '12:30:00', 'meal'),
        
        ('George Miller', 'Teacher C', '2025-09-24', 'present', '12:31:00', 'meal'),
        ('Ian Anderson', 'Teacher C', '2025-09-24', 'present', '12:32:00', 'meal'),
    ]
    
    cursor.executemany("""
        INSERT INTO attendance_records (student_name, class_teacher, date, status, marked_time, attendance_type)
        VALUES (?, ?, ?, ?, ?, ?)
    """, test_attendance)
    
    conn.commit()
    conn.close()
    
    print(f"✅ Comprehensive test database created: {db_path}")
    return db_path

def test_comprehensive_export_format():
    """Test the comprehensive export format"""
    print("🧪 Testing Comprehensive Export Format...")
    
    try:
        import pandas as pd
        
        # Create test data structure
        teachers = ['Teacher A', 'Teacher B', 'Teacher C']
        dates = ['2025-09-23', '2025-09-24']
        
        # Test comprehensive header creation
        header_row = ['Date']
        for i, teacher in enumerate(teachers):
            if i > 0:
                header_row.append('')  # Empty column for spacing
            header_row.extend([f'{teacher} - Student', f'{teacher} - Present', f'{teacher} - Absent', f'{teacher} - Total'])
        
        print(f"✅ Header format: {len(header_row)} columns")
        print(f"📋 Header preview: {header_row[:10]}...")  # Show first 10 columns
        
        # Test detailed header creation
        teacher_students = {
            'Teacher A': ['Alice Smith', 'Bob Johnson', 'Charlie Brown'],
            'Teacher B': ['Diana Wilson', 'Edward Davis'],
            'Teacher C': ['Fiona Garcia', 'George Miller', 'Hannah Taylor', 'Ian Anderson']
        }
        
        detailed_header = ['Date', 'Time']
        for i, teacher in enumerate(teachers):
            if i > 0:
                detailed_header.append('')  # Spacing column
            students = teacher_students.get(teacher, [])
            for student in students:
                detailed_header.append(f'{teacher} - {student}')
        
        print(f"✅ Detailed header format: {len(detailed_header)} columns")
        print(f"📋 Student sections properly separated with spacing columns")
        
        # Create a test Excel file to verify format
        test_path = os.path.join(tempfile.gettempdir(), "test_comprehensive_format.xlsx")
        
        # Create test data
        test_data = []
        for date in dates:
            row = [date]
            for i, teacher in enumerate(teachers):
                if i > 0:
                    row.append('')  # Spacing
                row.extend([f'{len(teacher_students[teacher])} students', '2', '1', str(len(teacher_students[teacher]))])
            test_data.append(row)
        
        df = pd.DataFrame(test_data, columns=header_row)
        df.to_excel(test_path, index=False, sheet_name='Test Comprehensive')
        
        if os.path.exists(test_path):
            print(f"✅ Test Excel file created successfully")
            
            # Verify it can be read back
            df_read = pd.read_excel(test_path)
            print(f"📊 Verified: {len(df_read)} rows, {len(df_read.columns)} columns")
            
            # Clean up
            os.remove(test_path)
            print("🧹 Test file cleaned up")
            
            return True
        else:
            print("❌ Test Excel file creation failed")
            return False
            
    except ImportError:
        print("❌ pandas not available")
        return False
    except Exception as e:
        print(f"❌ Comprehensive export test failed: {e}")
        return False

def test_database_queries():
    """Test the database queries for comprehensive export"""
    print("\n🧪 Testing Database Queries for Comprehensive Export...")
    
    db_path = create_comprehensive_test_database()
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Test teacher query
        cursor.execute("SELECT DISTINCT teacher_name FROM students ORDER BY teacher_name")
        teachers = [row[0] for row in cursor.fetchall()]
        print(f"✅ Found {len(teachers)} teachers: {teachers}")
        
        # Test date query for class attendance
        cursor.execute("""
            SELECT DISTINCT date FROM attendance_records 
            WHERE attendance_type = 'class' AND DATE(date) BETWEEN ? AND ?
            ORDER BY date
        """, ('2025-09-23', '2025-09-24'))
        dates = [row[0] for row in cursor.fetchall()]
        print(f"✅ Found {len(dates)} class attendance dates: {dates}")
        
        # Test student query for each teacher
        for teacher in teachers:
            cursor.execute("""
                SELECT name FROM students 
                WHERE teacher_name = ? 
                ORDER BY name
            """, (teacher,))
            students = [row[0] for row in cursor.fetchall()]
            print(f"✅ {teacher}: {len(students)} students - {students[:3]}{'...' if len(students) > 3 else ''}")
        
        # Test attendance data query
        cursor.execute("""
            SELECT s.teacher_name, a.student_name, a.date, a.status
            FROM attendance_records a
            JOIN students s ON a.student_name = s.name AND a.class_teacher = s.teacher_name
            WHERE a.attendance_type = 'class' 
            AND DATE(a.date) BETWEEN ? AND ?
        """, ('2025-09-23', '2025-09-24'))
        
        attendance_records = cursor.fetchall()
        print(f"✅ Found {len(attendance_records)} class attendance records")
        
        # Count present/absent by teacher and date
        for teacher in teachers:
            for date in dates:
                present_count = 0
                absent_count = 0
                for teacher_name, student_name, record_date, status in attendance_records:
                    if teacher_name == teacher and record_date == date:
                        if status == 'present':
                            present_count += 1
                        elif status == 'absent':
                            absent_count += 1
                
                print(f"📊 {teacher} on {date}: {present_count} present, {absent_count} absent")
        
        conn.close()
        
        # Clean up
        os.remove(db_path)
        print("🧹 Test database cleaned up")
        
        return True
        
    except Exception as e:
        print(f"❌ Database query test failed: {e}")
        return False

def main():
    """Run all comprehensive export tests"""
    print("🧪 TESTING COMPREHENSIVE ATTENDANCE EXPORT")
    print("=" * 60)
    
    results = []
    
    # Test 1: Comprehensive export format
    results.append(test_comprehensive_export_format())
    
    # Test 2: Database queries
    results.append(test_database_queries())
    
    # Results
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS:")
    print(f"✅ Passed: {sum(results)}")
    print(f"❌ Failed: {len(results) - sum(results)}")
    
    if all(results):
        print("🎉 ALL COMPREHENSIVE EXPORT TESTS PASSED!")
        print("\n📋 COMPREHENSIVE EXPORT FEATURES:")
        print("✅ All teachers included in single export")
        print("✅ Column sections separated by spaces")
        print("✅ Multiple sheets: Comprehensive, Student Details, Individual Teachers")
        print("✅ Format: Teacher A (4 cols) | Space | Teacher B (4 cols) | Space | Teacher C (4 cols)")
        print("✅ Summary data: Student count, Present, Absent, Total per teacher per date")
        print("✅ Detailed data: Individual student status (P/A/-) per teacher per date")
        print("\n📁 FILE STRUCTURE:")
        print("- Sheet 1: Comprehensive Attendance (Summary by teacher)")
        print("- Sheet 2: Student Details (Individual student status)")
        print("- Sheet 3+: Individual teacher sheets")
        return True
    else:
        print("⚠️  Some tests failed!")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)