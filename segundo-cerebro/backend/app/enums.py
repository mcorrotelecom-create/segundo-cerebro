"""Enumeraciones compartidas — sin dependencias externas a propósito.

La lógica de clasificación (app/classification.py) es lógica de negocio pura
y no debe depender del ORM. Los modelos de base de datos (app/models.py)
importan estos mismos enums para que la fuente de verdad sea una sola.
"""
import enum


class DocType(str, enum.Enum):
    FACTURA = "FACTURA"
    NOTA = "NOTA"
    CUENTA_AVANCE = "CUENTA_AVANCE"
    INFORME_MENSUAL = "INFORME_MENSUAL"
    INFORME_TECNICO = "INFORME_TECNICO"
    INFORME_PRUEBA = "INFORME_PRUEBA"
    ACTA = "ACTA"
    MINUTA = "MINUTA"
    SOMETIMIENTO = "SOMETIMIENTO"
    CONTRATO = "CONTRATO"
    PLAN_PROYECTO = "PLAN_PROYECTO"
    CRONOGRAMA = "CRONOGRAMA"
    PLANO = "PLANO"
    FICHA_TECNICA = "FICHA_TECNICA"
    OTRO = "OTRO"


class ClassificationSource(str, enum.Enum):
    FILENAME_RULE = "filename_rule"
    CONTENT_RULE = "content_rule"
    AI = "ai"
    MANUAL = "manual"


class DocumentStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    INDEXED = "indexed"
    ERROR = "error"
