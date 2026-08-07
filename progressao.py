"""
Mapa de progressão (Interno → Professor) — patentes de carreira. Lógica pura.

Como todos os modos somam XP, a progressão de carreira usa o XP total como
espinha. Cada patente tem um limiar de XP; a atual é a de maior limiar já
atingido.
"""

from __future__ import annotations

NIVEIS = [
    {"id": "interno", "emoji": "🩺", "nome": "Interno(a)", "xp": 0},
    {"id": "plantonista", "emoji": "🥼", "nome": "Médico(a) Plantonista", "xp": 500},
    {"id": "r1", "emoji": "📋", "nome": "Residente R1", "xp": 1500},
    {"id": "r2", "emoji": "📈", "nome": "Residente R2", "xp": 3500},
    {"id": "especialista", "emoji": "🎓", "nome": "Especialista", "xp": 7000},
    {"id": "preceptor", "emoji": "🏦", "nome": "Preceptor(a)", "xp": 12000},
    {"id": "professor", "emoji": "👑", "nome": "Professor(a)", "xp": 18000},
]


def indice_atual(xp: int) -> int:
    idx = 0
    for i, n in enumerate(NIVEIS):
        if xp >= n["xp"]:
            idx = i
    return idx


def patente_atual(xp: int) -> dict:
    return NIVEIS[indice_atual(xp)]


def proxima_patente(xp: int) -> dict | None:
    i = indice_atual(xp)
    return NIVEIS[i + 1] if i + 1 < len(NIVEIS) else None


def progresso(xp: int) -> dict:
    """Progresso rumo à próxima patente.

    Devolve {atual, proxima, faltam, pct}. Na patente máxima, proxima=None,
    faltam=0, pct=1.0.
    """
    atual = patente_atual(xp)
    prox = proxima_patente(xp)
    if prox is None:
        return {"atual": atual, "proxima": None, "faltam": 0, "pct": 1.0}
    base = atual["xp"]
    alvo = prox["xp"]
    pct = (xp - base) / (alvo - base) if alvo > base else 1.0
    return {
        "atual": atual,
        "proxima": prox,
        "faltam": max(0, alvo - xp),
        "pct": max(0.0, min(1.0, pct)),
    }
