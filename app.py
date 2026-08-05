"""
Quiz de Pediatria — hub da aplicação (interface + fluxo).

Dados das questões: quiz_engine.py + data/*.json.
Gamificação (XP, níveis, sequência): gamificacao.py.
Persistência do progresso (Supabase): persistencia.py.
Este arquivo cuida só da tela e da navegação.
"""

import streamlit as st

import gamificacao as gam
import persistencia
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


# ---------------------------------------------------------------------------
# Identificação do usuário (apelido) + carga do perfil
# O apelido fica na URL (?u=...) para sobreviver a refresh no mesmo dispositivo.
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


# recupera da URL, se já entrou antes neste dispositivo
if "identificador" not in st.session_state:
    u = st.query_params.get("u")
    if u:
        st.session_state.identificador = u
        st.session_state.perfil = persistencia.carregar_perfil(u)

# tela de entrada (se ainda não identificado)
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

# garante um perfil na sessão (fallback se algo limpou)
if "perfil" not in st.session_state:
    st.session_state.perfil = persistencia.carregar_perfil(IDENTIFICADOR)


def salvar() -> None:
    """Grava o perfil atual na persistência (no-op se não configurada)."""
    persistencia.salvar_perfil(IDENTIFICADOR, st.session_state.perfil)


# ---------------------------------------------------------------------------
# Estado da sessão do quiz
# ---------------------------------------------------------------------------
def reiniciar() -> None:
    # Limpa só o estado do quiz atual. O PERFIL (XP, nível, sequência) e o
    # IDENTIFICADOR são preservados de propósito.
    for chave in [
        "quiz",
        "indice",
        "acertos",
        "respondida",
        "escolha",
        "ultimo_resultado",
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
# Barra de XP / nível (sempre visível)
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
        fogo = f" · 🔥 {seq} seguidas" if seq >= 2 else ""
        st.markdown(
            f"**{perfil.xp_total} XP**  ·  faltam **{falta}** para o nível "
            f"{nivel + 1}{fogo}"
        )
        st.progress(xp_no_nivel / xp_prox)


barra_xp()
st.divider()


# ---------------------------------------------------------------------------
# Tela inicial
# ---------------------------------------------------------------------------
if not st.session_state.iniciado:
    with st.container(border=True):
        st.write("Escolha o tema e o número de questões para começar.")
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
            st.session_state.iniciado = True
            st.rerun()

    st.caption(
        f"{len(BANCO)} questões no banco. "
        "Uso educacional — não substitui protocolos oficiais nem julgamento clínico."
    )

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
                        # Gamificação + persistência: registra e salva.
                        st.session_state.ultimo_resultado = gam.registrar_resposta(
                            st.session_state.perfil, questao["categoria"], acertou
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

                # Feedback de XP
                resultado = st.session_state.get("ultimo_resultado")
                if resultado is not None:
                    linha = f"**+{resultado.xp_ganho} XP**"
                    if resultado.bonus_sequencia:
                        linha += (
                            f"  ·  🔥 bônus de sequência "
                            f"+{resultado.bonus_sequencia}"
                        )
                    st.markdown(linha)
                    if resultado.subiu_nivel:
                        st.success(
                            f"🎉 Você subiu para o nível {resultado.nivel_depois}!"
                        )

                rotulo = "Próxima questão" if indice + 1 < total else "Ver resultado"
                if st.button(rotulo, type="primary", use_container_width=True):
                    st.session_state.indice += 1
                    st.session_state.respondida = False
                    st.session_state.escolha = None
                    st.session_state.ultimo_resultado = None
                    st.rerun()

        st.caption(f"Placar: {st.session_state.acertos} acerto(s) até aqui.")
