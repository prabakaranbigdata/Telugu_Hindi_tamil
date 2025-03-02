from flask import Flask, render_template, request
import pytesseract
import cv2  # ✅ Import OpenCV
from PIL import Image
from googletrans import Translator
from indic_transliteration import sanscript
from indic_transliteration.sanscript import transliterate, IAST, HK, DEVANAGARI
from indic_transliteration import sanscript
from indic_transliteration.sanscript import transliterate
import os

import pandas as pd


app = Flask(__name__)

# ✅ Now OpenCV will work correctly in your code!


lang_map = {
    "Telugu": ("te", sanscript.TELUGU),
    "Hindi": ("hi", sanscript.DEVANAGARI),
    "Tamil": ("ta", sanscript.TAMIL),
}

# ✅ Your app should work fine now!


# 🔹 Image Preprocessing for Better OCR
def preprocess_image(image_path):
    image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    image = cv2.resize(image, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)  
    _, thresh = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)  
    return thresh

# 🔹 Extract Text using Tesseract OCR
def extract_text(image, lang_code):
    print(f"📝 Performing OCR (Language: {lang_code})...")
    #hi
    custom_config = f"--psm 4 -l tel"  # Improved OCR settings
    text = pytesseract.image_to_string(image, config=custom_config).strip()
    
    print(f"✅ Raw OCR Output: {text}") 
    return text

def extract_text_hindi(image, lang_code):
    print(f"📝 Performing OCR (Language: {lang_code})...")
    #hi
    custom_config = f"--psm 6 -l hin"  # Improved OCR settings
    text = pytesseract.image_to_string(image, config=custom_config).strip()
    
    print(f"✅ Raw OCR Output: {text}")
    return text

# 🔹 Transliteration & Translation
def get_transliterations(words, source_language):
    translator = Translator()
    print(f"🔹 Translating with HERE ------- source language: {source_language}")
    lang_code = lang_map.get(source_language, "auto")  # Fetch the language code from dropdown

    print(f"🔹 Translating with source language: {lang_code}")
    print(f"🔹 Translating with source language: {source_language}")

    output_data = []
    for word in words:
        tamil_meaning = "N/A"
        english_meaning = "N/A"
        english_transliteration = transliterate(word, source_language, IAST)  # ✅ Generate English Phonetics
        if source_language == "devanagari":
            tamil_transliteration = transliterate(word, sanscript.DEVANAGARI, sanscript.TAMIL)
           # tamil_transliteration = tamil_transliteration.replace("ஶ", "ச") 
        else: 
            tamil_transliteration = transliterate(word, sanscript.TELUGU, sanscript.TAMIL)
            tamil_transliteration = tamil_transliteration.replace("ஶ", "ச") 
        
        try:
           # tamil_meaning = translator.translate(word, src=lang_code, dest="ta").text  # ✅ Tamil Meaning
           if source_language == "devanagari":
                print(f"🔍 Hindi -------------devanagari-----------Extracted source_language: {source_language}")
                tamil_meaning = translate_to_tamil(word)  # Call Hindi-specific function
                english_meaning = translator.translate(word, src=lang_code, dest="en").text  # ✅ English Meaning
           else:
                print(f"🔍 Telugu ------------------------Extracted source_language: {source_language}")
                tamil_meaning = translator.translate(word, src="te", dest="ta").text
                english_meaning = translator.translate(word, src=lang_code, dest="en").text  # ✅ English Meaning
            
           print(f"✅ Translated '{word}' → Tamil: {tamil_meaning}, English: {english_meaning}, Phonetic: {english_transliteration}")
        except Exception as e:
            print(f"❌ Translation Error for '{word}': {e}")

        #output_data.append([word, english_transliteration, tamil_meaning, english_meaning])
        output_data.append([word, tamil_transliteration, tamil_meaning, english_transliteration, english_meaning])
        print("DEBUG: Output Data Structure ->", output_data)
    return output_data

correction_dict = {
    "के": "க்கு",
    "और": "மற்றும்",
    "भाषा": "மொழி",
}

def translate_to_tamil(word):
    translator = Translator()
    return correction_dict.get(word, translator.translate(word, src="hi", dest="ta").text)

    
@app.route("/", methods=["GET", "POST"])
def index():
    output_data = []

    if request.method == "POST":
        source_lang = request.form.get("language")
        uploaded_file = request.files.get("file")

        print(f"🔹 Received Language: {source_lang}")
        if source_lang not in lang_map:
            return "Error: Invalid source language", 400  

        tesseract_lang, translit_lang = lang_map[source_lang]

        if uploaded_file:
            file_path = "uploaded_image.jpg"
            uploaded_file.save(file_path)

            preprocessed_image = preprocess_image(file_path)
            print(f"🔍 Extracted tesseract_lang: {tesseract_lang}")
            
            if tesseract_lang == "hi":
                print(f"🔍 Hindi ------------------------Extracted tesseract_lang: {tesseract_lang}")
                extracted_text = extract_text_hindi(preprocessed_image, tesseract_lang)  # Call Hindi-specific function
                lang_code = "hi"  # Force Hindi
            else:
                extracted_text = extract_text(preprocessed_image, tesseract_lang)
                lang_code = "auto"  
            print(f"🔍 Extracted tesseract_lang: {extracted_text}")
            if extracted_text:
                words = extracted_text.split()
                print(f"🔍 Extracted Words: {words}")
                print(f"🔍 Extracted Words: {translit_lang}")
                output_data = get_transliterations(words, translit_lang)

                # Save output as CSV for download
                #df = pd.DataFrame(output_data, columns=["Input Word", "Tamil Meaning", "English Meaning"])
                #df = pd.DataFrame(output_data, columns=["Input Word", "Phonetic Transliteration", "Tamil Meaning", "English Meaning"])
                df = pd.DataFrame(output_data, columns=["Input Word", "Tamil Transliteration", "Tamil Meaning", "English Transliteration", "English Meaning"])

                df.to_csv("output.csv", index=False, encoding="utf-8-sig")

    return render_template("index.html", output_data=output_data)

from flask import send_file

@app.route("/download")
def download_file():
    return send_file("output.csv", as_attachment=True)



if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5003))  # Default to port 5002 if not specified
    app.run(host="0.0.0.0", port=port, debug=True)

