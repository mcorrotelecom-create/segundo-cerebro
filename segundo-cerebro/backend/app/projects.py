"""Fase 0 trabaja sobre un único proyecto piloto (ver config.default_project_*).
Cuando se agregue selección de proyecto en la interfaz (Fase 1+), este es el
único lugar que cambia: el resto del código ya recibe `project_id` como
parámetro y no asume que solo existe uno.
"""
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import Project

settings = get_settings()


def get_or_create_default_project(db: Session) -> Project:
    project = db.query(Project).filter(Project.code == settings.default_project_code).one_or_none()
    if project is None:
        project = Project(code=settings.default_project_code, name=settings.default_project_name)
        db.add(project)
        db.commit()
        db.refresh(project)
    return project
