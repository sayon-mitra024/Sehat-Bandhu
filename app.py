import os
import re
import sqlite3
import requests
import logging
import base64  # ## ENHANCEMENT: Added for encoding audio data
import io      # ## ENHANCEMENT: Added to handle audio data in memory

from flask import Flask, request, jsonify
from flask_cors import CORS
from googletrans import Translator
import spacy
import difflib
from gtts import gTTS  # ## ENHANCEMENT: Added Google Text-to-Speech library

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# --- Constants ---
DB_PATH = "medical_data.db"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    logging.warning("GEMINI_API_KEY environment variable is not set.")

GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"
app = Flask(__name__)
CORS(app)

# [ The rest of your helper functions (normalize_text, sanitize_text, NLP, Database) remain the same ]
# ... (No changes needed for the code from line 29 to 216 in your original file)
# --- Text Helper Functions ---
def normalize_text(s: str) -> str:
    if not s:
        return ""
    s = s.lower()
    s = re.sub(r'[^a-z0-9\s]', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def sanitize_text(s: str) -> str:
    """Removes asterisks and other unwanted characters from text."""
    if not s:
        return ""
    s = s.replace('*', '')
    s = re.sub(r'[\u200b-\u200f]', '', s) # Remove zero-width characters
    s = re.sub(r'\s+', ' ', s).strip()
    return s

# --- NLP and Medical Keyword Detection ---
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    print("Spacy 'en_core_web_sm' model not found. Please run: python -m spacy download en_core_web_sm")
    nlp = None

medical_keywords = {
    'fever', 'cough', 'headache', 'diabetes', 'hypertension', 'medicine', 'symptom',
    'treatment', 'virus', 'infection', 'health', 'asthma', 'allergy', 'cancer',
    'covid', 'flu', 'pain', 'inflammation', 'nausea', 'vomiting', 'diarrhea',
    'fatigue', 'insomnia', 'depression', 'anxiety', 'arthritis', 'vaccine',
    'heart', 'lungs', 'brain', 'stomach', 'kidneys', 'doctor', 'hospital', 'clinic',
    'prescription', 'pharmacy', 'blood pressure', 'heart attack', 'stroke', 'emergency',
    'name', 'who created you', 'developer', 'team', 'about you',
    'purpose', 'goal', 'what can you do', 'features', 'capabilities',
    'book appointment', 'appointment', 'schedule', 'help',
    'india', 'indian government', 'mohfw', 'ministry of health',
    'ors', 'hospital website', 'state health portal',
    'trusted sources', 'who', 'world health organization',
    'health ministry', 'helpline', 'emergency number',
    'library', 'books', 'read', 'knowledge base'
}
serious_condition_keywords = {
    'chest pain', 'difficulty breathing', 'severe pain', 'unconscious',
    'seizure', 'heavy bleeding', 'stroke symptoms', 'suicidal', 'emergency'
}

def is_medical_query(query: str) -> bool:
    if not query or not nlp:
        return False
    q_norm = normalize_text(query)
    doc = nlp(q_norm)
    for token in doc:
        if token.lemma_ in medical_keywords:
            return True
    for keyword in medical_keywords:
        if keyword in q_norm:
            return True
    return False

def has_serious_symptoms(query: str) -> bool:
    if not query:
        return False
    q_lower = query.lower()
    for keyword in serious_condition_keywords:
        if keyword in q_lower:
            return True
    return False

# --- Database Setup and Functions ---
def setup_database():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS medical_faq (
            id INTEGER PRIMARY KEY,
            question TEXT UNIQUE NOT NULL,
            answer TEXT NOT NULL
        )
        ''')
        data = [
        ("What is COVID-19?", "According to WHO, COVID-19 is caused by the SARS-CoV-2 virus."),
    ("How does COVID-19 spread?", "WHO says it spreads mainly via respiratory droplets and close contact."),
    ("What are the symptoms of flu?", "CDC lists fever, cough, sore throat, runny nose, body aches, and fatigue."),
    ("Why is handwashing important?", "WHO explains handwashing prevents spread of infectious diseases."),
    ("How long should I wash my hands?", "CDC recommends scrubbing with soap for at least 20 seconds."),
    ("What is hypertension?", "MoHFW defines hypertension as high blood pressure ≥140/90 mmHg."),
    ("What is diabetes?", "CDC describes it as a condition with high blood sugar due to insulin problems."),
    ("What are signs of dehydration?", "WHO mentions thirst, dark urine, fatigue, dizziness, and dry mouth."),
    ("Why is exercise important?", "WHO states it reduces risk of diabetes, obesity, and heart disease."),
    ("How much sleep do adults need?", "WHO recommends 7–9 hours of quality sleep per night."),
    ("What is a balanced diet?", "WHO advises including fruits, vegetables, whole grains, protein, and limited sugar/salt."),
    ("What are sources of vitamin C?", "CDC states citrus fruits, strawberries, bell peppers, and broccoli are rich in vitamin C."),
    ("Why is fiber important?", "WHO explains fiber aids digestion, prevents constipation, and lowers cholesterol."),
    ("What is BMI?", "WHO defines Body Mass Index as weight-for-height used to classify underweight, normal, overweight, and obesity."),
    ("What is the normal BMI range?", "WHO considers 18.5–24.9 as the healthy BMI range."),
    ("How much exercise weekly?", "WHO recommends at least 150 minutes of moderate activity per week."),
    ("What are healthy snacks?", "WHO suggests fruits, nuts, yogurt, and whole-grain crackers."),
    ("What is tuberculosis?", "WHO says TB is a bacterial infection that mainly affects the lungs."),
    ("How can HIV be prevented?", "WHO recommends safe sex, regular testing, and antiretroviral therapy."),
    ("What is hepatitis B?", "CDC defines it as a viral infection of the liver, preventable by vaccination."),
    ("What is dengue?", "WHO describes it as a mosquito-borne viral infection causing fever, rash, and pain."),
    ("How to prevent cholera?", "WHO advises safe water, good sanitation, and vaccination in risk areas."),
    ("What is measles?", "WHO states measles is a highly contagious viral disease preventable by vaccine."),
    ("What are early signs of stroke?", "CDC lists sudden numbness, confusion, trouble speaking, and vision issues."),
    ("How to lower cholesterol naturally?", "WHO recommends reducing saturated fats, exercising, and eating more fiber."),
    ("What causes osteoporosis?", "WHO notes low calcium, vitamin D deficiency, aging, and lack of exercise."),
    ("What are symptoms of asthma?", "CDC mentions wheezing, coughing, chest tightness, and shortness of breath."),
    ("How to prevent cancer?", "WHO advises avoiding tobacco, alcohol, unhealthy diet, and staying active."),
    ("What is PTSD?", "WHO defines Post-Traumatic Stress Disorder as triggered by traumatic events."),
    ("What is ADHD?", "CDC explains it as a brain disorder affecting attention and behavior."),
    ("How to reduce exam stress?", "WHO suggests proper sleep, time management, and relaxation techniques."),
    ("What is mindfulness?", "WHO describes it as focusing on the present moment to reduce stress."),
    ("Why is social support important?", "WHO emphasizes it improves resilience and reduces depression risk."),
    ("What are the 5 moments of hand hygiene?", "WHO lists: before patient contact, before clean procedure, after exposure risk, after contact, after surroundings."),
    ("How to prevent food poisoning?", "CDC recommends cooking food properly, avoiding cross-contamination, and refrigeration."),
    ("Why is vaccination important?", "WHO says vaccines prevent millions of deaths annually."),
    ("How to stay safe during heatwaves?", "WHO advises hydration, avoiding direct sun, and wearing light clothing."),
    ("How to stay safe during floods?", "WHO recommends avoiding contaminated water and preventing mosquito breeding."),
    ("When should a child get measles vaccine?", "WHO recommends at 9–12 months with a second dose later."),
    ("What is exclusive breastfeeding?", "WHO defines it as giving only breast milk for first 6 months."),
    ("What is Kangaroo Mother Care?", "WHO describes it as skin-to-skin contact for premature babies."),
    ("Why is vaccination during pregnancy important?", "WHO recommends tetanus and influenza vaccines to protect mother and child."),
    ("How to ensure good child nutrition?", "WHO advises breastfeeding, timely solid foods, and balanced meals."),
    ("Can antibiotics cure viral infections?", "WHO clarifies antibiotics do not work against viruses like flu or COVID-19."),
    ("Does garlic prevent COVID-19?", "WHO confirms garlic is healthy but does not prevent COVID-19."),
    ("Can vaccines cause autism?", "CDC states vaccines are safe and not linked to autism."),
    ("Does cold weather cause flu?", "WHO explains flu is caused by influenza virus, not by cold weather."),
    ("Can drinking alcohol kill coronavirus?", "WHO warns alcohol does not prevent COVID-19 and is harmful."),
    ("Why is mental health important?", "WHO emphasizes mental health is vital for overall well-being."),
    ("What are healthy ways to improve sleep?", "CDC recommends consistent sleep schedules, less screen time, and avoiding caffeine."),
    ("How to deal with depression?", "WHO advises seeking professional help, staying active, and building social support."),
    ("What is blood?", "Blood is a bodily fluid in humans and animals that delivers necessary substances such as nutrients and oxygen to cells."),
    ("What is blood pressure?", "Blood pressure is the pressure of circulating blood on the walls of blood vessels."),
    ("What is the name of this chatbot?", "My name is Sehat Bandhu 🩺, your AI-powered health assistant."),
    ("Who created you?", "I was created by  — the  students of India’s first AI-augmented multidisciplinary university, Chandigarh University (Uttar Pradesh Campus).\n\nOur team is called  Pragati Wave.\n\n Team Leader: Sayon Mitra\n Team Members :\n- Satyam Singh\n- Anmol Yadav\n- Kanika Singh\n- Kumar Anand\n- Vijwal Sonkar"),
    ("What can you do?", "I can answer medical-related questions, provide guidance, and help you find trusted health resources."),
    ("Are you a doctor?", "⚠️ No, I am not a doctor. I provide AI-generated information for guidance only. For serious conditions, consult a qualified healthcare professional."),
    ("Can you book an appointment?", "Yes ✅ I can guide you to book an appointment. Please use this link: https://ors.gov.in/copp/ for central government hospitals."),
    ("Book appointment in Uttar Pradesh", "Please visit the state health portal: https://uphealth.up.nic.in for booking an appointment in Uttar Pradesh."),
    ("Book appointment in Delhi", "You can book your appointment here: https://dshm.delhi.gov.in"),
    ("What are your trusted sources?", "I use WHO, Ministry of Health & Family Welfare (India), and other government/trusted medical websites as references."),
    ("What is your purpose?", "My purpose is to provide quick, reliable, and accessible medical information to everyone."),
    ("Can you give emergency advice?", "⚠️ In case of an emergency like chest pain, unconsciousness, or heavy bleeding, please call your local emergency number immediately (e.g., 108 in India).")
  ]
        try:
            cursor.executemany("INSERT OR IGNORE INTO medical_faq (question, answer) VALUES (?, ?)", data)
            conn.commit()
        except sqlite3.Error as e:
            logging.error("Database insert error: %s", e)

def fetch_from_db(query: str):
    if not query: return None
    q_norm = normalize_text(query)
    try:
        with sqlite3.connect(DB_PATH, timeout=10) as conn:
            cur = conn.cursor()
            cur.execute("SELECT answer FROM medical_faq WHERE lower(question)=? LIMIT 1", (query.lower(),))
            r = cur.fetchone()
            if r: return r[0]
            cur.execute("SELECT answer FROM medical_faq WHERE lower(question) LIKE ? LIMIT 1", ('%' + query.lower() + '%',))
            r = cur.fetchone()
            if r: return r[0]
            cur.execute("SELECT question, answer FROM medical_faq")
            rows = cur.fetchall()
            if not rows: return None
            questions = [row[0] for row in rows]
            norm_questions = [normalize_text(q) for q in questions]
            matches = difflib.get_close_matches(q_norm, norm_questions, n=1, cutoff=0.7)
            if matches:
                idx = norm_questions.index(matches[0])
                return rows[idx][1]
    except sqlite3.Error as e:
        logging.error("Database fetch error: %s", e)
    return None

def save_to_db(question: str, answer: str):
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT OR IGNORE INTO medical_faq (question, answer) VALUES (?, ?)", (question, answer))
            conn.commit()
    except sqlite3.Error as e:
        logging.error("Failed to save new entry to DB: %s", e)

# --- Translation and API Services ---
translator = Translator()

def translate_text(text, dest_lang, src_lang='auto'):
    if not text:
        return "", "en"
    try:
        translated = translator.translate(text, dest=dest_lang, src=src_lang)
        detected_lang = translated.src if hasattr(translated, 'src') else 'en'
        return translated.text, detected_lang
    except Exception as e:
        logging.warning("Translation failed: %s. Falling back.", e)
        return text, 'en'

def fetch_from_gemini(query: str):
    if not GEMINI_API_KEY:
        logging.error("GEMINI_API_KEY not available for Gemini API call.")
        return None
    prompt = (f"Please answer the following medical question clearly and concisely. "
              f"Do not provide a diagnosis. The question is: '{query}'")
    headers = {'Content-Type': 'application/json'}
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    url = f"{GEMINI_API_URL}?key={GEMINI_API_KEY}"
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=15)
        response.raise_for_status()
        data = response.json()
        candidates = data.get("candidates", [])
        if candidates:
            text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
            return sanitize_text(text)
    except Exception as e:
        logging.error("Gemini API request failed or parsing failed: %s", e)
    return None

# --- Core Logic for Processing a Query ---
## ENHANCEMENT: This function now returns both the text response and the detected language.
def get_bot_response(original_text: str):
    if not original_text:
        return "Please provide a question.", "en"

    # Detect the original language and translate to English for processing
    q_en, original_lang = translate_text(original_text, 'en')
    logging.info(f"Detected language: '{original_lang}'. Processing query: '{q_en}'")

    if not is_medical_query(q_en):
        response_en = "I am a medical assistant and can only answer health-related questions."
        # Translate the fixed response back to the user's original language
        final_response, _ = translate_text(response_en, original_lang)
        return final_response, original_lang

    answer_en = fetch_from_db(q_en)
    source = "Database"
    
    if not answer_en:
        logging.info("No answer in DB. Querying Gemini AI...")
        answer_en = fetch_from_gemini(q_en)
        source = "Gemini AI"
        if answer_en:
            save_to_db(q_en, answer_en)

    if not answer_en:
        response_en = "I'm sorry, I couldn't find information on that topic. Please consult a qualified healthcare professional."
        final_response, _ = translate_text(response_en, original_lang)
        return final_response, original_lang

    final_answer_en = answer_en
    if has_serious_symptoms(q_en):
        final_answer_en += "\n\n**Based on your query, your symptoms could be serious. Please consult a doctor immediately.**"

    if source == "Gemini AI":
        final_answer_en += "\n\n⚠️ **Disclaimer**: I’m an AI, not a doctor. Please consult a healthcare professional for serious issues."

    # Translate the complete English answer back to the user's original language
    final_response, _ = translate_text(final_answer_en, original_lang)
    final_response = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', final_response)
    
    return final_response, original_lang

# --- Flask Route ---
@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        user_message = data.get('message')
        
        if not user_message:
            return jsonify({'error': 'No message provided'}), 400
        
        # ## ENHANCEMENT: The bot logic now automatically determines the language.
        bot_text, bot_lang = get_bot_response(user_message)
        
        audio_base64 = None
        try:
            # ## ENHANCEMENT: Generate speech from the text response.
            mp_file = io.BytesIO()
            # Use the detected language for TTS. Fallback to English if language is not supported by gTTS.
            tts = gTTS(text=bot_text.replace('<b>', '').replace('</b>', ''), lang=bot_lang, slow=False)
            tts.write_to_fp(mp_file)
            mp_file.seek(0)
            # ## ENHANCEMENT: Encode the audio to Base64 to send it in the JSON response.
            audio_base64 = base64.b64encode(mp_file.read()).decode('utf-8')
        except Exception as e:
            logging.error(f"Could not generate TTS for lang '{bot_lang}': {e}")
            # Try with English as a fallback
            try:
                mp_file = io.BytesIO()
                tts = gTTS(text=bot_text.replace('<b>', '').replace('</b>', ''), lang='en', slow=False)
                tts.write_to_fp(mp_file)
                mp_file.seek(0)
                audio_base64 = base64.b64encode(mp_file.read()).decode('utf-8')
            except Exception as fallback_e:
                logging.error(f"Fallback TTS to English also failed: {fallback_e}")
        
        # ## ENHANCEMENT: Return both the text and the audio data.
        return jsonify({'response': bot_text, 'audio': audio_base64})

    except Exception as e:
        logging.error(f"Error in /chat endpoint: {e}")
        return jsonify({'error': 'An internal server error occurred'}), 500

# --- Main Entry Point ---
if __name__ == "__main__":
    setup_database()
    app.run(debug=True, port=5000)