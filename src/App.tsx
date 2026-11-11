import { useState } from "react";
import "./App.css";

// Adresse deines FastAPI-Übungsservers (api_demo.py)
const API = "http://127.0.0.1:8010";

// Form der Antwort von GET /search (entspricht SearchResponse in api_demo.py)
type SearchResponse = {
  found: boolean;
  context: string;
  sources: string[];
  message: string;
};

export default function App() {
  const [question, setQuestion] = useState("");
  const [result, setResult] = useState<SearchResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function runSearch() {
    if (question.trim().length < 2) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await fetch(`${API}/search?question=${encodeURIComponent(question)}`);
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail ?? `Server antwortete mit ${res.status}`);
      }
      setResult(await res.json());
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
    <header className="header">
      <div className="header-inner">
        <h1>Wissen Assistant</h1>
        <p>Unterlagen durchsuchen – per Frage oder direkt per Code.</p>
      </div>
    </header>
    <main className="page">

      <div className="search">
        <input
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && runSearch()}
          placeholder="Frage oder Code eingeben, z. B. DEMO-100"
          aria-label="Suchbegriff"
        />
        <button onClick={runSearch} disabled={loading}>
          {loading ? "Suche läuft…" : "Suchen"}
        </button>
      </div>

      {error && <p className="error">Fehler: {error}</p>}

      {result && !result.found && (
        <p className="empty">Keine Treffer. {result.message}</p>
      )}

      {result?.found && (
        <section className="results">
          <h2>Quellen ({result.sources.length})</h2>
          <ul className="sources">
            {result.sources.map((s) => {
              const { file, dir, page } = splitSource(s);
              return (
                <li key={s}>
                  <span className="file">{file}</span>
                  {page && <span className="page">Seite {page}</span>}
                  <span className="path">{dir}</span>
                </li>
              );
            })}
          </ul>

          <h2>Gefundener Kontext</h2>
          <pre className="context">{result.context}</pre>
        </section>
      )}
    </main>
    </>
  );
}

// "C:\...\Ordner\Datei.pdf (Seite 3)" -> Dateiname, Ordnerpfad, Seitenzahl
function splitSource(source: string) {
  const m = source.match(/^(.*) \(Seite (.*)\)$/);
  const fullPath = m ? m[1] : source;
  const page = m ? m[2] : "";
  const cut = Math.max(fullPath.lastIndexOf("\\"), fullPath.lastIndexOf("/"));
  return {
    file: cut >= 0 ? fullPath.slice(cut + 1) : fullPath,
    dir: cut >= 0 ? fullPath.slice(0, cut) : "",
    page,
  };
}
