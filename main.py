import os
import base64
import re
from flask import Flask, request, jsonify, send_from_directory
from openai import OpenAI
from dotenv import load_dotenv
from whoosh.index import open_dir
from whoosh.qparser import QueryParser
from whoosh.index import create_in, open_dir
from whoosh.fields import *
from whoosh.qparser import QueryParser
from bs4 import BeautifulSoup
from datetime import datetime
from flask_cors import CORS
import logging
from datetime import datetime
from pathlib import Path
from flask_jwt_extended import JWTManager, create_access_token, get_jwt_identity, jwt_required
from datetime import timedelta
import hashlib

load_dotenv()
app = Flask(__name__, static_folder='public', static_url_path='')
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CORS(app)
#
# Add these after your existing imports
app.config['JWT_SECRET_KEY'] = 'm$9@T3^%m7Q6$y7Y%74!Y9@H*3T+N!5'  # Change this to a secure secret key
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=1)  # Set token expiration to 1 day
jwt = JWTManager(app)

# Admin credentials (in production, use a secure database)
ADMIN_USERNAME = "admin"
# Store password hash instead of plain text
ADMIN_PASSWORD_HASH = hashlib.sha256("zUzZuUd@cs".encode()).hexdigest()

@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return jsonify({"error": "Missing username or password"}), 400

        # Check credentials
        if username == ADMIN_USERNAME and hashlib.sha256(password.encode()).hexdigest() == ADMIN_PASSWORD_HASH:
            # Create access token
            access_token = create_access_token(identity=username)
            return jsonify({
                "token": access_token,
                "message": "Login successful"
            }), 200
        else:
            return jsonify({"error": "Invalid credentials"}), 401

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route('/')
def serve_index():
    return send_from_directory(app.static_folder, 'index.html')

# Serve static files from public folder
@app.route('/<path:path>')
def serve_static(path):
    if os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    return send_from_directory(app.static_folder, 'index.html')

