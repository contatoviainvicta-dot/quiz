"""
Quiz de Pediatria — hub da aplicação (interface + fluxo).

Dados das questões: quiz_engine.py + data/*.json.
Gamificação (XP, níveis, sequência, ofensiva diária): gamificacao.py.
Persistência do progresso (Supabase): persistencia.py.
Este arquivo cuida só da tela e da navegação.
"""

import calendar as _cal
import dataclasses
import random
import time
from datetime import date, datetime, timedelta, timezone

import pandas as pd
import streamlit as st

import conquistas
import gamificacao as gam
import cartas
import casos as casos_mod
import bosses as boss_mod
import diagnostico as diag_mod
import pacientes as pac_mod
import persistencia
import plantao
import progressao
import revisao
from quiz_engine import (
    QuestaoInvalida,
    carregar_questoes,
    filtrar,
    listar_categorias,
    preparar_quiz,
)

# ---------------------------------------------------------------------------
# Configuração da página
# ---------------------------------------------------------------------------
st.set_page_config(page_title="Quiz de Pediatria", page_icon="🩺", layout="centered")

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Baloo+2:wght@500;600;700;800&family=Nunito+Sans:wght@400;600;700;800&display=swap');

    :root {
      --tinta:#153A35; --teal:#0E8388; --teal-2:#0A6A6E;
      --menta:#EAF3F3; --menta-borda:#D6E8E7; --papel:#F6FBFA;
      --ouro:#E6A700; --cinza:#6E8582;
    }

    /* Tipografia global */
    .stApp, .stApp p, .stApp li, .stApp label, .stApp span,
    .stApp div, .stMarkdown {
      font-family:'Nunito Sans', system-ui, 'Segoe UI Emoji',
        'Apple Color Emoji', 'Noto Color Emoji', sans-serif;
    }
    .stApp h1, .stApp h2, .stApp h3, .cabecalho, .kpi .valor,
    .patente .nome, .carta-reveal .nome {
      font-family:'Baloo 2', system-ui, 'Segoe UI Emoji',
        'Apple Color Emoji', 'Noto Color Emoji', sans-serif; letter-spacing:.2px;
    }
    .stApp code, .stApp pre { font-family:ui-monospace, monospace; }

    /* Botões */
    .stButton > button {
      border-radius:12px; font-weight:800; padding:.5rem 1rem;
      border:1px solid var(--menta-borda);
      transition:transform .06s ease, box-shadow .15s ease, border-color .15s ease;
    }
    .stButton > button:hover { transform:translateY(-1px);
      box-shadow:0 4px 14px rgba(14,131,136,.18); border-color:var(--teal); }
    .stButton > button:active { transform:translateY(0); }
    .stButton > button[kind="primary"],
    .stButton button[data-testid="stBaseButton-primary"],
    .stButton button[data-testid="baseButton-primary"] {
      background:linear-gradient(135deg,var(--teal),var(--teal-2));
      border:none; color:#fff; box-shadow:0 2px 8px rgba(14,131,136,.28); }
    .stButton > button[kind="primary"]:hover,
    .stButton button[data-testid="stBaseButton-primary"]:hover,
    .stButton button[data-testid="baseButton-primary"]:hover {
      box-shadow:0 7px 20px rgba(14,131,136,.34); }

    /* Container com borda */
    [data-testid="stVerticalBlockBorderWrapper"] {
      border-radius:16px !important; border-color:var(--menta-borda) !important;
      box-shadow:0 1px 3px rgba(20,60,55,.05); }

    /* Abas */
    .stTabs [data-baseweb="tab-list"] { gap:4px; }
    .stTabs [data-baseweb="tab"] { border-radius:10px 10px 0 0;
      font-weight:800; padding:6px 14px; }
    .stTabs [aria-selected="true"] { color:var(--teal); }

    /* Barra de progresso arredondada */
    .stProgress > div > div > div > div { border-radius:999px; }

    /* Hero */
    .cabecalho { font-size:2.35rem; font-weight:800; letter-spacing:-.5px;
                 line-height:1.08; margin-bottom:.1rem; color:var(--teal); }
    .subtitulo { color:var(--cinza); margin-top:0; margin-bottom:1.1rem;
                 font-size:.95rem; }
    .tag { display:inline-block; background:#EAF3F3; color:#0E8388;
           padding:2px 10px; border-radius:999px; font-size:0.8rem;
           font-weight:600; margin-bottom:0.6rem; }
    .cal { border-collapse: collapse; width: 100%; max-width: 360px; }
    .cal th { color:#4A6363; font-weight:600; font-size:.72rem; padding:4px 0; }
    .cal td { text-align:center; padding:2px 0; }
    .cal .cel { display:inline-flex; flex-direction:column; align-items:center;
                justify-content:center; width:36px; height:40px; border-radius:10px;
                font-size:.85rem; line-height:1.05; }
    .cal .num { }
    .cal .fogo { font-size:.72rem; margin-top:1px; }
    .cal .apagado { color:#C2CFCF; }
    .cal .estudou { color:#0E8388; font-weight:700; background:#EAF3F3; }
    .cal .hoje { outline:2px solid #0E8388; outline-offset:-2px; }
    .kpis { display:flex; flex-wrap:wrap; gap:12px; margin:.2rem 0 1rem; }
    .kpi { flex:1 1 130px; background:#fff; border:1px solid #E6EEEE;
           border-radius:14px; padding:12px 14px;
           box-shadow:0 1px 3px rgba(14,131,136,.06); }
    .kpi .rotulo { color:#4A6363; font-size:.7rem; font-weight:700;
                   text-transform:uppercase; letter-spacing:.4px; }
    .kpi .valor { color:#0E8388; font-size:1.6rem; font-weight:800;
                  line-height:1.15; margin-top:2px; }
    .kpi .sub { color:#7A8C8C; font-size:.72rem; margin-top:2px; }
    .tema { margin-bottom:11px; }
    .tema .cab { display:flex; justify-content:space-between; font-size:.9rem; }
    .tema .nome { font-weight:600; color:#1B2A2A; }
    .tema .pct { color:#0E8388; font-weight:700; }
    .barra { background:#EAF3F3; border-radius:999px; height:8px;
             overflow:hidden; margin-top:3px; }
    .barra > span { display:block; height:100%; background:#0E8388;
                    border-radius:999px; }
    .tema .meta { color:#7A8C8C; font-size:.72rem; margin-top:2px; }
    .medalhas { display:flex; flex-wrap:wrap; gap:10px; margin-top:.3rem; }
    .medalha { flex:1 1 150px; border:1px solid #E6EEEE; border-radius:12px;
               padding:10px 12px; background:#fff; }
    .medalha.bloq { opacity:.45; filter:grayscale(1); }
    .medalha .emoji { font-size:1.5rem; line-height:1; }
    .medalha .nome { font-weight:700; font-size:.85rem; color:#1B2A2A;
                     margin-top:3px; }
    .medalha .desc { font-size:.72rem; color:#7A8C8C; }
    .medalha .data { font-size:.68rem; color:#0E8388; font-weight:600;
                     margin-top:2px; }
    .moedas-pill { display:inline-flex; align-items:center; gap:6px;
                   background:linear-gradient(135deg,#FFF3CE,#FFE39B);
                   border:1px solid #E6C864; color:#7A5B12; font-weight:800;
                   padding:7px 15px; border-radius:999px; font-size:1.1rem;
                   box-shadow:0 1px 3px rgba(230,200,100,.35); white-space:nowrap; }
    .moedas-pill .ico { font-size:1.3rem; }
    .carta-reveal { max-width:230px; margin:.4rem auto; border:3px solid #ccc;
                    border-radius:16px; padding:16px; text-align:center;
                    box-shadow:0 3px 12px rgba(0,0,0,.10); }
    .carta-reveal .rar { font-weight:800; font-size:.72rem; text-transform:uppercase;
                         letter-spacing:1px; }
    .carta-reveal .emoji { font-size:3rem; line-height:1.1; }
    .carta-reveal .nome { font-weight:800; font-size:1.05rem; margin-top:2px; }
    .carta-reveal .desc { font-size:.78rem; color:#7A8C8C; margin-top:4px; }
    .carta-reveal .estado { margin-top:10px; font-weight:700; font-size:.9rem;
                            color:#0E8388; }
    .cartas-grid { display:flex; flex-wrap:wrap; gap:10px; margin-top:.4rem; }
    .carta { flex:1 1 120px; max-width:155px; border:2px solid #E6EEEE;
             border-radius:12px; padding:10px 8px; text-align:center;
             background:#fff; position:relative; }
    .carta.bloq { opacity:.5; filter:grayscale(1); }
    .carta .emoji { font-size:1.9rem; line-height:1.1; }
    .carta .nome { font-weight:700; font-size:.76rem; margin-top:3px;
                   line-height:1.1; }
    .carta .rar { font-size:.62rem; font-weight:700; text-transform:uppercase;
                  letter-spacing:.4px; margin-top:2px; }
    .carta .qtd { position:absolute; top:5px; right:8px; font-size:.66rem;
                  color:#7A8C8C; font-weight:700; }
    .carta .ef { font-size:.62rem; color:#0E8388; font-weight:700;
                 margin-top:3px; line-height:1.1; }
    .trilha { display:flex; flex-direction:column; gap:6px; margin-top:.4rem; }
    .patente { display:flex; align-items:center; gap:12px; padding:10px 12px;
               border-radius:12px; border:1px solid #E6EEEE; background:#fff; }
    .patente .ico { font-size:1.6rem; width:2.1rem; text-align:center; }
    .patente .nome { font-weight:700; color:#1B2A2A; }
    .patente .req { font-size:.72rem; color:#7A8C8C; }
    .patente.feita { border-color:#BFE0DF; }
    .patente.feita .nome { color:#0E8388; }
    .patente.atual { background:#EAF3F3; border:2px solid #0E8388; }
    .patente.bloq { opacity:.5; }

    /* Cartão de status da carreira */
    .status { border-radius:18px; overflow:hidden; background:#fff;
      border:1px solid var(--menta-borda);
      box-shadow:0 6px 22px rgba(14,131,136,.10); margin-bottom:1rem; }
    .status-cab { background:linear-gradient(135deg,#0E8388,#0A6A6E);
      color:#fff; padding:14px 16px; display:flex; align-items:center;
      justify-content:space-between; gap:10px; }
    .status-user .nome { font-family:'Baloo 2',system-ui,sans-serif;
      font-weight:800; font-size:1.2rem; line-height:1; }
    .status-user .patente { font-size:.8rem; opacity:.92; margin-top:3px; }
    .status-moedas { background:rgba(255,255,255,.18);
      border:1px solid rgba(255,255,255,.4); color:#fff; font-weight:800;
      padding:6px 13px; border-radius:999px; font-size:1.05rem;
      white-space:nowrap; }
    .status-corpo { padding:13px 16px 15px; }
    .status-xp-linha { display:flex; justify-content:space-between;
      font-size:.86rem; font-weight:700; color:var(--tinta); }
    .status-xp-linha .nivel { color:var(--teal); }
    .status .barra { height:10px; margin-top:5px; }
    .status-prox { color:var(--cinza); font-size:.72rem; margin-top:5px; }
    .status-chips { display:flex; flex-wrap:wrap; gap:8px; margin-top:11px; }
    .status-chip { background:var(--menta); border:1px solid var(--menta-borda);
      color:var(--tinta); font-weight:700; font-size:.78rem; padding:5px 11px;
      border-radius:999px; }
    .status-chip.fogo { background:#FFF1E8; border-color:#F6D3BE;
      color:#B5541F; }

    /* Micro-interações e refinos */
    .kpi, .medalha, .carta, .patente {
      transition:transform .08s ease, box-shadow .15s ease; }
    .kpi:hover, .medalha:hover, .patente:hover, .carta:hover {
      transform:translateY(-1px); box-shadow:0 5px 16px rgba(14,131,136,.12); }
    .barra > span { background:linear-gradient(90deg,#0E8388,#13A6AC); }
    .patente.atual { box-shadow:0 4px 16px rgba(14,131,136,.16); }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# Carregamento do banco (em cache — só lê os arquivos uma vez, não a cada rerun)
# ---------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def obter_banco() -> list[dict]:
    return carregar_questoes()


try:
    BANCO = obter_banco()
except (QuestaoInvalida, ValueError, OSError) as erro:
    st.error(f"Não foi possível carregar as questões: {erro}")
    st.stop()

if not BANCO:
    st.warning("Nenhuma questão encontrada na pasta data/. Adicione um arquivo JSON.")
    st.stop()

CATEGORIAS = listar_categorias(BANCO)


@st.cache_data(show_spinner=False)
def obter_casos() -> list[dict]:
    try:
        return casos_mod.carregar_casos("casos")
    except Exception:
        return []


CASOS = obter_casos()


@st.cache_data(show_spinner=False)
def obter_diagnosticos() -> list[dict]:
    try:
        return diag_mod.carregar("diagnosticos")
    except Exception:
        return []


DIAGS = obter_diagnosticos()


@st.cache_data(show_spinner=False)
def obter_pacientes() -> list[dict]:
    try:
        return pac_mod.carregar("pacientes")
    except Exception:
        return []


PACIENTES = obter_pacientes()

# Data de hoje (UTC) — usada pela ofensiva diária.
HOJE = datetime.now(timezone.utc).date().isoformat()


# ---------------------------------------------------------------------------
# Identificação do usuário (apelido) + carga do perfil
# ---------------------------------------------------------------------------
def _entrar(apelido: str) -> None:
    apelido = apelido.strip().lower()
    if not apelido:
        st.warning("Digite um apelido para continuar.")
        return
    st.session_state.identificador = apelido
    st.query_params["u"] = apelido
    st.session_state.perfil = persistencia.carregar_perfil(apelido)
    st.rerun()


if "identificador" not in st.session_state:
    u = st.query_params.get("u")
    if u:
        st.session_state.identificador = u
        st.session_state.perfil = persistencia.carregar_perfil(u)

if "identificador" not in st.session_state:
    st.markdown(
        '<div class="cabecalho">🩺 Quiz de Pediatria</div>', unsafe_allow_html=True
    )
    st.markdown(
        '<p class="subtitulo">Entre com um apelido para o seu progresso ser '
        "salvo e acompanhar você entre os dispositivos.</p>",
        unsafe_allow_html=True,
    )
    with st.container(border=True):
        apelido = st.text_input(
            "Apelido de estudo", max_chars=40, placeholder="ex.: rodrigo"
        )
        if st.button("Entrar", type="primary", use_container_width=True):
            _entrar(apelido)
        if not persistencia.disponivel():
            st.caption(
                "⚠️ Persistência não configurada: você pode entrar, mas o "
                "progresso não será salvo ainda (falta configurar o Supabase)."
            )
    st.stop()

IDENTIFICADOR = st.session_state.identificador

# Garante que o perfil na sessão tem todos os campos da versão ATUAL.
# Protege contra um objeto de uma versão anterior preso no session_state depois
# de um deploy (senão campos novos quebram com AttributeError). Compara os
# campos do objeto com os do Perfil atual — funciona para qualquer fase futura.
def _perfil_atual(obj) -> bool:
    if not dataclasses.is_dataclass(obj):
        return False
    campos = {f.name for f in dataclasses.fields(gam.Perfil)}
    return campos.issubset(set(vars(obj)))


_p = st.session_state.get("perfil")
if _p is None:
    st.session_state.perfil = persistencia.carregar_perfil(IDENTIFICADOR)
elif not _perfil_atual(_p):
    try:
        st.session_state.perfil = gam.perfil_de_dict(gam.perfil_para_dict(_p))
    except Exception:
        st.session_state.perfil = persistencia.carregar_perfil(IDENTIFICADOR)


def salvar() -> None:
    persistencia.salvar_perfil(IDENTIFICADOR, st.session_state.perfil)


# Efeitos passivos das cartas possuídas (XP / moedas / dica grátis diária).
EFEITOS = cartas.efeitos_ativos(st.session_state.perfil.cartas)


# ---------------------------------------------------------------------------
# Estado da sessão do quiz
# ---------------------------------------------------------------------------
def reiniciar() -> None:
    for chave in [
        "quiz",
        "indice",
        "acertos",
        "respondida",
        "escolha",
        "ultimo_resultado",
        "ultimo_sr",
        "modo",
        "novas_conquistas",
        "dica_usada",
        "dica_eliminada",
    ]:
        st.session_state.pop(chave, None)
    for chave in list(st.session_state.keys()):
        if (chave.startswith("plantao_") or chave.startswith("caso")
                or chave.startswith("diag") or chave.startswith("pac")
                or chave.startswith("boss")):
            st.session_state.pop(chave, None)
    st.session_state.iniciado = False


if "iniciado" not in st.session_state:
    st.session_state.iniciado = False


# ---------------------------------------------------------------------------
# Barra lateral: quem está estudando + trocar de usuário
# ---------------------------------------------------------------------------
with st.sidebar:
    st.caption(f"Estudando como **{IDENTIFICADOR}**")
    if persistencia.disponivel():
        st.caption("✅ Progresso salvo na nuvem.")
    else:
        st.warning("Sem persistência: o progresso não está sendo salvo.")
    if st.button("Trocar de usuário", use_container_width=True):
        for chave in [
            "identificador",
            "perfil",
            "iniciado",
            "quiz",
            "indice",
            "acertos",
            "respondida",
            "escolha",
            "ultimo_resultado",
            "ultimo_sr",
            "modo",
            "novas_conquistas",
            "dica_usada",
            "dica_eliminada",
            "ultima_carta",
        ]:
            st.session_state.pop(chave, None)
        for chave in list(st.session_state.keys()):
            if (chave.startswith("plantao_") or chave.startswith("caso")
                    or chave.startswith("diag") or chave.startswith("pac")
                    or chave.startswith("boss")):
                st.session_state.pop(chave, None)
        st.query_params.clear()
        st.rerun()


# ---------------------------------------------------------------------------
# Cabeçalho
# ---------------------------------------------------------------------------
st.markdown('<div class="cabecalho">🩺 Quiz de Pediatria</div>', unsafe_allow_html=True)
st.markdown(
    '<p class="subtitulo">Estudo rápido em perguntas e respostas — '
    "neonatologia, emergência, desenvolvimento e mais.</p>",
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# Barra de XP / nível + ofensiva (sempre visível)
# ---------------------------------------------------------------------------
def barra_xp() -> None:
    perfil = st.session_state.perfil
    nivel, xp_no_nivel, xp_prox = gam.nivel_por_xp(perfil.xp_total)

    col_a, col_b, col_c = st.columns([1.1, 3, 1.3], vertical_alignment="center")
    with col_a:
        st.metric("Nível", nivel)
    with col_b:
        falta = xp_prox - xp_no_nivel
        seq = perfil.sequencia_atual
        extra = f" · {seq} acertos seguidos" if seq >= 2 else ""
        st.markdown(
            f"**{perfil.xp_total} XP**  ·  faltam **{falta}** para o nível "
            f"{nivel + 1}{extra}"
        )
        st.progress(xp_no_nivel / xp_prox)
    with col_c:
        st.markdown(
            f'<div class="moedas-pill"><span class="ico">🪙</span>'
            f"{perfil.moedas}</div>",
            unsafe_allow_html=True,
        )


def bloco_ofensiva() -> None:
    perfil = st.session_state.perfil
    ofensiva = gam.ofensiva_atual(perfil, HOJE)

    concluiu_hoje = HOJE in perfil.dias_estudados
    feito = perfil.respondidas_no_dia if perfil.data_corrente == HOJE else 0

    linha = f"🔥 **{ofensiva}** dia(s) de ofensiva"
    if perfil.melhor_ofensiva:
        linha += f"  ·  melhor: {perfil.melhor_ofensiva}"
    st.markdown(linha)

    if concluiu_hoje:
        st.caption(f"✅ Meta de hoje concluída ({gam.META_DIARIA}/{gam.META_DIARIA}).")
    else:
        faltam = max(0, gam.META_DIARIA - feito)
        st.progress(min(feito, gam.META_DIARIA) / gam.META_DIARIA)
        st.caption(
            f"Meta de hoje: {feito}/{gam.META_DIARIA} questões — "
            f"faltam {faltam} para manter a ofensiva."
        )

    with st.expander("📅 Calendário do mês"):
        _render_calendario(perfil)


def _render_calendario(perfil) -> None:
    hoje = date.fromisoformat(HOJE)
    estudados = set(perfil.dias_estudados)

    meses = [
        "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
        "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro",
    ]
    st.markdown(f"**{meses[hoje.month - 1]} de {hoje.year}**")

    cal = _cal.Calendar(firstweekday=6)  # domingo primeiro
    semanas = cal.monthdayscalendar(hoje.year, hoje.month)

    html = ['<table class="cal"><thead><tr>']
    for h in ["D", "S", "T", "Q", "Q", "S", "S"]:
        html.append(f"<th>{h}</th>")
    html.append("</tr></thead><tbody>")
    for semana in semanas:
        html.append("<tr>")
        for dia in semana:
            if dia == 0:
                html.append("<td></td>")
                continue
            iso = date(hoje.year, hoje.month, dia).isoformat()
            estudou = iso in estudados
            classes = "cel " + ("estudou" if estudou else "apagado")
            if iso == HOJE:
                classes += " hoje"
            fogo = '<span class="fogo">🔥</span>' if estudou else ""
            html.append(
                f'<td><span class="{classes}">'
                f'<span class="num">{dia}</span>{fogo}</span></td>'
            )
        html.append("</tr>")
    html.append("</tbody></table>")
    st.markdown("".join(html), unsafe_allow_html=True)

    prefixo = f"{hoje.year:04d}-{hoje.month:02d}"
    no_mes = sum(1 for d in perfil.dias_estudados if d.startswith(prefixo))
    st.caption(f"🔥 {no_mes} dia(s) estudado(s) em {meses[hoje.month - 1]}.")


def _cards_html(cards) -> str:
    itens = "".join(
        f'<div class="kpi"><div class="rotulo">{r}</div>'
        f'<div class="valor">{v}</div><div class="sub">{s}</div></div>'
        for r, v, s in cards
    )
    return f'<div class="kpis">{itens}</div>'


def _contexto_conquistas(perfil) -> dict:
    """Estatísticas do perfil no formato que as conquistas avaliam."""
    nivel, _, _ = gam.nivel_por_xp(perfil.xp_total)
    dominadas = revisao.contagens(perfil.revisao, len(BANCO), HOJE)["dominadas"]
    max_tema = max(
        (d.get("respondidas", 0) for d in perfil.por_categoria.values()),
        default=0,
    )
    return {
        "respondidas": perfil.respondidas,
        "acertos": perfil.acertos,
        "precisao": gam.precisao(perfil.acertos, perfil.respondidas),
        "nivel": nivel,
        "melhor_sequencia": perfil.melhor_sequencia,
        "melhor_ofensiva": perfil.melhor_ofensiva,
        "dias_estudados": len(perfil.dias_estudados),
        "dominadas": dominadas,
        "max_tema": max_tema,
    }


def _verificar_conquistas(perfil) -> list:
    """Desbloqueia conquistas novas, grava a data e devolve os ids novos."""
    desbloqueadas = conquistas.avaliar(_contexto_conquistas(perfil))
    novas = [i for i in desbloqueadas if i not in perfil.conquistas]
    for i in novas:
        perfil.conquistas[i] = HOJE
    if novas:
        perfil.moedas += gam.MOEDAS_CONQUISTA * len(novas)
    return novas


def _grafico_tendencia(perfil) -> None:
    hoje = date.fromisoformat(HOJE)
    dias = [hoje - timedelta(days=i) for i in range(13, -1, -1)]
    rotulos = [d.strftime("%d/%m") for d in dias]
    xp = [perfil.historico.get(d.isoformat(), {}).get("xp", 0) for d in dias]
    qs = [perfil.historico.get(d.isoformat(), {}).get("respondidas", 0) for d in dias]

    st.markdown("**Tendência — últimos 14 dias**")
    st.caption("XP por dia")
    st.bar_chart(pd.DataFrame({"XP": xp}, index=rotulos), height=170, color="#0E8388")
    st.caption("Questões por dia")
    st.bar_chart(
        pd.DataFrame({"Questões": qs}, index=rotulos), height=150, color="#7FC5C8"
    )


def _render_medalhas(perfil) -> None:
    st.markdown("**Conquistas**")
    ganhas = sum(1 for c in conquistas.CONQUISTAS if c["id"] in perfil.conquistas)
    st.caption(f"{ganhas} de {len(conquistas.CONQUISTAS)} desbloqueadas")

    blocos = []
    for c in conquistas.CONQUISTAS:
        data = perfil.conquistas.get(c["id"])
        if data:
            try:
                data_fmt = date.fromisoformat(data).strftime("%d/%m/%Y")
            except Exception:
                data_fmt = data
            rodape = f'<div class="data">conquistada em {data_fmt}</div>'
            classe = "medalha"
        else:
            rodape = '<div class="data">bloqueada</div>'
            classe = "medalha bloq"
        blocos.append(
            f'<div class="{classe}"><div class="emoji">{c["emoji"]}</div>'
            f'<div class="nome">{c["nome"]}</div>'
            f'<div class="desc">{c["desc"]}</div>{rodape}</div>'
        )
    st.markdown(f'<div class="medalhas">{"".join(blocos)}</div>', unsafe_allow_html=True)


def render_dashboard(perfil) -> None:
    if perfil.respondidas == 0:
        st.info("Responda algumas questões para ver suas estatísticas aqui.")
        return

    # Desbloqueia conquistas que já foram atingidas (idempotente) e salva se novas.
    if _verificar_conquistas(perfil):
        salvar()

    nivel, _, _ = gam.nivel_por_xp(perfil.xp_total)
    prec = gam.precisao(perfil.acertos, perfil.respondidas)
    ofensiva = gam.ofensiva_atual(perfil, HOJE)

    st.markdown(
        _cards_html(
            [
                ("Nível", str(nivel), f"{perfil.xp_total} XP"),
                ("Precisão", f"{prec}%", f"{perfil.acertos}/{perfil.respondidas}"),
                ("Ofensiva", f"🔥 {ofensiva}", f"melhor: {perfil.melhor_ofensiva}"),
                (
                    "Respondidas",
                    str(perfil.respondidas),
                    f"melhor seq.: {perfil.melhor_sequencia}",
                ),
                ("Moedas", f"🪙 {perfil.moedas}", "para dicas"),
            ]
        ),
        unsafe_allow_html=True,
    )

    st.markdown("**Repetição espaçada**")
    cont = revisao.contagens(perfil.revisao, len(BANCO), HOJE)
    st.markdown(
        _cards_html(
            [
                ("Revisar hoje", str(cont["revisar_hoje"]), "pendentes"),
                ("Aprendendo", str(cont["aprendendo"]), "em progresso"),
                ("Dominadas", str(cont["dominadas"]), "nível máximo"),
                ("Novas", str(cont["novas"]), "não vistas"),
            ]
        ),
        unsafe_allow_html=True,
    )

    st.markdown("**Desempenho por tema**")
    linhas = [l for l in gam.desempenho_por_categoria(perfil) if l["respondidas"] > 0]
    if not linhas:
        st.caption("Responda algumas questões para ver o desempenho por tema.")
        return

    forte, fraca = gam.destaques(perfil)
    blocos = []
    for l in linhas:
        marca = ""
        if forte and l["tema"] == forte["tema"]:
            marca = " 💪"
        elif fraca and l["tema"] == fraca["tema"]:
            marca = " 📌"
        pct = l["precisao"]
        blocos.append(
            f'<div class="tema"><div class="cab">'
            f'<span class="nome">{l["tema"]}{marca}</span>'
            f'<span class="pct">{pct}%</span></div>'
            f'<div class="barra"><span style="width:{pct}%"></span></div>'
            f'<div class="meta">{l["acertos"]}/{l["respondidas"]} acertos · '
            f'{l["xp"]} XP</div></div>'
        )
    st.markdown("".join(blocos), unsafe_allow_html=True)
    if forte or fraca:
        st.caption("💪 tema mais forte · 📌 tema a reforçar")

    st.divider()
    _grafico_tendencia(perfil)

    st.divider()
    _render_medalhas(perfil)

    if perfil.historico_pacientes:
        st.divider()
        st.markdown("**📁 Histórico de pacientes**")
        for r in perfil.historico_pacientes[:20]:
            with st.container(border=True):
                st.markdown(f"**{r['nome']}** · {r['idade']}  —  {r['data']}")
                st.caption(
                    f"Condutas: {r.get('condutas', 0)}/{r.get('total_condutas', 0)} · "
                    f"Pontos: {r.get('score', 0)}/{r.get('maxp', 0)} · "
                    f"Questões do tema: {r.get('quiz_acertos', 0)}/"
                    f"{r.get('quiz_total', 0)}"
                )
                if r.get("desfecho"):
                    st.caption(r["desfecho"])


def render_cartas(perfil) -> None:
    st.markdown("**🃏 Cartas colecionáveis**")
    resumo = cartas.colecao_resumo(perfil.cartas)
    st.caption(
        f"Coleção: {resumo['possuidas']} de {resumo['total']} cartas · "
        + " · ".join(
            f"{cartas.RARIDADES[r]['rotulo']} {v['tem']}/{v['total']}"
            for r, v in resumo["por_raridade"].items()
        )
    )

    efeitos_txt = cartas.efeitos_texto(perfil.cartas)
    if efeitos_txt:
        st.success("🎁 Efeitos ativos: " + "  ·  ".join(efeitos_txt))

    # --- Loja de pacotes ---
    custo = cartas.PACOTE_CUSTO
    col_a, col_b = st.columns([1, 1.4], vertical_alignment="center")
    with col_a:
        st.markdown(
            f'<div class="moedas-pill"><span class="ico">🪙</span>'
            f"{perfil.moedas}</div>",
            unsafe_allow_html=True,
        )
    with col_b:
        if perfil.moedas >= custo:
            if st.button(
                f"Abrir pacote ({custo} 🪙)", type="primary", use_container_width=True
            ):
                perfil.moedas -= custo
                cid = cartas.abrir_pacote()
                nova = cid not in perfil.cartas
                perfil.cartas[cid] = perfil.cartas.get(cid, 0) + 1
                reembolso = 0 if nova else cartas.REEMBOLSO_DUPLICATA
                perfil.moedas += reembolso
                st.session_state.ultima_carta = {
                    "id": cid, "nova": nova, "reembolso": reembolso
                }
                salvar()
                d = cartas.definicao(cid)
                if nova and d["raridade"] == "lendaria":
                    st.balloons()
                st.rerun()
        else:
            st.caption(
                f"Junte {custo} 🪙 para abrir um pacote (você tem {perfil.moedas})."
            )

    # --- Carta revelada ---
    uc = st.session_state.get("ultima_carta")
    if uc:
        d = cartas.definicao(uc["id"])
        r = cartas.RARIDADES[d["raridade"]]
        estado = (
            "✨ Nova carta!"
            if uc["nova"]
            else f"Repetida · +{uc['reembolso']} 🪙 de volta"
        )
        efeito_html = (
            f'<div class="estado" style="color:{r["cor"]}">🎁 {d["efeito"]["texto"]}'
            f"</div>"
            if d.get("efeito")
            else ""
        )
        st.markdown(
            f'<div class="carta-reveal" style="border-color:{r["cor"]}">'
            f'<div class="rar" style="color:{r["cor"]}">{r["rotulo"]}</div>'
            f'<div class="emoji">{d["emoji"]}</div>'
            f'<div class="nome">{d["nome"]}</div>'
            f'<div class="desc">{d["desc"]}</div>'
            f'<div class="estado">{estado}</div>{efeito_html}</div>',
            unsafe_allow_html=True,
        )

    # --- Galeria da coleção ---
    st.markdown("**Coleção**")
    ordem = {"lendaria": 0, "epica": 1, "rara": 2, "comum": 3}
    catalogo = sorted(cartas.CARTAS, key=lambda c: ordem[c["raridade"]])
    blocos = []
    for c in catalogo:
        r = cartas.RARIDADES[c["raridade"]]
        qtd = perfil.cartas.get(c["id"], 0)
        if qtd > 0:
            badge = f'<div class="qtd">x{qtd}</div>' if qtd > 1 else ""
            efeito = (
                f'<div class="ef">🎁 {c["efeito"]["texto"]}</div>'
                if c.get("efeito")
                else ""
            )
            blocos.append(
                f'<div class="carta" style="border-color:{r["cor"]}">{badge}'
                f'<div class="emoji">{c["emoji"]}</div>'
                f'<div class="nome">{c["nome"]}</div>'
                f'<div class="rar" style="color:{r["cor"]}">{r["rotulo"]}</div>'
                f"{efeito}</div>"
            )
        else:
            blocos.append(
                '<div class="carta bloq">'
                '<div class="emoji">❓</div>'
                '<div class="nome">???</div>'
                f'<div class="rar">{r["rotulo"]}</div></div>'
            )
    st.markdown(
        f'<div class="cartas-grid">{"".join(blocos)}</div>', unsafe_allow_html=True
    )


def _timer_visual(segundos: int) -> None:
    """Cronômetro visual (JS no navegador). Só visual — o placar usa o tempo
    medido no servidor ao responder."""
    html = f"""
        <div style="font-family:system-ui,-apple-system,sans-serif;text-align:center">
          <div id="t" style="font-size:2rem;font-weight:800;color:#0E8388">
            {segundos}</div>
          <div style="background:#EAF3F3;border-radius:999px;height:10px;
                      overflow:hidden;margin-top:6px">
            <div id="bar" style="height:100%;background:#0E8388;width:100%"></div>
          </div>
        </div>
        <script>
          var total={segundos}, restante={segundos};
          var el=document.getElementById('t'), bar=document.getElementById('bar');
          var iv=setInterval(function(){{
            restante-=0.1;
            if(restante<=0){{
              restante=0; clearInterval(iv);
              el.textContent='Tempo esgotado'; el.style.color='#C0392B';
            }} else {{ el.textContent=Math.ceil(restante); }}
            bar.style.width=(100*restante/total)+'%';
            if(restante<=total*0.3){{
              bar.style.background='#C0392B'; el.style.color='#C0392B';
            }}
          }},100);
        </script>
        """
    # st.iframe é a API atual (Streamlit recente); cai para components.html
    # em versões antigas.
    if hasattr(st, "iframe"):
        st.iframe(html, height=95)
    else:  # pragma: no cover
        import streamlit.components.v1 as components

        components.html(html, height=95)


def render_plantao() -> None:
    quiz = st.session_state.plantao_quiz
    total = len(quiz)
    idx = st.session_state.plantao_indice
    perfil = st.session_state.perfil

    st.markdown("### 🚨 Modo Plantão")

    # ---- Fim da sessão ----
    if idx >= total:
        score = st.session_state.plantao_score
        acertos = st.session_state.plantao_acertos
        novo_recorde = score > perfil.recorde_plantao
        if novo_recorde:
            perfil.recorde_plantao = score
            salvar()

        st.metric("Pontuação", score)
        st.caption(
            f"{acertos} de {total} acertos · recorde: {perfil.recorde_plantao}"
        )
        if novo_recorde and score > 0:
            st.success("🏆 Novo recorde!")
            st.balloons()
        if st.button("Sair do plantão", type="primary", use_container_width=True):
            reiniciar()
            st.rerun()
        return

    questao = quiz[idx]

    # Marca o início do cronômetro na primeira exibição desta questão.
    if st.session_state.get("plantao_inicio_idx") != idx:
        st.session_state.plantao_inicio = time.time()
        st.session_state.plantao_inicio_idx = idx

    respondida = st.session_state.plantao_respondida
    st.caption(
        f"Questão {idx + 1} de {total}  ·  Pontos: {st.session_state.plantao_score}"
    )
    if not respondida:
        _timer_visual(plantao.LIMITE_SEG)

    with st.container(border=True):
        st.markdown(
            f'<span class="tag">{questao["categoria"]}</span>', unsafe_allow_html=True
        )
        st.markdown(f"**{questao['pergunta']}**")

        escolha = st.radio(
            "Selecione uma alternativa:",
            options=list(range(len(questao["opcoes"]))),
            format_func=lambda i: questao["opcoes"][i],
            index=None,
            key=f"plradio_{idx}",
            disabled=respondida,
        )

        if not respondida:
            if st.button("Responder", type="primary", use_container_width=True):
                if escolha is None:
                    st.warning("Escolha uma alternativa antes de responder.")
                else:
                    elapsed = time.time() - st.session_state.plantao_inicio
                    acertou = escolha == questao["correta"]
                    expirou = plantao.expirou(elapsed)
                    pontos = plantao.pontuar(acertou, elapsed)

                    st.session_state.plantao_escolha = escolha
                    st.session_state.plantao_respondida = True
                    st.session_state.plantao_score += pontos
                    if acertou:
                        st.session_state.plantao_acertos += 1
                    st.session_state.plantao_ultimo = {
                        "acertou": acertou, "expirou": expirou,
                        "pontos": pontos, "elapsed": elapsed,
                    }
                    # Conta como estudo normal (XP / moedas / revisão / conquistas).
                    gam.registrar_resposta(
                        perfil, questao["categoria"], acertou, hoje=HOJE,
                        bonus_xp_pct=EFEITOS["xp_pct"],
                        bonus_moedas=EFEITOS["moeda_flat"],
                    )
                    revisao.registrar(
                        perfil.revisao, revisao.qid(questao["pergunta"]), acertou, HOJE
                    )
                    _verificar_conquistas(perfil)
                    salvar()
                    st.rerun()
        else:
            correta = questao["correta"]
            u = st.session_state.plantao_ultimo
            if u["expirou"]:
                st.error(
                    f"⏱️ Tempo esgotado! +0 pontos. Resposta certa: "
                    f"**{questao['opcoes'][correta]}**"
                )
            elif u["acertou"]:
                st.success(
                    f"Correto! **+{u['pontos']} pontos** · {u['elapsed']:.1f}s"
                )
            else:
                st.error(
                    f"Incorreto. Resposta certa: **{questao['opcoes'][correta]}**"
                )

            rotulo = "Próxima" if idx + 1 < total else "Ver resultado"
            if st.button(rotulo, type="primary", use_container_width=True):
                st.session_state.plantao_indice += 1
                st.session_state.plantao_respondida = False
                st.session_state.plantao_escolha = None
                st.session_state.plantao_ultimo = None
                st.rerun()


def render_caso() -> None:
    caso = st.session_state.caso
    etapas = caso["etapas"]
    total = len(etapas)
    i = st.session_state.caso_etapa
    perfil = st.session_state.perfil

    st.markdown(f"### 🩺 {caso['titulo']}")
    st.progress(min(i, total) / total)

    # ---- Fim do caso ----
    if i >= total:
        score = st.session_state.caso_score
        maxp = st.session_state.caso_maxpontos
        prev = perfil.casos_completos.get(caso["id"], -1)
        melhorou = score > prev
        if melhorou:
            perfil.casos_completos[caso["id"]] = score
            # Recompensa: os pontos do caso viram XP + moedas (uma vez por melhora).
            perfil.xp_total += score
            perfil.moedas += 5
            h = perfil.historico.setdefault(
                HOJE, {"xp": 0, "respondidas": 0, "acertos": 0}
            )
            h["xp"] += score
            _verificar_conquistas(perfil)
            salvar()

        st.metric("Pontuação do caso", f"{score} / {maxp}")
        if melhorou and score > 0:
            st.success(f"🏆 Melhor resultado neste caso!  +{score} XP · +5 🪙")
        st.caption(
            "Uso educacional — confira sempre as condutas nos protocolos vigentes "
            "(SBP / Ministério da Saúde / seu serviço)."
        )
        if st.button("Voltar", type="primary", use_container_width=True):
            reiniciar()
            st.rerun()
        return

    etapa = etapas[i]
    st.caption(f"Etapa {i + 1} de {total}  ·  Pontos: {st.session_state.caso_score}")

    with st.container(border=True):
        st.markdown(f"**{etapa['titulo']}**")
        st.write(etapa["texto"])

        if etapa["tipo"] != "decisao":
            rotulo = "Continuar" if i + 1 < total else "Concluir caso"
            if st.button(rotulo, type="primary", use_container_width=True):
                st.session_state.caso_etapa += 1
                st.rerun()
            return

        respondida = st.session_state.caso_respondida
        escolha = st.radio(
            etapa["pergunta"],
            options=list(range(len(etapa["opcoes"]))),
            format_func=lambda j: etapa["opcoes"][j],
            index=None,
            key=f"caso_radio_{i}",
            disabled=respondida,
        )

        if not respondida:
            if st.button("Confirmar decisão", type="primary", use_container_width=True):
                if escolha is None:
                    st.warning("Escolha uma alternativa antes de confirmar.")
                else:
                    acertou = escolha == etapa["correta"]
                    if acertou:
                        st.session_state.caso_score += casos_mod.PONTOS_DECISAO
                    st.session_state.caso_escolha = escolha
                    st.session_state.caso_respondida = True
                    st.session_state.caso_ultimo = {"acertou": acertou}
                    st.rerun()
        else:
            correta = etapa["correta"]
            if st.session_state.caso_ultimo["acertou"]:
                st.success(
                    f"Boa decisão! +{casos_mod.PONTOS_DECISAO} pontos"
                )
            else:
                st.error(
                    f"Reveja: a melhor conduta seria **{etapa['opcoes'][correta]}**"
                )
            st.info(etapa["explicacao"])

            rotulo = "Continuar" if i + 1 < total else "Concluir caso"
            if st.button(rotulo, type="primary", use_container_width=True):
                st.session_state.caso_etapa += 1
                st.session_state.caso_respondida = False
                st.session_state.caso_escolha = None
                st.session_state.caso_ultimo = None
                st.rerun()


def render_diagnostico() -> None:
    caso = st.session_state.diag
    perfil = st.session_state.perfil
    solicitados = st.session_state.diag_solicitados
    fechado = st.session_state.diag_fechado

    st.markdown(f"### 🔎 {caso['titulo']}")
    with st.container(border=True):
        st.write(caso["apresentacao"])

    if not fechado:
        st.markdown(f"**Exames** — cada um custa {diag_mod.CUSTO_EXAME} pontos:")
        for idx, ex in enumerate(caso["exames"]):
            if idx in solicitados:
                st.success(f"🔬 **{ex['nome']}** — {ex['resultado']}")
            else:
                if st.button(
                    f"Solicitar: {ex['nome']}  (−{diag_mod.CUSTO_EXAME} pts)",
                    key=f"diag_ex_{idx}",
                    use_container_width=True,
                ):
                    st.session_state.diag_solicitados.append(idx)
                    st.rerun()

        st.divider()
        possiveis = diag_mod.pontuar(True, len(solicitados))
        st.caption(
            f"Exames solicitados: {len(solicitados)} · "
            f"se acertar agora, vale {possiveis} pontos."
        )
        escolha = st.radio(
            "Seu diagnóstico:",
            options=list(range(len(caso["diagnosticos"]))),
            format_func=lambda j: caso["diagnosticos"][j],
            index=None,
            key="diag_radio",
        )
        if st.button("Fechar diagnóstico", type="primary", use_container_width=True):
            if escolha is None:
                st.warning("Escolha um diagnóstico antes de fechar.")
            else:
                acertou = escolha == caso["correta"]
                pontos = diag_mod.pontuar(acertou, len(solicitados))
                st.session_state.diag_escolha = escolha
                st.session_state.diag_acertou = acertou
                st.session_state.diag_pontos = pontos
                st.session_state.diag_fechado = True
                prev = perfil.diagnosticos_completos.get(caso["id"], -1)
                if pontos > prev:
                    perfil.diagnosticos_completos[caso["id"]] = pontos
                    perfil.xp_total += pontos
                    perfil.moedas += 5
                    h = perfil.historico.setdefault(
                        HOJE, {"xp": 0, "respondidas": 0, "acertos": 0}
                    )
                    h["xp"] += pontos
                    _verificar_conquistas(perfil)
                salvar()
                st.rerun()
    else:
        correta = caso["correta"]
        n = len(solicitados)
        if st.session_state.diag_acertou:
            st.success(
                f"✅ Correto: **{caso['diagnosticos'][correta]}**  ·  "
                f"**{st.session_state.diag_pontos} pontos** ({n} exame(s))"
            )
        else:
            st.error(
                f"O diagnóstico correto era **{caso['diagnosticos'][correta]}**  ·  "
                f"0 pontos"
            )
        st.info(caso["explicacao"])
        st.caption(
            "Uso educacional — confira sempre as condutas nos protocolos vigentes "
            "(SBP / Ministério da Saúde / seu serviço)."
        )
        if st.button("Voltar", type="primary", use_container_width=True):
            reiniciar()
            st.rerun()


def _render_pac_questao(pac) -> None:
    """Questão-surpresa do tema, dentro do prontuário aberto."""
    perfil = st.session_state.perfil
    q = st.session_state.pac_q
    respondida = st.session_state.pac_q_respondida
    st.markdown("**🎓 Questão do tema**")
    with st.container(border=True):
        st.markdown(
            f'<span class="tag">{q["categoria"]}</span>', unsafe_allow_html=True
        )
        st.markdown(f"**{q['pergunta']}**")
        escolha = st.radio(
            "Selecione uma alternativa:",
            options=list(range(len(q["opcoes"]))),
            format_func=lambda j: q["opcoes"][j],
            index=None,
            key="pac_q_radio",
            disabled=respondida,
        )
        if not respondida:
            if st.button("Responder", type="primary", use_container_width=True):
                if escolha is None:
                    st.warning("Escolha uma alternativa antes de responder.")
                else:
                    acertou = escolha == q["correta"]
                    gam.registrar_resposta(
                        perfil, q["categoria"], acertou, hoje=HOJE,
                        bonus_xp_pct=EFEITOS["xp_pct"],
                        bonus_moedas=EFEITOS["moeda_flat"],
                    )
                    revisao.registrar(
                        perfil.revisao, revisao.qid(q["pergunta"]), acertou, HOJE
                    )
                    _verificar_conquistas(perfil)
                    st.session_state.pac_quiz_total += 1
                    if acertou:
                        st.session_state.pac_quiz_acertos += 1
                    st.session_state.pac_q_escolha = escolha
                    st.session_state.pac_q_respondida = True
                    salvar()
                    st.rerun()
        else:
            correta = q["correta"]
            if st.session_state.pac_q_escolha == correta:
                st.success("Correto!")
            else:
                st.error(f"Resposta certa: **{q['opcoes'][correta]}**")
            st.info(q["explicacao"])
            if st.button(
                "Voltar ao prontuário", type="primary", use_container_width=True
            ):
                st.session_state.pac_q = None
                st.session_state.pac_q_respondida = False
                st.session_state.pac_q_escolha = None
                st.rerun()


def _fechar_prontuario(pac) -> None:
    """Encerra o atendimento: recompensa, arquiva no histórico e marca fechado."""
    perfil = st.session_state.perfil
    score = st.session_state.pac_score
    maxp = st.session_state.pac_maxpontos
    momentos_feitos = min(st.session_state.pac_momento, len(pac["momentos"]))

    # Recompensa (uma vez, se melhorou a pontuação de condutas deste paciente).
    prev = perfil.pacientes_completos.get(pac["id"], -1)
    if score > prev:
        perfil.pacientes_completos[pac["id"]] = score
        perfil.xp_total += score
        perfil.moedas += 5
        h = perfil.historico.setdefault(
            HOJE, {"xp": 0, "respondidas": 0, "acertos": 0}
        )
        h["xp"] += score

    resumo = {
        "id": pac["id"], "nome": pac["nome"], "idade": pac["idade"],
        "data": HOJE, "score": score, "maxp": maxp,
        "condutas": momentos_feitos, "total_condutas": len(pac["momentos"]),
        "quiz_acertos": st.session_state.pac_quiz_acertos,
        "quiz_total": st.session_state.pac_quiz_total,
        "desfecho": pac.get("desfecho", ""),
    }
    perfil.historico_pacientes.insert(0, resumo)
    perfil.historico_pacientes = perfil.historico_pacientes[:50]
    _verificar_conquistas(perfil)
    salvar()
    st.session_state.pac_resumo = resumo
    st.session_state.pac_fechado = True


def render_paciente() -> None:
    pac = st.session_state.pac
    perfil = st.session_state.perfil
    momentos = pac["momentos"]
    total = len(momentos)

    # ---- Resumo de fechamento ----
    if st.session_state.get("pac_fechado"):
        r = st.session_state.pac_resumo
        st.markdown(f"### 📁 Prontuário encerrado: {r['nome']}")
        with st.container(border=True):
            st.markdown(f"**{r['nome']}** · {r['idade']}")
            st.write(
                f"Condutas conduzidas: {r['condutas']}/{r['total_condutas']}  ·  "
                f"Pontos: {r['score']}/{r['maxp']}  ·  "
                f"Questões do tema: {r['quiz_acertos']}/{r['quiz_total']}"
            )
            if r.get("desfecho"):
                st.caption(r["desfecho"])
        st.success("Prontuário arquivado no histórico (aba 📊 Dashboard).")
        if st.button("Voltar", type="primary", use_container_width=True):
            reiniciar()
            st.rerun()
        return

    st.markdown(f"### 🧑‍⚕️ Prontuário aberto: {pac['nome']}")

    # Ficha persistente.
    with st.container(border=True):
        st.markdown(f"**{pac['nome']}** · {pac['idade']} · {pac['sexo']}")
        if pac.get("comorbidades"):
            st.caption(f"Comorbidades: {pac['comorbidades']}")
        st.caption(pac["historia"])

    i = st.session_state.pac_momento
    st.caption(
        f"Condutas: {min(i, total)}/{total}  ·  Pontos: "
        f"{st.session_state.pac_score}  ·  Questões do tema: "
        f"{st.session_state.pac_quiz_acertos}/{st.session_state.pac_quiz_total}"
    )

    # Se há uma questão-surpresa ativa, ela toma a tela.
    if st.session_state.get("pac_q") is not None:
        _render_pac_questao(pac)
        return

    # ---- Conduta atual do atendimento (se ainda houver) ----
    if i < total:
        m = momentos[i]
        with st.container(border=True):
            if m.get("estado"):
                st.markdown(f"🩺 **Estado atual:** {m['estado']}")
            st.write(m["texto"])

            respondida = st.session_state.pac_respondida
            escolha = st.radio(
                m["pergunta"],
                options=list(range(len(m["opcoes"]))),
                format_func=lambda j: m["opcoes"][j],
                index=None,
                key=f"pac_radio_{i}",
                disabled=respondida,
            )
            if not respondida:
                if st.button(
                    "Decidir conduta", type="primary", use_container_width=True
                ):
                    if escolha is None:
                        st.warning("Escolha uma conduta antes de decidir.")
                    else:
                        acertou = escolha == m["correta"]
                        if acertou:
                            st.session_state.pac_score += pac_mod.PONTOS_MOMENTO
                        st.session_state.pac_escolha = escolha
                        st.session_state.pac_respondida = True
                        st.session_state.pac_ultimo = {"acertou": acertou}
                        st.rerun()
            else:
                correta = m["correta"]
                acertou = st.session_state.pac_ultimo["acertou"]
                if acertou:
                    st.success(f"Boa conduta! +{pac_mod.PONTOS_MOMENTO} pontos")
                else:
                    st.error(
                        f"Reveja: a melhor conduta seria **{m['opcoes'][correta]}**"
                    )
                st.info(m["explicacao"])
                evo = m.get("evolucao_boa") if acertou else m.get("evolucao_ruim")
                if evo:
                    st.markdown(f"➡️ *{evo}*")
                if st.button(
                    "Avançar no atendimento", type="primary",
                    use_container_width=True,
                ):
                    st.session_state.pac_momento += 1
                    st.session_state.pac_respondida = False
                    st.session_state.pac_escolha = None
                    st.session_state.pac_ultimo = None
                    st.rerun()
    else:
        st.success(
            "✅ Sem novas condutas pendentes. O prontuário segue aberto — "
            "revise com questões do tema ou feche quando quiser."
        )

    # ---- Ações sempre disponíveis ----
    st.divider()
    col_q, col_f = st.columns(2)
    with col_q:
        if st.button("🎓 Questão surpresa do tema", use_container_width=True):
            tema = pac.get("tema", "Todas")
            fonte = filtrar(BANCO, tema)
            if not fonte:
                fonte = BANCO
            st.session_state.pac_q = preparar_quiz(fonte, "Todas", 1)[0]
            st.session_state.pac_q_respondida = False
            st.session_state.pac_q_escolha = None
            st.rerun()
    with col_f:
        if st.button(
            "📁 Fechar prontuário", type="primary", use_container_width=True
        ):
            _fechar_prontuario(pac)
            st.rerun()


def render_boss() -> None:
    boss = st.session_state.boss
    perfil = st.session_state.perfil
    st.markdown(f"### {boss['emoji']} {boss['nome']}")

    fim = st.session_state.boss_fim
    if fim == "win":
        primeira = boss["id"] not in perfil.bosses_vencidos
        if primeira:
            perfil.bosses_vencidos.append(boss["id"])
            perfil.xp_total += boss["xp"]
            perfil.moedas += 20
            h = perfil.historico.setdefault(
                HOJE, {"xp": 0, "respondidas": 0, "acertos": 0}
            )
            h["xp"] += boss["xp"]
            _verificar_conquistas(perfil)
            salvar()
            st.balloons()
        st.success(f"🏆 Você derrotou o {boss['nome']}!")
        if primeira:
            st.success(f"Recompensa: +{boss['xp']} XP · +20 🪙")
        else:
            st.caption("Você já havia derrotado este chefão (prêmio só na 1ª vez).")
        if st.button("Voltar", type="primary", use_container_width=True):
            reiniciar()
            st.rerun()
        return

    if fim == "lose":
        st.error(f"💀 O {boss['nome']} venceu desta vez.")
        st.caption("Estude mais um pouco e volte para a revanche!")
        if st.button("Voltar", type="primary", use_container_width=True):
            reiniciar()
            st.rerun()
        return

    hp = st.session_state.boss_hp
    vidas = st.session_state.boss_vidas
    st.markdown(f"**HP do chefão** — {hp}/{boss['hp']}")
    st.progress(hp / boss["hp"])
    st.markdown(
        "**Suas vidas:** " + "❤️" * vidas + "🤍" * (boss["vidas"] - vidas)
    )

    idx = st.session_state.boss_idx
    pool = st.session_state.boss_pool
    if idx >= len(pool):  # segurança: acabou o pool sem decidir
        st.session_state.boss_fim = "lose"
        st.rerun()

    questao = pool[idx]
    respondida = st.session_state.boss_respondida
    with st.container(border=True):
        st.markdown(
            f'<span class="tag">{questao["categoria"]}</span>', unsafe_allow_html=True
        )
        st.markdown(f"**{questao['pergunta']}**")

        escolha = st.radio(
            "Selecione uma alternativa:",
            options=list(range(len(questao["opcoes"]))),
            format_func=lambda j: questao["opcoes"][j],
            index=None,
            key=f"boss_radio_{idx}",
            disabled=respondida,
        )

        if not respondida:
            if st.button("Atacar", type="primary", use_container_width=True):
                if escolha is None:
                    st.warning("Escolha uma alternativa antes de atacar.")
                else:
                    acertou = escolha == questao["correta"]
                    gam.registrar_resposta(
                        perfil, questao["categoria"], acertou, hoje=HOJE,
                        bonus_xp_pct=EFEITOS["xp_pct"],
                        bonus_moedas=EFEITOS["moeda_flat"],
                    )
                    revisao.registrar(
                        perfil.revisao, revisao.qid(questao["pergunta"]), acertou, HOJE
                    )
                    _verificar_conquistas(perfil)
                    if acertou:
                        st.session_state.boss_hp -= 1
                    else:
                        st.session_state.boss_vidas -= 1
                    st.session_state.boss_respondida = True
                    st.session_state.boss_ultimo = {"acertou": acertou}
                    if st.session_state.boss_hp <= 0:
                        st.session_state.boss_fim = "win"
                    elif st.session_state.boss_vidas <= 0:
                        st.session_state.boss_fim = "lose"
                    salvar()
                    st.rerun()
        else:
            correta = questao["correta"]
            if st.session_state.boss_ultimo["acertou"]:
                st.success("💥 Acertou! Dano no chefão.")
            else:
                st.error(
                    f"Errou — você perdeu uma vida. Resposta certa: "
                    f"**{questao['opcoes'][correta]}**"
                )
            st.info(questao["explicacao"])
            if st.button("Continuar", type="primary", use_container_width=True):
                st.session_state.boss_idx += 1
                st.session_state.boss_respondida = False
                st.session_state.boss_escolha = None
                st.session_state.boss_ultimo = None
                st.rerun()


def render_carreira(perfil) -> None:
    xp = perfil.xp_total
    prog = progressao.progresso(xp)
    atual = prog["atual"]
    prox = prog["proxima"]
    idx_atual = progressao.indice_atual(xp)

    st.markdown("**🗺️ Mapa de progressão** — de Interno(a) a Professor(a).")
    st.markdown(f"### {atual['emoji']} {atual['nome']}")
    if prox is not None:
        st.progress(prog["pct"])
        st.caption(
            f"{xp} XP · faltam **{prog['faltam']} XP** para "
            f"{prox['emoji']} {prox['nome']}"
        )
    else:
        st.success("🏆 Título máximo alcançado: Professor(a)!")

    # Trilha de patentes.
    blocos = []
    for i, n in enumerate(progressao.NIVEIS):
        if i < idx_atual:
            classe, status = "patente feita", "✓ alcançado"
        elif i == idx_atual:
            classe, status = "patente atual", "você está aqui"
        else:
            classe, status = "patente bloq", f"faltam {n['xp'] - xp} XP"
        blocos.append(
            f'<div class="{classe}"><div class="ico">{n["emoji"]}</div>'
            f'<div><div class="nome">{n["nome"]}</div>'
            f'<div class="req">{n["xp"]} XP · {status}</div></div></div>'
        )
    st.markdown(f'<div class="trilha">{"".join(blocos)}</div>', unsafe_allow_html=True)

    # Panorama — amarra todos os modos.
    st.divider()
    st.markdown("**Panorama da carreira**")
    nivel, _, _ = gam.nivel_por_xp(xp)
    casos_f = len(perfil.casos_completos)
    diag_f = len(perfil.diagnosticos_completos)
    boss_f = len(perfil.bosses_vencidos)
    med_f = len(perfil.conquistas)
    st.markdown(
        _cards_html(
            [
                ("Nível", str(nivel), f"{xp} XP"),
                ("Casos", f"{casos_f}/{len(CASOS)}", "clínicos"),
                ("Diagnósticos", f"{diag_f}/{len(DIAGS)}", "resolvidos"),
                ("Pacientes", str(len(perfil.historico_pacientes)), "atendidos"),
                ("Bosses", f"{boss_f}/{len(boss_mod.BOSSES)}", "derrotados"),
                ("Plantão", str(perfil.recorde_plantao), "recorde"),
                ("Medalhas", f"{med_f}/{len(conquistas.CONQUISTAS)}", "conquistas"),
            ]
        ),
        unsafe_allow_html=True,
    )
    st.caption(
        "Cada modo — quiz, plantão, casos, diagnósticos, pacientes e bosses — "
        "soma XP e faz você subir na carreira."
    )


def render_status(perfil) -> None:
    """Cartão de status: identidade + patente + moedas + nível/XP + ofensiva."""
    nome = st.session_state.identificador
    xp = perfil.xp_total
    nivel, xp_no_nivel, xp_prox = gam.nivel_por_xp(xp)
    patente = progressao.patente_atual(xp)
    ofensiva = gam.ofensiva_atual(perfil, HOJE)
    concluiu = HOJE in perfil.dias_estudados
    feito = perfil.respondidas_no_dia if perfil.data_corrente == HOJE else 0
    pct = int(round(100 * xp_no_nivel / xp_prox)) if xp_prox else 0
    falta = xp_prox - xp_no_nivel
    melhor = f" · melhor {perfil.melhor_ofensiva}" if perfil.melhor_ofensiva else ""
    meta = (
        "meta de hoje concluída ✓" if concluiu
        else f"meta hoje {min(feito, gam.META_DIARIA)}/{gam.META_DIARIA}"
    )
    st.markdown(
        f'<div class="status">'
        f'<div class="status-cab">'
        f'<div class="status-user"><div class="nome">{nome}</div>'
        f'<div class="patente">{patente["emoji"]} {patente["nome"]}</div></div>'
        f'<div class="status-moedas">🪙 {perfil.moedas}</div></div>'
        f'<div class="status-corpo">'
        f'<div class="status-xp-linha"><span class="nivel">Nível {nivel}</span>'
        f'<span>{xp_no_nivel} / {xp_prox} XP</span></div>'
        f'<div class="barra"><span style="width:{pct}%"></span></div>'
        f'<div class="status-prox">faltam {falta} XP para o nível {nivel + 1}</div>'
        f'<div class="status-chips">'
        f'<div class="status-chip fogo">🔥 {ofensiva} dia(s){melhor}</div>'
        f'<div class="status-chip">🎯 {meta}</div>'
        f'</div></div></div>',
        unsafe_allow_html=True,
    )


render_status(st.session_state.perfil)
with st.expander("📅 Calendário do mês"):
    _render_calendario(st.session_state.perfil)
st.divider()


# ---------------------------------------------------------------------------
# Tela inicial
# ---------------------------------------------------------------------------
if not st.session_state.iniciado:
    perfil = st.session_state.perfil
    aba_estudar, aba_dash, aba_carreira, aba_cartas = st.tabs(
        ["📚 Estudar", "📊 Dashboard", "🗺️ Carreira", "🃏 Cartas"]
    )

    with aba_estudar:
        # --- Revisão espaçada ---
        with st.container(border=True):
            st.markdown("**📚 Revisão espaçada**")
            cont = revisao.contagens(perfil.revisao, len(BANCO), HOJE)
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Revisar hoje", cont["revisar_hoje"])
            m2.metric("Aprendendo", cont["aprendendo"])
            m3.metric("Dominadas", cont["dominadas"])
            m4.metric("Novas", cont["novas"])

            pendentes = cont["revisar_hoje"]
            if pendentes > 0:
                n = min(pendentes, 20)  # sessão de revisão até 20 questões
                if st.button(
                    f"Revisar agora ({n})", type="primary", use_container_width=True
                ):
                    por_id = {revisao.qid(q["pergunta"]): q for q in BANCO}
                    ids = revisao.devidas(perfil.revisao, HOJE)
                    selecionadas = [por_id[i] for i in ids if i in por_id][:n]
                    st.session_state.quiz = preparar_quiz(
                        selecionadas, "Todas", len(selecionadas)
                    )
                    st.session_state.indice = 0
                    st.session_state.acertos = 0
                    st.session_state.respondida = False
                    st.session_state.escolha = None
                    st.session_state.ultimo_resultado = None
                    st.session_state.ultimo_sr = None
                    st.session_state.novas_conquistas = []
                    st.session_state.dica_usada = False
                    st.session_state.dica_eliminada = None
                    st.session_state.modo = "revisao"
                    st.session_state.iniciado = True
                    st.rerun()
            else:
                st.caption(
                    "Nada para revisar hoje 🎉 Responda questões novas para "
                    "alimentar a revisão — o que você errar volta amanhã, e o que "
                    "acertar volta em intervalos cada vez maiores."
                )

        # --- Novo quiz por tema ---
        with st.container(border=True):
            st.write("Ou faça um quiz novo por tema.")
            categoria = st.selectbox("Tema", CATEGORIAS, index=0)

            disponiveis = len(filtrar(BANCO, categoria))
            if disponiveis <= 1:
                quantidade = disponiveis
                st.caption(f"Este tema tem {disponiveis} questão disponível.")
            else:
                quantidade = st.slider(
                    "Número de questões",
                    min_value=1,
                    max_value=disponiveis,
                    value=min(5, disponiveis),
                )

            if st.button("Começar", type="primary", use_container_width=True):
                st.session_state.quiz = preparar_quiz(BANCO, categoria, quantidade)
                st.session_state.indice = 0
                st.session_state.acertos = 0
                st.session_state.respondida = False
                st.session_state.escolha = None
                st.session_state.ultimo_resultado = None
                st.session_state.ultimo_sr = None
                st.session_state.novas_conquistas = []
                st.session_state.dica_usada = False
                st.session_state.dica_eliminada = None
                st.session_state.modo = "tema"
                st.session_state.iniciado = True
                st.rerun()

        # --- Modo Plantão (cronometrado) ---
        with st.container(border=True):
            st.markdown(
                f"**🚨 Modo Plantão** — {plantao.QUESTOES} questões, "
                f"{plantao.LIMITE_SEG}s cada, pontos por velocidade."
            )
            st.caption(f"🏆 Recorde: {perfil.recorde_plantao} pontos")
            if st.button("Começar plantão", use_container_width=True):
                emerg = filtrar(BANCO, "Emergência")
                fonte = emerg if len(emerg) >= plantao.QUESTOES else BANCO
                st.session_state.plantao_quiz = preparar_quiz(
                    fonte, "Todas", plantao.QUESTOES
                )
                st.session_state.plantao_indice = 0
                st.session_state.plantao_score = 0
                st.session_state.plantao_acertos = 0
                st.session_state.plantao_respondida = False
                st.session_state.plantao_escolha = None
                st.session_state.plantao_ultimo = None
                st.session_state.plantao_inicio_idx = -1
                st.session_state.modo = "plantao"
                st.session_state.iniciado = True
                st.rerun()

        # --- Casos clínicos progressivos (caso surpresa) ---
        if CASOS:
            with st.container(border=True):
                st.markdown(
                    "**🩺 Casos clínicos** — um caso surpresa para você conduzir "
                    "etapa por etapa."
                )
                n_feitos = sum(
                    1 for c in CASOS if c["id"] in perfil.casos_completos
                )
                st.caption(f"{n_feitos} de {len(CASOS)} casos já concluídos.")
                if st.button(
                    "🎲 Caso clínico surpresa", use_container_width=True
                ):
                    info = random.choice(CASOS)
                    st.session_state.caso = info
                    st.session_state.caso_etapa = 0
                    st.session_state.caso_score = 0
                    st.session_state.caso_maxpontos = casos_mod.pontuacao_maxima(info)
                    st.session_state.caso_respondida = False
                    st.session_state.caso_escolha = None
                    st.session_state.caso_ultimo = None
                    st.session_state.modo = "caso"
                    st.session_state.iniciado = True
                    st.rerun()

        # --- Diagnóstico progressivo (surpresa) ---
        if DIAGS:
            with st.container(border=True):
                st.markdown(
                    "**🔎 Diagnóstico progressivo** — um caso surpresa: peça "
                    "exames e feche o diagnóstico. Menos exames = mais pontos."
                )
                n_diag = sum(
                    1 for c in DIAGS if c["id"] in perfil.diagnosticos_completos
                )
                st.caption(f"{n_diag} de {len(DIAGS)} casos já resolvidos.")
                if st.button(
                    "🎲 Diagnóstico surpresa", use_container_width=True
                ):
                    st.session_state.diag = random.choice(DIAGS)
                    st.session_state.diag_solicitados = []
                    st.session_state.diag_fechado = False
                    st.session_state.diag_escolha = None
                    st.session_state.diag_acertou = False
                    st.session_state.diag_pontos = 0
                    st.session_state.modo = "diagnostico"
                    st.session_state.iniciado = True
                    st.rerun()

        # --- Pacientes virtuais (prontuário surpresa) ---
        if PACIENTES:
            with st.container(border=True):
                st.markdown(
                    "**🧑‍⚕️ Paciente virtual** — receba um paciente surpresa, "
                    "conduza o atendimento com questões do tema e feche o "
                    "prontuário quando quiser."
                )
                st.caption(
                    f"{len(perfil.historico_pacientes)} prontuário(s) no histórico."
                )
                if st.button(
                    "🎲 Paciente surpresa", use_container_width=True
                ):
                    info_p = random.choice(PACIENTES)
                    st.session_state.pac = info_p
                    st.session_state.pac_momento = 0
                    st.session_state.pac_score = 0
                    st.session_state.pac_maxpontos = pac_mod.pontuacao_maxima(info_p)
                    st.session_state.pac_respondida = False
                    st.session_state.pac_escolha = None
                    st.session_state.pac_ultimo = None
                    st.session_state.pac_quiz_total = 0
                    st.session_state.pac_quiz_acertos = 0
                    st.session_state.pac_q = None
                    st.session_state.pac_q_respondida = False
                    st.session_state.pac_q_escolha = None
                    st.session_state.pac_fechado = False
                    st.session_state.modo = "paciente"
                    st.session_state.iniciado = True
                    st.rerun()

        # --- Bosses (chefões) ---
        with st.container(border=True):
            st.markdown("**👾 Bosses** — chefões que valem muito XP.")
            for b in boss_mod.BOSSES:
                if b["id"] in perfil.bosses_vencidos:
                    st.markdown(f"✅ {b['emoji']} **{b['nome']}** — derrotado")
                elif boss_mod.desbloqueado(b, perfil.respondidas):
                    if st.button(
                        f"Enfrentar {b['emoji']} {b['nome']}  (+{b['xp']} XP)",
                        key=f"btn_boss_{b['id']}",
                        use_container_width=True,
                    ):
                        tema = b["tema"]
                        fonte = filtrar(BANCO, tema) if tema != "Todas" else BANCO
                        if not fonte:
                            fonte = BANCO
                        n = min(boss_mod.tamanho_pool(b), len(fonte))
                        st.session_state.boss = b
                        st.session_state.boss_pool = preparar_quiz(fonte, "Todas", n)
                        st.session_state.boss_idx = 0
                        st.session_state.boss_hp = b["hp"]
                        st.session_state.boss_vidas = b["vidas"]
                        st.session_state.boss_respondida = False
                        st.session_state.boss_escolha = None
                        st.session_state.boss_ultimo = None
                        st.session_state.boss_fim = None
                        st.session_state.modo = "boss"
                        st.session_state.iniciado = True
                        st.rerun()
                else:
                    faltam = b["desbloqueio"] - perfil.respondidas
                    st.caption(
                        f"🔒 {b['emoji']} {b['nome']} — desbloqueia com "
                        f"{b['desbloqueio']} questões (faltam {faltam})."
                    )

        st.caption(
            f"{len(BANCO)} questões no banco. "
            "Uso educacional — não substitui protocolos oficiais nem julgamento "
            "clínico."
        )

    with aba_dash:
        render_dashboard(perfil)

    with aba_carreira:
        render_carreira(perfil)

    with aba_cartas:
        render_cartas(perfil)

# ---------------------------------------------------------------------------
# Tela de questões / resultado
# ---------------------------------------------------------------------------
else:
    if st.session_state.get("modo") == "plantao":
        render_plantao()
        st.stop()

    if st.session_state.get("modo") == "caso":
        render_caso()
        st.stop()

    if st.session_state.get("modo") == "diagnostico":
        render_diagnostico()
        st.stop()

    if st.session_state.get("modo") == "paciente":
        render_paciente()
        st.stop()

    if st.session_state.get("modo") == "boss":
        render_boss()
        st.stop()

    quiz = st.session_state.quiz
    total = len(quiz)
    indice = st.session_state.indice

    # ---- Fim do quiz ----
    if indice >= total:
        acertos = st.session_state.acertos
        percentual = round(100 * acertos / total)

        st.subheader("Resultado")
        col1, col2 = st.columns(2)
        col1.metric("Acertos", f"{acertos} de {total}")
        col2.metric("Aproveitamento", f"{percentual}%")
        st.progress(percentual / 100)

        if percentual >= 80:
            st.success("Excelente! Domínio sólido do conteúdo.")
        elif percentual >= 50:
            st.info("Bom caminho. Vale revisar os pontos que escaparam.")
        else:
            st.warning("Hora de revisar com calma — você chega lá.")

        if st.button("Recomeçar", type="primary", use_container_width=True):
            reiniciar()
            st.rerun()

    # ---- Questão atual ----
    else:
        questao = quiz[indice]

        st.progress(indice / total)
        if st.session_state.get("modo") == "revisao":
            st.caption(f"🔁 Revisão · questão {indice + 1} de {total}")
        else:
            st.caption(f"Questão {indice + 1} de {total}")
        st.markdown(
            f'<span class="tag">{questao["categoria"]}</span>', unsafe_allow_html=True
        )

        with st.container(border=True):
            st.markdown(f"**{questao['pergunta']}**")

            eliminada = st.session_state.get("dica_eliminada")
            opcoes_visiveis = [
                i for i in range(len(questao["opcoes"])) if i != eliminada
            ]
            escolha = st.radio(
                "Selecione uma alternativa:",
                options=opcoes_visiveis,
                format_func=lambda i: questao["opcoes"][i],
                index=None,
                key=f"radio_{indice}",
                disabled=st.session_state.respondida,
            )

            if not st.session_state.respondida:
                usou_dica = st.session_state.get("dica_usada", False)
                custo = gam.DICA_CUSTO
                perfil = st.session_state.perfil
                dica_gratis_disp = (
                    EFEITOS["dica_gratis"]
                    and perfil.dica_gratis_usada_em != HOJE
                )

                def _aplicar_dica():
                    erradas = [
                        i
                        for i in range(len(questao["opcoes"]))
                        if i != questao["correta"]
                    ]
                    st.session_state.dica_eliminada = random.choice(erradas)
                    st.session_state.dica_usada = True

                if usou_dica:
                    st.caption("💡 Dica usada: uma alternativa errada foi removida.")
                elif len(questao["opcoes"]) > 2:
                    if dica_gratis_disp:
                        if st.button(
                            "💡 Usar dica grátis (carta) — remove uma alternativa errada",
                            use_container_width=True,
                        ):
                            perfil.dica_gratis_usada_em = HOJE
                            _aplicar_dica()
                            salvar()
                            st.rerun()
                    elif perfil.moedas >= custo:
                        if st.button(
                            f"💡 Usar dica ({custo} 🪙) — remove uma alternativa errada",
                            use_container_width=True,
                        ):
                            perfil.moedas -= custo
                            _aplicar_dica()
                            salvar()
                            st.rerun()
                    else:
                        st.caption(
                            f"💡 Dica custa {custo} 🪙 — você tem {perfil.moedas}."
                        )

                if st.button("Responder", type="primary", use_container_width=True):
                    if escolha is None:
                        st.warning("Escolha uma alternativa antes de responder.")
                    else:
                        st.session_state.escolha = escolha
                        st.session_state.respondida = True
                        acertou = escolha == questao["correta"]
                        if acertou:
                            st.session_state.acertos += 1
                        st.session_state.ultimo_resultado = gam.registrar_resposta(
                            st.session_state.perfil,
                            questao["categoria"],
                            acertou,
                            hoje=HOJE,
                            com_dica=st.session_state.get("dica_usada", False),
                            bonus_xp_pct=EFEITOS["xp_pct"],
                            bonus_moedas=EFEITOS["moeda_flat"],
                        )
                        # Repetição espaçada: reagenda esta questão.
                        st.session_state.ultimo_sr = revisao.registrar(
                            st.session_state.perfil.revisao,
                            revisao.qid(questao["pergunta"]),
                            acertou,
                            HOJE,
                        )
                        st.session_state.novas_conquistas = _verificar_conquistas(
                            st.session_state.perfil
                        )
                        salvar()
                        st.rerun()
            else:
                correta = questao["correta"]
                escolhida = st.session_state.escolha
                if escolhida == correta:
                    st.success("Correto!")
                else:
                    st.error(
                        f"Incorreto. Resposta certa: **{questao['opcoes'][correta]}**"
                    )
                st.info(questao["explicacao"])

                resultado = st.session_state.get("ultimo_resultado")
                if resultado is not None:
                    linha = f"**+{resultado.xp_ganho} XP**"
                    if resultado.bonus_sequencia:
                        linha += (
                            f"  ·  ⭐ bônus de sequência "
                            f"+{resultado.bonus_sequencia}"
                        )
                    if resultado.moedas_ganhas:
                        linha += f"  ·  +{resultado.moedas_ganhas} 🪙"
                    st.markdown(linha)
                    if resultado.subiu_nivel:
                        st.success(
                            f"🎉 Você subiu para o nível {resultado.nivel_depois}!"
                        )
                    if resultado.dia_completado:
                        st.success(
                            f"🔥 Meta diária concluída! Ofensiva de "
                            f"{resultado.ofensiva} dia(s)."
                        )

                sr = st.session_state.get("ultimo_sr")
                if sr is not None:
                    dias = revisao.intervalo_do_nivel(sr["nivel"])
                    quando = "amanhã" if dias == 1 else f"em {dias} dias"
                    st.caption(f"🔁 Esta questão volta para revisão {quando}.")

                for cid in st.session_state.get("novas_conquistas") or []:
                    d = conquistas.definicao(cid)
                    if d:
                        st.success(
                            f"{d['emoji']} Conquista desbloqueada: **{d['nome']}**!"
                        )

                rotulo = "Próxima questão" if indice + 1 < total else "Ver resultado"
                if st.button(rotulo, type="primary", use_container_width=True):
                    st.session_state.indice += 1
                    st.session_state.respondida = False
                    st.session_state.escolha = None
                    st.session_state.ultimo_resultado = None
                    st.session_state.ultimo_sr = None
                    st.session_state.novas_conquistas = []
                    st.session_state.dica_usada = False
                    st.session_state.dica_eliminada = None
                    st.rerun()

        st.caption(f"Placar: {st.session_state.acertos} acerto(s) até aqui.")
