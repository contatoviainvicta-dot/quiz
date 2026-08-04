"""
Gamificação — lógica pura de XP, níveis, sequência e progresso por tema.

Não importa o Streamlit de propósito: assim dá para testar com pytest e, no
futuro, trocar a camada de persistência (agora é session_state, que reseta ao
atualizar a página; depois pode virar Supabase ou localStorage) sem tocar em
nada aqui.

O 'perfil' é serializável (perfil_para_dict / perfil_de_dict). Quando a
persistência real entrar, basta salvar/carregar esse dict — a lógica não muda.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

# ---------------------------------------------------------------------------
# Regras de XP — ficam todas num lugar só, fáceis de ajustar
# ---------------------------------------------------------------------------
XP_ACERTO = 15           # acertou a questão
XP_ERRO = 2              # errou (recompensa a tentativa, incentiva continuar)
XP_BONUS_SEQUENCIA = 30  # bônus a cada N acertos seguidos
PASSO_SEQUENCIA = 10     # tamanho da sequência que dá bônus

# Curva de níveis: o nível 1 exige 100 XP para virar o nível 2; cada nível
# seguinte exige +50 XP a mais que o anterior (100, 150, 200, ...).
XP_NIVEL_BASE = 100
XP_NIVEL_INCREMENTO = 50


@dataclass
class Perfil:
    """Progresso acumulado do usuário. Tudo aqui é serializável."""

    xp_total: int = 0
    respondidas: int = 0
    acertos: int = 0
    sequencia_atual: int = 0
    melhor_sequencia: int = 0
    # por_categoria[tema] = {"respondidas": int, "acertos": int, "xp": int}
    por_categoria: dict = field(default_factory=dict)


@dataclass
class Resultado:
    """O que aconteceu ao registrar uma resposta (para a interface exibir)."""

    xp_ganho: int
    bonus_sequencia: int
    nivel_antes: int
    nivel_depois: int
    subiu_nivel: bool


def perfil_novo() -> Perfil:
    """Cria um perfil zerado."""
    return Perfil()


def _bucket_categoria(perfil: Perfil, categoria: str) -> dict:
    """Devolve (criando se preciso) o dicionário de progresso de um tema."""
    return perfil.por_categoria.setdefault(
        categoria, {"respondidas": 0, "acertos": 0, "xp": 0}
    )


def nivel_por_xp(xp_total: int) -> tuple[int, int, int]:
    """Converte XP total em (nível, xp_dentro_do_nível, xp_para_o_próximo).

    Ex.: com 120 XP -> nível 2, 20 XP dentro do nível, faltam 150 para o 3.
    """
    nivel = 1
    restante = xp_total
    passo = XP_NIVEL_BASE
    while restante >= passo:
        restante -= passo
        nivel += 1
        passo += XP_NIVEL_INCREMENTO
    return nivel, restante, passo


def precisao(acertos: int, respondidas: int) -> int:
    """Precisão em % inteiro (0 quando ainda não respondeu nada)."""
    return round(100 * acertos / respondidas) if respondidas else 0


def registrar_resposta(perfil: Perfil, categoria: str, acertou: bool) -> Resultado:
    """Atualiza o perfil com uma resposta e devolve o que mudou.

    Aplica XP de acerto/erro, cuida da sequência de acertos e do bônus a cada
    PASSO_SEQUENCIA acertos seguidos, e informa se o usuário subiu de nível.
    """
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

    nivel_depois, _, _ = nivel_por_xp(perfil.xp_total)
    return Resultado(
        xp_ganho=total,
        bonus_sequencia=bonus,
        nivel_antes=nivel_antes,
        nivel_depois=nivel_depois,
        subiu_nivel=nivel_depois > nivel_antes,
    )


def perfil_para_dict(perfil: Perfil) -> dict:
    """Serializa o perfil (para salvar em JSON/banco no futuro)."""
    return asdict(perfil)


def perfil_de_dict(dados: dict) -> Perfil:
    """Reconstrói um perfil a partir de um dict (tolerante a campos ausentes)."""
    p = Perfil()
    p.xp_total = dados.get("xp_total", 0)
    p.respondidas = dados.get("respondidas", 0)
    p.acertos = dados.get("acertos", 0)
    p.sequencia_atual = dados.get("sequencia_atual", 0)
    p.melhor_sequencia = dados.get("melhor_sequencia", 0)
    p.por_categoria = dados.get("por_categoria", {}) or {}
    return p
