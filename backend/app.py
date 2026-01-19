from flask import Flask, jsonify, request
from flask_cors import CORS
from deep_translator import GoogleTranslator
import time
import os

app = Flask(__name__)
CORS(app)

@app.route('/')
def hello_world():
    return jsonify({"message": "Hello from Flask Backend!"})

@app.route('/api/data')
def get_data():
    # Read README.md from the parent directory
    try:
        readme_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'README.md')
        with open(readme_path, 'r', encoding='utf-8') as f:
            readme_content = f.read()
    except Exception as e:
        readme_content = f"Error reading README.md: {str(e)}"

    data = {
        "status": "success",
        "timestamp": time.time(),
        "readme": readme_content
    }
    return jsonify(data)

@app.route('/api/guide')
def get_guide():
    lang = request.args.get('lang', 'en')
    
    try:
        # Read HOW_TO_USE.md from the backend directory (current directory)
        guide_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'HOW_TO_USE.md')
        with open(guide_path, 'r', encoding='utf-8') as f:
            guide_content = f.read()
            
        if lang != 'en':
            # Translate content
            translator = GoogleTranslator(source='auto', target=lang)
            # We translate paragraph by paragraph to avoid length limits better (though deep-translator handles limits well usually)
            # Simple approach: Translate the whole thing if it's not too huge.
            # For markdown, let's just translate the whole blob.
            guide_content = translator.translate(guide_content)
            
    except Exception as e:
        guide_content = f"Error processing guide: {str(e)}"
    
    return jsonify({"content": guide_content})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
