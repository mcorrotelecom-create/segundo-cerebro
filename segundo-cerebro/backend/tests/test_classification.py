"""Pruebas de la clasificación por nombre de archivo, sobre patrones reales
observados en el proyecto piloto SHCI Hospital del Niño. Sin dependencias
externas — corre con `python3 -m unittest` en cualquier entorno.
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.classification import classify_filename
from app.enums import DocType


class TestClassification(unittest.TestCase):
    def test_known_form_code_f59_informe_mensual(self):
        r = classify_filename(
            "F59 Informe mensual de seguimiento y ejecución del proyecto HDN-AGOSTO.pdf"
        )
        self.assertEqual(r.doc_type, DocType.INFORME_MENSUAL)
        self.assertEqual(r.doc_code, "F59")
        self.assertGreaterEqual(r.confidence, 0.9)

    def test_known_form_code_f46_minuta(self):
        r = classify_filename("F46 Minuta de Reunión_Subcontratista v02_06ago.26.docx")
        self.assertEqual(r.doc_type, DocType.MINUTA)
        self.assertEqual(r.doc_code, "F46")

    def test_factura(self):
        r = classify_filename("FACTURA 982-ACCIONA CONSTRUCCION, S.A. - CUENTA 1.pdf")
        self.assertEqual(r.doc_type, DocType.FACTURA)

    def test_nota_formal_con_codigo(self):
        r = classify_filename("NOTA ACC-HDN-TEC-1098-2025.pdf")
        self.assertEqual(r.doc_type, DocType.NOTA)
        self.assertIsNotNone(r.doc_code)

    def test_plantilla_mediciones_es_cuenta_avance_con_disciplina_sci(self):
        r = classify_filename(
            "PLANTILLA DE MEDICIONES SCI 3 7MAR24  TG V5 para cta.xlsx",
            folder_hint="04.CUENTAS/CUENTA # 1",
        )
        self.assertEqual(r.doc_type, DocType.CUENTA_AVANCE)
        self.assertEqual(r.discipline, "SCI")

    def test_plano_dwg_con_nivel_y_fecha(self):
        r = classify_filename("1. P0122019 ROC N-200 HOSPITAL DEL NIÑO 18MAY23.dwg")
        self.assertEqual(r.doc_type, DocType.PLANO)
        self.assertEqual(r.discipline, "SCI")
        self.assertEqual(r.level_zone, "N-200")
        self.assertEqual(r.doc_date.isoformat(), "2023-05-18")

    def test_contrato_subcontrato(self):
        r = classify_filename("050624 PE1134 Telecom-Subcontrato.pdf")
        self.assertEqual(r.doc_type, DocType.CONTRATO)

    def test_documento_sin_pistas_cae_en_otro_con_confianza_baja(self):
        r = classify_filename("documento_generico_xyz.pdf")
        self.assertEqual(r.doc_type, DocType.OTRO)
        self.assertLess(r.confidence, 0.5)

    def test_sometimiento_por_carpeta(self):
        r = classify_filename("TFP161.pdf", folder_hint="05.SOMETIMIENTOS/POR APROBAR")
        self.assertEqual(r.doc_type, DocType.SOMETIMIENTO)


if __name__ == "__main__":
    unittest.main()
