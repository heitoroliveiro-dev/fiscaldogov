"""Novas tentativas da coleta (T061, FR-013, research §5).

Até 3 tentativas por requisição (a original + 2 novas), com esperas de 5 s e
20 s. Só falha passageira tenta de novo: rede, tempo esgotado, HTTP 5xx e 429.
A espera é injetada, então nenhum teste dorme de verdade.
"""

import httpx
import pytest

from etl.adaptadores.camara.api_v2 import CamaraApiV2, criar_cliente, erro_passageiro
from etl.dominio.entidades import IdentificadorExterno, SistemaExterno
from etl.pipeline.tentativas import ESPERAS_S, com_tentativas
from etl.portas import RespostaInvalida

BASE = "https://dadosabertos.camara.leg.br/api/v2"
CELSO_SABINO = IdentificadorExterno(SistemaExterno.CAMARA_V2, "204496")
HISTORICO_VALIDO = {
    "dados": [
        {
            "dataHora": "2023-02-01T00:00",
            "idLegislatura": 57,
            "situacao": "Exercício",
            "condicaoEleitoral": "Titular",
            "siglaPartido": "PDT",
            "uriPartido": f"{BASE}/partidos/36786",
            "siglaUf": "PA",
            "descricaoStatus": "Entrada",
        }
    ]
}


class _Operacao:
    """Falha com os erros dados, em ordem, e depois devolve 'ok'."""

    def __init__(self, *erros: Exception) -> None:
        self._erros = list(erros)
        self.chamadas = 0

    def __call__(self) -> str:
        self.chamadas += 1
        if self._erros:
            raise self._erros.pop(0)
        return "ok"


def _passageira(erro: Exception) -> bool:
    return isinstance(erro, ConnectionError)


def test_esperas_sao_5_e_20_segundos() -> None:
    assert ESPERAS_S == (5, 20)


def test_sucesso_na_primeira_nao_espera_nem_registra() -> None:
    esperas: list[float] = []
    registros: list[dict] = []

    resultado = com_tentativas(
        _Operacao(),
        passageira=_passageira,
        descricao="x",
        esperar=esperas.append,
        registrar=registros.append,
    )

    assert (resultado, esperas, registros) == ("ok", [], [])


def test_falha_passageira_tenta_de_novo_com_esperas_crescentes() -> None:
    esperas: list[float] = []
    operacao = _Operacao(ConnectionError("a"), ConnectionError("b"))

    resultado = com_tentativas(
        operacao, passageira=_passageira, descricao="x", esperar=esperas.append
    )

    assert (resultado, operacao.chamadas, esperas) == ("ok", 3, [5, 20])


def test_tres_falhas_passageiras_propagam_a_ultima_sem_quarta_chamada() -> None:
    esperas: list[float] = []
    operacao = _Operacao(ConnectionError("1"), ConnectionError("2"), ConnectionError("3"))

    with pytest.raises(ConnectionError, match="3"):
        com_tentativas(operacao, passageira=_passageira, descricao="x", esperar=esperas.append)

    assert (operacao.chamadas, esperas) == (3, [5, 20])


def test_falha_permanente_propaga_na_hora() -> None:
    esperas: list[float] = []
    operacao = _Operacao(ValueError("permanente"))

    with pytest.raises(ValueError, match="permanente"):
        com_tentativas(operacao, passageira=_passageira, descricao="x", esperar=esperas.append)

    assert (operacao.chamadas, esperas) == (1, [])


def test_cada_tentativa_que_falha_e_registrada() -> None:
    registros: list[dict] = []
    operacao = _Operacao(ConnectionError("1"), ConnectionError("2"), ConnectionError("3"))

    with pytest.raises(ConnectionError):
        com_tentativas(
            operacao,
            passageira=_passageira,
            descricao="GET /deputados",
            esperar=lambda _: None,
            registrar=registros.append,
        )

    assert registros == [
        {
            "requisicao": "GET /deputados",
            "tentativa": 1,
            "erro": "ConnectionError",
            "detalhe": "1",
            "espera_s": 5,
        },
        {
            "requisicao": "GET /deputados",
            "tentativa": 2,
            "erro": "ConnectionError",
            "detalhe": "2",
            "espera_s": 20,
        },
        {
            "requisicao": "GET /deputados",
            "tentativa": 3,
            "erro": "ConnectionError",
            "detalhe": "3",
            "espera_s": None,
        },
    ]


