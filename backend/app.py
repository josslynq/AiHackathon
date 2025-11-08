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

    # Use the available model
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

@app.route("/debug-gemini", methods=["GET"])
def debug_gemini():
    """Test if Gemini API key works"""
    test_prompt = "Hello, respond with 'AI is working!' if you can read this."

    try:
        ai_response = call_gemini_direct(test_prompt)
        return jsonify({
            "success": True,
            "api_key_exists": bool(GEMINI_API_KEY),
            "api_key_preview": GEMINI_API_KEY[:10] + "..." if GEMINI_API_KEY else "None",
            "ai_response": ai_response
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "api_key_exists": bool(GEMINI_API_KEY),
            "api_key_preview": GEMINI_API_KEY[:10] + "..." if GEMINI_API_KEY else "None",
            "error": str(e)
        })

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
        As a Bengali language pronunciation expert, analyze this student's attempt:

        TARGET WORD: {target_word}
        TRANSLITERATION: {target_transliteration} 
        MEANING: {target_meaning}
        STUDENT'S ATTEMPT: "{spoken_text}"

        Provide specific, actionable feedback on pronunciation.
        Keep it concise (2-3 sentences) and encouraging.
        Focus on vowel sounds, consonants, and rhythm.
        """

        ai_feedback = call_gemini_direct(prompt)

        return jsonify({
            "feedback": f"🤖 AI Feedback: {ai_feedback}",
            "spoken_text": spoken_text,
            "ai_used": "Gemini 2.0 Flash"
        })

    except Exception as e:
        return jsonify({
            "feedback": f"⚠️ AI unavailable. You said: {spoken_text}",
            "spoken_text": spoken_text,
            "error": str(e)
        })

@app.route("/transliterate", methods=["POST"])
def transliterate():
    data = request.json
    bengali_text = data.get("bengali_text")

    try:
        prompt = f"""
        Convert this Bengali text to English transliteration using standard romanization:
        "{bengali_text}"
        
        Provide ONLY the transliteration, no explanations or additional text.
        Be accurate with Bengali pronunciation rules.
        """

        transliteration = call_gemini_direct(prompt)

        return jsonify({
            "original": bengali_text,
            "transliteration": transliteration,
            "ai_used": "Gemini 2.0 Flash"
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
        You are a friendly {language} language tutor. The student said:
        "{user_message}"
        
        Respond naturally in {language} (with English transliteration and translation).
        Keep it short, educational, and encouraging.
        
        Format your response as:
        [Bengali Text] (transliteration) - [English Translation]
        """

        ai_response = call_gemini_direct(prompt)

        return jsonify({
            "user_message": user_message,
            "ai_response": ai_response,
            "ai_used": "Gemini 2.0 Flash"
        })

    except Exception as e:
        return jsonify({"error": f"Conversation failed: {str(e)}"}), 500

if __name__ == "__main__":
    print("🚀 Starting Bengali Tutor with Gemini 2.0 Flash...")
    print(f"🔑 API Key Loaded: {bool(GEMINI_API_KEY)}")
    app.run(port=5001, debug=True)