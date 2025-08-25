"""
Test script to verify project structure
"""
import os

def check_project_structure():
    """Check if all required directories and files exist"""
    required_dirs = ['models', 'services', 'api', 'static']
    required_files = [
        'main.py',
        'requirements.txt', 
        'config.py',
        '.env.example',
        'models/__init__.py',
        'services/__init__.py', 
        'api/__init__.py',
        'static/index.html',
        'static/styles.css',
        'static/app.js'
    ]
    
    print("Checking project structure...")
    
    # Check directories
    for directory in required_dirs:
        if os.path.exists(directory):
            print(f"✓ Directory '{directory}' exists")
        else:
            print(f"✗ Directory '{directory}' missing")
    
    # Check files
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✓ File '{file_path}' exists")
        else:
            print(f"✗ File '{file_path}' missing")
    
    print("\nProject structure setup complete!")

if __name__ == "__main__":
    check_project_structure()