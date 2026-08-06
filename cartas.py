"""
Cartas colecionáveis — catálogo e abertura de pacotes. Lógica pura, testável.

O pacote é comprado com moedas (o app debita). Abrir sorteia primeiro uma
raridade (por peso) e depois uma carta daquela raridade. Cartas repetidas
devolvem algumas moedas (REEMBOLSO_DUPLICATA), decidido no app.

A coleção do usuário fica em perfil.cartas = {id_da_carta: quantidade}.
"""

from __future__ import annotations

import random

PACOTE_CUSTO = 20        # moedas por pacote
REEMBOLSO_DUPLICATA = 5  # moedas devolvidas ao tirar carta repetida

# Raridades: peso = chance relativa no pacote; cor para a interface.
RARIDADES = {
    "comum": {"peso": 60, "cor": "#8AA0A0", "rotulo": "Comum"},
    "rara": {"peso": 28, "cor": "#0E8388", "rotulo": "Rara"},
    "epica": {"peso": 10, "cor": "#7B4BC4", "rotulo": "Épica"},
    "lendaria": {"peso": 2, "cor": "#D98A00", "rotulo": "Lendária"},
}

CARTAS = [
    # --- Comuns ---
    {"id": "estetoscopio", "emoji": "🩺", "nome": "Estetoscópio de Plantão",
     "raridade": "comum", "desc": "O clássico que nunca falha."},
    {"id": "termometro", "emoji": "🌡️", "nome": "Termômetro Fiel",
     "raridade": "comum", "desc": "37,8 °C? Fica de olho."},
    {"id": "otoscopio", "emoji": "🔦", "nome": "Otoscópio Curioso",
     "raridade": "comum", "desc": "Sempre espiando um ouvidinho."},
    {"id": "balanca", "emoji": "⚖️", "nome": "Balança do RN",
     "raridade": "comum", "desc": "Cada grama conta."},
    {"id": "mamadeira", "emoji": "🍼", "nome": "Mamadeira Cheia",
     "raridade": "comum", "desc": "Energia para crescer."},
    {"id": "caderneta", "emoji": "📔", "nome": "Caderneta da Criança",
     "raridade": "comum", "desc": "A história toda em um caderno."},
    {"id": "fralda", "emoji": "🧷", "nome": "Fralda Seca",
     "raridade": "comum", "desc": "Missão cumprida."},
    {"id": "gorro", "emoji": "🧢", "nome": "Gorrinho do RN",
     "raridade": "comum", "desc": "Contra a perda de calor."},
    # --- Raras ---
    {"id": "apgar", "emoji": "💯", "nome": "APGAR 10",
     "raridade": "rara", "desc": "Nota cheia no primeiro minuto.",
     "efeito": {"tipo": "xp_pct", "valor": 0.05, "texto": "+5% XP"}},
    {"id": "vacina", "emoji": "💉", "nome": "Vacina em Dia",
     "raridade": "rara", "desc": "Calendário impecável."},
    {"id": "aleitamento", "emoji": "🤱", "nome": "Aleitamento de Ouro",
     "raridade": "rara", "desc": "Livre demanda, sempre.",
     "efeito": {"tipo": "moeda_flat", "valor": 1, "texto": "+1 🪙 por acerto"}},
    {"id": "reanimacao", "emoji": "🫁", "nome": "Reanimação Neonatal",
     "raridade": "rara", "desc": "Minuto de ouro dominado."},
    {"id": "curva", "emoji": "📈", "nome": "Curva de Crescimento",
     "raridade": "rara", "desc": "Sempre no percentil certo."},
    # --- Épicas ---
    {"id": "raciocinio", "emoji": "🧠", "nome": "Raciocínio Clínico",
     "raridade": "epica", "desc": "O diagnóstico salta aos olhos.",
     "efeito": {"tipo": "xp_pct", "valor": 0.10, "texto": "+10% XP"}},
    {"id": "plantonista", "emoji": "⚡", "nome": "Plantonista Incansável",
     "raridade": "epica", "desc": "24 horas e segue firme.",
     "efeito": {"tipo": "moeda_flat", "valor": 2, "texto": "+2 🪙 por acerto"}},
    {"id": "guardiao", "emoji": "🛡️", "nome": "Guardião do RN",
     "raridade": "epica", "desc": "Vigília constante no berçário."},
    # --- Lendárias ---
    {"id": "pediatra_lenda", "emoji": "👑", "nome": "Pediatra Lendário",
     "raridade": "lendaria", "desc": "Referência de uma geração.",
     "efeito": {"tipo": "xp_pct", "valor": 0.15, "texto": "+15% XP"}},
    {"id": "maos_salvam", "emoji": "✨", "nome": "Mãos que Salvam",
     "raridade": "lendaria", "desc": "Onde há cuidado, há esperança.",
     "efeito": {"tipo": "dica_gratis", "valor": 1, "texto": "1 dica grátis por dia"}},
]

