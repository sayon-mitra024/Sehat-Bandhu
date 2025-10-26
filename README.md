# 🩺 Sehat Bandhu - AI Health Companion

[![Project Status](https://img.shields.io/badge/Status-SIH%202025%20Submission-blue.svg)](https://sih.gov.in/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Author](https://img.shields.io/badge/Author-Your%20Name-7d3cff.svg)]()
[![Built With](https://img.shields.io/badge/Tech-Flask%2C%20Gemini%2C%20gTTS%2C%20SQLite-orange.svg)]()

## 💡 Project Overview and Purpose

**Sehat Bandhu** (meaning "Health Friend") is a comprehensive, AI-powered health assistant designed to democratize access to basic medical information. Developed as a solution for the Smart India Hackathon (SIH 2025), the project addresses critical barriers to healthcare—**language diversity** and the need for **instant, reliable information**.

The core purpose is to provide an accessible, 24/7 consultation platform that can communicate with users in their native language and issue critical safety warnings for serious symptoms, seamlessly integrating generative AI with a structured knowledge base.

---

## ✨ Key Technical Achievements

This project, developed entirely by a single author, demonstrates advanced, full-stack integration focusing on accessibility and resilience:

1.  **Hybrid Knowledge Architecture:** Implements a two-tier information retrieval system:
    * **Tier 1 (Speed):** Uses a **SQLite3** database for lightning-fast retrieval of official, pre-verified FAQs and quick-response data.
    * **Tier 2 (Intelligence):** Integrates the **Google Gemini Pro API** for sophisticated reasoning, complex query handling, and generating context-aware advice when the database fails to provide a direct match.
2.  **Full Multilingual Bi-Directional Pipeline:** The system automatically detects the user's input language, translates it to English for reliable backend processing, and then translates the final, sanitized response back to the user's native tongue.
3.  **End-to-End Audio Functionality (TTS/STT):**
    * **Text-to-Speech (TTS):** The Flask backend generates audio using `gTTS`, which is **Base64-encoded** and streamed to the frontend via JSON for automatic, instantaneous playback.
    * **Speech-to-Text (STT):** Utilizes the native Web Speech API for hands-free voice input, enhancing accessibility.
4.  **Integrated Safety Protocol:** Employs **SpaCy** and keyword matching to screen for serious medical symptoms (e.g., "chest pain," "difficulty breathing"), overriding the normal flow to issue immediate, non-diagnostic **emergency disclaimers** and contact prompts.

---

## 💻 Code Analysis and Developer's Guide

This guide details the purpose of each file and highlights the key functional blocks, which is crucial for reviewers spending limited time with the codebase.

### 1. `app.py` (Backend Logic & API - Flask/Python)

This is the **controller and business logic hub**. When reading the code, focus on the defined pipeline within the `/chat` route.

| Section (Function Name) | Purpose | Key Technical Focus |
| :--- | :--- | :--- |
| **Setup & Utilities** | Initialization, constants, and helper functions like `normalize_text` and `sanitize_text`. | **Input Sanitization** using regex (`re`) is vital to cleaning user and AI-generated text. |
| **Database Functions** | `setup_database`, `fetch_from_db`, `save_to_db`. Handles SQLite persistence and lookups. | Implements **Fuzzy Search** (`difflib`) to ensure high-recall from the internal FAQ database. |
| **Safety Logic** | `is_medical_query` & `has_serious_symptoms`. | **Critical Safety Logic**; checks against a predefined list of high-risk keywords using **SpaCy** to ensure non-diagnostic warnings are prioritized. |
| **`get_bot_response` (The Core)** | Orchestrates the full query flow: **Translate User Query** $\rightarrow$ **DB Check** $\rightarrow$ **Gemini Call** $\rightarrow$ **Translate Bot Response**. | The central **Orchestration** point for multilingual, hybrid AI resolution. |
| **`/chat` Route** | The primary API endpoint. | **Audio Encoding:** Responsible for converting the `gTTS` audio stream into a **Base64 string** for transport within the JSON response. |

### 2. `sehatBandhu.html` (Frontend Interface - HTML/JS)

This is the presentation layer, focused on user interaction, voice input, and audio playback management.

| Section | Purpose | Key Technical Focus |
| :--- | :--- | :--- |
| **`<script>` Block: `sendMessage()`** | The core AJAX function. It sends the user text to the backend and **extracts both the `response` text and the `audio` Base64 string** from the JSON response. | **Response Processing:** Retrieves and handles the hybrid text/audio data structure from the Flask server. |
| **`<script>` Block: `playAudio()`** | Decodes the Base64 audio string received from the backend, creates an **in-memory Audio object** (`new Audio()`), and initiates playback. | **Base64 Decoding and Playback:** Direct, client-side handling of the audio stream. |
| **Speech Recognition** | Integration of `window.SpeechRecognition` (Web Speech API). | **Accessibility:** Manages the microphone state and converts user speech into text input. |

### 3. `STYLE.CSS` (Styling - CSS3)

Provides a modern, professional, and responsive aesthetic.

| Section | Purpose | Key Technical Focus |
| :--- | :--- | :--- |
| **Chatbot Styling** | Styles the chat bubbles, input, and buttons. | Includes the **CSS animation** (`@keyframes pulse`) for the microphone button, providing crucial visual feedback when the microphone is active. |
| **Responsiveness** | Uses media queries (`@media (max-width:768px)`) to optimize the layout. | Ensures the application is functional and aesthetically pleasing across all device sizes.

---

## 🛠️ Installation and Execution

To run the project locally, you will need to set up a Python environment and acquire the necessary API key.

### Prerequisites

1.  **Python 3.8+**
2.  A **Google Gemini API Key**

### Setup Steps

1.  **Clone the Repository:**
    ```bash
    git clone [https://github.com/sayon-mitra024/Sehat-Bandhu](https://github.com/sayon-mitra024/Sehat-Bandhu)
    cd Sehat-Bandhu
    ```

2.  **Environment Setup:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # Windows: venv\Scripts\activate
    ```

3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    python -m spacy download en_core_web_sm
    ```
    *(Note: Create a `requirements.txt` file listing all dependencies: `flask`, `flask-cors`, `googletrans`, `spacy`, `requests`, and `gtts`.)*

4.  **Configure API Key:**
    Set your Gemini API Key as an environment variable (`GEMINI_API_KEY`) for secure operation.

5.  **Run the Flask Server:**
    ```bash
    python app.py
    ```
    The application will launch on `http://127.0.0.1:5000/`.

6.  **Access the Application:**
    Open the `sehatBandhu.html` file in your web browser and click **Start Chat** to begin interacting.

---

## 👤 Author and Contact

This project was conceived, designed, and developed entirely by a single author.

**Author:** **Sayon Mitra**

* **Email:** sayonmitraoffical@gmail.com
* **GitHub:** https://github.com/sayon-mitra024
* **LinkedIn:** https://www.linkedin.com/in/sayonmitra

I welcome feedback, inquiries, and collaboration proposals regarding this solution.
