"use client";

import { useEffect, useRef, useState } from "react";
import { listDocuments, uploadDocument } from "./lib/api";

function sourceLabel(doc) {
  const parts = [];
  if (doc.doc_code) parts.push(doc.doc_code);
  if (doc.discipline) parts.push(doc.discipline);
  if (doc.level_zone) parts.push(doc.level_zone);
  return parts.join(" · ");
}

export default function DocumentsPage() {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [message, setMessage] = useState(null);
  const [folderHint, setFolderHint] = useState("");
  const fileInputRef = useRef(null);

  async function refresh() {
    setLoading(true);
    try {
      setDocuments(await listDocuments());
    } catch (err) {
      setMessage({ type: "error", text: err.message });
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    refresh();
  }, []);

  async function handleUpload(e) {
    e.preventDefault();
    const file = fileInputRef.current?.files?.[0];
    if (!file) {
      setMessage({ type: "error", text: "Elige un archivo primero." });
      return;
    }
    setUploading(true);
    setMessage(null);
    try {
      const doc = await uploadDocument(file, folderHint);
      setMessage({
        type: "ok",
        text: `"${doc.original_filename}" clasificado como ${doc.doc_type} (confianza ${(doc.classification_confidence * 100).toFixed(0)}%) — ${doc.chunk_count} fragmentos indexados.`,
      });
      fileInputRef.current.value = "";
      await refresh();
    } catch (err) {
      setMessage({ type: "error", text: err.message });
    } finally {
      setUploading(false);
    }
  }

  return (
    <>
      <h1>Documentos del proyecto</h1>
      <p className="lead">
        Fase 0: sube un documento y el sistema lo clasifica automáticamente (tipo, disciplina, nivel/zona,
        fecha) y lo indexa para búsqueda. Cada resultado de búsqueda cita exactamente de dónde salió.
      </p>

      <form className="card" onSubmit={handleUpload}>
        <div className="field-row">
          <input type="file" ref={fileInputRef} accept=".pdf,.xlsx,.xlsm,.xls,.docx" />
          <input
            type="text"
            placeholder="Carpeta de origen (opcional, ej. 04.CUENTAS/CUENTA # 1)"
            value={folderHint}
            onChange={(e) => setFolderHint(e.target.value)}
          />
          <button type="submit" disabled={uploading}>
            {uploading ? "Procesando…" : "Subir e indexar"}
          </button>
        </div>
        {message && (
          <p className={`status-msg ${message.type}`}>{message.text}</p>
        )}
      </form>

      <div className="card">
        {loading ? (
          <p className="empty">Cargando…</p>
        ) : documents.length === 0 ? (
          <p className="empty">Todavía no hay documentos. Sube el primero arriba.</p>
        ) : (
          <table className="doclist">
            <thead>
              <tr>
                <th>Documento</th>
                <th>Tipo</th>
                <th>Clasificación</th>
                <th>Estado</th>
                <th>Fragmentos</th>
              </tr>
            </thead>
            <tbody>
              {documents.map((doc) => (
                <tr key={doc.id}>
                  <td>{doc.original_filename}</td>
                  <td>
                    <span className="badge type">{doc.doc_type || "OTRO"}</span>
                  </td>
                  <td>{sourceLabel(doc) || "—"}</td>
                  <td>
                    <span className={`badge status-${doc.status}`}>{doc.status}</span>
                  </td>
                  <td>{doc.chunk_count}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </>
  );
}
