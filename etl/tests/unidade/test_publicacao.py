"""Disparo da publicação por workflow_dispatch do publicar.yml (T039, contracts/publicacao.md)."""

import json

import httpx
import pytest

from etl.adaptadores.publicacao.github import PublicadorGitHub, criar_cliente_github
from etl.portas import CredencialInvalida

REPOSITORIO = "heitoroliveiro-dev/fiscaldogov"
TOKEN = "token-ficticio-de-teste"  # noqa: S105 — valor de teste, não é credencial


def _publicador(resposta: httpx.Response, pedidos: list[httpx.Request] | None = None):
    def responder(pedido: httpx.Request) -> httpx.Response:
        if pedidos is not None:
            pedidos.append(pedido)
        return resposta

    cliente = criar_cliente_github(httpx.MockTransport(responder))
    return PublicadorGitHub(cliente, REPOSITORIO, TOKEN)


def test_dispara_o_workflow_na_main_com_o_id_da_execucao() -> None:
    pedidos: list[httpx.Request] = []

    _publicador(httpx.Response(200, json={"workflow_run_id": 1}), pedidos).disparar(42)

    (pedido,) = pedidos
    assert pedido.method == "POST"
    assert str(pedido.url) == (
        "https://api.github.com/repos/heitoroliveiro-dev/fiscaldogov"
        "/actions/workflows/publicar.yml/dispatches"
    )
    assert json.loads(pedido.content) == {"ref": "main", "inputs": {"execucao_id": "42"}}
    assert pedido.headers["Authorization"] == f"Bearer {TOKEN}"
    assert pedido.headers["Accept"] == "application/vnd.github+json"
    assert pedido.headers["X-GitHub-Api-Version"] == "2026-03-10"


def test_resposta_sem_corpo_tambem_e_sucesso() -> None:
    _publicador(httpx.Response(204)).disparar(42)


@pytest.mark.parametrize("status", [401, 403])
def test_token_recusado_e_credencial_invalida_sem_vazar_o_token(status: int) -> None:
    with pytest.raises(CredencialInvalida) as erro:
        _publicador(httpx.Response(status)).disparar(42)

    assert TOKEN not in str(erro.value)
    assert str(status) in str(erro.value)


def test_outro_erro_http_propaga() -> None:
    with pytest.raises(httpx.HTTPStatusError):
        _publicador(httpx.Response(500)).disparar(42)


@pytest.mark.parametrize("repositorio", ["fiscaldogov", "a/b/c", "a/../b", "dono/repo?x=1"])
def test_repositorio_fora_do_formato_dono_nome_e_recusado(repositorio: str) -> None:
    cliente = criar_cliente_github(httpx.MockTransport(lambda _: httpx.Response(200)))

    with pytest.raises(ValueError, match="GITHUB_REPOSITORIO"):
        PublicadorGitHub(cliente, repositorio, TOKEN)
