from flask import Flask, request, jsonify
import google.generativeai as genai
import os

app = Flask(__name__)

# Configure your Gemini API key directly or via environment variable
# Replace "YOUR_API_KEY_HERE" with your actual Gemini API key
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

@app.route('/analyze', methods=['POST'])
def analyze():
    if 'image' not in request.files:
        return jsonify({"error": "No image provided"}), 400
    
    image_file = request.files['image']
    target_language = request.form.get('language', 'Spanish')
    
    try:
        image_bytes = image_file.read()
        
        # Use Gemini Flash for fast visual analysis
        model = genai.GenerativeModel('gemini-3.8-flash')
        
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
        
        response = model.generate_content([
            prompt,
            {"mime_type": image_file.content_type or "image/jpeg", "data": image_bytes}
        ])
        
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
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(port=5000, debug=True)