_POR_ID = {c["id"]: c for c in CARTAS}
_POR_RARIDADE = {r: [c for c in CARTAS if c["raridade"] == r] for r in RARIDADES}


def definicao(ident: str) -> dict | None:
    return _POR_ID.get(ident)


def cartas_da_raridade(raridade: str) -> list:
    return _POR_RARIDADE.get(raridade, [])


def sortear_raridade(rng) -> str:
    chaves = list(RARIDADES.keys())
    pesos = [RARIDADES[k]["peso"] for k in chaves]
    return rng.choices(chaves, weights=pesos, k=1)[0]


def abrir_pacote(rng=None) -> str:
    """Sorteia uma carta (raridade por peso, depois carta da raridade)."""
    rng = rng or random
    raridade = sortear_raridade(rng)
    return rng.choice(_POR_RARIDADE[raridade])["id"]


def colecao_resumo(cartas_usuario: dict) -> dict:
    """Resumo da coleção: total, possuídas e por raridade."""
    possuidas = sum(1 for c in CARTAS if c["id"] in cartas_usuario)
    por_raridade = {}
    for r in RARIDADES:
        do_r = _POR_RARIDADE[r]
        tem = sum(1 for c in do_r if c["id"] in cartas_usuario)
        por_raridade[r] = {"tem": tem, "total": len(do_r)}
    return {
        "total": len(CARTAS),
        "possuidas": possuidas,
        "por_raridade": por_raridade,
    }


def efeitos_ativos(cartas_usuario: dict) -> dict:
    """Soma os efeitos das cartas POSSUÍDAS (duplicatas não empilham).

    Devolve {xp_pct, moeda_flat, dica_gratis} — o app repassa esses valores
    para o cálculo de XP/moedas/dica.
    """
    xp_pct = 0.0
    moeda_flat = 0
    dica_gratis = False
    for cid in cartas_usuario:
        c = _POR_ID.get(cid)
        ef = c.get("efeito") if c else None
        if not ef:
            continue
        if ef["tipo"] == "xp_pct":
            xp_pct += ef["valor"]
        elif ef["tipo"] == "moeda_flat":
            moeda_flat += int(ef["valor"])
        elif ef["tipo"] == "dica_gratis":
            dica_gratis = True
    return {"xp_pct": xp_pct, "moeda_flat": moeda_flat, "dica_gratis": dica_gratis}


def efeitos_texto(cartas_usuario: dict) -> list:
    """Lista de textos dos efeitos ativos, para exibir na interface."""
    ef = efeitos_ativos(cartas_usuario)
    partes = []
    if ef["xp_pct"]:
        partes.append(f"+{round(ef['xp_pct'] * 100)}% XP")
    if ef["moeda_flat"]:
        partes.append(f"+{ef['moeda_flat']} 🪙 por acerto")
    if ef["dica_gratis"]:
        partes.append("1 dica grátis por dia")
    return partes
