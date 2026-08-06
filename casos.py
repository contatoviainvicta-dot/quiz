"""
Casos clínicos progressivos — carregamento e validação. Lógica pura, testável.

Um caso é um dicionário com etapas em sequência. Cada etapa é 'info' (só texto,
avança) ou 'decisao' (texto + pergunta com opções, uma correta). Os casos ficam
em arquivos JSON na pasta 'casos/' (separada de data/, para não se misturar com
o banco de questões).

Formato do arquivo:
{
  "casos": [
    {
      "id": "bronquiolite-01",
      "titulo": "...",
      "resumo": "...",
      "nivel": "básico",
      "etapas": [
        {"tipo": "info", "titulo": "Queixa principal", "texto": "..."},
        {"tipo": "decisao", "titulo": "Conduta", "texto": "...",
         "pergunta": "...", "opcoes": ["...", "..."], "correta": 0,
         "explicacao": "..."}
      ]
    }
  ]
}
"""

from __future__ import annotations

import json
from pathlib import Path

TIPOS = {"info", "decisao"}
PONTOS_DECISAO = 10  # pontos por decisão correta


class CasoInvalido(ValueError):
    """Erro de estrutura em um caso clínico."""


def _validar(caso: dict, origem: str) -> None:
    for campo in ("id", "titulo", "etapas"):
        if campo not in caso:
            raise CasoInvalido(f"{origem}: caso sem '{campo}'")
    if not isinstance(caso["etapas"], list) or not caso["etapas"]:
        raise CasoInvalido(f"{origem}: caso '{caso['id']}' sem etapas")
    for et in caso["etapas"]:
        if et.get("tipo") not in TIPOS:
            raise CasoInvalido(
                f"{origem}: etapa com tipo inválido em '{caso['id']}'"
            )
        if "titulo" not in et or "texto" not in et:
            raise CasoInvalido(
                f"{origem}: etapa sem 'titulo'/'texto' em '{caso['id']}'"
            )
        if et["tipo"] == "decisao":
            for campo in ("pergunta", "opcoes", "correta", "explicacao"):
                if campo not in et:
                    raise CasoInvalido(
                        f"{origem}: decisão sem '{campo}' em '{caso['id']}'"
                    )
            if not isinstance(et["opcoes"], list) or len(et["opcoes"]) < 2:
                raise CasoInvalido(
                    f"{origem}: decisão precisa de 2+ opções em '{caso['id']}'"
                )
            if not isinstance(et["correta"], int) or not (
                0 <= et["correta"] < len(et["opcoes"])
            ):
                raise CasoInvalido(
                    f"{origem}: 'correta' fora do intervalo em '{caso['id']}'"
                )


def carregar_casos(base: str = "casos") -> list[dict]:
    """Lê e valida todos os casos da pasta. Devolve [] se a pasta não existe."""
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
                raise CasoInvalido(f"id de caso duplicado: {caso['id']}")
            ids.add(caso["id"])
            casos.append(caso)
    return casos


def listar_casos(banco: list[dict]) -> list[dict]:
    """Resumo dos casos para a tela de seleção."""
    return [
        {
            "id": c["id"],
            "titulo": c["titulo"],
            "resumo": c.get("resumo", ""),
            "nivel": c.get("nivel", ""),
        }
        for c in banco
    ]


def caso_por_id(banco: list[dict], ident: str) -> dict | None:
    for c in banco:
        if c["id"] == ident:
            return c
    return None


def decisoes(caso: dict) -> list[dict]:
    return [e for e in caso["etapas"] if e["tipo"] == "decisao"]


def pontuacao_maxima(caso: dict) -> int:
    return len(decisoes(caso)) * PONTOS_DECISAO
