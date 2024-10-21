import os
import re

def rename_files(directory):
    for root, dirs, files in os.walk(directory):
        for filename in files:
            if filename.endswith('.html'):
                # Split the filename by underscores
                parts = filename.split('_')
                
                # Check if the filename has at least 3 parts
                if len(parts) >= 3:
                    # Keep only the second part
                    new_name = parts[1] + '.html'
                    
                    # Full paths for old and new filenames
                    old_file = os.path.join(root, filename)
                    new_file = os.path.join(root, new_name)
                    
                    # Rename the file
                    os.rename(old_file, new_file)
                    print(f"Renamed: {filename} -> {new_name}")

# Usage
base_directory = r"C:\K1\projects\zuzzuu_app\python_app_doc_generator\api\resource"
rename_files(base_directory)
print("File renaming complete.")