from flask import Flask, jsonify, request
from flask_cors import CORS
import json

app = Flask(__name__)
CORS(app)

@app.route("/lesson", methods=["GET"])
def lesson():
    lang = request.args.get("lang", "Bengali")
    try:
        with open("languages.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        lesson_data = data.get(lang)
        if lesson_data:
            return jsonify(lesson_data)
        else:
            return jsonify({"error": f"No data found for {lang}"}), 404
    except FileNotFoundError:
        return jsonify({"error": "languages.json not found"}), 500

if __name__ == "__main__":
    app.run(port=5000, debug=True)
