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
XP_ACERTO_COM_DICA = 8   # acertou depois de usar dica
XP_ERRO = 2
XP_BONUS_SEQUENCIA = 30
PASSO_SEQUENCIA = 10

# Moedas 🪙 — economia simples de ganhar/gastar
MOEDAS_ACERTO = 1         # por acerto
MOEDAS_META_DIARIA = 5    # bônus ao cumprir a meta do dia
MOEDAS_CONQUISTA = 10     # por conquista desbloqueada (creditada no app)
DICA_CUSTO = 5            # preço de uma dica no quiz

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
    # histórico diário para gráficos: historico[dia] = {xp, respondidas, acertos}
    historico: dict = field(default_factory=dict)
    # conquistas desbloqueadas: {id: "YYYY-MM-DD"}
    conquistas: dict = field(default_factory=dict)
    # moedas 🪙 acumuladas
    moedas: int = 0
    # cartas colecionáveis: {id_da_carta: quantidade}
    cartas: dict = field(default_factory=dict)
    # dia (ISO) em que a dica grátis da carta foi usada pela última vez
    dica_gratis_usada_em: str = ""
    # melhor pontuação no modo plantão
    recorde_plantao: int = 0
    # casos clínicos concluídos: {caso_id: melhor_pontuacao}
    casos_completos: dict = field(default_factory=dict)
    # diagnósticos progressivos concluídos: {caso_id: melhor_pontuacao}
    diagnosticos_completos: dict = field(default_factory=dict)
    # pacientes virtuais concluídos: {paciente_id: melhor_pontuacao}
    pacientes_completos: dict = field(default_factory=dict)
    # bosses derrotados (ids)
    bosses_vencidos: list = field(default_factory=list)
    # histórico de prontuários fechados (resumos)
    historico_pacientes: list = field(default_factory=list)


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
    moedas_ganhas: int    # moedas 🪙 ganhas nesta resposta


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


def desempenho_por_categoria(perfil: Perfil) -> list[dict]:
    """Lista por tema com respondidas, acertos, precisão e XP.

    Ordenada da maior para a menor precisão (desempate: mais respondidas).
    """
    linhas = []
    for tema, d in perfil.por_categoria.items():
        resp = d.get("respondidas", 0)
        ac = d.get("acertos", 0)
        linhas.append(
            {
                "tema": tema,
                "respondidas": resp,
                "acertos": ac,
                "precisao": precisao(ac, resp),
                "xp": d.get("xp", 0),
            }
        )
    linhas.sort(key=lambda x: (-x["precisao"], -x["respondidas"], x["tema"]))
    return linhas


def destaques(perfil: Perfil, minimo: int = 3) -> tuple[dict | None, dict | None]:
    """Tema mais forte e o a reforçar, entre os com pelo menos 'minimo' respostas.

    Devolve (mais_forte, mais_fraca). Se só há um tema elegível, a segunda vem
    None. Se nenhum atinge o mínimo, devolve (None, None).
    """
    elegiveis = [
        l for l in desempenho_por_categoria(perfil) if l["respondidas"] >= minimo
    ]
    if not elegiveis:
        return None, None
    forte = max(elegiveis, key=lambda x: (x["precisao"], x["respondidas"]))
    fraca = min(elegiveis, key=lambda x: (x["precisao"], -x["respondidas"]))
    if forte["tema"] == fraca["tema"]:
        return forte, None
    return forte, fraca


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
    com_dica: bool = False,
    bonus_xp_pct: float = 0.0,
    bonus_moedas: int = 0,
) -> Resultado:
    """Atualiza o perfil com uma resposta e devolve o que mudou.

    'hoje' é a data (ISO, UTC) usada para a ofensiva diária; se None, usa a
    data UTC atual. 'com_dica' reduz o XP do acerto. 'bonus_xp_pct' e
    'bonus_moedas' vêm dos efeitos das cartas (calculados no app).
    """
    hoje = hoje or _hoje_utc()
    nivel_antes, _, _ = nivel_por_xp(perfil.xp_total)

    if acertou:
        ganho = XP_ACERTO_COM_DICA if com_dica else XP_ACERTO
    else:
        ganho = XP_ERRO
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
    if bonus_xp_pct:
        total = round(total * (1 + bonus_xp_pct))
    perfil.xp_total += total
    bucket["xp"] += total

    # histórico diário (para os gráficos de tendência)
    h = perfil.historico.setdefault(
        hoje, {"xp": 0, "respondidas": 0, "acertos": 0}
    )
    h["xp"] += total
    h["respondidas"] += 1
    if acertou:
        h["acertos"] += 1

    dia_completado = _registrar_dia(perfil, hoje)

    # Moedas: por acerto (+ bônus de cartas) + bônus ao fechar a meta do dia.
    moedas_ganhas = 0
    if acertou:
        moedas_ganhas += MOEDAS_ACERTO + bonus_moedas
    if dia_completado:
        moedas_ganhas += MOEDAS_META_DIARIA
    perfil.moedas += moedas_ganhas

    nivel_depois, _, _ = nivel_por_xp(perfil.xp_total)
    return Resultado(
        xp_ganho=total,
        bonus_sequencia=bonus,
        nivel_antes=nivel_antes,
        nivel_depois=nivel_depois,
        subiu_nivel=nivel_depois > nivel_antes,
        dia_completado=dia_completado,
        ofensiva=ofensiva_atual(perfil, hoje),
        moedas_ganhas=moedas_ganhas,
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
    p.historico = dados.get("historico", {}) or {}
    p.conquistas = dados.get("conquistas", {}) or {}
    p.moedas = dados.get("moedas", 0)
    p.cartas = dados.get("cartas", {}) or {}
    p.dica_gratis_usada_em = dados.get("dica_gratis_usada_em", "")
    p.recorde_plantao = dados.get("recorde_plantao", 0)
    p.casos_completos = dados.get("casos_completos", {}) or {}
    p.diagnosticos_completos = dados.get("diagnosticos_completos", {}) or {}
    p.pacientes_completos = dados.get("pacientes_completos", {}) or {}
    p.bosses_vencidos = dados.get("bosses_vencidos", []) or []
    p.historico_pacientes = dados.get("historico_pacientes", []) or []
    return p
