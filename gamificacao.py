"""
Gamificação — lógica pura de XP, níveis, sequência de acertos e ofensiva diária.

Não importa o Streamlit de propósito: assim dá para testar com pytest e trocar
a camada de persistência sem tocar aqui. O 'perfil' é serializável
(perfil_para_dict / perfil_de_dict).

Dois "streaks" distintos, de propósito:
  - sequencia_*  -> acertos seguidos (dá bônus de XP dentro de uma sessão)
  - ofensiva     -> DIAS consecutivos em que a meta diária foi cumprida (o 🔥)

Regra da ofensiva: um dia "conta" quando o usuário responde META_DIARIA
questões naquele dia. A virada do dia é em UTC (definida por quem chama, que
passa a data 'hoje'; o padrão usa a data UTC atual).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timedelta, timezone

# ---------------------------------------------------------------------------
# Regras de XP
# ---------------------------------------------------------------------------
XP_ACERTO = 15
XP_ERRO = 2
XP_BONUS_SEQUENCIA = 30
PASSO_SEQUENCIA = 10

# Curva de níveis: nível 1 exige 100 XP; cada nível seguinte exige +50.
XP_NIVEL_BASE = 100
XP_NIVEL_INCREMENTO = 50

# ---------------------------------------------------------------------------
# Regra da ofensiva diária
# ---------------------------------------------------------------------------
META_DIARIA = 5  # questões respondidas no dia para o dia "contar"


@dataclass
class Perfil:
    """Progresso acumulado do usuário. Tudo aqui é serializável."""

    xp_total: int = 0
    respondidas: int = 0
    acertos: int = 0
    # sequência de acertos (bônus de XP)
    sequencia_atual: int = 0
    melhor_sequencia: int = 0
    # progresso por tema: por_categoria[tema] = {"respondidas","acertos","xp"}
    por_categoria: dict = field(default_factory=dict)
    # ofensiva diária (dias consecutivos com a meta cumprida)
    dias_estudados: list = field(default_factory=list)  # ["2026-08-05", ...]
    data_corrente: str = ""       # dia ao qual 'respondidas_no_dia' se refere
    respondidas_no_dia: int = 0
    melhor_ofensiva: int = 0
    # repetição espaçada: estado por questão (ver revisao.py)
    revisao: dict = field(default_factory=dict)


@dataclass
class Resultado:
    """O que aconteceu ao registrar uma resposta (para a interface exibir)."""

    xp_ganho: int
    bonus_sequencia: int
    nivel_antes: int
    nivel_depois: int
    subiu_nivel: bool
    dia_completado: bool  # acabou de bater a meta diária nesta resposta
    ofensiva: int         # ofensiva atual (dias) após esta resposta


def perfil_novo() -> Perfil:
    return Perfil()


def _hoje_utc() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def _bucket_categoria(perfil: Perfil, categoria: str) -> dict:
    return perfil.por_categoria.setdefault(
        categoria, {"respondidas": 0, "acertos": 0, "xp": 0}
    )


def nivel_por_xp(xp_total: int) -> tuple[int, int, int]:
    """Converte XP total em (nível, xp_dentro_do_nível, xp_para_o_próximo)."""
    nivel = 1
    restante = xp_total
    passo = XP_NIVEL_BASE
    while restante >= passo:
        restante -= passo
        nivel += 1
        passo += XP_NIVEL_INCREMENTO
    return nivel, restante, passo


def precisao(acertos: int, respondidas: int) -> int:
    return round(100 * acertos / respondidas) if respondidas else 0


def ofensiva_atual(perfil: Perfil, hoje: str | None = None) -> int:
    """Dias consecutivos com meta cumprida, terminando em hoje ou ontem.

    Se o último dia estudado foi há 2+ dias, a ofensiva está quebrada (0).
    É calculada na hora a partir de 'dias_estudados', então nunca fica velha.
    """
    hoje = hoje or _hoje_utc()
    dias = set(perfil.dias_estudados)
    d = date.fromisoformat(hoje)

    if hoje in dias:
        cursor = d
    elif (d - timedelta(days=1)).isoformat() in dias:
        cursor = d - timedelta(days=1)
    else:
        return 0

    n = 0
    while cursor.isoformat() in dias:
        n += 1
        cursor -= timedelta(days=1)
    return n


def _registrar_dia(perfil: Perfil, hoje: str) -> bool:
    """Atualiza a contagem do dia. Devolve True se a meta foi batida AGORA."""
    if perfil.data_corrente != hoje:
        perfil.data_corrente = hoje
        perfil.respondidas_no_dia = 0
    perfil.respondidas_no_dia += 1

    if hoje in perfil.dias_estudados:
        return False  # meta do dia já tinha sido cumprida
    if perfil.respondidas_no_dia >= META_DIARIA:
        perfil.dias_estudados.append(hoje)
        perfil.dias_estudados.sort()
        atual = ofensiva_atual(perfil, hoje)
        perfil.melhor_ofensiva = max(perfil.melhor_ofensiva, atual)
        return True
    return False


def registrar_resposta(
    perfil: Perfil,
    categoria: str,
    acertou: bool,
    hoje: str | None = None,
) -> Resultado:
    """Atualiza o perfil com uma resposta e devolve o que mudou.

    'hoje' é a data (ISO, UTC) usada para a ofensiva diária; se None, usa a
    data UTC atual. Passe explicitamente nos testes.
    """
    hoje = hoje or _hoje_utc()
    nivel_antes, _, _ = nivel_por_xp(perfil.xp_total)

    ganho = XP_ACERTO if acertou else XP_ERRO
    perfil.respondidas += 1
    bucket = _bucket_categoria(perfil, categoria)
    bucket["respondidas"] += 1

    if acertou:
        perfil.acertos += 1
        bucket["acertos"] += 1
        perfil.sequencia_atual += 1
        perfil.melhor_sequencia = max(
            perfil.melhor_sequencia, perfil.sequencia_atual
        )
    else:
        perfil.sequencia_atual = 0

    bonus = 0
    if acertou and perfil.sequencia_atual % PASSO_SEQUENCIA == 0:
        bonus = XP_BONUS_SEQUENCIA

    total = ganho + bonus
    perfil.xp_total += total
    bucket["xp"] += total

    dia_completado = _registrar_dia(perfil, hoje)

    nivel_depois, _, _ = nivel_por_xp(perfil.xp_total)
    return Resultado(
        xp_ganho=total,
        bonus_sequencia=bonus,
        nivel_antes=nivel_antes,
        nivel_depois=nivel_depois,
        subiu_nivel=nivel_depois > nivel_antes,
        dia_completado=dia_completado,
        ofensiva=ofensiva_atual(perfil, hoje),
    )


def perfil_para_dict(perfil: Perfil) -> dict:
    return asdict(perfil)


def perfil_de_dict(dados: dict) -> Perfil:
    """Reconstrói um perfil a partir de um dict (tolerante a campos ausentes).

    Perfis antigos (sem os campos de ofensiva) são carregados normalmente; os
    campos novos entram com valor padrão.
    """
    p = Perfil()
    p.xp_total = dados.get("xp_total", 0)
    p.respondidas = dados.get("respondidas", 0)
    p.acertos = dados.get("acertos", 0)
    p.sequencia_atual = dados.get("sequencia_atual", 0)
    p.melhor_sequencia = dados.get("melhor_sequencia", 0)
    p.por_categoria = dados.get("por_categoria", {}) or {}
    p.dias_estudados = dados.get("dias_estudados", []) or []
    p.data_corrente = dados.get("data_corrente", "")
    p.respondidas_no_dia = dados.get("respondidas_no_dia", 0)
    p.melhor_ofensiva = dados.get("melhor_ofensiva", 0)
    p.revisao = dados.get("revisao", {}) or {}
    return p
