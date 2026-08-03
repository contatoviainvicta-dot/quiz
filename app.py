"""
Quiz de Pediatria — estudo rápido em formato de perguntas e respostas.
Feito em Streamlit. Pronto para publicar no Streamlit Community Cloud via GitHub.

Autor: Rodrigo
Uso educacional. Não substitui protocolos oficiais nem julgamento clínico.
"""

import random
import streamlit as st

# ---------------------------------------------------------------------------
# Configuração da página
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Quiz de Pediatria",
    page_icon="🩺",
    layout="centered",
)

# Um toque de estilo, sem depender de classes internas do Streamlit
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
# Banco de questões
# Cada questão: categoria, pergunta, opções, índice da correta, explicação.
# Conteúdo de nível de graduação, baseado em ensino clássico de pediatria.
# ---------------------------------------------------------------------------
QUESTOES = [
    {
        "categoria": "Neonatologia",
        "pergunta": "Quantos parâmetros o escore de Apgar avalia?",
        "opcoes": ["3", "4", "5", "6"],
        "correta": 2,
        "explicacao": "São 5: frequência cardíaca, esforço respiratório, tônus "
        "muscular, irritabilidade reflexa e cor. Mnemônico em inglês: "
        "Appearance, Pulse, Grimace, Activity, Respiration.",
    },
    {
        "categoria": "Neonatologia",
        "pergunta": "Em quais momentos o Apgar é aferido de rotina?",
        "opcoes": [
            "No 1º e no 5º minuto de vida",
            "Apenas ao nascer",
            "No 5º e no 10º minuto",
            "A cada minuto na 1ª hora",
        ],
        "correta": 0,
        "explicacao": "1º e 5º minuto. Se o escore for menor que 7 no 5º minuto, "
        "repete-se a cada 5 minutos até 20 minutos.",
    },
    {
        "categoria": "Neonatologia",
        "pergunta": "Um recém-nascido com FC de 90 bpm recebe quantos pontos no "
        "item frequência cardíaca do Apgar?",
        "opcoes": ["0", "1", "2", "Não pontua"],
        "correta": 1,
        "explicacao": "FC ausente = 0; FC abaixo de 100 bpm = 1; FC de 100 bpm ou "
        "mais = 2. Como 90 é menor que 100, o item recebe 1 ponto.",
    },
    {
        "categoria": "Neonatologia",
        "pergunta": "Na reanimação neonatal, a FC permanece abaixo de 60 bpm "
        "apesar de ventilação com pressão positiva adequada. Qual a conduta?",
        "opcoes": [
            "Manter só a ventilação e reavaliar em 1 minuto",
            "Iniciar massagem cardíaca coordenada com a ventilação",
            "Administrar oxigênio livre",
            "Aspirar vias aéreas novamente",
        ],
        "correta": 1,
        "explicacao": "FC abaixo de 60 bpm após VPP efetiva indica massagem "
        "cardíaca, coordenada com a ventilação na relação 3:1.",
    },
    {
        "categoria": "Neonatologia",
        "pergunta": "Qual a faixa considerada normal para a frequência cardíaca do "
        "recém-nascido?",
        "opcoes": [
            "60 a 100 bpm",
            "80 a 120 bpm",
            "120 a 160 bpm",
            "160 a 200 bpm",
        ],
        "correta": 2,
        "explicacao": "A FC normal do recém-nascido fica em torno de 120 a 160 bpm. "
        "A frequência respiratória normal é de 40 a 60 irpm.",
    },
    {
        "categoria": "Neonatologia",
        "pergunta": "Icterícia que surge nas primeiras 24 horas de vida deve ser "
        "considerada:",
        "opcoes": [
            "Sempre fisiológica",
            "Sempre patológica, exige investigação",
            "Esperada no aleitamento materno",
            "Sinal de boa adaptação",
        ],
        "correta": 1,
        "explicacao": "Icterícia nas primeiras 24 horas é sempre patológica e "
        "precisa de investigação. A icterícia fisiológica surge após 24 horas.",
    },
    {
        "categoria": "Neonatologia",
        "pergunta": "A vitamina K aplicada ao nascimento previne qual condição?",
        "opcoes": [
            "Anemia ferropriva",
            "Doença hemorrágica do recém-nascido",
            "Hipoglicemia neonatal",
            "Sepse precoce",
        ],
        "correta": 1,
        "explicacao": "A vitamina K profilática previne a doença hemorrágica do "
        "recém-nascido (sangramento por deficiência de vitamina K).",
    },
    {
        "categoria": "Imunização",
        "pergunta": "Quais vacinas são aplicadas ao nascimento no calendário do "
        "PNI (Brasil)?",
        "opcoes": [
            "BCG e Hepatite B",
            "Tríplice viral e VIP",
            "Pentavalente e Rotavírus",
            "Meningocócica C e Pneumocócica",
        ],
        "correta": 0,
        "explicacao": "Ao nascer aplicam-se BCG (dose única) e a 1ª dose de "
        "Hepatite B, idealmente nas primeiras 12 a 24 horas de vida.",
    },
    {
        "categoria": "Imunização",
        "pergunta": "A vacina BCG protege principalmente contra as formas graves "
        "de qual doença?",
        "opcoes": ["Coqueluche", "Tuberculose", "Difteria", "Hepatite"],
        "correta": 1,
        "explicacao": "A BCG protege contra as formas graves da tuberculose, "
        "como a tuberculose miliar e a meningite tuberculosa.",
    },
    {
        "categoria": "Desenvolvimento",
        "pergunta": "Por volta de que idade surge o sorriso social?",
        "opcoes": ["Ao nascer", "2 meses", "6 meses", "12 meses"],
        "correta": 1,
        "explicacao": "O sorriso social costuma aparecer por volta de 2 meses "
        "(entre 6 e 8 semanas).",
    },
    {
        "categoria": "Desenvolvimento",
        "pergunta": "Qual a idade média em que a criança senta sem apoio?",
        "opcoes": ["3 meses", "6 meses", "9 meses", "12 meses"],
        "correta": 1,
        "explicacao": "Sentar sem apoio ocorre em média aos 6 meses.",
    },
    {
        "categoria": "Desenvolvimento",
        "pergunta": "Qual a idade média para a marcha sem apoio?",
        "opcoes": ["9 meses", "12 meses", "18 meses", "24 meses"],
        "correta": 1,
        "explicacao": "A marcha independente surge em média aos 12 meses, com "
        "faixa de normalidade entre 9 e 15 meses.",
    },
    {
        "categoria": "Emergência",
        "pergunta": "Qual o principal agente da bronquiolite viral aguda no "
        "lactente?",
        "opcoes": [
            "Influenza",
            "Vírus sincicial respiratório (VSR)",
            "Adenovírus",
            "Rinovírus",
        ],
        "correta": 1,
        "explicacao": "O vírus sincicial respiratório (VSR) é a causa mais comum "
        "de bronquiolite em lactentes.",
    },
    {
        "categoria": "Emergência",
        "pergunta": "A crise febril típica ocorre caracteristicamente em qual "
        "faixa etária?",
        "opcoes": [
            "0 a 3 meses",
            "6 meses a 5 anos",
            "5 a 10 anos",
            "Acima de 10 anos",
        ],
        "correta": 1,
        "explicacao": "A crise febril típica ocorre entre 6 meses e 5 anos, com "
        "pico por volta dos 18 meses.",
    },
    {
        "categoria": "Emergência",
        "pergunta": "Na diarreia aguda do lactente, qual a principal complicação a "
        "ser prevenida?",
        "opcoes": [
            "Desidratação",
            "Anemia",
            "Hipertensão",
            "Obesidade",
        ],
        "correta": 0,
        "explicacao": "A desidratação é o maior risco. A hidratação oral com "
        "sais de reidratação é a base do tratamento.",
    },
    {
        "categoria": "Aleitamento",
        "pergunta": "Até que idade se recomenda o aleitamento materno exclusivo?",
        "opcoes": ["3 meses", "4 meses", "6 meses", "12 meses"],
        "correta": 2,
        "explicacao": "Recomenda-se aleitamento materno exclusivo até os 6 meses "
        "e complementado até 2 anos ou mais.",
    },
    {
        "categoria": "Farmacologia",
        "pergunta": "Qual a dose usual de paracetamol para analgesia/antitermia "
        "em pediatria, por dose?",
        "opcoes": [
            "1 a 3 mg/kg",
            "10 a 15 mg/kg",
            "30 a 50 mg/kg",
            "Dose fixa de 500 mg",
        ],
        "correta": 1,
        "explicacao": "A dose usual é de 10 a 15 mg/kg por dose, a cada 4 a 6 "
        "horas, respeitando o teto diário. Sempre confira o protocolo local.",
    },
]

