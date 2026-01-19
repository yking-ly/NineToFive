from flask import Flask, jsonify
from flask_cors import CORS
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

if __name__ == '__main__':
    app.run(debug=True, port=5000)
