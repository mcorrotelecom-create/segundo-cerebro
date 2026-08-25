/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Exporta HTML/CSS/JS estáticos (carpeta "out") en vez de necesitar un
  // servidor Node propio. El Dockerfile de la raíz copia esa carpeta
  // dentro del backend, que la sirve junto con la API — un solo servicio
  // desplegado, sin un segundo servidor de Node corriendo aparte.
  output: "export",
  // Cada ruta queda como su propia carpeta con index.html (ej. "/buscar/
  // index.html" en vez de "/buscar.html") — así el servidor estático del
  // backend la resuelve directo, sin necesitar reglas de reescritura.
  trailingSlash: true,
};

module.exports = nextConfig;
