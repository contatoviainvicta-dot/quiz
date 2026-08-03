"""
Testes do motor do quiz. Rode com:  pytest
"""

import json
from pathlib import Path

import pytest

from quiz_engine import (
    QuestaoInvalida,
    carregar_questoes,
    filtrar,
    listar_categorias,
    preparar_quiz,
)

RAIZ = Path(__file__).resolve().parent.parent
DATA = RAIZ / "data"


# --- Carregamento e validação dos dados reais -------------------------------
def test_banco_carrega():
    banco = carregar_questoes(DATA)
    assert len(banco) > 0
    for q in banco:
        assert 0 <= q["correta"] < len(q["opcoes"])
        assert len(q["opcoes"]) >= 2
        assert q["categoria"]


def test_categorias_tem_todas_na_frente():
    banco = carregar_questoes(DATA)
    cats = listar_categorias(banco)
    assert cats[0] == "Todas"
    assert len(cats) == len(set(cats))  # sem duplicatas


def test_filtro_por_categoria():
    banco = carregar_questoes(DATA)
    neo = filtrar(banco, "Neonatologia")
    assert neo and all(q["categoria"] == "Neonatologia" for q in neo)
    assert len(filtrar(banco, "Todas")) == len(banco)


# --- Preparação e embaralhamento --------------------------------------------
def test_preparar_respeita_quantidade():
    banco = carregar_questoes(DATA)
    prep = preparar_quiz(banco, "Todas", 3, seed=1)
    assert len(prep) == 3


def test_embaralhar_preserva_resposta_correta():
    banco = carregar_questoes(DATA)
    for seed in range(100):
        prep = preparar_quiz(banco, "Todas", 5, seed=seed)
        for p in prep:
            original = next(o for o in banco if o["pergunta"] == p["pergunta"])
            assert (
                p["opcoes"][p["correta"]]
                == original["opcoes"][original["correta"]]
            )


def test_seed_reproduz_mesmo_resultado():
    banco = carregar_questoes(DATA)
    a = preparar_quiz(banco, "Todas", 5, seed=42)
    b = preparar_quiz(banco, "Todas", 5, seed=42)
    assert a == b


# --- Validação de erros -----------------------------------------------------
def test_correta_fora_do_intervalo(tmp_path):
    ruim = {
        "categoria": "Teste",
        "questoes": [
            {"pergunta": "?", "opcoes": ["A", "B"], "correta": 5, "explicacao": "x"}
        ],
    }
    (tmp_path / "ruim.json").write_text(json.dumps(ruim), encoding="utf-8")
    with pytest.raises(QuestaoInvalida):
        carregar_questoes(tmp_path)


def test_campo_faltando(tmp_path):
    ruim = {
        "categoria": "Teste",
        "questoes": [{"pergunta": "?", "opcoes": ["A", "B"], "correta": 0}],
    }
    (tmp_path / "ruim.json").write_text(json.dumps(ruim), encoding="utf-8")
    with pytest.raises(QuestaoInvalida):
        carregar_questoes(tmp_path)


def test_arquivo_sem_cabecalho(tmp_path):
    (tmp_path / "ruim.json").write_text(json.dumps([{"a": 1}]), encoding="utf-8")
    with pytest.raises(QuestaoInvalida):
        carregar_questoes(tmp_path)
