"""Alertas no Telegram (T065, FR-029, FR-020a, research §10).

A mensagem diz o tipo da falha e o execucao_id; credencial recusada aparece
como "falha de autenticação: <credencial>". Falha no envio só vai para o log,
e o token nunca: a URL da API do Telegram carrega o token.
"""

import json
import logging

import httpx
import pytest

from etl.adaptadores.alertas.telegram import AlertadorTelegram, criar_cliente_telegram
from etl.pipeline.alertas import descrever_erro, montar_alerta
from etl.portas import CredencialInvalida

TOKEN = "123456:token-ficticio-de-teste"  # noqa: S105 — valor de teste, não é credencial
CHAT_ID = "987654"


def test_mensagem_tem_o_tipo_e_o_execucao_id() -> None:
    texto = montar_alerta(
        "coleta com falha", 42, [{"etapa": "coleta", "tipo": "HTTPStatusError", "mensagem": "503"}]
    )

    assert "coleta com falha" in texto
    assert "execução 42" in texto
    assert "coleta: HTTPStatusError — 503" in texto


def test_alerta_sem_execucao_nao_inventa_um_id() -> None:
    texto = montar_alerta("publicação com falha", None, [])

    assert "execução" not in texto


def test_credencial_recusada_vira_falha_de_autenticacao() -> None:
    erro = CredencialInvalida("token de publicação do GitHub", "HTTP 401")

    texto = montar_alerta(
        "coleta com pendências", 7, [{"etapa": "publicacao", **descrever_erro(erro)}]
    )

    assert "publicacao: falha de autenticação: token de publicação do GitHub" in texto


def test_descrever_erro_comum_tem_tipo_e_mensagem() -> None:
    assert descrever_erro(ValueError("ruim")) == {"tipo": "ValueError", "mensagem": "ruim"}


def _alertador(*respostas: httpx.Response | Exception, pedidos: list[httpx.Request], esperas: list):
    fila = list(respostas)

    def responder(pedido: httpx.Request) -> httpx.Response:
        pedidos.append(pedido)
        resposta = fila.pop(0)
        if isinstance(resposta, Exception):
            raise resposta
        return resposta

    cliente = criar_cliente_telegram(httpx.MockTransport(responder))
    return AlertadorTelegram(cliente, TOKEN, CHAT_ID, esperar=esperas.append)


def test_envia_sendmessage_para_o_chat_configurado() -> None:
    pedidos: list[httpx.Request] = []

    _alertador(httpx.Response(200, json={"ok": True}), pedidos=pedidos, esperas=[]).alertar("oi")

    (pedido,) = pedidos
    assert pedido.method == "POST"
    assert str(pedido.url) == f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    assert json.loads(pedido.content) == {"chat_id": CHAT_ID, "text": "oi"}


def test_uma_nova_tentativa_quando_o_envio_falha() -> None:
    pedidos: list[httpx.Request] = []
    esperas: list[float] = []

    _alertador(
        httpx.ConnectError("sem rede"),
        httpx.Response(200, json={"ok": True}),
        pedidos=pedidos,
        esperas=esperas,
    ).alertar("oi")

    assert (len(pedidos), esperas) == (2, [5])


@pytest.mark.parametrize(
    "falhas",
    [
        (httpx.Response(401), httpx.Response(401)),
        (httpx.ConnectError("sem rede"), httpx.ReadTimeout("lento")),
        (httpx.Response(500), httpx.Response(502)),
    ],
    ids=["token-recusado", "rede", "5xx"],
)
def test_falha_no_envio_so_vai_para_o_log_sem_o_token(
    falhas: tuple, caplog: pytest.LogCaptureFixture
) -> None:
    pedidos: list[httpx.Request] = []

    with caplog.at_level(logging.ERROR):
        _alertador(*falhas, pedidos=pedidos, esperas=[]).alertar("oi")  # não levanta

    assert len(pedidos) == 2  # a original + uma nova tentativa
    assert "alerta não enviado" in caplog.text
    registrado = caplog.text + "".join(str(vars(r)) for r in caplog.records)
    assert TOKEN.split(":")[1] not in registrado
