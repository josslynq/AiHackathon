from flask import Flask, jsonify, request
from flask_cors import CORS
import json
import requests
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def call_gemini_direct(prompt):
    """Call Gemini with the correct model name"""
    if not GEMINI_API_KEY:
        raise Exception("No Gemini API key found")

    model = "gemini-2.0-flash"
    url = f"https://generativelanguage.googleapis.com/v1/models/{model}:generateContent?key={GEMINI_API_KEY}"

    headers = {'Content-Type': 'application/json'}
    data = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }

    response = requests.post(url, headers=headers, json=data, timeout=10)
    if response.status_code == 200:
        result = response.json()
        return result['candidates'][0]['content']['parts'][0]['text']
    else:
        raise Exception(f"Gemini API error: {response.status_code} - {response.text}")

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

@app.route("/analyze-pronunciation", methods=["POST"])
def analyze_pronunciation():
    data = request.json
    spoken_text = data.get("spoken_text")
    target_word = data.get("target_word")
    target_transliteration = data.get("target_transliteration")
    target_meaning = data.get("target_meaning")

    try:
        prompt = f"""
        As a Bengali pronunciation coach, give brief feedback (1-2 sentences max):

        Target: {target_word} ({target_transliteration})
        Student said: "{spoken_text}"

        Focus on one specific improvement. Keep it very short.
        """

        ai_feedback = call_gemini_direct(prompt)

        return jsonify({
            "feedback": ai_feedback,
            "spoken_text": spoken_text
        })

    except Exception as e:
        return jsonify({
            "feedback": f"You said: {spoken_text}",
            "spoken_text": spoken_text,
            "error": str(e)
        })

@app.route("/transliterate", methods=["POST"])
def transliterate():
    data = request.json
    bengali_text = data.get("bengali_text")

    try:
        prompt = f"""
        Convert to English transliteration: "{bengali_text}"
        Only output transliteration, no explanations.
        """

        transliteration = call_gemini_direct(prompt)

        return jsonify({
            "original": bengali_text,
            "transliteration": transliteration
        })

    except Exception as e:
        return jsonify({
            "original": bengali_text,
            "transliteration": f"[Fallback: {bengali_text}]",
            "error": str(e)
        })

@app.route("/conversation-practice", methods=["POST"])
def conversation_practice():
    data = request.json
    user_message = data.get("message")
    language = data.get("language", "Bengali")

    try:
        prompt = f"""
        You are a Bengali tutor. Student said: "{user_message}"
        
        Respond in Bengali with transliteration and brief translation.
        Keep response under 2 sentences. Be concise.
        """

        ai_response = call_gemini_direct(prompt)

        return jsonify({
            "user_message": user_message,
            "ai_response": ai_response
        })

    except Exception as e:
        return jsonify({"error": f"Conversation failed: {str(e)}"}), 500

# 🆕 FIXED QUESTION ROUTE - SHORT RESPONSES
@app.route("/ask-question", methods=["POST"])
def ask_question():
    data = request.json
    question = data.get("question")

    try:
        prompt = f"""
        Student asks: "{question}"
        
        Give a SHORT answer (2-3 sentences max). 
        If teaching a phrase, format as:
        Bengali (transliteration) - English
        
        No long explanations. Be direct and concise.
        """

        answer = call_gemini_direct(prompt)

        return jsonify({
            "question": question,
            "answer": answer
        })

    except Exception as e:
        return jsonify({"error": f"Question failed: {str(e)}"}), 500

if __name__ == "__main__":
    print("🚀 Starting Fixed Bengali Tutor...")
    print(f"🔑 API Key Loaded: {bool(GEMINI_API_KEY)}")
    app.run(port=5001, debug=True)