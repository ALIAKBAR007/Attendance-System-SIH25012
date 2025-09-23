#!/usr/bin/env python3
"""
Test script to demonstrate the new streamlined attendance system
"""
import datetime
from database import AttendanceDatabase

def test_new_attendance_system():
    print("=== Testing New Streamlined Attendance System ===\n")
    
    # Initialize database
    db = AttendanceDatabase()
    
    # Test data
    teacher_name = "Mr. Smith"
    test_date = datetime.date.today().isoformat()
    
    print(f"Testing with teacher: {teacher_name}")
    print(f"Date: {test_date}\n")
    
    # Get attendance for teacher (should show all students as ABSENT by default)
    print("1. Getting attendance for teacher's class:")
    attendance_data = db.get_attendance_for_teacher(teacher_name)
    
    if attendance_data:
        for student in attendance_data:
            print(f"   - {student['student_name']}: {student['status']}")
    else:
        print("   No students found for this teacher")
    
    print("\n2. Getting attendance summary:")
    summary = db.get_attendance_summary(teacher_name)
    print(f"   Total Students: {summary['total_students']}")
    print(f"   Present: {summary['present_students']}")
    print(f"   Absent: {summary['absent_students']}")
    print(f"   Attendance %: {summary['attendance_percentage']:.1f}%")
    
    # Test marking a student present (if students exist)
    if attendance_data:
        first_student = attendance_data[0]['student_name']
        print(f"\n3. Marking {first_student} as PRESENT:")
        
        success = db.mark_student_present(first_student, teacher_name)
        if success:
            print(f"   ✓ Successfully marked {first_student} as present")
            
            # Get updated summary
            updated_summary = db.get_attendance_summary(teacher_name)
            print(f"   Updated Present: {updated_summary['present_students']}")
            print(f"   Updated Attendance %: {updated_summary['attendance_percentage']:.1f}%")
        else:
            print(f"   ✗ Failed to mark {first_student} as present")
    
    print("\n4. Testing dynamic filtering (only shows this teacher's class):")
    attendance_filtered = db.get_attendance_for_teacher(teacher_name, test_date)
    print(f"   Found {len(attendance_filtered)} students in {teacher_name}'s class")
    
    print("\n=== Test Complete ===")

if __name__ == "__main__":
    test_new_attendance_system()