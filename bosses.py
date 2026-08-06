"""
Bosses (chefões) — configuração e desbloqueio. Lógica pura, testável.

Um chefão desbloqueia depois que o usuário responde 'desbloqueio' questões no
total. A batalha usa questões do banco (do 'tema', ou "Todas"): acerto tira HP
do chefão, erro tira uma das suas vidas. Zerar o HP do chefão = vitória e um
grande prêmio de XP (só na primeira vez).

Cada chefão:
    id, emoji, nome, tema, desbloqueio (questões), hp, vidas, xp (prêmio)
"""

from __future__ import annotations

BOSSES = [
    {
        "id": "boss-neo",
        "emoji": "👶",
        "nome": "Chefão da Neonatologia",
        "tema": "Neonatologia",
        "desbloqueio": 30,
        "hp": 6,
        "vidas": 3,
        "xp": 120,
    },
    {
        "id": "boss-emerg",
        "emoji": "🚨",
        "nome": "Chefão da Emergência",
        "tema": "Emergência",
        "desbloqueio": 100,
        "hp": 8,
        "vidas": 3,
        "xp": 200,
    },
    {
        "id": "boss-final",
        "emoji": "👑",
        "nome": "Chefão Final",
        "tema": "Todas",
        "desbloqueio": 250,
        "hp": 10,
        "vidas": 2,
        "xp": 350,
    },
]

_POR_ID = {b["id"]: b for b in BOSSES}


def por_id(ident: str) -> dict | None:
    return _POR_ID.get(ident)


def desbloqueado(boss: dict, respondidas: int) -> bool:
    return respondidas >= boss["desbloqueio"]


def tamanho_pool(boss: dict) -> int:
    """Quantas questões preparar: suficiente para decidir a batalha, com folga."""
    return boss["hp"] + boss["vidas"] + 3
