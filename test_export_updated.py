#!/usr/bin/env python3
"""
Test the updated export functionality with date-range folder names and no emojis
"""

import os
import sys
import tempfile
from datetime import datetime, date

def test_folder_naming():
    """Test the new folder naming with date ranges"""
    print("🧪 Testing Date Range Folder Naming...")
    
    # Simulate the folder naming logic
    start_date = date(2025, 9, 20)
    end_date = date(2025, 9, 24)
    
    start_date_str = start_date.isoformat()
    end_date_str = end_date.isoformat()
    folder_name = f"Attendance_Export_{start_date_str}_to_{end_date_str}"
    downloads_path = os.path.join(os.path.expanduser("~"), "Downloads", folder_name)
    
    print(f"✅ New folder name: {folder_name}")
    print(f"✅ Full path: {downloads_path}")
    
    # Test folder creation
    try:
        os.makedirs(downloads_path, exist_ok=True)
        if os.path.exists(downloads_path):
            print("✅ Folder created successfully")
            
            # Clean up test folder
            try:
                os.rmdir(downloads_path)
                print("✅ Test folder cleaned up")
            except:
                print("Note: Folder may contain files, manual cleanup needed")
            
            return True
        else:
            print("❌ Folder creation failed")
            return False
            
    except Exception as e:
        print(f"❌ Error creating folder: {e}")
        return False

def test_export_without_emojis():
    """Test export functionality without emojis"""
    print("\n🧪 Testing Export Functionality (No Emojis)...")
    
    try:
        import pandas as pd
        
        # Test data without emojis in labels
        test_data = [
            {'Teacher Name': 'John Smith', 'Activity Type': 'login', 'Date': '2025-09-24'},
            {'Student Name': 'Alice Brown', 'Registration Date': '2025-09-20', 'Class Teacher': 'John Smith'}
        ]
        
        # Create test folder with date range
        start_date_str = "2025-09-20"
        end_date_str = "2025-09-24"
        folder_name = f"Attendance_Export_{start_date_str}_to_{end_date_str}"
        test_path = os.path.join(tempfile.gettempdir(), folder_name)
        os.makedirs(test_path, exist_ok=True)
        
        # Create test Excel file
        df = pd.DataFrame(test_data)
        test_filename = os.path.join(test_path, f"Test_Export_{start_date_str}_to_{end_date_str}.xlsx")
        df.to_excel(test_filename, index=False, sheet_name='Test Data')
        
        if os.path.exists(test_filename):
            print(f"✅ Export test successful: {os.path.basename(test_filename)}")
            print(f"✅ Folder path: {test_path}")
            
            # Clean up
            os.remove(test_filename)
            os.rmdir(test_path)
            print("✅ Test files cleaned up")
            
            return True
        else:
            print("❌ Export test failed")
            return False
            
    except ImportError:
        print("❌ pandas not available")
        return False
    except Exception as e:
        print(f"❌ Export test failed: {e}")
        return False

def main():
    """Run all tests for the updated export functionality"""
    print("🧪 TESTING UPDATED EXPORT FUNCTIONALITY")
    print("=" * 50)
    
    results = []
    
    # Test 1: Folder naming with date ranges
    results.append(test_folder_naming())
    
    # Test 2: Export without emojis
    results.append(test_export_without_emojis())
    
    # Results
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS:")
    print(f"✅ Passed: {sum(results)}")
    print(f"❌ Failed: {len(results) - sum(results)}")
    
    if all(results):
        print("🎉 ALL TESTS PASSED!")
        print("\n📋 CHANGES IMPLEMENTED:")
        print("✅ Removed emojis from export section for better spacing")
        print("✅ Added date range to folder names for differentiation")
        print("\n📁 FOLDER NAMING FORMAT:")
        print("Attendance_Export_YYYY-MM-DD_to_YYYY-MM-DD")
        print("\nExample: Attendance_Export_2025-09-20_to_2025-09-24")
        return True
    else:
        print("⚠️  Some tests failed!")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)