# ADR-0014: Distribución con venv y dependencias fijadas

**Fecha**: 2026-11-08
**Estado**: accepted (D-26, D-36; resuelve T-08)
**Decisores**: usuario · Claude Code (propuesta)

## Contexto
El jurado evalúa el **ZIP descargado de GitHub** con un README que permita instalar, configurar, ejecutar y probar (rúbrica: implementación 30 %).

## Decisión
Entorno virtual `.venv` con Python 3.12; `requirements.txt` (ejecución) y `requirements-dev.txt` (pruebas) con **versiones exactas fijadas** (`==`), cada dependencia justificada y con licencia verificada al instalar. Recursos estáticos de terceros (htmx) **vendorizados** con su licencia. Sin PyInstaller en el hackatón. Prueba final: instalar desde el ZIP en una carpeta limpia siguiendo solo el README.

## Alternativas consideradas
### PyInstaller / ejecutable
- **Por qué no**: tiempo de empaquetado y problemas conocidos; P2.
### Gestores adicionales (uv, poetry)
- **Por qué no**: otra herramienta que instalar; pip + venv basta.

## Consecuencias
### Positivas
- Reproducible con herramientas estándar.
### Negativas
- El evaluador necesita Python 3.12 instalado.
### Riesgos
- Dependencias transitivas sin fijar → registrar `pip freeze` en un archivo de bloqueo y probar el ZIP.
