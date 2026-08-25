"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

export default function NavBar() {
  const pathname = usePathname();
  return (
    <header className="appbar">
      <div className="brand">
        <span>Segundo Cerebro</span> de Ingeniería
      </div>
      <nav className="tabs">
        <Link href="/" className={pathname === "/" ? "active" : ""}>
          Documentos
        </Link>
        <Link href="/buscar" className={pathname === "/buscar" ? "active" : ""}>
          Buscar
        </Link>
      </nav>
    </header>
  );
}
