#!/usr/bin/env python3
"""
Quick test to verify the export tab GUI is properly visible
"""

import os
import sys
import time
from datetime import datetime

# Add the project directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_gui_export_tab():
    """Test if the export tab is properly created in the GUI"""
    print("🧪 Testing Export Tab GUI Components...")
    
    try:
        # Import the main application
        import main_gui_ctk
        
        print("✅ Successfully imported main_gui_ctk")
        
        # Create the application instance (without running mainloop)
        app = main_gui_ctk.IntegratedAttendanceSystem()
        
        print("✅ Successfully created application instance")
        
        # Check if we can access the login tab initially
        if hasattr(app, 'tabview'):
            print(f"✅ Main tabview exists with tabs: {app.tabview._tab_dict.keys()}")
        
        # Simulate teacher login to access admin panel
        if hasattr(app, 'db'):
            print("✅ Database connection exists")
            
        # Test admin panel access (simulate login)
        app.current_teacher = "Test Teacher"  # Simulate logged in teacher
        
        # Create admin panel
        app.create_admin_panel()
        
        # Check if admin tabview was created
        if hasattr(app, 'admin_tabview'):
            admin_tabs = list(app.admin_tabview._tab_dict.keys())
            print(f"✅ Admin tabview created with tabs: {admin_tabs}")
            
            # Check if export tab exists
            if "📊 Data Export" in admin_tabs:
                print("✅ Data Export tab found in admin panel!")
                
                # Check if export button exists
                export_tab = app.admin_tabview.tab("📊 Data Export")
                if hasattr(app, 'export_button'):
                    print("✅ Export button exists in the application")
                    print(f"📤 Button text: {app.export_button.cget('text')}")
                    print(f"🎯 Button command: {app.export_button.cget('command')}")
                else:
                    print("❌ Export button not found")
                    return False
                    
                # Check if export checkboxes exist
                checkboxes = ['export_teacher_data', 'export_student_data', 'export_class_attendance', 'export_meal_attendance']
                for checkbox_name in checkboxes:
                    if hasattr(app, checkbox_name):
                        checkbox = getattr(app, checkbox_name)
                        print(f"✅ {checkbox_name}: {checkbox.cget('text')}")
                    else:
                        print(f"❌ {checkbox_name} not found")
                        return False
                
                # Check if date pickers exist
                if hasattr(app, 'export_start_date') and hasattr(app, 'export_end_date'):
                    print("✅ Date pickers exist for export functionality")
                else:
                    print("❌ Date pickers not found")
                    return False
                
                print("🎉 All export tab GUI components found!")
                return True
            else:
                print("❌ Data Export tab not found in admin panel")
                return False
        else:
            print("❌ Admin tabview not created")
            return False
            
    except Exception as e:
        print(f"❌ Error testing GUI: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run the GUI test"""
    print("🧪 Starting Export Tab GUI Test")
    print("=" * 50)
    
    success = test_gui_export_tab()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ Export Tab GUI Test PASSED!")
        print("📊 The Data Export tab and all components are properly set up.")
    else:
        print("❌ Export Tab GUI Test FAILED!")
        print("⚠️  Check the error messages above.")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)