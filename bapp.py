import os
from google import genai
# Requires the Google Gen AI SDK: python -m pip install google-genai
from google.genai import types

# Initialize the Gemini client
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

def analyze_object_bilingual(image_path, target_language):
    with open(image_path, "rb") as f:
        image_bytes = f.read()

    # Updated prompt with Definition at the top
    prompt = f"""
    Analyze the attached image and identify the main object.
    
    Please format your response clearly in this exact order:
    1. Definition: A clear, comprehensive definition explaining what the object is and what it does, provided in both English and {target_language}.
    2. English Name: The name of the object in English.
    3. Translated Name: The name of the object translated into {target_language}.
    4. Background Fact: An interesting fact about this object written in both English and {target_language}.
    """

    response = client.models.generate_content(
        model="gemini-3.8-flash",
        contents=[
            types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"),
            prompt
        ]
    )
    
    return response.text

if __name__ == "__main__":
    chosen_language = "Spanish"
    image_filename = "sample_object.jpg"
    
    print(f"Target Language: {chosen_language}")
    print("Analyzing image with Gemini...")
    
    # result = analyze_object_bilingual(image_filename, chosen_language)
    # print("\n--- AI Response ---")
    # print(result)