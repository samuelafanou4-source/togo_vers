from fastapi import FastAPI, File, Query, UploadFile, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import json
import io
from pydantic_settings import BaseSettings, SettingsConfigDict
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
from google import genai
from haversine import calcul_de_l_haversine
from fastapi import Security, Depends
from fastapi.security import api_key



class Settings(BaseSettings):
    gemini_api_key: str
    api_secret_key:str
    model_config = SettingsConfigDict(env_file=".env")
settings = Settings() 

app = FastAPI(title="togo_vers")

Client = genai.Client(api_key=settings.gemini_api_key)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

cle_api = "herit"
api_key_header = api_key.APIKeyHeader(name=cle_api)

with open("togo_vers.json", "r", encoding="utf-8") as fichier:
    BASE_MONUMENT = json.load(fichier)

with open("hotel.json", "r", encoding="utf-8") as fichier_hotel:
    BASE_HOTEL = json.load(fichier_hotel)


class Monument(BaseModel):
    id: int
    nom: str
    histoire: str
    latitude: float
    longitude: float

class hotel(BaseModel):
    nom: str
    latitude: float
    longitude: float
    prix_nuit: int

@app.get("/")
def read_root():
    return{"message": "Bienvenue sur l'API Togo_vers ! Le moteur est fonctionnel"}

@app.get("/monument", response_model=List[Monument])
def get_Monument():
    return BASE_MONUMENT

@app.get("/hotel")
def get_hotel_proche(lat: float = Query(..., description="Latitude du monument"), long: float = Query(..., description="Longitude du monument")):

    hotel_avec_distance = []

    for h in BASE_HOTEL:

        distances = calcul_de_l_haversine(lat, long, h["latitude"], h["longitude"])
        hotel_data = h.copy()
        hotel_data["distance_km"] = distances
        hotel_avec_distance.append(hotel_data)
    hotel_tries = sorted(hotel_avec_distance, key=lambda x: x["distance_km"])

    return hotel_tries





@app.post("/predict")
async def predict_monument(file: UploadFile = File(..., description="photo prise par le touriste")):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="le fichier doit etre une image")
    
    try:
        image_bytes = await file.read()
        image = Image.open(io.BytesIO(image_bytes))

        max_size = 1024
        image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)


        prompt = """
        Agis en tant que guide expert du Togo. Analyse cette photo touristique.
        Identifie le monument ou le lieu (ex: Monument de l'Indépendance, Colombe de la Paix, Palais de Lomé, Tata Tamberma, Grand Marché).
        
        Tu dois renvoyer TOUJOURS une histoire courte (3 lignes maximum) au cas où le lieu n'est pas dans notre base.
        
        Réponds STRICTEMENT au format JSON suivant, sans balises Markdown :
        {
          "monument": "Nom officiel du lieu",
          "histoire": "Histoire ou description culturelle rapide en français."
        }
        """

        response = Client.models.generate_content(
            model='gemini-2.5-flash',
            contents = [image, prompt]
        )

        texte_brut = response.text.strip()
        if texte_brut.startswith("```json"):
            texte_brut = texte_brut.replace("```json", "").replace("```", "").strip()
        elif texte_brut.startswith("```"):
            texte_brut = texte_brut.replace("```", "").strip()
        

        data_touristique = json.loads(texte_brut)
        data_tour = data_touristique.get("monument", "").lower()

        donnees_finales = None

        for m in BASE_MONUMENT:

            if data_tour in m["nom"].lower() or m["nom"].lower() in data_tour:
                donnees_finales = {
                    "monument": m["nom"],
                    "histoire": m["histoire"],
                    "latitude": m["latitude"],
                    "longitude": m["longitude"],
                    "source": "local_database"
                }
                break

            if not donnees_finales:
                donnees_finales = {
                "monument": data_touristique.get("monument", "Monulent inconnu"),
                "histoire": data_touristique.get("histoire", "Monument identifié au Togo. Description officielle en cours de rédaction"),
                "latitude": data_touristique.get("latitude", 6.1311),
                "longitude": data_touristique.get("longitude", 1.2227),
                "source": "ai_fallback"
                }

        return{
                "prediction_status": "success",
                "data": donnees_finales
        }
    
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Format JSON invalide gemini ne peut pas le renvoyé")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'analyse avec Gemini : {str(e)}")


