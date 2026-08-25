"""Clasificación de documentos por convención de nombre de archivo.

Principio de diseño (ver propuesta técnica §05 y el diagnóstico del piloto):
el proyecto YA tiene un sistema de formatos codificados (F14, F27, F42, F46,
F59...) y una nomenclatura consistente para planos y notas. Esta plataforma
reconoce y respeta ese vocabulario en vez de inventar uno nuevo.

Esta clasificación es puramente por nombre de archivo (y opcionalmente una
pista de carpeta). Es determinística, rápida y no cuesta un centavo de API.
Cuando el nombre no alcanza para decidir con confianza, el resultado queda
con confidence baja y classification_source="filename_rule" de todos modos
— la clasificación asistida por IA sobre el contenido (Fase 1) es la que
sube la confianza, nunca esta capa inventa una respuesta seguraque no tiene.
"""
import re
from dataclasses import dataclass, field
from datetime import date

from app.enums import ClassificationSource, DocType

# Catálogo de formatos institucionales ya en uso en el proyecto (ver
# diagnóstico: F14 Plan de Proyecto, F27 Acta de entrega de planos, F42 Acta
# de reunión, F46 Minuta, F59 Informe mensual). Se extiende con el tiempo
# a medida que aparecen formatos nuevos — es un diccionario, no código.
KNOWN_FORMS: dict[str, DocType] = {
    "F14": DocType.PLAN_PROYECTO,
    "F27": DocType.ACTA,
    "F42": DocType.ACTA,
    "F46": DocType.MINUTA,
    "F59": DocType.INFORME_MENSUAL,
}

DISCIPLINE_KEYWORDS: list[tuple[str, str]] = [
    (r"\bSCI\b|ROCIADOR|SPRINKLER|CONTRA\s*INCEND|\bROC\b", "SCI"),
    (r"\bHVAC\b|AIRE\s*ACONDICIONADO|CLIMATIZAC", "HVAC"),
    (r"EL[ÉE]CTRIC", "ELECTRICO"),
    (r"PLOMER[ÍI]A|SANITARI|AGUA\s*POTABLE", "PLOMERIA"),
    (r"GAS(ES)?\s*M[ÉE]DIC", "GASES_MEDICOS"),
]

# Orden importa: reglas más específicas primero.
DOC_TYPE_RULES: list[tuple[str, DocType, float]] = [
    (r"\bFACTURA\b", DocType.FACTURA, 0.9),
    (r"^NOTA\b|\bNOTA\s+[A-Z]+-[A-Z]+-[A-Z]+-\d+", DocType.NOTA, 0.85),
    (r"INFORME\s+MENSUAL", DocType.INFORME_MENSUAL, 0.9),
    (r"INFORME\s+T[ÉE]CNICO", DocType.INFORME_TECNICO, 0.85),
    (r"PRUEBAS?\b", DocType.INFORME_PRUEBA, 0.7),
    (r"INFORME\s+DE\s+CUENTA|\bINFOME\b", DocType.INFORME_TECNICO, 0.6),
    (r"PLANTILLA\s+DE\s+MEDICIONES|CUENTAS?\s+No\.?\s*\d|CUENTA\s*#\s*\d", DocType.CUENTA_AVANCE, 0.85),
    (r"MINUTA", DocType.MINUTA, 0.85),
    (r"ACTA\s+DE\s+(ENTREGA|REUNI[ÓO]N)", DocType.ACTA, 0.85),
    (r"SOMETIMIENTO|TABLA\s+DE\s+CONTENIDOS", DocType.SOMETIMIENTO, 0.7),
    (r"SUBCONTRATO|CONTRATO|ADENDA", DocType.CONTRATO, 0.8),
    (r"PLAN\s+DE\s+PROYECTO", DocType.PLAN_PROYECTO, 0.85),
    (r"CRONOGRAMA", DocType.CRONOGRAMA, 0.85),
    (r"FICHA\s+T[ÉE]CNICA|\bTFP\d+\b", DocType.FICHA_TECNICA, 0.6),
]

LEVEL_ZONE_PATTERN = re.compile(r"\bN-?\s?(\d{2,4})\b|NIVEL\s*-?\s?(\d{1,4})", re.IGNORECASE)

