import os
import base64
import re
from flask import Flask, request, jsonify
from openai import OpenAI
from dotenv import load_dotenv
from whoosh.index import open_dir
from whoosh.qparser import QueryParser
from whoosh.index import create_in, open_dir
from whoosh.fields import *
from whoosh.qparser import QueryParser
from bs4 import BeautifulSoup
from datetime import datetime



load_dotenv()

app = Flask(__name__)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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
docs_dir = os.path.join("C:", "K1", "projects", "zuzzuu_app", "docs", "New Docs")
for root, dirs, files in os.walk(docs_dir):
    for file in files:
        if file.endswith(".html"):
            file_path = os.path.join(root, file)
            with open(file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            writer = index.writer()
            writer.add_document(title=file, path=file_path, content=html_content)
            writer.commit()

@app.route('/search1', methods=['GET'])
def search():
    # Get the search query from the URL parameters
    search_query = request.args.get('q')
    if not search_query:
        return jsonify({"error": "Please provide a search query using the 'q' parameter."}), 400

    # Perform the search using Whoosh
    results_list = []
    with index.searcher() as searcher:
        query = QueryParser("content", index.schema).parse(search_query)
        results = searcher.search(query)

        # Collect the results into a list of dictionaries
        for result in results:
            results_list.append({
                'title': result['title'],
                'path': result['path']
            })

    # Return the search results as a JSON response
    return jsonify({"results": results_list})

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

@app.route('/api/search', methods=['GET'])
def search_endpoint():
    search_term = request.args.get('q')
    directory = request.args.get('dir', 'C:\\K1\\projects\\zuzzuu_app\\docs\\New Docs\\all')  # Default directory
    
    if not search_term:
        return jsonify({"error": "No search term provided"}), 400
    
    results = search_html_files(directory, search_term)
    return jsonify({"results": results})

@app.route('/api/files', methods=['GET'])
def get_files():
    directory = r"C:\K1\projects\zuzzuu_app\docs\New Docs\all"
    files = []
    for filename in os.listdir(directory):
        if filename.endswith('.html'):
            file_path = os.path.join(directory, filename)
            created_timestamp = os.path.getctime(file_path)
            created_date = datetime.fromtimestamp(created_timestamp).strftime('%Y-%m-%d %H:%M:%S')
            files.append({
                'name': filename,
                'createdDate': created_date
            })
    return jsonify(files)

if __name__ == '__main__':
    app.run(debug=True)