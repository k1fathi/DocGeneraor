import os
import base64
from flask import Flask, request, jsonify
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

MODEL_NAME = "gpt-4o-mini"

DEFAULT_PROMPT = "Provide detailed instructions on how to use each item effectively in this image. Include specific examples and step-by-step guides to ensure clarity and ease of use in HTML format"

def analyze_image(image_source, is_url=False, prompt=DEFAULT_PROMPT):
    if is_url:
        image_url = image_source
    else:
        image_base64 = base64.b64encode(image_source.read()).decode('utf-8')
        image_url = f"data:image/jpeg;base64,{image_base64}"

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": image_url
                            }
                        }
                    ]
                }
            ],
            max_tokens=300
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"An error occurred: {str(e)}"

def ensure_dir_exists(path):
    os.makedirs(path, exist_ok=True)

@app.route('/analyze_image', methods=['POST'])
def analyze_image_endpoint():
    prefix = request.form.get('prefix', 'output')
    output_path = request.form.get('output_path', '')
    prompt = request.form.get('prompt', DEFAULT_PROMPT)

    if 'image' in request.files:
        image_file = request.files['image']
        if image_file.filename == '':
            return jsonify({"error": "No selected image file"}), 400
        analysis_content = analyze_image(image_file, is_url=False, prompt=prompt)
    elif 'image_url' in request.form:
        image_url = request.form['image_url']
        analysis_content = analyze_image(image_url, is_url=True, prompt=prompt)
    else:
        return jsonify({"error": "No image file or URL provided"}), 400

    if output_path:
        output_path = os.path.normpath(output_path)
        ensure_dir_exists(output_path)
        filename = os.path.join(output_path, f"{prefix}_en.html")
    else:
        filename = f"{prefix}_en.html"

    with open(filename, 'w', encoding='utf-8') as f:
        f.write(analysis_content)

    return jsonify({"message": f"Analysis complete. Results saved to {filename}", "content": analysis_content})

if __name__ == '__main__':
    app.run(debug=True)