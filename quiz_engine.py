"""
Motor do quiz — carrega, valida, filtra e prepara as questões.

Não depende do Streamlit de propósito: assim a lógica pode ser testada
isoladamente (pytest) e reaproveitada em outros contextos.

Formato de cada arquivo em data/ (JSON):

    {
      "categoria": "Neonatologia",
      "questoes": [
        {
          "pergunta": "Texto da pergunta?",
          "opcoes": ["A", "B", "C", "D"],
          "correta": 2,
          "explicacao": "Por que essa é a resposta."
        }
      ]
    }

Campos opcionais por questão (livres, ignorados pelo motor): "dificuldade",
"fonte", "tags". Servem para você organizar/expandir sem quebrar nada.
"""

from __future__ import annotations

import json
import random
from pathlib import Path

# Campos obrigatórios em cada questão (a categoria vem do cabeçalho do arquivo)
CAMPOS_OBRIGATORIOS = {"pergunta", "opcoes", "correta", "explicacao"}

DATA_DIR = Path(__file__).parent / "data"


class QuestaoInvalida(ValueError):
    """Erro de validação de uma questão ou de um arquivo de dados."""


def _validar(questao: dict, origem: str, pos: int) -> None:
    faltando = CAMPOS_OBRIGATORIOS - questao.keys()
    if faltando:
        raise QuestaoInvalida(f"{origem}[{pos}]: faltam os campos {sorted(faltando)}")

    opcoes = questao["opcoes"]
    if not isinstance(opcoes, list) or len(opcoes) < 2:
        raise QuestaoInvalida(
            f"{origem}[{pos}]: 'opcoes' precisa ser uma lista com ao menos 2 itens"
        )

    correta = questao["correta"]
    if not isinstance(correta, int) or not 0 <= correta < len(opcoes):
        raise QuestaoInvalida(
            f"{origem}[{pos}]: 'correta' ({correta}) fora do intervalo das opções"
        )


def carregar_questoes(data_dir: Path | str = DATA_DIR) -> list[dict]:
    """Lê todos os JSON em data_dir (inclui subpastas) e devolve o banco.

    Valida cada questão na carga: se algo estiver malformado, levanta
    QuestaoInvalida apontando o arquivo e a posição — fica fácil achar o erro
    mesmo com milhares de questões.
    """
    data_dir = Path(data_dir)
    banco: list[dict] = []

    for arquivo in sorted(data_dir.rglob("*.json")):
        with open(arquivo, encoding="utf-8") as f:
            conteudo = json.load(f)

        if not isinstance(conteudo, dict):
            raise QuestaoInvalida(
                f"{arquivo.name}: o arquivo deve ser um objeto com 'categoria' "
                "e 'questoes'"
            )

        categoria = conteudo.get("categoria")
        questoes = conteudo.get("questoes")
        if not categoria or questoes is None:
            raise QuestaoInvalida(
                f"{arquivo.name}: o arquivo precisa ter 'categoria' e 'questoes'"
            )
        if not isinstance(questoes, list):
            raise QuestaoInvalida(f"{arquivo.name}: 'questoes' precisa ser uma lista")

        for pos, q in enumerate(questoes):
            registro = {**q, "categoria": categoria}
            _validar(registro, arquivo.name, pos)
            banco.append(registro)

    return banco


def listar_categorias(banco: list[dict]) -> list[str]:
    """Categorias presentes no banco, com 'Todas' na frente."""
    return ["Todas"] + sorted({q["categoria"] for q in banco})


def filtrar(banco: list[dict], categoria: str) -> list[dict]:
    if categoria == "Todas":
        return list(banco)
    return [q for q in banco if q["categoria"] == categoria]


def preparar_quiz(
    banco: list[dict],
    categoria: str,
    quantidade: int,
    seed: int | None = None,
) -> list[dict]:
    """Sorteia as questões do tema e embaralha as alternativas.

    'seed' é opcional e serve para tornar o sorteio reproduzível (útil em
    testes). Em produção, deixe None para sorteio aleatório a cada partida.
    """
    rng = random.Random(seed)

    pool = filtrar(banco, categoria)
    rng.shuffle(pool)
    pool = pool[:quantidade]

    preparadas: list[dict] = []
    for q in pool:
        indices = list(range(len(q["opcoes"])))
        rng.shuffle(indices)
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
