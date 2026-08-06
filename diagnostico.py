"""
Diagnóstico progressivo — carregamento, validação e pontuação. Lógica pura.

O usuário vê a apresentação, pode SOLICITAR exames (cada um revela um resultado,
mas custa pontos) e depois fecha um diagnóstico. Menos exames + diagnóstico
correto = mais pontos.

Arquivos JSON na pasta 'diagnosticos/':
{
  "casos": [
    {
      "id": "dor-abdominal-01",
      "titulo": "...",
      "apresentacao": "...",
      "exames": [{"nome": "Hemograma", "resultado": "..."}, ...],
      "diagnosticos": ["...", "..."],
      "correta": 0,
      "explicacao": "..."
    }
  ]
}
"""

from __future__ import annotations

import json
from pathlib import Path

PONTOS_ACERTO = 50   # pontos de um diagnóstico correto sem pedir exames
CUSTO_EXAME = 5      # desconto por exame solicitado
PONTOS_MIN = 10      # piso de pontos para um diagnóstico correto


class DiagnosticoInvalido(ValueError):
    """Erro de estrutura em um caso de diagnóstico progressivo."""


def _validar(caso: dict, origem: str) -> None:
    for campo in ("id", "titulo", "apresentacao", "exames", "diagnosticos",
                  "correta", "explicacao"):
        if campo not in caso:
            raise DiagnosticoInvalido(f"{origem}: caso sem '{campo}'")
    if not isinstance(caso["exames"], list) or not caso["exames"]:
        raise DiagnosticoInvalido(f"{origem}: '{caso['id']}' sem exames")
    for ex in caso["exames"]:
        if "nome" not in ex or "resultado" not in ex:
            raise DiagnosticoInvalido(
                f"{origem}: exame sem 'nome'/'resultado' em '{caso['id']}'"
            )
    if not isinstance(caso["diagnosticos"], list) or len(caso["diagnosticos"]) < 2:
        raise DiagnosticoInvalido(
            f"{origem}: '{caso['id']}' precisa de 2+ diagnósticos"
        )
    if not isinstance(caso["correta"], int) or not (
        0 <= caso["correta"] < len(caso["diagnosticos"])
    ):
        raise DiagnosticoInvalido(
            f"{origem}: 'correta' fora do intervalo em '{caso['id']}'"
        )


def carregar(base: str = "diagnosticos") -> list[dict]:
    """Lê e valida os casos de diagnóstico. Devolve [] se a pasta não existe."""
    pasta = Path(base)
    if not pasta.exists():
        return []
    casos = []
    ids = set()
    for arquivo in sorted(pasta.rglob("*.json")):
        dados = json.loads(arquivo.read_text(encoding="utf-8"))
        for caso in dados.get("casos", []):
            _validar(caso, arquivo.name)
            if caso["id"] in ids:
                raise DiagnosticoInvalido(f"id duplicado: {caso['id']}")
            ids.add(caso["id"])
            casos.append(caso)
    return casos


def listar(banco: list[dict]) -> list[dict]:
    return [
        {"id": c["id"], "titulo": c["titulo"], "apresentacao": c["apresentacao"]}
        for c in banco
    ]


def por_id(banco: list[dict], ident: str) -> dict | None:
    for c in banco:
        if c["id"] == ident:
            return c
    return None


def pontuar(acertou: bool, n_exames: int) -> int:
    """Pontos: 0 se errou; senão PONTOS_ACERTO menos o custo dos exames (com piso)."""
    if not acertou:
        return 0
    return max(PONTOS_MIN, PONTOS_ACERTO - n_exames * CUSTO_EXAME)
