"""
Conquistas (medalhas) — definições e avaliação. Lógica pura, sem Streamlit.

Cada conquista tem um critério que é uma função sobre um 'contexto' (dict com
estatísticas já calculadas do perfil). Manter o critério dependente só do
contexto deixa este módulo independente de gamificacao/revisao e fácil de testar.

Contexto esperado (montado por quem chama):
    respondidas, acertos, precisao, nivel, melhor_sequencia,
    melhor_ofensiva, dias_estudados, dominadas, max_tema
"""

from __future__ import annotations

CONQUISTAS = [
    {
        "id": "estreia",
        "emoji": "🎬",
        "nome": "Estreia",
        "desc": "Responder 10 questões",
        "criterio": lambda c: c["respondidas"] >= 10,
    },
    {
        "id": "plantao",
        "emoji": "🩺",
        "nome": "Primeiro Plantão",
        "desc": "Responder 50 questões",
        "criterio": lambda c: c["respondidas"] >= 50,
    },
    {
        "id": "maratona",
        "emoji": "🏃",
        "nome": "Maratonista",
        "desc": "Responder 250 questões",
        "criterio": lambda c: c["respondidas"] >= 250,
    },
    {
        "id": "quinhentao",
        "emoji": "🏅",
        "nome": "Quinhentão",
        "desc": "Responder 500 questões",
        "criterio": lambda c: c["respondidas"] >= 500,
    },
    {
        "id": "precisao",
        "emoji": "🎯",
        "nome": "Precisão Cirúrgica",
        "desc": "90% de precisão com 50+ respondidas",
        "criterio": lambda c: c["precisao"] >= 90 and c["respondidas"] >= 50,
    },
    {
        "id": "sangue_frio",
        "emoji": "❄️",
        "nome": "Sangue Frio",
        "desc": "20 acertos seguidos",
        "criterio": lambda c: c["melhor_sequencia"] >= 20,
    },
    {
        "id": "ofensiva7",
        "emoji": "🔥",
        "nome": "Ofensiva de 7",
        "desc": "7 dias seguidos de estudo",
        "criterio": lambda c: c["melhor_ofensiva"] >= 7,
    },
    {
        "id": "ofensiva30",
        "emoji": "🗓️",
        "nome": "Constância",
        "desc": "30 dias seguidos de estudo",
        "criterio": lambda c: c["melhor_ofensiva"] >= 30,
    },
    {
        "id": "elefante",
        "emoji": "🐘",
        "nome": "Memória de Elefante",
        "desc": "50 questões dominadas na revisão",
        "criterio": lambda c: c["dominadas"] >= 50,
    },
    {
        "id": "residente",
        "emoji": "🌟",
        "nome": "Residente",
        "desc": "Alcançar o nível 5",
        "criterio": lambda c: c["nivel"] >= 5,
    },
    {
        "id": "dedicacao",
        "emoji": "📚",
        "nome": "Dedicação",
        "desc": "Estudar em 15 dias",
        "criterio": lambda c: c["dias_estudados"] >= 15,
    },
    {
        "id": "especialista",
        "emoji": "🧠",
        "nome": "Especialista",
        "desc": "100 questões em um mesmo tema",
        "criterio": lambda c: c["max_tema"] >= 100,
    },
]

_POR_ID = {a["id"]: a for a in CONQUISTAS}


def avaliar(contexto: dict) -> set:
    """Ids das conquistas cujo critério é satisfeito pelo contexto."""
    return {a["id"] for a in CONQUISTAS if a["criterio"](contexto)}


def definicao(ident: str) -> dict | None:
    """Definição (emoji, nome, desc) de uma conquista pelo id."""
    return _POR_ID.get(ident)
