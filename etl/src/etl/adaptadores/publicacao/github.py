"""Disparo do build do site: workflow_dispatch do publicar.yml (T039, contracts/publicacao.md).

POST /repos/{dono}/{nome}/actions/workflows/publicar.yml/dispatches na main,
com o execucao_id como input. A doc vigente (2026-10-28) responde 200 com o id
da execução do workflow; 204 também é aceito. Token recusado (401/403) vira
CredencialInvalida, para o alerta apontar a causa (FR-020a).
"""

import re

import httpx

from etl.adaptadores.camara.api_v2 import USER_AGENT
from etl.portas import CredencialInvalida

API_GITHUB = "https://api.github.com"
VERSAO_DA_API = "2026-03-10"
WORKFLOW = "publicar.yml"
REF = "main"
TEMPO_LIMITE_S = 30
_DONO_E_NOME = re.compile(r"[A-Za-z0-9-]+/[A-Za-z0-9._-]+")


def criar_cliente_github(transporte: httpx.BaseTransport | None = None) -> httpx.Client:
    return httpx.Client(
        base_url=API_GITHUB,
        headers={
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": VERSAO_DA_API,
            "User-Agent": USER_AGENT,
        },
        timeout=TEMPO_LIMITE_S,
        transport=transporte,
    )


class PublicadorGitHub:
    def __init__(self, cliente: httpx.Client, repositorio: str, token: str) -> None:
        if not _DONO_E_NOME.fullmatch(repositorio) or ".." in repositorio:
            raise ValueError("GITHUB_REPOSITORIO precisa ser dono/nome")
        self._cliente = cliente
        self._caminho = f"/repos/{repositorio}/actions/workflows/{WORKFLOW}/dispatches"
        self._token = token

    def disparar(self, execucao_id: int) -> None:
        resposta = self._cliente.post(
            self._caminho,
            json={"ref": REF, "inputs": {"execucao_id": str(execucao_id)}},
            headers={"Authorization": f"Bearer {self._token}"},
        )
        if resposta.status_code in (401, 403):
            raise CredencialInvalida(
                f"GitHub recusou o token de publicação (HTTP {resposta.status_code})"
            )
        resposta.raise_for_status()
