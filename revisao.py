"""
Repetição espaçada (estilo Anki/Leitner) — lógica pura, testável.

Cada questão tem um "nível" (0..5) que indica o intervalo até a próxima
revisão. Acertar sobe um nível; errar volta ao nível 0 (revisão em 1 dia).

    INTERVALOS = [1, 3, 7, 15, 30, 90]  # dias por nível

O estado fica num dict guardado no perfil (perfil.revisao), serializável:

    estado[ident] = {
        "nivel": int,          # 0..5
        "proxima": "YYYY-MM-DD",
        "acertos": int,
        "erros": int,
    }

'ident' é um hash curto e estável do enunciado (qid), então não depende de
posição no banco e sobrevive a reordenações.
"""

from __future__ import annotations

import hashlib
from datetime import date, timedelta

INTERVALOS = [1, 3, 7, 15, 30, 90]  # dias
NIVEL_MAX = len(INTERVALOS) - 1


def qid(pergunta: str) -> str:
    """Identificador estável e curto de uma questão (hash do enunciado)."""
    return hashlib.sha1(pergunta.encode("utf-8")).hexdigest()[:12]


def registrar(estado: dict, ident: str, acertou: bool, hoje: str) -> dict:
    """Atualiza o agendamento de uma questão e devolve o novo registro.

    Acertar: sobe um nível (até o máximo) e agenda pelo intervalo do novo nível.
    Errar: volta ao nível 0 (revisão em 1 dia).
    """
    rec = estado.get(ident)
    prev = rec["nivel"] if rec else -1  # -1 = questão nova
    nivel = min(prev + 1, NIVEL_MAX) if acertou else 0

    proxima = (date.fromisoformat(hoje) + timedelta(days=INTERVALOS[nivel])).isoformat()
    novo = {
        "nivel": nivel,
        "proxima": proxima,
        "acertos": (rec["acertos"] if rec else 0) + (1 if acertou else 0),
        "erros": (rec["erros"] if rec else 0) + (0 if acertou else 1),
    }
    estado[ident] = novo
    return novo


def devidas(estado: dict, hoje: str) -> list[str]:
    """Ids das questões cuja revisão está vencida (proxima <= hoje).

    Ordenadas da mais atrasada para a menos atrasada.
    """
    itens = [(i, r["proxima"]) for i, r in estado.items() if r["proxima"] <= hoje]
    itens.sort(key=lambda t: t[1])
    return [i for i, _ in itens]


def contagens(estado: dict, total_banco: int, hoje: str) -> dict:
    """Resumo para o painel de revisão."""
    rastreadas = len(estado)
    revisar_hoje = sum(1 for r in estado.values() if r["proxima"] <= hoje)
    dominadas = sum(1 for r in estado.values() if r["nivel"] >= NIVEL_MAX)
    aprendendo = rastreadas - dominadas
    novas = max(0, total_banco - rastreadas)
    return {
        "revisar_hoje": revisar_hoje,
        "aprendendo": aprendendo,
        "dominadas": dominadas,
        "novas": novas,
    }


def intervalo_do_nivel(nivel: int) -> int:
    """Dias de intervalo de um nível (para exibir 'volta em X dias')."""
    return INTERVALOS[max(0, min(nivel, NIVEL_MAX))]
