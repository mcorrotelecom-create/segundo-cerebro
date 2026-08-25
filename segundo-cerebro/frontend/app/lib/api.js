// Vacío por defecto = mismo origen (el caso normal: la interfaz y la API
// se sirven juntas desde un solo servicio). Solo se llena si alguna vez
// corres frontend y backend como dos servicios separados.
export const API_URL = process.env.NEXT_PUBLIC_API_URL || "";

export async function listDocuments() {
  const res = await fetch(`${API_URL}/documents`, { cache: "no-store" });
  if (!res.ok) throw new Error(`No se pudo listar documentos (${res.status})`);
  return res.json();
}

export async function uploadDocument(file, folderHint) {
  const form = new FormData();
  form.append("file", file);
  const url = new URL(`${API_URL}/documents/upload`, window.location.origin);
  if (folderHint) url.searchParams.set("folder_hint", folderHint);
  const res = await fetch(url.toString(), { method: "POST", body: form });
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(`Fallo al subir el documento (${res.status}): ${detail}`);
  }
  return res.json();
}

export async function search(query) {
  const url = new URL(`${API_URL}/search`, window.location.origin);
  url.searchParams.set("q", query);
  const res = await fetch(url.toString(), { cache: "no-store" });
  if (!res.ok) throw new Error(`Falló la búsqueda (${res.status})`);
  return res.json();
}