CATEGORIAS = ["Todas"] + sorted({q["categoria"] for q in QUESTOES})


# ---------------------------------------------------------------------------
# Preparação das questões (embaralha ordem e alternativas)
# ---------------------------------------------------------------------------
def preparar_quiz(categoria: str, quantidade: int) -> list:
    """Filtra por categoria, embaralha e reordena as alternativas."""
    pool = [q for q in QUESTOES if categoria == "Todas" or q["categoria"] == categoria]
    random.shuffle(pool)
    pool = pool[:quantidade]

    preparadas = []
    for q in pool:
        indices = list(range(len(q["opcoes"])))
        random.shuffle(indices)
        opcoes = [q["opcoes"][i] for i in indices]
        nova_correta = indices.index(q["correta"])
        preparadas.append(
            {
                "categoria": q["categoria"],
                "pergunta": q["pergunta"],
                "opcoes": opcoes,
                "correta": nova_correta,
                "explicacao": q["explicacao"],
            }
        )
    return preparadas


# ---------------------------------------------------------------------------
# Estado da sessão
# ---------------------------------------------------------------------------
def reiniciar():
    for chave in ["quiz", "indice", "acertos", "respondida", "escolha"]:
        st.session_state.pop(chave, None)
    st.session_state.iniciado = False


