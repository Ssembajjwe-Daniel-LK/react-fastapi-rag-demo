# RAG – React-Frontend

Eine einfache Weboberfläche zum Durchsuchen technischer Unterlagen aus dem Wissen_Assistant_RAG.
Man gibt eine Frage oder einen Code (z. B. `DEMO-100`) ein und bekommt den passenden Textausschnitt
mit Quellenangabe (Datei, Seite) angezeigt.

## Aufbau

```
React-Frontend  ──REST (GET /search)──▶  Backend (FastAPI and chunk.py)
```

- **Frontend (dieses Repo):** React + TypeScript mit Vite. Es zeigt nur die Suche und die Ergebnisse an
  und ruft dafür die REST-API des Backends auf.
- **Backend (nicht in diesem Repo):** Ein FastAPI-Server, der die Suchlogik aus `chunk.py` nutzt.
  `chunk.py` enthält die eigentliche RAG-Logik (Code-Lookup, Vektor- und Volltextsuche).

## Starten

Voraussetzung: Node.js 20.19+ oder 22.12+ und ein laufendes Backend unter `http://127.0.0.1:8010`.

```bash
npm install
npm run dev
```

Danach im Browser öffnen: http://localhost:5173

Die Backend-Adresse steht in `src/App.tsx` (`const API`).
