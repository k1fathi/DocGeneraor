import os
import re
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class FileRenamer:
    def __init__(self, root_path):
        self.root_path = root_path
        self.changes_made = []yield
        
    def format_name(self, name):
        """Add space after numbers in the name."""
        return re.sub(r'(\d+)([A-Za-z])', r'\1 \2', name)

    def rename_items(self):
        """Recursively rename files and folders starting from root_path."""
        try:
            # Walk through directory tree in bottom-up order
            for root, dirs, files in os.walk(self.root_path, topdown=False):
                # First rename files
                for name in files:
                    if name.endswith('.html'):  # Only process HTML files
                        self.process_rename(root, name)

                # Then rename directories
                for name in dirs:
                    self.process_rename(root, name)

        except Exception as e:
            logger.error(f"Error during renaming process: {str(e)}")
            raise

    def process_rename(self, root, name):
        """Process individual file or directory rename."""
        new_name = self.format_name(name)
        if new_name != name:
            old_path = os.path.join(root, name)
            new_path = os.path.join(root, new_name)
            
            try:
                os.rename(old_path, new_path)
                self.changes_made.append({
                    'old': old_path,
                    'new': new_path,
                    'timestamp': datetime.now().isoformat()
                })
                logger.info(f'Renamed: {name} -> {new_name}')
            except Exception as e:
                logger.error(f'Error renaming {name}: {str(e)}')

    def show_summary(self):
        """Show summary of all changes made."""
        if self.changes_made:
            logger.info("\nSummary of changes made:")
            for change in self.changes_made:
                logger.info(f"Renamed: {os.path.basename(change['old'])} -> {os.path.basename(change['new'])}")
            logger.info(f"\nTotal changes made: {len(self.changes_made)}")
        else:
            logger.info("No changes were necessary.")

def main():
    # Set the specific path
    resource_path = r"C:\K1\projects\zuzzuu_app\python_app_doc_generator\api\resource"
    
    # Verify the path exists
    if not os.path.exists(resource_path):
        logger.error(f"Path does not exist: {resource_path}")
        return

    # Create renamer instance
    renamer = FileRenamer(resource_path)
    
    # Show what's going to happen
    logger.info(f"This will rename files and folders in: {resource_path}")
    logger.info("Example: '04Web' will become '04 Web'")
    
    # Ask for confirmation
    response = input("Do you want to proceed? (y/n): ").lower()
    
    if response == 'y':
        try:
            renamer.rename_items()
            renamer.show_summary()
            logger.info("\nRenaming process completed successfully!")
        except Exception as e:
            logger.error(f"An error occurred during the renaming process: {str(e)}")
    else:
        logger.info("Operation cancelled by user.")

if __name__ == "__main__":
    main()