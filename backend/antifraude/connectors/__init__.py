"""Conectores de entrada: convierten mensajes externos en mensajes internos.

Previstos: análisis manual (fase a), conector simulado SIEMPRE etiquetado
(ADR-0015) y Gmail por polling de ``history.list`` (fase f, ADR-0004).
Los conectores no analizan: solo entregan mensajes al pipeline.
Sin implementar en F0-03.
"""
