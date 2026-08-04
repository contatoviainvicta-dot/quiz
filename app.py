"""
Quiz de Pediatria — hub da aplicação (interface + fluxo).

Toda a lógica de dados vive em quiz_engine.py e as questões em data/*.json.
A gamificação (XP, níveis, sequência) vive em gamificacao.py.
Este arquivo cuida só da tela e da navegação.
"""

import streamlit as st

import gamificacao as gam
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
# Estado da sessão
# ---------------------------------------------------------------------------
def reiniciar() -> None:
    # Limpa só o estado do quiz atual. O PERFIL (XP, nível, sequência) é
    # preservado de propósito — ele acompanha o usuário entre as partidas.
    for chave in ["quiz", "indice", "acertos", "respondida", "escolha", "ultimo_resultado"]:
        st.session_state.pop(chave, None)
    st.session_state.iniciado = False


if "iniciado" not in st.session_state:
    st.session_state.iniciado = False

# O perfil nasce uma vez por sessão. (Na Fase 2 ele passará a ser carregado de
# uma persistência real; hoje vive só na sessão e reseta ao atualizar a página.)
if "perfil" not in st.session_state:
    st.session_state.perfil = gam.perfil_novo()


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
                        # Gamificação: registra a resposta e guarda o resultado
                        # para exibir o XP ganho no feedback abaixo.
                        st.session_state.ultimo_resultado = gam.registrar_resposta(
                            st.session_state.perfil, questao["categoria"], acertou
                        )
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
