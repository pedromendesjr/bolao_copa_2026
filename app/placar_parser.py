"""
placar_parser.py
================
Converte um palpite digitado como texto único ("2x1", "2-1", "2 1")
em um par de inteiros (placar_a, placar_b).

Funções puras, testáveis isoladamente.

Formatos aceitos (separador pode ser x, X, -, : ou espaço):
    "2x1"   → (2, 1)
    "2 x 1" → (2, 1)
    "2-1"   → (2, 1)
    "2:1"   → (2, 1)
    "2 1"   → (2, 1)
    "10x0"  → (10, 0)

Rejeitado (retorna None):
    ""          → vazio
    "2"         → falta um placar
    "abc"       → não numérico
    "2x"        → falta o segundo número
    "2x1x3"     → separadores demais
    "-1x2"      → negativo
    "21x0"      → placar acima de 20 (improvável, evita erro de digitação)
"""
from __future__ import annotations

import re

# Captura: dígitos, separador (x/X/-/:/espaços), dígitos
_PADRAO = re.compile(r"^\s*(\d{1,2})\s*[xX:\-\s]\s*(\d{1,2})\s*$")

_MAX_GOLS = 20


def parse_placar(texto: str) -> tuple[int, int] | None:
    """
    Converte texto em (placar_a, placar_b) ou None se inválido.
    """
    if not texto:
        return None
    m = _PADRAO.match(texto)
    if not m:
        return None
    a, b = int(m.group(1)), int(m.group(2))
    if a > _MAX_GOLS or b > _MAX_GOLS:
        return None
    return (a, b)


def formatar_placar(placar_a: int, placar_b: int) -> str:
    """Formata um par de placares no formato canônico 'AxB'."""
    return f"{placar_a}x{placar_b}"