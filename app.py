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
import persistencia
import plantao
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
    .cabecalho { font-size: 2.0rem; font-weight: 800; letter-spacing: -0.5px;
                 margin-bottom: 0.1rem; }
    .subtitulo { color: #4A6363; margin-top: 0; margin-bottom: 1.2rem; }
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
        if chave.startswith("plantao_"):
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
            if chave.startswith("plantao_"):
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


barra_xp()
bloco_ofensiva()
st.divider()


# ---------------------------------------------------------------------------
# Tela inicial
# ---------------------------------------------------------------------------
if not st.session_state.iniciado:
    perfil = st.session_state.perfil
    aba_estudar, aba_dash, aba_cartas = st.tabs(
        ["📚 Estudar", "📊 Dashboard", "🃏 Cartas"]
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

        st.caption(
            f"{len(BANCO)} questões no banco. "
            "Uso educacional — não substitui protocolos oficiais nem julgamento "
            "clínico."
        )

    with aba_dash:
        render_dashboard(perfil)

    with aba_cartas:
        render_cartas(perfil)

# ---------------------------------------------------------------------------
# Tela de questões / resultado
# ---------------------------------------------------------------------------
else:
    if st.session_state.get("modo") == "plantao":
        render_plantao()
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
