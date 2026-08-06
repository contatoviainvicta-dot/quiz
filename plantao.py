"""
Modo Plantão — pontuação por velocidade. Lógica pura, testável.

Cada questão tem um limite de tempo (LIMITE_SEG). Acertar dentro do tempo rende
pontos proporcionais ao tempo restante (mais rápido, mais pontos), com um piso.
Errar ou estourar o tempo = 0 pontos.
"""

from __future__ import annotations

QUESTOES = 10       # questões por sessão de plantão
LIMITE_SEG = 20     # tempo máximo por questão (segundos)
PONTOS_MAX = 20     # pontos de um acerto instantâneo
PONTOS_MIN = 5      # piso de pontos para um acerto dentro do tempo


def expirou(elapsed: float, limite: float = LIMITE_SEG) -> bool:
    """True se o tempo estourou."""
    return elapsed > limite


def pontuar(acertou: bool, elapsed: float, limite: float = LIMITE_SEG) -> int:
    """Pontos de uma resposta no plantão.

    - Errou ou estourou o tempo: 0.
    - Acertou dentro do tempo: entre PONTOS_MIN e PONTOS_MAX, proporcional ao
      tempo restante.
    """
    if not acertou or expirou(elapsed, limite):
        return 0
    restante = max(0.0, limite - elapsed)
    return max(PONTOS_MIN, round(PONTOS_MAX * restante / limite))