if "iniciado" not in st.session_state:
    st.session_state.iniciado = False


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
# Tela inicial
# ---------------------------------------------------------------------------
if not st.session_state.iniciado:
    with st.container(border=True):
        st.write("Escolha o tema e o número de questões para começar.")
        categoria = st.selectbox("Tema", CATEGORIAS, index=0)

        disponiveis = len(
            [q for q in QUESTOES if categoria == "Todas" or q["categoria"] == categoria]
        )
        maximo = max(3, disponiveis)
        quantidade = st.slider(
            "Número de questões",
            min_value=3,
            max_value=maximo,
            value=min(5, maximo),
        )

        if st.button("Começar", type="primary", use_container_width=True):
            st.session_state.quiz = preparar_quiz(categoria, quantidade)
            st.session_state.indice = 0
            st.session_state.acertos = 0
            st.session_state.respondida = False
            st.session_state.escolha = None
            st.session_state.iniciado = True
            st.rerun()

    st.caption(
        "Uso educacional. Não substitui protocolos oficiais nem julgamento clínico."
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

        st.progress((indice) / total)
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

            # Botão responder
            if not st.session_state.respondida:
                if st.button("Responder", type="primary", use_container_width=True):
                    if escolha is None:
                        st.warning("Escolha uma alternativa antes de responder.")
                    else:
                        st.session_state.escolha = escolha
                        st.session_state.respondida = True
                        if escolha == questao["correta"]:
                            st.session_state.acertos += 1
                        st.rerun()

            # Feedback
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

                rotulo = "Próxima questão" if indice + 1 < total else "Ver resultado"
                if st.button(rotulo, type="primary", use_container_width=True):
                    st.session_state.indice += 1
                    st.session_state.respondida = False
                    st.session_state.escolha = None
                    st.rerun()

        # Placar em tempo real
        st.caption(f"Placar: {st.session_state.acertos} acerto(s) até aqui.")