# Fechas típicas encontradas en el proyecto: "18MAY23", "22-03-2024", "31AGO23"
_MONTHS_ES = {
    "ENE": 1, "FEB": 2, "MAR": 3, "ABR": 4, "MAY": 5, "JUN": 6,
    "JUL": 7, "AGO": 8, "SEP": 9, "SET": 9, "OCT": 10, "NOV": 11, "DIC": 12,
}
DATE_COMPACT_PATTERN = re.compile(r"(\d{1,2})([A-Z]{3})(\d{2,4})", re.IGNORECASE)
DATE_ISO_LIKE_PATTERN = re.compile(r"(\d{1,2})[-_](\d{1,2})[-_](\d{2,4})")


@dataclass
class ClassificationResult:
    doc_type: DocType
    doc_code: str | None = None
    discipline: str | None = None
    level_zone: str | None = None
    doc_date: date | None = None
    confidence: float = 0.0
    source: ClassificationSource = ClassificationSource.FILENAME_RULE
    reasons: list[str] = field(default_factory=list)


def _extract_form_code(name: str) -> tuple[str, DocType] | None:
    m = re.match(r"\s*(F\d{2})\b", name, re.IGNORECASE)
    if not m:
        return None
    code = m.group(1).upper()
    if code in KNOWN_FORMS:
        return code, KNOWN_FORMS[code]
    return None


def _extract_date(name: str) -> date | None:
    m = DATE_COMPACT_PATTERN.search(name)
    if m:
        day, mon_txt, year = m.groups()
        month = _MONTHS_ES.get(mon_txt.upper())
        if month:
            year_i = int(year)
            year_i = 2000 + year_i if year_i < 100 else year_i
            try:
                return date(year_i, month, int(day))
            except ValueError:
                pass
    m = DATE_ISO_LIKE_PATTERN.search(name)
    if m:
        a, b, c = (int(x) for x in m.groups())
        year = c if c > 31 else (2000 + c if c < 100 else c)
        # heurística dd-mm-yyyy (convención observada en el proyecto)
        day, month = a, b
        try:
            return date(year, month, day)
        except ValueError:
            return None
    return None


def classify_filename(filename: str, folder_hint: str | None = None) -> ClassificationResult:
    """Clasifica un documento a partir de su nombre de archivo (y, si se
    conoce, la carpeta donde vivía) usando reglas determinísticas.
    """
    name = filename.strip()
    haystack = f"{name} {folder_hint or ''}".upper()
    reasons: list[str] = []

    # 1) Formato institucional conocido (F##) — máxima prioridad y confianza.
    form = _extract_form_code(name)
    if form:
        code, doc_type = form
        reasons.append(f"nombre inicia con formato conocido {code}")
        result = ClassificationResult(
            doc_type=doc_type, doc_code=code, confidence=0.95, reasons=reasons
        )
    else:
        # 2) Extensión .dwg siempre es plano, sin ambigüedad.
        if name.lower().endswith(".dwg"):
            result = ClassificationResult(doc_type=DocType.PLANO, confidence=0.95, reasons=["extensión .dwg"])
        else:
            doc_type = DocType.OTRO
            confidence = 0.2
            for pattern, dtype, conf in DOC_TYPE_RULES:
                if re.search(pattern, haystack):
                    doc_type = dtype
                    confidence = conf
                    reasons.append(f"coincide con patrón de {dtype.value}")
                    break
            result = ClassificationResult(doc_type=doc_type, confidence=confidence, reasons=reasons)

    # Código de nota formal, si aplica (ej. "NOTA ACC-HDN-TEC-1098-2025")
    nota_match = re.search(r"NOTA[\s-]+[A-Z]+-[A-Z]+-[A-Z]+-\d+-\d+", haystack)
    if nota_match and not result.doc_code:
        result.doc_code = nota_match.group(0).replace("  ", " ").title()

    # Disciplina
    for pattern, disc in DISCIPLINE_KEYWORDS:
        if re.search(pattern, haystack):
            result.discipline = disc
            reasons.append(f"disciplina detectada: {disc}")
            break

    # Nivel / zona
    lv = LEVEL_ZONE_PATTERN.search(haystack)
    if lv:
        num = lv.group(1) or lv.group(2)
        result.level_zone = f"N-{num}"
        reasons.append(f"nivel/zona detectado: N-{num}")

    # Fecha
    dt = _extract_date(name)
    if dt:
        result.doc_date = dt
        reasons.append(f"fecha detectada en el nombre: {dt.isoformat()}")

    result.reasons = reasons
    return result
