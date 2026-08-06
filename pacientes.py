"""
Pacientes virtuais — carregamento, validação e pontuação. Lógica pura, testável.

Um paciente tem uma ficha (nome, idade, sexo, comorbidades, história) e uma
sequência de 'momentos'. Cada momento mostra o estado clínico atual e uma
decisão; a escolha correta pontua e revela a evolução ('boa'); a errada mostra
a evolução 'ruim' (mas o acompanhamento continua). No fim, um desfecho.

Arquivos JSON na pasta 'pacientes/':
{
  "pacientes": [
    {
      "id": "asma-joao-01",
      "nome": "João", "idade": "6 anos", "sexo": "masculino",
      "comorbidades": "Asma leve", "historia": "...",
      "momentos": [
        {"titulo": "Admissão", "estado": "FR 40, SatO2 92%...",
         "texto": "...", "pergunta": "...", "opcoes": ["...","..."],
         "correta": 0, "explicacao": "...",
         "evolucao_boa": "...", "evolucao_ruim": "..."}
      ],
      "desfecho": "..."
    }
  ]
}
"""

from __future__ import annotations

import json
from pathlib import Path

PONTOS_MOMENTO = 10  # pontos por decisão correta


class PacienteInvalido(ValueError):
    """Erro de estrutura em um paciente virtual."""


def _validar(pac: dict, origem: str) -> None:
    for campo in ("id", "nome", "idade", "sexo", "historia", "momentos"):
        if campo not in pac:
            raise PacienteInvalido(f"{origem}: paciente sem '{campo}'")
    if not isinstance(pac["momentos"], list) or not pac["momentos"]:
        raise PacienteInvalido(f"{origem}: '{pac['id']}' sem momentos")
    for m in pac["momentos"]:
        for campo in ("titulo", "texto", "pergunta", "opcoes", "correta",
                      "explicacao"):
            if campo not in m:
                raise PacienteInvalido(
                    f"{origem}: momento sem '{campo}' em '{pac['id']}'"
                )
        if not isinstance(m["opcoes"], list) or len(m["opcoes"]) < 2:
            raise PacienteInvalido(
                f"{origem}: momento precisa de 2+ opções em '{pac['id']}'"
            )
        if not isinstance(m["correta"], int) or not (
            0 <= m["correta"] < len(m["opcoes"])
        ):
            raise PacienteInvalido(
                f"{origem}: 'correta' fora do intervalo em '{pac['id']}'"
            )


def carregar(base: str = "pacientes") -> list[dict]:
    """Lê e valida os pacientes. Devolve [] se a pasta não existe."""
    pasta = Path(base)
    if not pasta.exists():
        return []
    pacientes = []
    ids = set()
    for arquivo in sorted(pasta.rglob("*.json")):
        dados = json.loads(arquivo.read_text(encoding="utf-8"))
        for pac in dados.get("pacientes", []):
            _validar(pac, arquivo.name)
            if pac["id"] in ids:
                raise PacienteInvalido(f"id duplicado: {pac['id']}")
            ids.add(pac["id"])
            pacientes.append(pac)
    return pacientes


def listar(banco: list[dict]) -> list[dict]:
    return [
        {
            "id": p["id"],
            "nome": p["nome"],
            "idade": p["idade"],
            "resumo": p.get("historia", "")[:80],
        }
        for p in banco
    ]


def por_id(banco: list[dict], ident: str) -> dict | None:
    for p in banco:
        if p["id"] == ident:
            return p
    return None


def pontuacao_maxima(paciente: dict) -> int:
    return len(paciente["momentos"]) * PONTOS_MOMENTO