def analyze_image(image_file):
    image_base64 = base64.b64encode(image_file.read()).decode('utf-8')
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": """
                    Analyze this image and create a detailed user guide in HTML format. Follow these specific guidelines:

                    1. HTML Structure:
                       - Use <!DOCTYPE html> declaration.
                       - Use <html lang="en"> as the root element.
                       - Include a <head> section with meta tags, title, and a <style> section.
                       - Wrap the main content in <body> with a <div class="container">.

                    2. CSS Styling:
                       Include a <style> section in <head> with the following CSS:
                       - body: font-family: Arial, sans-serif; background-color: #f9f9f9; margin: 0; padding: 20px;
                       - .container: width: 80%; margin: auto; background: #ffffff; border-radius: 8px; box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1); padding: 20px;
                       - h1, h2: color: #333;
                       - ul: list-style-type: none; padding: 0;
                       - li: background: #eaeaea; margin: 5px 0; padding: 10px; border-radius: 4px;
                       - .example: background: #f0f8ff; border-left: 4px solid #007bff; padding: 10px; margin-bottom: 20px;
                       - .code: background: #f8f8f8; border: 1px solid #ccc; padding: 10px; font-family: monospace; overflow: auto;
                       - .button: background: #007bff; color: white; border: none; padding: 10px 15px; border-radius: 4px; cursor: pointer; margin-top: 10px;
                       - .button:hover: background: #0056b3;
                       - .actions: display: flex; gap: 10px;

                    3. Content Structure:
                       - Start with an <h1> title summarizing the main topic.
                       - Use <h2> tags for main sections (e.g., "Main Components", "Usage Instructions", "Detailed Explanation of Features", "Use Case Scenario").
                       - Use unordered lists <ul> with <li> items for features, components, or instructions.
                       - Wrap example content in <div class="example">.
                       - Use <div class="code"> for code-like or step-by-step instructions, wrapping inline code with <code> tags.
                       - Create buttons using <button class="button">.

                    4. Content Details:
                       - Provide a comprehensive overview of the main components or features visible in the image.
                       - Include detailed explanations for each major feature or component.
                       - Add usage instructions with clear steps.
                       - Include a "Use Case Scenario" section that demonstrates how a user would typically interact with the interface or system shown in the image.
                       - Use <b> tags to emphasize important terms or labels.

                    5. Formatting:
                       - Ensure proper indentation and nesting of HTML elements.
                       - Use semantic HTML where appropriate (e.g., <header>, <main>, <footer> if applicable).

                    6. Do not include:
                       - "Troubleshooting" or "Further Assistance" sections.
                       - Any placeholder content or lorem ipsum text.
                       - Any introductory text before the <!DOCTYPE html> declaration.

                    Ensure the content directly relates to what's visible in the image, providing clear and concise explanations. The HTML should be well-formatted and properly nested. Focus on creating user-friendly documentation that guides the reader through using the interface or system effectively.
                    """
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_base64}"
                        }
                    }
                ]
            }
        ],
        max_tokens=1000
    )
    
    return response.choices[0].message.content

def extract_html_content(content):
    # Remove any text before <!DOCTYPE html>
    doctype_index = content.find('<!DOCTYPE html>')
    if doctype_index != -1:
        content = content[doctype_index:]
    
    # Extract content between <html> tags, including the tags themselves
    match = re.search(r'<html.*?>.*</html>', content, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(0)
    
    # If no <html> tags found, check for <body> tags
    match = re.search(r'<body.*?>.*</body>', content, re.DOTALL | re.IGNORECASE)
    if match:
        return f'<html lang="en">{match.group(0)}</html>'
    
    # If neither <html> nor <body> tags are found, wrap the content in html and body tags
    return f'<html lang="en"><body>{content}</body></html>'

@app.route('/analyze_image', methods=['POST'])
def analyze_image_endpoint():
    if 'image' not in request.files:
        return jsonify({"error": "No image file provided"}), 400
    
    image_file = request.files['image']
    if image_file.filename == '':
        return jsonify({"error": "No selected image file"}), 400
    
    output_folder = request.form.get('output_folder', '')
    if not output_folder:
        return jsonify({"error": "No output folder provided"}), 400

    html_content = analyze_image(image_file)
    extracted_content = extract_html_content(html_content)
    
    os.makedirs(output_folder, exist_ok=True)
    filename = os.path.join(output_folder, "en.html")
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(extracted_content)
    
    return jsonify({"message": f"Analysis complete. Results saved to {filename}", "html_content": extracted_content})

@app.route('/translate_html', methods=['POST'])
def translate_html_endpoint():
    if 'html_file' not in request.files:
        return jsonify({"error": "No HTML file provided"}), 400
    
    html_file = request.files['html_file']
    if html_file.filename == '':
        return jsonify({"error": "No selected HTML file"}), 400
    
    target_language = request.form.get('target_language', 'tr')
    output_folder = request.form.get('output_folder', '')
    
    if not output_folder:
        return jsonify({"error": "No output folder provided"}), 400
    
    # Read the contents of the HTML file
    html_content = html_file.read().decode('utf-8')
    
    # Translate the HTML content using OpenAI Chat Completions
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "user",
                "content": f"Translate the following HTML content from English to {target_language.upper()}:\n\n{html_content}"
            }
        ]
    )
    
    translated_content = response.choices[0].message.content
    result=extract_html_content(translated_content)
    
    # Save the translated HTML content to a file
    os.makedirs(output_folder, exist_ok=True)
    output_file = os.path.join(output_folder, f'{target_language}.html')
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(result)
    
    return jsonify({"message": f"Translation complete. Output saved to {output_file}"})

# Set up the Whoosh index
index_dir = "whoosh_index"
if not os.path.exists(index_dir):
    os.makedirs(index_dir)

schema = Schema(title=TEXT(stored=True), path=ID(stored=True), content=TEXT)
index = create_in(index_dir, schema)

# Index the HTML files in the "C:\K1\projects\zuzzuu_app\docs\New Docs" directory
#docs_dir = os.path.join("C:", "K1", "projects", "zuzzuu_app", "docs", "New Docs")
docs_dir = os.path.join("resource")
for root, dirs, files in os.walk(docs_dir):
    for file in files:
        if file.endswith(".html"):
            file_path = os.path.join(root, file)
            with open(file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            writer = index.writer()
            writer.add_document(title=file, path=file_path, content=html_content)
            writer.commit()

def search_html_files(directory, search_term):
    results = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.html'):
                file_path = os.path.join(root, file)
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    soup = BeautifulSoup(content, 'html.parser')
                    text_content = soup.get_text()
                    if re.search(search_term, text_content, re.IGNORECASE):
                        results.append(file_path)
    return results

def get_files_for_language(language):
    try:
        # Use Path for better cross-platform compatibility
        current_dir = Path(__file__).resolve().parent
        resource_dir = current_dir / 'resource' / language

        # Check if directory exists
        if not resource_dir.exists():
            logger.error(f"Directory not found: {resource_dir}")
            return []

        files = []
        # Walk through directory
        for file_path in resource_dir.rglob('*.html'):
            try:
                # Get relative path from resource directory
                relative_path = file_path.relative_to(resource_dir)
                
                # Get file creation time
                created_timestamp = os.path.getctime(str(file_path))
                created_date = datetime.fromtimestamp(created_timestamp).strftime('%Y-%m-%d %H:%M:%S')
                
                # Create file info dictionary
                file_info = {
                    'name': file_path.name,
                    'path': str(relative_path).replace('\\', '/'),
                    'createdDate': created_date,
                    'folder': str(relative_path.parent).replace('\\', '/') if relative_path.parent != Path('.') else ''
                }
                
                files.append(file_info)
                logger.info(f"Found file: {file_info['path']}")
                
            except Exception as e:
                logger.error(f"Error processing file {file_path}: {str(e)}")
                continue

        # Sort files by folder and name
        files.sort(key=lambda x: (x['folder'], x['name']))
        
        logger.info(f"Total files found: {len(files)}")
        return files

    except Exception as e:
        logger.error(f"Error scanning directory: {str(e)}")
        return []

# Example debugging function
def debug_directory_structure(language):
    try:
        current_dir = Path(__file__).resolve().parent
        resource_dir = current_dir / 'resource' / language
        
        logger.info(f"Current directory: {current_dir}")
        logger.info(f"Resource directory: {resource_dir}")
        logger.info(f"Resource directory exists: {resource_dir.exists()}")
        
        if resource_dir.exists():
            logger.info("Directory contents:")
            for item in resource_dir.rglob('*'):
                logger.info(f"  {item.relative_to(resource_dir)}")
    
    except Exception as e:
        logger.error(f"Error debugging directory structure: {str(e)}")

@app.route('/api/files', methods=['GET'])
@jwt_required()
def api_get_files():
    language = request.args.get('lang', 'en').lower()  # Default to English if no language specified
    if language not in ['en', 'tr']:
        return jsonify({"error": "Invalid language specified"}), 400
    
    files = get_files_for_language(language)
    return jsonify(files)

@app.route('/api/file/<path:filepath>', methods=['GET'])
@jwt_required()
def get_file_content(filepath):
    language = request.args.get('lang', 'en').lower()
    if language not in ['en', 'tr']:
        return jsonify({"error": "Invalid language specified"}), 400

    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        full_path = os.path.join(current_dir, 'resource', language, filepath)
        
        # Security check to prevent directory traversal
        if not os.path.abspath(full_path).startswith(os.path.abspath(os.path.join(current_dir, 'resource'))):
            return jsonify({"error": "Invalid file path"}), 403

        if not os.path.exists(full_path):
            return jsonify({"error": "File not found"}), 404

        with open(full_path, 'r', encoding='utf-8') as file:
            content = file.read()
            return jsonify({"content": content})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/search', methods=['GET'])
@jwt_required()
def search_endpoint():
    search_term = request.args.get('q')
    language = request.args.get('lang', 'en').lower()  # Default to English if not specified
    
    if not search_term:
        return jsonify({"error": "No search term provided"}), 400
    
    if language not in ['en', 'tr']:
        return jsonify({"error": "Invalid language specified"}), 400

    # Get the absolute path to the language-specific resource directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    directory = os.path.join(current_dir, 'resource', language)
    
    results = search_html_files(directory, search_term, language)
    return jsonify({"results": results})

def search_html_files(directory, search_term, language):
    results = []
    
    try:
        # Walk through all subdirectories in the language-specific folder
        for root, _, files in os.walk(directory):
            for filename in files:
                if filename.endswith('.html'):
                    file_path = os.path.join(root, filename)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            # Use BeautifulSoup to extract text content without HTML tags
                            soup = BeautifulSoup(content, 'html.parser')
                            text_content = soup.get_text().lower()
                            
                            if search_term.lower() in text_content:
                                # Get relative path from the language directory
                                relative_path = os.path.relpath(file_path, directory)
                                created_timestamp = os.path.getctime(file_path)
                                created_date = datetime.fromtimestamp(created_timestamp).strftime('%Y-%m-%d %H:%M:%S')
                                
                                # Find a snippet of text around the search term
                                snippet = get_text_snippet(text_content, search_term.lower())
                                
                                results.append({
                                    'name': filename,
                                    'path': relative_path.replace('\\', '/'),
                                    'createdDate': created_date,
                                    'folder': os.path.dirname(relative_path).replace('\\', '/'),
                                    'snippet': snippet,
                                    'language': language
                                })
                    except Exception as e:
                        print(f"Error reading file {file_path}: {str(e)}")
                        continue
                        
    except Exception as e:
        print(f"Error searching directory: {str(e)}")
        return []
        
    return results

def get_text_snippet(content, search_term, context_length=100):
    """
    Extract a snippet of text around the search term with some context.
    """
    try:
        # Find the position of the search term
        pos = content.lower().find(search_term.lower())
        if pos == -1:
            return ""
        
        # Calculate the start and end positions for the snippet
        start = max(0, pos - context_length)
        end = min(len(content), pos + len(search_term) + context_length)
        
        # Extract the snippet
        snippet = content[start:end].strip()
        
        # Add ellipsis if we're not at the start/end of the content
        if start > 0:
            snippet = "..." + snippet
        if end < len(content):
            snippet = snippet + "..."
            
        return snippet
        
    except Exception as e:
        print(f"Error creating snippet: {str(e)}")
        return ""

# Helper function to check if a file path is within the resource directory
def is_valid_file_path(file_path, resource_path):
    return os.path.abspath(file_path).startswith(os.path.abspath(resource_path))

# Error handlers for JWT
@jwt.unauthorized_loader
def unauthorized_callback(callback):
    return jsonify({
        'error': 'Unauthorized access',
        'message': 'Missing or invalid token'
    }), 401

@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_data):
    return jsonify({
        'error': 'Token has expired',
        'message': 'Please log in again'
    }), 401

@jwt.invalid_token_loader
def invalid_token_callback(error_string):
    return jsonify({
        'error': 'Invalid token',
        'message': 'Please log in again'
    }), 401

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)