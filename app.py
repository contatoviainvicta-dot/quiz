"""
Quiz de Pediatria — hub da aplicação (interface + fluxo).

Dados das questões: quiz_engine.py + data/*.json.
Gamificação (XP, níveis, sequência, ofensiva diária): gamificacao.py.
Persistência do progresso (Supabase): persistencia.py.
Este arquivo cuida só da tela e da navegação.
"""

import calendar as _cal
import dataclasses
from datetime import date, datetime, timezone

import streamlit as st

import gamificacao as gam
import persistencia
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
    ]:
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
        ]:
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

    col_a, col_b = st.columns([1, 3], vertical_alignment="center")
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


def render_dashboard(perfil) -> None:
    if perfil.respondidas == 0:
        st.info("Responda algumas questões para ver suas estatísticas aqui.")
        return

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


barra_xp()
bloco_ofensiva()
st.divider()


# ---------------------------------------------------------------------------
# Tela inicial
# ---------------------------------------------------------------------------
if not st.session_state.iniciado:
    perfil = st.session_state.perfil
    aba_estudar, aba_dash = st.tabs(["📚 Estudar", "📊 Dashboard"])

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
                st.session_state.modo = "tema"
                st.session_state.iniciado = True
                st.rerun()

        st.caption(
            f"{len(BANCO)} questões no banco. "
            "Uso educacional — não substitui protocolos oficiais nem julgamento "
            "clínico."
        )

    with aba_dash:
        render_dashboard(perfil)

# ---------------------------------------------------------------------------
# Tela de questões / resultado
# ---------------------------------------------------------------------------
else:
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

            escolha = st.radio(
                "Selecione uma alternativa:",
                options=list(range(len(questao["opcoes"]))),
                format_func=lambda i: questao["opcoes"][i],
                index=None,
                key=f"radio_{indice}",
                disabled=st.session_state.respondida,
            )

            if not st.session_state.respondida:
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
                        )
                        # Repetição espaçada: reagenda esta questão.
                        st.session_state.ultimo_sr = revisao.registrar(
                            st.session_state.perfil.revisao,
                            revisao.qid(questao["pergunta"]),
                            acertou,
                            HOJE,
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

                rotulo = "Próxima questão" if indice + 1 < total else "Ver resultado"
                if st.button(rotulo, type="primary", use_container_width=True):
                    st.session_state.indice += 1
                    st.session_state.respondida = False
                    st.session_state.escolha = None
                    st.session_state.ultimo_resultado = None
                    st.session_state.ultimo_sr = None
                    st.rerun()

        st.caption(f"Placar: {st.session_state.acertos} acerto(s) até aqui.")
