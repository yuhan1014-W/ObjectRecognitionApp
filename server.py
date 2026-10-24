from flask import Flask, request, jsonify
from google import genai
from google.genai import types
import logging
import os

app = Flask(__name__)
logger = logging.getLogger(__name__)

@app.route('/analyze', methods=['POST'])
def analyze():
    if 'image' not in request.files:
        return jsonify({"error": "No image provided"}), 400
    
    image_file = request.files['image']
    target_language = request.form.get('language', 'Spanish')
    
    try:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            logger.error("GEMINI_API_KEY is not configured")
            return jsonify({"error": "The analysis service is not configured. Set GEMINI_API_KEY in the backend environment."}), 503

        image_bytes = image_file.read()
        
        # Prompt strictly requesting all 6 required fields
        prompt = f"""
        Analyze this image. Provide the response strictly using these exact prefixes:
        English Name: [The name of the object in English]
        Translated Name: [The name of the object translated into {target_language}]
        English Definition: [A definition or description of the object in English]
        Translated Definition: [The definition or description of the object translated into {target_language}]
        English Background: [Background facts or information about the object in English]
        Translated Background: [Background facts or information about the object translated into {target_language}]
        """
        
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                prompt,
                types.Part.from_bytes(
                    data=image_bytes,
                    mime_type=image_file.content_type or "image/jpeg",
                ),
            ],
        )
        
        raw_text = response.text.strip()
        
        # Initialize fallback values
        english_name = "Unknown Object"
        translated_name = "Unknown"
        english_definition = "Not available"
        translated_definition = "Not available"
        english_background = "Not available"
        translated_background = "Not available"
        
        # Parse Gemini's output line by line
        for line in raw_text.split('\n'):
            if line.startswith("English Name:"):
                english_name = line.replace("English Name:", "").strip()
            elif line.startswith("Translated Name:"):
                translated_name = line.replace("Translated Name:", "").strip()
            elif line.startswith("English Definition:"):
                english_definition = line.replace("English Definition:", "").strip()
            elif line.startswith("Translated Definition:"):
                translated_definition = line.replace("Translated Definition:", "").strip()
            elif line.startswith("English Background:"):
                english_background = line.replace("English Background:", "").strip()
            elif line.startswith("Translated Background:"):
                translated_background = line.replace("Translated Background:", "").strip()

        return jsonify({
            "english_name": english_name,
            "translated_name": translated_name,
            "english_definition": english_definition,
            "translated_definition": translated_definition,
            "english_background": english_background,
            "translated_background": translated_background
        })

    except Exception as e:
        logger.exception("Gemini image analysis failed")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(port=5000, debug=True)