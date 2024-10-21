import os
import shutil
import re

def organize_files(source_dir, target_dir):
    # Ensure target directory exists
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)

    # Get all HTML files
    files = [f for f in os.listdir(source_dir) if f.endswith('.html')]

    # Dictionary to store file groups
    file_groups = {}

    for file in files:
        # Extract the base name (everything before the first underscore)
        match = re.match(r'(\d+[A-Za-z]+)_', file)
        if match:
            base_name = match.group(1)
            if base_name not in file_groups:
                file_groups[base_name] = []
            file_groups[base_name].append(file)

    # Create folders and move files
    for base_name, group_files in file_groups.items():
        # Create folder
        folder_path = os.path.join(target_dir, base_name)
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

        # Move files to the folder
        for file in group_files:
            src = os.path.join(source_dir, file)
            dst = os.path.join(folder_path, file)
            shutil.move(src, dst)

    print("File organization complete.")

# Usage
source_directory = r"C:\K1\projects\zuzzuu_app\python_app_doc_generator\resource"
target_directory = r"C:\K1\projects\zuzzuu_app\python_app_doc_generator\api\resource\TR_cat"
organize_files(source_directory, target_directory)