"""Fonte oficial fora do ar (T066, FR-012, FR-013, FR-016, FR-029).

O adaptador real da Câmara recebe só HTTP 503: são 3 tentativas registradas,
a execução termina `falha` (código 1), nenhum dado muda, a publicação não é
disparada e o alerta é chamado. Falha no envio do alerta não muda nada disso.
"""

from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any

import httpx
import pytest
from apoio_coleta import (
    BASE,
    AlertadorFalso,
    PublicadorFalso,
    banco_limpo,
    contar,
    linhas,
    montar_coleta,
)

from etl.__main__ import codigo_de_saida
from etl.adaptadores.camara.api_v2 import CamaraApiV2, criar_cliente
from etl.adaptadores.persistencia.banco import Banco
from etl.portas import Gatilho, StatusExecucao

DADOS = ("parlamentar", "mandato", "periodo_exercicio", "filiacao", "partido")


@pytest.fixture
def banco(url_escrita: str) -> Iterator[Banco]:
    with banco_limpo(url_escrita) as banco:
        yield banco


def _camara_fora_do_ar(pedidos: list[httpx.Request]) -> Callable[..., CamaraApiV2]:
    def responder(pedido: httpx.Request) -> httpx.Response:
        pedidos.append(pedido)
        return httpx.Response(503)

    def criar(ao_receber: Callable[[str, Any], None], ao_tentar: Callable[[dict], None]):
        cliente = criar_cliente(BASE, httpx.MockTransport(responder))
        return CamaraApiV2(cliente, ao_receber, esperar=lambda _: None, ao_tentar=ao_tentar)

    return criar


def _executar(banco: Banco, pasta: Path, alertador: AlertadorFalso):
    pedidos: list[httpx.Request] = []
    publicador = PublicadorFalso()
    antes = {tabela: contar(banco, tabela) for tabela in DADOS}
    resultado = montar_coleta(
        banco, pasta, _camara_fora_do_ar(pedidos), alertador=alertador, publicador=publicador
    ).executar(Gatilho.AGENDADA)
    depois = {tabela: contar(banco, tabela) for tabela in DADOS}
    return resultado, pedidos, publicador, antes, depois


def test_fonte_fora_do_ar_tres_tentativas_falha_sem_dados_sem_publicar_com_alerta(
    banco: Banco, tmp_path: Path
) -> None:
    alertador = AlertadorFalso()

    resultado, pedidos, publicador, antes, depois = _executar(banco, tmp_path, alertador)

    assert resultado.status is StatusExecucao.FALHA
    assert codigo_de_saida(resultado.status) == 1
    assert len(pedidos) == 3
    (execucao,) = linhas(
        banco,
        "SELECT status, tentativas FROM execucao_etl WHERE id = :id",
        id=resultado.execucao_id,
    )
    assert execucao.status == "falha"
    assert [(t["tentativa"], t["detalhe"]) for t in execucao.tentativas] == [
        (1, "HTTP 503"),
        (2, "HTTP 503"),
        (3, "HTTP 503"),
    ]
    assert depois == antes
    assert publicador.disparos == []
    (alerta,) = alertador.textos
    assert "coleta com falha" in alerta
    assert f"execução {resultado.execucao_id}" in alerta


def test_falha_no_envio_do_alerta_nao_muda_o_resultado(banco: Banco, tmp_path: Path) -> None:
    alertador = AlertadorFalso(falhar=True)

    resultado, *_ = _executar(banco, tmp_path, alertador)

    assert resultado.status is StatusExecucao.FALHA
    assert len(alertador.textos) == 1
    (execucao,) = linhas(
        banco, "SELECT status FROM execucao_etl WHERE id = :id", id=resultado.execucao_id
    )
    assert execucao.status == "falha"
