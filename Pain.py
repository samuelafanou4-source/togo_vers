from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional
import json
from fastapi.middleware.cors import CORSMiddleware



app = FastAPI(title="togo_vers")

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
