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
        Convert this Bengali text to English transliteration: "{bengali_text}"
        Provide ONLY the transliteration, no explanations.
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
    conversation_history = data.get("history", [])
    language = data.get("language", "Bengali")

    try:
        # Build conversation context
        history_text = ""
        for msg in conversation_history[-4:]:
            history_text += f"{msg['sender']}: {msg['text']}\n"

        prompt = f"""
        You are a friendly Bengali language tutor having a conversation with a student.
        
        Previous conversation:
        {history_text}
        
        Student's latest message: "{user_message}"
        
        Your task:
        1. Respond naturally in Bengali (1-2 sentences)
        2. Include English transliteration in parentheses
        3. Include English translation after a dash
        4. Ask a follow-up question to keep the conversation going
        5. Add a brief language tip at the end
        
        Format your response EXACTLY like this:
        [Bengali response] (transliteration) - [English translation]
        💡 Tip: [brief language tip]
        ❓ Follow-up: [question to continue conversation]
        
        Make sure all three parts are present and properly formatted.
        """

        ai_response = call_gemini_direct(prompt)

        # 🆕 CLEAN TRANSLITERATION FOR USER MESSAGE
        user_transliteration = ""
        user_translation = ""
        try:
            # Simple transliteration without explanations
            translit_prompt = f"""
            Convert this text to English transliteration: "{user_message}"
            Only provide the transliteration, no explanations.
            """
            user_transliteration = call_gemini_direct(translit_prompt)

            # Simple translation without explanations
            translate_prompt = f"""
            Translate this text to English: "{user_message}"
            Only provide the translation, no explanations.
            """
            user_translation = call_gemini_direct(translate_prompt)
        except Exception as e:
            print(f"Transliteration/translation error: {e}")
            user_transliteration = user_message
            user_translation = user_message

        return jsonify({
            "user_message": user_message,
            "user_transliteration": user_transliteration.strip(),
            "user_translation": user_translation.strip(),
            "ai_response": ai_response
        })

    except Exception as e:
        return jsonify({"error": f"Conversation failed: {str(e)}"}), 500

@app.route("/ask-question", methods=["POST"])
def ask_question():
    data = request.json
    question = data.get("question")

    try:
        prompt = f"""
        Student asks: "{question}"
        
        You are a Bengali language tutor. Answer the student's question helpfully and accurately.
        
        CRITICAL FORMATTING RULES:
        1. If teaching phrases/words, ALWAYS format as: Bengali (transliteration) - English meaning
        2. Keep answers concise (2-3 sentences max)
        3. Focus on practical language learning
        4. Include relevant Bengali examples when helpful
        
        Examples of good responses:
        - "To say 'thank you' in Bengali: ধন্যবাদ (dhonnobad) - thank you"
        - "The word for water is: পানি (pani) - water"
        - "In formal situations, use: আপনি (apni) - you (formal)"
        
        If the question is about Bengali culture/language, provide specific, accurate information.
        Always include the Bengali script, transliteration, and English meaning for any taught words.
        """

        answer = call_gemini_direct(prompt)

        # Improved word extraction
        extract_prompt = f"""
        Analyze this Bengali language teaching response: "{answer}"
        
        Extract ALL Bengali vocabulary words and phrases that would be useful for a language learner to save.
        Look for patterns like: [Bengali script] (transliteration) - [English meaning]
        
        Return as JSON array of objects with:
        - bengali: the Bengali word/phrase
        - transliteration: English transliteration  
        - english: English meaning
        
        Only include complete word entries that have all three components.
        If no complete word entries found, return empty array.
        
        Example format: [{{"bengali": "ধন্যবাদ", "transliteration": "dhonnobad", "english": "thank you"}}]
        
        IMPORTANT: Only return valid JSON, no other text.
        """

        try:
            extraction_result = call_gemini_direct(extract_prompt)
            extraction_result = extraction_result.strip()
            # Clean up JSON response
            if extraction_result.startswith('```json'):
                extraction_result = extraction_result.replace('```json', '').replace('```', '')
            elif extraction_result.startswith('```'):
                extraction_result = extraction_result.replace('```', '')

            extracted_words = json.loads(extraction_result)
        except Exception as e:
            print(f"Word extraction error: {e}")
            print(f"Raw extraction result: {extraction_result}")
            extracted_words = []

        return jsonify({
            "question": question,
            "answer": answer,
            "extracted_words": extracted_words
        })

    except Exception as e:
        return jsonify({"error": f"Question failed: {str(e)}"}), 500

if __name__ == "__main__":
    print("🚀 Starting Clean Response Bengali Tutor...")
    print(f"🔑 API Key Loaded: {bool(GEMINI_API_KEY)}")
    app.run(port=5001, debug=True)