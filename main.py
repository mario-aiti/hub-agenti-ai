import os
import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from google import genai
from google.genai import types

app = FastAPI(title="Hub Agenti AI - Produzione")

# Configurazione API Gemini
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key) if api_key else None

# --- TOOL 1: I MUSCOLI PER WORDPRESS ---
def crea_post_wordpress(titolo: str, contenuto: str, stato: str = "draft") -> str:
    """Pubblica un articolo su WordPress usando le REST API native."""
    wp_url = os.getenv("WP_URL") # Es: https://iltuosito.com/wp-json/wp/v2
    user = os.getenv("WP_USERNAME")
    password = os.getenv("WP_APP_PASSWORD")
    
    if not wp_url or not user or not password:
        return "Errore: Credenziali WordPress mancanti nelle variabili d'ambiente."
        
    url = f"{wp_url}/posts"
    payload = {"title": titolo, "content": contenuto, "status": stato}
    
    try:
        response = requests.post(url, json=payload, auth=(user, password), timeout=10)
        if response.status_code == 201:
            return f"Successo: Articolo creato con ID {response.json().get('id')}"
        return f"Errore WP: {response.status_code} - {response.text}"
    except Exception as e:
        return f"Errore di connessione a WP: {str(e)}"

# Mappatura dei tool disponibili per l'agente
tools_disponibili = {"crea_post_wordpress": crea_post_wordpress}

class ComandoUtente(BaseModel):
    prompt: str

@app.get("/")
def check():
    return {
        "status": "online",
        "llm_connected": client is not None,
        "wp_configured": os.getenv("WP_URL") is not None
    }

@app.post("/esegui")
def esegui_agente(comando: ComandoUtente):
    if not client:
        raise HTTPException(status_code=500, detail="Chiave API Gemini mancante.")
        
    try:
        # L'agente analizza il prompt e decide se usare il tool di WordPress
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=comando.prompt,
            config=types.GenerateContentConfig(
                tools=[crea_post_wordpress],
                system_instruction=(
                    "Sei un agente esperto di Copywriting e SEO. Se l'utente ti chiede di scrivere "
                    "e pubblicare/salvare un articolo, genera il testo in HTML pulito e invocato il tool "
                    "crea_post_wordpress inserendo titolo e contenuto. Se non richiesto esplicitamente, rispondi solo al testo."
                )
            )
        )
        
        # Se il cervello decide di attivare i muscoli (chiamata a funzione)
        if response.function_calls:
            for call in response.function_calls:
                if call.name in tools_disponibili:
                    risultato_tool = tools_disponibili[call.name](**call.args)
                    return {"esito_agente": "Tool Eseguito", "dettaglio": risultato_tool}
                    
        return {"esito_agente": "Risposta Testuale", "risposta": response.text}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
