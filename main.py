from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from google import genai
from google.genai import types
import os
import requests

app = FastAPI()

# Il client inizializza automaticamente Gemini usando la variabile GEMINI_API_KEY su Render
client = genai.Client()

class RichiestaPrompt(BaseModel):
    prompt: str

def crea_post_google_business(testo_post: str):
    """
    Funzione (Tool) per pubblicare un aggiornamento di tipo Novità su Google Business Profile.
    """
    account_id = os.environ.get('GOOGLE_BUSINESS_ACCOUNT_ID')
    location_id = os.environ.get('GOOGLE_BUSINESS_LOCATION_ID')
    api_key = os.environ.get('GEMINI_API_KEY')
    
    # URL standard e documentato delle API ufficiali di Google My Business
    url = f"https://mybusiness.googleapis.com/v4/accounts/{account_id}/locations/{location_id}/localPosts?key={api_key}"
    
    payload = {
        "languageCode": "it",
        "summary": testo_post,
        "topicType": "STANDARD"
    }
    
    try:
        response = requests.post(url, json=payload)
        if response.status_code in [200, 201]:
            return f"Successo! Post pubblicato su Google Business Profile con ID: {response.json().get('name')}"
        else:
            return f"Errore API Google Business: {response.status_code} - {response.text}"
    except Exception as e:
        return f"Eccezione durante la chiamata API: {str(e)}"

@app.post("/esegui")
async def esegui_agente(richiesta: RichiestaPrompt):
    try:
        # Chiamata a Gemini 2.5 Flash con istruzioni e attivazione dei tool
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=richiesta.prompt,
            config=types.GenerateContentConfig(
                system_instruction=(
                    "Sei l'Agente Direttore Marketing di Visual Brand Studio. Il tuo compito è "
                    "analizzare le richieste dell'utente, strutturare strategie di comunicazione, "
                    "identificare parole chiave per il territorio e utilizzare il tool a disposizione "
                    "per pubblicare aggiornamenti sulla scheda Google quando l'utente ti chiede di pubblicare."
                ),
                # Mettiamo la funzione a disposizione del modello
                tools=[crea_post_google_business],
            ),
        )
        return {"esito_agente": "Operazione completata", "risposta": response.text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
