import os
import shutil

def copy_html_files(source_dir, dest_dir):
    # Ensure the destination directory exists
    os.makedirs(dest_dir, exist_ok=True)

    # Walk through the directory tree
    for root, dirs, files in os.walk(source_dir):
        for file in files:
            if file.lower().endswith('.html'):
                # Get the full path of the file
                file_path = os.path.join(root, file)
                
                # Create the new filename
                relative_path = os.path.relpath(root, source_dir)
                new_filename = '_'.join(relative_path.split(os.sep) + [file])
                
                # Create the destination path
                dest_path = os.path.join(dest_dir, new_filename)
                
                # Copy the file
                shutil.copy2(file_path, dest_path)
                print(f"Copied: {file_path} -> {dest_path}")

# Set the source and destination directories
source_directory = r"C:\K1\projects\zuzzuu_app\docs\New Docs"
destination_directory = r"C:\K1\projects\zuzzuu_app\docs\New Docs\all"

# Run the function
copy_html_files(source_directory, destination_directory)

print("File copying completed.")