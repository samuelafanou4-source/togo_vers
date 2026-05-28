from fastapi import FastAPI, File, UploadFile, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import json
import io
from pydantic_settings import BaseSettings, SettingsConfigDict
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
from google import genai


class Settings(BaseSettings):
    gemini_api_key: str
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

with open("togo_vers.json", "r", encoding="utf-8") as fichier:
    BASE_MONUMENT = json.load(fichier)


class Monument(BaseModel):
    id: int
    nom: str
    histoire: str
    latitude: float
    longitude: float


@app.get("/")
def read_root():
    return{"message": "Bienvenue sur l'API Togo_vers ! Le moteur est fonctionnel"}

@app.get("/monument", response_model=List[Monument])
def get_Monument():
    return BASE_MONUMENT


@app.post("/predict")
async def predict_monument(file: UploadFile = File(..., description="photo prise par le touriste")):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="le fichier doit etre une image")
    
    try:
        image_bytes = await file.read()
        image = Image.open(io.BytesIO(image_bytes))
        prompt = """
        Analyse cette photo prise par un touriste au  Togo (il peut s'agir d'un monument comme l'Indépendance, la Colombe de la Paix, le Palais de Lomé, un Tata Tamberma, ou un objet d'art artisanal).
        Agis en tant que guide touristique expert du Togo, spécialisé dans la culture et l'histoire locale.
        Tu dois obligatoirement générer une réponse STRICTEMENT au format JSON en respectant scrupuleusement la structure suivante :
        {
        "monument": "Nom officiel du monument ou de l'objet",
        "histoire": "Un récit historique captivant, fluide et instructif en français (environ 3 à 5 lignes)",
        "latitude": 6.1311,
        "longitude": 1.2227
        }

        Important : Ne renvoie aucun texte d'introduction ni de conclusion, pas de balises Markdown. Uniquement le bloc JSON brut. Donne des coordonnées GPS réelles et précises du lieu si tu le reconnais.
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

        return{
                "prediction_status": "success",
                "data": data_touristique
        }
    
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Format JSON invalide gemini ne peut pas le renvoyé")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'analyse avec Gemini : {str(e)}")