def _status(codigo: int) -> httpx.HTTPStatusError:
    pedido = httpx.Request("GET", f"{BASE}/deputados")
    return httpx.HTTPStatusError("erro", request=pedido, response=httpx.Response(codigo))


@pytest.mark.parametrize(
    "erro",
    [
        httpx.ConnectError("sem rede"),
        httpx.ReadTimeout("tempo esgotado"),
        httpx.RemoteProtocolError("conexão caiu"),
        _status(500),
        _status(503),
        _status(429),
    ],
    ids=["rede", "tempo-esgotado", "conexao-caiu", "500", "503", "429"],
)
def test_passageiros_para_a_camara(erro: Exception) -> None:
    assert erro_passageiro(erro)


@pytest.mark.parametrize(
    "erro",
    [_status(400), _status(404), _status(403), RespostaInvalida("formato"), ValueError("x")],
    ids=["400", "404", "403", "resposta-invalida", "outro"],
)
def test_permanentes_para_a_camara(erro: Exception) -> None:
    assert not erro_passageiro(erro)


def _camara(*respostas: httpx.Response, esperas: list[float], tentativas: list[dict]):
    fila = list(respostas)
    pedidos: list[httpx.Request] = []

    def responder(pedido: httpx.Request) -> httpx.Response:
        pedidos.append(pedido)
        return fila.pop(0)

    cliente = criar_cliente(BASE, httpx.MockTransport(responder))
    camara = CamaraApiV2(
        cliente, lambda *_: None, esperar=esperas.append, ao_tentar=tentativas.append
    )
    return camara, pedidos


def test_camara_absorve_queda_passageira_e_registra_as_tentativas() -> None:
    esperas: list[float] = []
    tentativas: list[dict] = []
    camara, pedidos = _camara(
        httpx.Response(503),
        httpx.Response(429),
        httpx.Response(200, json=HISTORICO_VALIDO),
        esperas=esperas,
        tentativas=tentativas,
    )

    historico = camara.historico(CELSO_SABINO)

    assert len(historico.eventos) == 1
    assert (len(pedidos), esperas) == (3, [5, 20])
    assert [(t["tentativa"], t["detalhe"]) for t in tentativas] == [
        (1, "HTTP 503"),
        (2, "HTTP 429"),
    ]
    assert tentativas[0]["requisicao"] == "GET /deputados/204496/historico"


def test_camara_com_404_falha_na_primeira() -> None:
    esperas: list[float] = []
    camara, pedidos = _camara(httpx.Response(404), esperas=esperas, tentativas=[])

    with pytest.raises(httpx.HTTPStatusError):
        camara.historico(CELSO_SABINO)

    assert (len(pedidos), esperas) == (1, [])


def test_camara_com_json_invalido_falha_na_primeira() -> None:
    esperas: list[float] = []
    camara, pedidos = _camara(httpx.Response(200, text="<html>"), esperas=esperas, tentativas=[])

    with pytest.raises(RespostaInvalida):
        camara.historico(CELSO_SABINO)

    assert (len(pedidos), esperas) == (1, [])


def test_camara_fora_do_ar_tenta_tres_vezes_e_desiste() -> None:
    esperas: list[float] = []
    tentativas: list[dict] = []
    camara, pedidos = _camara(
        httpx.Response(503),
        httpx.Response(503),
        httpx.Response(503),
        esperas=esperas,
        tentativas=tentativas,
    )

    with pytest.raises(httpx.HTTPStatusError):
        camara.historico(CELSO_SABINO)

    assert (len(pedidos), esperas, len(tentativas)) == (3, [5, 20], 3)
