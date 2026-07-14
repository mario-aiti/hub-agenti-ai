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

# ==========================================
# 1. SUB-AGENTI SPECIALIZZATI (GENERATORI DI CONTENUTO)
# ==========================================

def sub_agente_wordpress(argomento: str) -> str:
    """Sub-Agente specializzato nella scrittura di articoli per il blog del sito web."""
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=f"Scrivi un articolo approfondito su: {argomento}",
            config=types.GenerateContentConfig(
                system_instruction=(
                    "Sei il Copywriter Senior specializzato in SEO per Visual Brand Studio. "
                    "Scrivi articoli per il blog del sito web. Struttura il testo in paragrafi con titoli chiari (H2, H3), "
                    "introduzione accattivante, corpo del testo ricco di valore e una conclusione con Call to Action. "
                    "Usa un tono professionale, autorevole ed esaustivo. Lunghezza minima: 500 parole."
                )
            )
        )
        return response.text
    except Exception as e:
        return f"Errore generazione WordPress: {str(e)}"

def sub_agente_facebook(argomento: str) -> str:
    """Sub-Agente specializzato nella creazione di post per la pagina Facebook."""
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=f"Crea un post Facebook su: {argomento}",
            config=types.GenerateContentConfig(
                system_instruction=(
                    "Sei il Social Media Manager per Facebook di Visual Brand Studio. "
                    "Crea post orientati alla community locale e alle piccole/medie imprese. "
                    "Usa un tono caloroso, diretto ed empatico. Includi spaziature pulite per facilitare la lettura, "
                    "emoji pertinenti (senza esagerare) e una domanda finale per stimolare i commenti."
                )
            )
        )
        return response.text
    except Exception as e:
        return f"Errore generazione Facebook: {str(e)}"

def sub_agente_linkedin(argomento: str) -> str:
    """Sub-Agente specializzato nella creazione di post per la pagina LinkedIn."""
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=f"Crea un post LinkedIn su: {argomento}",
            config=types.GenerateContentConfig(
                system_instruction=(
                    "Sei il Brand Strategist B2B di Visual Brand Studio. "
                    "Crea post per LinkedIn focalizzati su leadership di pensiero, dati di settore, "
                    "case history o consigli pratici per imprenditori e direttori marketing. "
                    "Usa un tono professionale, analitico e orientato al business. No fuffa, formatting asciutto."
                )
            )
        )
        return response.text
    except Exception as e:
        return f"Errore generazione LinkedIn: {str(e)}"


# ==========================================
# 2. TOOL OPERATIVI (PUBBLICAZIONE REALE VIA API)
# ==========================================

def pubblica_su_wordpress(titolo: str, contenuto_html: str):
    """Pubblica l'articolo generato direttamente sul sito WordPress tramite REST API."""
    wp_url = os.environ.get('WP_SITE_URL')  # Es: https://www.visualbrandstudio.it/wp-json/wp/v2/posts
    wp_user = os.environ.get('WP_API_USER')
    wp_password = os.environ.get('WP_API_PASSWORD') # Password applicazione generata da WP
    
    try:
        response = requests.post(
            wp_url,
            json={"title": titolo, "content": contenuto_html, "status": "draft"}, # Nasce come bozza per sicurezza
            auth=(wp_user, wp_password)
        )
        if response.status_code in [200, 201]:
            return f"Successo WordPress! Articolo salvato in bozza. ID: {response.json().get('id')}"
        return f"Errore WP: {response.status_code} - {response.text}"
    except Exception as e:
        return f"Eccezione WP: {str(e)}"

def esegui_pubblicazione_social(canale: str, testo: str):
    """Esegue l'invio fisico del post verso Facebook o Google Business Profile."""
    # Nota: Qui inseriremo le funzioni di POST a Facebook e GBP che abbiamo già testato
    if canale.lower() == "facebook":
        page_id = os.environ.get('FB_PAGE_ID')
        access_token = os.environ.get('FB_PAGE_ACCESS_TOKEN')
        url = f"https://graph.facebook.com/v21.0/{page_id}/feed"
        res = requests.post(url, data={"message": testo, "access_token": access_token})
        return f"Meta Status: {res.status_code}"
    # Quando LinkedIn sarà approvato, aggiungeremo l'if per gestire l'URN aziendale qui
    return f"Canale {canale} non configurato o non supportato"


# ==========================================
# 3. ORCHESTRATORE CENTRALE (IL DIRETTORE)
# ==========================================

@app.post("/esegui")
async def esegui_hub(richiesta: RichiestaPrompt):
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=richiesta.prompt,
            config=types.GenerateContentConfig(
                system_instruction=(
                    "Sei il Direttore Marketing Digitale di Visual Brand Studio. "
                    "Il tuo compito è analizzare la richiesta dell'utente. "
                    "Se l'utente chiede di diversificare i contenuti o pubblicare su canali specifici, "
                    "DEVI prima invocare i sub-agenti corretti (sub_agente_wordpress, sub_agente_facebook, sub_agente_linkedin) "
                    "per farti scrivere i testi su misura. "
                    "Una volta ottenuti i testi dai sub-agenti, invoca i tool di pubblicazione reali "
                    "(pubblica_su_wordpress, esegui_pubblicazione_social) per mandarli online."
                ),
                # L'orchestratore ha pieno accesso sia ai creativi (Sub-Agenti) sia ai bracci destri (Tool API)
                tools=[
                    sub_agente_wordpress, 
                    sub_agente_facebook, 
                    sub_agente_linkedin, 
                    pubblica_su_wordpress, 
                    esegui_pubblicazione_social
                ],
            ),
        )
        return {"esito": "Processo orchestrato con successo", "registro_operazioni": response.text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
