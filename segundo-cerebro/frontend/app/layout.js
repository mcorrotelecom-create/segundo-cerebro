import "./globals.css";
import NavBar from "./components/NavBar";

export const metadata = {
  title: "Segundo Cerebro de Ingeniería",
  description: "Fase 0 — ingesta, clasificación y búsqueda de documentos del proyecto.",
};

export default function RootLayout({ children }) {
  return (
    <html lang="es">
      <body>
        <NavBar />
        <div className="shell">{children}</div>
      </body>
    </html>
  );
}
