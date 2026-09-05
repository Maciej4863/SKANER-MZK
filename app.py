import streamlit as st
import datetime
import json
import google.generativeai as genai
from PIL import Image

st.set_page_config(page_title="Skaner MZK Starogard", layout="centered")
st.title("🚌 Skaner Biletów MZK")

# Twój klucz API Google Gemini
GEMINI_API_KEY = "AQ.Ab8RN6LX29rai6JtXSiuexR_ySO8JU0kWq0AGovQXnx5EMEfJA"

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

if "control_start_time" not in st.session_state:
    st.session_state.control_start_time = None

if st.session_state.control_start_time is None:
    if st.button("🚨 ROZPOCZNIJ KONTROLĘ", use_container_width=True, type="primary"):
        st.session_state.control_start_time = datetime.datetime.now()
        st.rerun()
    st.info("Kliknij po ruszeniu autobusu z przystanku.")
else:
    col_info, col_btn = st.columns([2, 1])
    with col_info:
        st.success(f"⏱️ Start kontroli: **{st.session_state.control_start_time.strftime('%H:%M:%S')}**")
    with col_btn:
        if st.button("🏁 ZAKOŃCZ", use_container_width=True, type="secondary"):
            st.session_state.control_start_time = None
            st.rerun()

st.divider()

if st.session_state.control_start_time is not None:
    picture = st.camera_input("Zrób zdjęcie biletu")

    if picture:
        image = Image.open(picture)
        
        now = datetime.datetime.now()
        start_time_str = st.session_state.control_start_time.strftime("%Y-%m-%d %H:%M:%S")
        current_time_str = now.strftime("%Y-%m-%d %H:%M:%S")

        prompt = f"""
        Jesteś precyzyjnym skanerem biletów MZK Starogard Gdański.
        
        DANE SYSTEMOWE KONTROLI:
        - Czas rozpoczęcia kontroli: {start_time_str}
        - Aktualny czas: {current_time_str}
        
        FORMATY NADRUKÓW MZK STAROGARD GDAŃSKI:
        1. Kasownik igłowy: Pionowy nadruk po prawej stronie w zielonej strzałce.
           Ciąg znaków zawiera datę i godzinę DDMMYY HH:MM (np. '190826 17:16' oznacza 19.08.2026 godzina 17:16).
        2. Bilet z biletomatu: Poziomy nadruk na środku biletu.
           Format: YYYY.MM.DD HH:MM (np. '2026.08.21 19:07').
        
        ZASADY WERYFIKACJI:
        - Weryfikacja 1: Bilet jest NIEWAŻNY (wazny: false), jeśli godzina skasowania jest PÓŹNIEJSZA niż czas rozpoczęcia kontroli ({start_time_str}).
        - Weryfikacja 2: Bilet jest NIEWAŻNY (wazny: false), jeśli od skasowania do teraz ({current_time_str}) minęło więcej niż 60 minut.
        
        Zwróć ODPOWIEDŹ WYŁĄCZNIE w czystym formacie JSON bez znaczników markdown:
        {{
            "wazny": true,
            "data_skasowania": "YYYY-MM-DD HH:MM",
            "kod_kasownika": "numer lub biletomat",
            "powod": "Krótkie wyjaśnienie po polsku"
        }}
        """

        with st.spinner("Odczytywanie nadruku MZK..."):
            try:
                response = model.generate_content([prompt, image])
                text_response = response.text.strip()
                
                if text_response.startswith("```json"):
                    text_response = text_response[7:-3].strip()
                elif text_response.startswith("```"):
                    text_response = text_response[3:-3].strip()

                result = json.loads(text_response)

                if result["wazny"]:
                    st.success("🟢 BILET WAŻNY")
                    st.write(f"**Odczytana data:** {result['data_skasowania']}")
                    st.write(f"**Kasownik/Urządzenie:** {result['kod_kasownika']}")
                else:
                    st.error("🔴 BILET NIEWAŻNY – WYPISZ MANDAT")
                    st.write(f"**Powód:** {result['powod']}")
                    st.write(f"**Odczytana data:** {result['data_skasowania']}")

            except Exception as e:
                st.error(f"Błąd analizy obrazu: {e}")
