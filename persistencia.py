"""
Persistência do perfil — camada que salva e carrega o progresso.

Isola o resto do app de ONDE os dados moram. Hoje: Supabase (Postgres).
Se as credenciais não estiverem configuradas (ou o pacote não instalado),
cai para um modo "só sessão": nada é salvo, mas o app não quebra.

A lógica de gamificação (gamificacao.py) não sabe nada daqui — ela só mexe no
objeto Perfil. Este módulo traduz Perfil <-> linha do banco.
"""

from __future__ import annotations

from datetime import datetime, timezone

import streamlit as st

import gamificacao as gam

TABELA = "quiz_perfis"


@st.cache_resource(show_spinner=False)
def _cliente():
    """Cria o cliente Supabase uma vez (cache_resource).

    Devolve None se o pacote não estiver instalado ou os secrets não existirem
    — nesse caso o app roda em modo 'só sessão'.
    """
    try:
        from supabase import create_client

        url = st.secrets["supabase"]["url"]
        chave = st.secrets["supabase"]["key"]
    except Exception:
        return None

    try:
        return create_client(url, chave)
    except Exception:
        return None


def disponivel() -> bool:
    """True se há persistência real configurada."""
    return _cliente() is not None


def carregar_perfil(identificador: str) -> gam.Perfil:
    """Lê o perfil do banco. Se não existir (ou sem persistência), devolve novo."""
    cli = _cliente()
    if cli is None:
        return gam.perfil_novo()
    try:
        resp = (
            cli.table(TABELA)
            .select("dados")
            .eq("id", identificador)
            .limit(1)
            .execute()
        )
        linhas = resp.data or []
        if linhas and linhas[0].get("dados"):
            return gam.perfil_de_dict(linhas[0]["dados"])
    except Exception:
        # Falha de rede/consulta não deve derrubar o app; começa perfil novo.
        pass
    return gam.perfil_novo()


def salvar_perfil(identificador: str, perfil: gam.Perfil) -> bool:
    """Grava (upsert) o perfil no banco. Devolve True se salvou de fato."""
    cli = _cliente()
    if cli is None:
        return False
    try:
        cli.table(TABELA).upsert(
            {
                "id": identificador,
                "dados": gam.perfil_para_dict(perfil),
                "atualizado_em": datetime.now(timezone.utc).isoformat(),
            }
        ).execute()
        return True
    except Exception:
        return False
