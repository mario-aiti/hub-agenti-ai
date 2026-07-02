from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from google import genai
from google.genai import types
import os
import requests

app = FastAPI()
client = genai.Client()

class RichiestaPrompt(BaseModel):
    prompt: str

def crea_post_google_business(testo_post: str):
    """Pubblica un aggiornamento di testo su Google Business Profile."""
    account_id = os.environ.get('GOOGLE_BUSINESS_ACCOUNT_ID')
    location_id = os.environ.get('GOOGLE_BUSINESS_LOCATION_ID')
    api_key = os.environ.get('GEMINI_API_KEY')
    url = f"https://mybusiness.googleapis.com/v4/accounts/{account_id}/locations/{location_id}/localPosts?key={api_key}"
    payload = {"languageCode": "it", "summary": testo_post, "topicType": "STANDARD"}
    try:
        response = requests.post(url, json=payload)
        if response.status_code in [200, 201]:
            return f"Successo GBP! ID Post: {response.json().get('name')}"
        return f"Errore GBP: {response.status_code} - {response.text}"
    except Exception as e:
        return f"Eccezione GBP: {str(e)}"

def pubblica_su_facebook(testo_post: str):
    """Pubblica un post sul feed della pagina aziendale di Facebook."""
    page_id = os.environ.get('FB_PAGE_ID')
    access_token = os.environ.get('FB_PAGE_ACCESS_TOKEN')
    
    # Protocollo ufficiale Meta Graph API v21.0 per pubblicazione feed
    url = f"https://graph.facebook.com/v21.0/{page_id}/feed"
    payload = {
        "message": testo_post,
        "access_token": access_token
    }
    try:
        response = requests.post(url, data=payload)
        if response.status_code == 200:
            return f"Successo Meta! Post pubblicato su Facebook. ID: {response.json().get('id')}"
        else:
            return f"Errore Meta API: {response.status_code} - {response.text}"
    except Exception as e:
        return f"Eccezione Meta: {str(e)}"

@app.post("/esegui")
async def esegui_agente(richiesta: RichiestaPrompt):
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=richiesta.prompt,
            config=types.GenerateContentConfig(
                system_instruction=(
                    "Sei l'Agente Direttore Marketing di Visual Brand Studio. Il tuo compito è "
                    "analizzare le richieste, strutturare strategie di comunicazione ad alto impatto per imprenditori "
                    "e utilizzare i tool a tua disposizione per pubblicare i contenuti sui canali corretti "
                    "(Google Business Profile o Facebook)."
                ),
                # Mettiamo i due muscoli reali a disposizione dell'intelligenza di Gemini
                tools=[crea_post_google_business, pubblica_su_facebook],
            ),
        )
        return {"esito_agente": "Operazione completata", "risposta": response.text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
