"use client";

import { useState } from "react";
import { search } from "../lib/api";

function formatSource(hit) {
  const ref = hit.source_ref || {};
  const bits = [];
  if (ref.page) bits.push(`página ${ref.page}`);
  if (ref.sheet) bits.push(`hoja "${ref.sheet}"`);
  if (ref.rows) bits.push(`filas ${ref.rows}`);
  if (ref.paragraph !== undefined) bits.push(`párrafo ${ref.paragraph}`);
  if (ref.table) bits.push(`tabla ${ref.table}`);
  if (ref.note) bits.push(ref.note.replaceAll("_", " "));
  return bits.length ? bits.join(" · ") : "sin referencia específica";
}

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  async function handleSearch(e) {
    e.preventDefault();
    if (!query.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const data = await search(query.trim());
      setResults(data.results);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <h1>Buscar en el proyecto</h1>
      <p className="lead">
        Búsqueda híbrida (texto completo + semántica). Cada resultado muestra exactamente de qué
        documento y de qué parte de ese documento salió — la cita, no solo la respuesta.
      </p>

      <form className="card" onSubmit={handleSearch}>
        <div className="field-row">
          <input
            type="text"
            placeholder='Ej. "rociadores nivel -200", "factura cuenta 1"…'
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          <button type="submit" disabled={loading}>
            {loading ? "Buscando…" : "Buscar"}
          </button>
        </div>
        {error && <p className="status-msg error">{error}</p>}
      </form>

      {results !== null && (
        <div>
          {results.length === 0 ? (
            <p className="empty">Sin resultados para esa búsqueda.</p>
          ) : (
            results.map((hit) => (
              <div className="hit" key={hit.chunk_id}>
                <div className="hit-meta">
                  <span className="badge type">{hit.doc_type || "OTRO"}</span>
                  <span>{hit.document_filename}</span>
                  <span className="badge">{hit.match_type}</span>
                  <span className="badge">score {hit.score.toFixed(3)}</span>
                </div>
                <div className="hit-text">{hit.text}</div>
                <div className="hit-source">Fuente: {formatSource(hit)}</div>
              </div>
            ))
          )}
        </div>
      )}
    </>
  );
}
