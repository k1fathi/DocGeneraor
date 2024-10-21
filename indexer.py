from whoosh.index import create_in
from whoosh.fields import Schema, TEXT, ID
from whoosh.qparser import QueryParser
from whoosh.index import open_dir
import os
from bs4 import BeautifulSoup

# Directory where your HTML files are stored
html_directory = r'C:\K1\projects\zuzzuu_app\docs\New Docs'

# Directory to store the index
index_directory = 'indexdir'
if not os.path.exists(index_directory):
    os.mkdir(index_directory)

# Define the schema for your index
schema = Schema(title=TEXT(stored=True), path=ID(stored=True), content=TEXT)

# Create an index in the specified directory
index = create_in(index_directory, schema)
writer = index.writer()

# Index all HTML files in the directory
for filename in os.listdir(html_directory):
    if filename.endswith(".html"):
        file_path = os.path.join(html_directory, filename)
        with open(file_path, 'r', encoding='utf-8') as file:
            # Parse the HTML content
            soup = BeautifulSoup(file, 'html.parser')
            title = soup.title.string if soup.title else 'No Title'
            content = soup.get_text()

            # Add the file content to the index
            writer.add_document(title=title, path=file_path, content=content)
            print(f"Indexed: {filename}")

writer.commit()
print("Indexing complete!")
