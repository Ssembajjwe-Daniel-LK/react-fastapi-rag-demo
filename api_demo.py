"""
api_demo.py - Demo-Backend für das React-Frontend (öffentliche Version).

Stellt dieselbe REST-Schnittstelle bereit wie das echte Backend
(GET /health, GET /search, GET /codes/{code}), arbeitet aber nur mit ein paar
fest eingebauten BEISPIEL-Dokumenten. Es braucht keine Datenbank, kein Ollama und
keinen Zugriff auf echte Unterlagen.

Im echten Projekt kommt die Suchlogik aus chunk.py (Code-Lookup, Vektorsuche mit
Chroma und Volltextsuche mit SQLite FTS5). Die Antwortformate hier sind identisch,
sodass das Frontend mit beiden Backends funktioniert.

Start:
    pip install fastapi uvicorn
    uvicorn api_demo:app --host 127.0.0.1 --port 8010

Danach:
    http://127.0.0.1:8010/docs         <- Swagger-UI
    http://127.0.0.1:8010/openapi.json <- OpenAPI-Spezifikation
"""

import re

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# --------------------------------------------------------------------------- #
# Beispiel-Daten (frei erfunden)
# --------------------------------------------------------------------------- #
# Jeder Eintrag entspricht einer Dokumentseite: Pfad, Seite, Text und die
# Codes, die auf dieser Seite vorkommen.
DOCS = [
    {
        "filepath": r"C:\Dokumente\Beispiel\Handbuch_Steuerung.pdf",
        "page_num": "3",
        "text": "Die Steuerung DEMO-100 wird mit 24 V Gleichspannung versorgt. "
                "Vor der Inbetriebnahme alle Steckverbindungen prüfen.",
        "codes": ["DEMO-100"],
    },
    {
        "filepath": r"C:\Dokumente\Beispiel\Handbuch_Steuerung.pdf",
        "page_num": "7",
        "text": "Fehlercode E12 bedeutet Übertemperatur. Lüfter reinigen und "
                "Umgebungstemperatur prüfen. Danach die Steuerung DEMO-100 neu starten.",
        "codes": ["DEMO-100", "E12"],
    },
    {
        "filepath": r"C:\Dokumente\Beispiel\Zeichnung_Kabelsatz.pdf",
        "page_num": "1",
        "text": "Kabelsatz DEMO-K7: 12-polig, Länge 1,5 m, Stecker Typ A auf Typ B. "
                "Pinbelegung siehe Tabelle 2.",
        "codes": ["DEMO-K7"],
    },
    {
        "filepath": r"C:\Dokumente\Beispiel\Wartungsplan.docx",
        "page_num": "2",
        "text": "Wartungsintervall: alle 6 Monate Sichtprüfung der Platine, "
                "jährlich Austausch der Pufferbatterie.",
        "codes": [],
    },
]

# Code -> Liste der Seiten, auf denen er vorkommt (Groß-/Kleinschreibung egal)
CODE_LOOKUP: dict[str, list[dict]] = {}
for doc in DOCS:
    for c in doc["codes"]:
        CODE_LOOKUP.setdefault(c.upper(), []).append(doc)

# --------------------------------------------------------------------------- #
# App + CORS
# --------------------------------------------------------------------------- #
app = FastAPI(
    title="Wissen Assistant - Demo-API",
    description="Beispiel-Backend mit derselben Schnittstelle wie das echte RAG-Backend.",
)

# Vite-Dev-Server des React-Frontends läuft auf Port 5173
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["GET"],
    allow_headers=["*"],
)


# --------------------------------------------------------------------------- #
# Antwort-Modelle (gleiche Form wie im echten Backend)
# --------------------------------------------------------------------------- #
class SearchResponse(BaseModel):
    found: bool
    context: str = ""
    sources: list[str] = []
    message: str = ""


class CodeHit(BaseModel):
    text: str
    filepath: str
    page_num: str
    quelle: str


class CodeResponse(BaseModel):
    found: bool
    code: str
    results: list[CodeHit]


# --------------------------------------------------------------------------- #
# Hilfsfunktionen
# --------------------------------------------------------------------------- #
def source_label(doc: dict) -> str:
    """Quellenangabe im selben Format wie das echte Backend: 'Pfad (Seite X)'."""
    return f"{doc['filepath']} (Seite {doc['page_num']})"


def build_response(hits: list[dict]) -> dict:
    if not hits:
        return {"found": False, "message": "Keine passenden Stellen in den Beispiel-Dokumenten."}
    context = "\n\n".join(f"[{source_label(d)}]\n{d['text']}" for d in hits)
    return {"found": True, "context": context, "sources": [source_label(d) for d in hits]}


# --------------------------------------------------------------------------- #
# Endpoints
# --------------------------------------------------------------------------- #
@app.get("/health")
def health():
    """Prüft, ob der Server läuft."""
    return {"status": "ok", "demo": True, "codes": len(CODE_LOOKUP), "pages": len(DOCS)}


@app.get("/search", response_model=SearchResponse)
def search(question: str = Query(..., min_length=2, max_length=500)):
    """Frage oder Code -> passende Textstellen + Quellen.

    1. Kommt ein bekannter Code in der Frage vor, werden direkt dessen Seiten geliefert.
    2. Sonst einfache Stichwortsuche: Seiten nach Anzahl gemeinsamer Wörter sortiert.
       (Im echten Backend übernimmt das eine Hybrid-Suche aus Vektor- und Volltextsuche.)
    """
    words = {w.upper() for w in re.findall(r"[\w-]+", question)}

    code_hits = [d for w in words if w in CODE_LOOKUP for d in CODE_LOOKUP[w]]
    if code_hits:
        unique = list({source_label(d): d for d in code_hits}.values())
        return build_response(unique)

    keywords = {w for w in words if len(w) > 2}
    scored = []
    for doc in DOCS:
        doc_words = {w.upper() for w in re.findall(r"[\w-]+", doc["text"])}
        score = len(keywords & doc_words)
        if score:
            scored.append((score, doc))
    scored.sort(key=lambda x: x[0], reverse=True)
    return build_response([d for _, d in scored[:3]])


@app.get("/codes/{code:path}", response_model=CodeResponse)
def code_lookup(code: str):
    """Exakter Code-Lookup (Groß-/Kleinschreibung egal)."""
    key = code.strip().upper()
    if key not in CODE_LOOKUP:
        raise HTTPException(status_code=404, detail=f"Code '{code}' nicht gefunden.")
    results = [
        {"text": d["text"], "filepath": d["filepath"], "page_num": d["page_num"], "quelle": source_label(d)}
        for d in CODE_LOOKUP[key]
    ]
    return {"found": True, "code": key, "results": results}
