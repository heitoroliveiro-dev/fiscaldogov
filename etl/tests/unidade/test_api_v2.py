"""Adaptador da API v2 da Câmara (contracts/fonte-camara-api-v2.md, T025).

Um transporte httpx falso serve as respostas reais gravadas; as páginas 2 em
diante da lista são cópias sintéticas da página 1, só para chegar aos 513.
"""

import copy
import json
import re
from datetime import UTC, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import httpx
import pytest

from etl.adaptadores.camara.api_v2 import USER_AGENT, CamaraApiV2, criar_cliente
from etl.dominio.entidades import (
    Condicao,
    EventoHistorico,
    IdentificadorExterno,
    Partido,
    SistemaExterno,
)
from etl.portas import FonteIncompleta, RespostaInvalida

FIXTURES = Path(__file__).parents[1] / "fixtures" / "camara"
BASE = "https://dadosabertos.camara.leg.br/api/v2"
URL_HISTORICO = f"{BASE}/deputados/204496/historico"
AGORA = datetime(2026, 10, 28, 6, 0, tzinfo=UTC)
BRASILIA = ZoneInfo("America/Sao_Paulo")
CELSO_SABINO = IdentificadorExterno(SistemaExterno.CAMARA_V2, "204496")


def _ler(nome: str) -> dict:
    return json.loads((FIXTURES / nome).read_text(encoding="utf-8"))


PAGINA1 = _ler("deputados-pagina1-2026-10-28.json")
HISTORICO = _ler("historico-204496-2026-10-28.json")


def _url_pagina(numero: int) -> str:
    # mesmo formato do links[rel=next] real
    return f"{BASE}/deputados?pagina={numero}&itens=100"


def _paginas(total: int) -> dict[int, dict]:
    reais = PAGINA1["dados"]
    deputados = [
        reais[i] if i < len(reais) else {**reais[0], "id": 900_000 + i, "nome": f"Sintético {i}"}
        for i in range(total)
    ]
    blocos = [deputados[i : i + 100] for i in range(0, total, 100)] or [[]]
    paginas = {}
    for numero, bloco in enumerate(blocos, start=1):
        links = [{"rel": "self", "href": _url_pagina(numero)}]
        if numero < len(blocos):
            links.append({"rel": "next", "href": _url_pagina(numero + 1)})
        paginas[numero] = {"dados": bloco, "links": links}
    return paginas


class _Camara:
    """Transporte falso: serve páginas e históricos e guarda cada pedido."""

    def __init__(self, paginas: dict[int, dict] | None = None, historico: object = HISTORICO):
        self.paginas = paginas if paginas is not None else _paginas(513)
        self.historico = historico
        self.pedidos: list[httpx.Request] = []

    def __call__(self, pedido: httpx.Request) -> httpx.Response:
        self.pedidos.append(pedido)
        if pedido.url.path == "/api/v2/deputados":
            return httpx.Response(200, json=self.paginas[int(pedido.url.params["pagina"])])
        if pedido.url.path == "/api/v2/deputados/204496/historico":
            if isinstance(self.historico, bytes):
                return httpx.Response(200, content=self.historico)
            return httpx.Response(200, json=self.historico)
        return httpx.Response(404)


def _fonte(camara: _Camara, brutos: list | None = None) -> CamaraApiV2:
    cliente = criar_cliente(BASE, transporte=httpx.MockTransport(camara))
    recebidos = brutos if brutos is not None else []
    return CamaraApiV2(
        cliente,
        ao_receber=lambda url, conteudo: recebidos.append((url, conteudo)),
        relogio=lambda: AGORA,
    )


# --- lista de deputados em exercício ------------------------------------------


def test_paginacao_segue_links_next_ate_o_fim() -> None:
    camara = _Camara()

    deputados = _fonte(camara).listar_em_exercicio()

    assert len(deputados) == 513
    assert [p.url.params["pagina"] for p in camara.pedidos] == ["1", "2", "3", "4", "5", "6"]
    assert camara.pedidos[0].url.params["itens"] == "100"


def test_deputado_da_lista_vira_parlamentar_com_origem() -> None:
    primeiro = PAGINA1["dados"][0]

    deputado = _fonte(_Camara()).listar_em_exercicio()[0]

    assert deputado.nome_parlamentar == primeiro["nome"]
    assert deputado.identificador == IdentificadorExterno(
        SistemaExterno.CAMARA_V2, str(primeiro["id"])
    )
    assert deputado.url_foto == primeiro["urlFoto"]
    assert deputado.origem.url == f"{BASE}/deputados?itens=100&pagina=1"
    assert deputado.origem.coletado_em == AGORA


def test_cabecalhos_e_timeout_de_30_segundos() -> None:
    camara = _Camara()
    fonte = _fonte(camara)

    fonte.listar_em_exercicio()
    fonte.historico(CELSO_SABINO)

    for pedido in camara.pedidos:
        assert pedido.headers["User-Agent"] == USER_AGENT
        assert pedido.headers["Accept"] == "application/json"
        assert pedido.extensions["timeout"] == {
            "connect": 30.0,
            "read": 30.0,
            "write": 30.0,
            "pool": 30.0,
        }
    assert USER_AGENT == "fiscaldogov-etl (+https://github.com/heitoroliveiro-dev/fiscaldogov)"


@pytest.mark.parametrize("total", [0, 499])
def test_lista_vazia_ou_com_menos_de_500_e_fonte_incompleta(total: int) -> None:
    with pytest.raises(FonteIncompleta):
        _fonte(_Camara(paginas=_paginas(total))).listar_em_exercicio()


def test_500_deputados_bastam() -> None:
    assert len(_fonte(_Camara(paginas=_paginas(500))).listar_em_exercicio()) == 500


@pytest.mark.parametrize(
    ("campo", "valor"),
    [("nome", None), ("id", "204496"), ("nome", 42), ("urlFoto", 1)],
)
def test_campo_usado_ausente_ou_de_tipo_inesperado_e_resposta_invalida(
    campo: str, valor: object
) -> None:
    paginas = _paginas(513)
    deputado = paginas[1]["dados"][0]
    if valor is None:
        del deputado[campo]
    else:
        deputado[campo] = valor

    with pytest.raises(RespostaInvalida, match=campo):
        _fonte(_Camara(paginas=paginas)).listar_em_exercicio()


def test_resposta_bruta_e_entregue_mesmo_quando_invalida() -> None:
    # guardada para diagnóstico (contrato, tabela de falhas)
    paginas = _paginas(513)
    del paginas[1]["dados"][0]["nome"]
    brutos: list = []

    with pytest.raises(RespostaInvalida):
        _fonte(_Camara(paginas=paginas), brutos).listar_em_exercicio()

    assert [url for url, _ in brutos] == [f"{BASE}/deputados?itens=100&pagina=1"]


def test_resposta_bruta_entregue_ja_sanitizada() -> None:
    paginas = _paginas(513)
    paginas[1]["dados"][0]["cpf"] = "00000000000"
    brutos: list = []

    _fonte(_Camara(paginas=paginas), brutos).listar_em_exercicio()

    _, conteudo = brutos[0]
    assert "cpf" not in conteudo["dados"][0]
    assert len(brutos) == 6


def test_json_invalido_e_resposta_invalida() -> None:
    with pytest.raises(RespostaInvalida):
        _fonte(_Camara(historico=b"<html>manutencao</html>")).historico(CELSO_SABINO)


# --- histórico ----------------------------------------------------------------


def test_historico_traduz_os_eventos_para_o_dominio() -> None:
    historico = _fonte(_Camara()).historico(CELSO_SABINO)

    assert len(historico.eventos) == 22
    assert historico.origem.url == URL_HISTORICO
    assert historico.origem.coletado_em == AGORA
    assert historico.eventos[1] == EventoHistorico(
        # a API não informa fuso: horário de Brasília (contrato da fonte)
        data_hora=datetime(2023, 2, 1, 12, 5, tzinfo=BRASILIA),
        legislatura=57,
        em_exercicio=True,
        condicao=Condicao.TITULAR,
        partido=Partido("UNIÃO", IdentificadorExterno(SistemaExterno.CAMARA_V2_PARTIDO, "38009")),
        uf="PA",
        descricao="Entrada - Posse de Eleito Titular - Posse na Sessão Preparatória",
    )


def test_evento_sem_situacao_e_evento_de_licenca() -> None:
    eventos = _fonte(_Camara()).historico(CELSO_SABINO).eventos

    inicio_da_legislatura, licenca = eventos[0], eventos[2]
    assert (inicio_da_legislatura.em_exercicio, inicio_da_legislatura.condicao) == (None, None)
    assert licenca.em_exercicio is False


def test_sem_partido_vira_partido_nulo() -> None:
    eventos = _fonte(_Camara()).historico(CELSO_SABINO).eventos

    (sem_partido,) = [
        e for e in eventos if e.data_hora == datetime(2021, 9, 9, 18, 10, tzinfo=BRASILIA)
    ]
    assert sem_partido.partido is None


def test_historico_vazio_e_fonte_incompleta() -> None:
    with pytest.raises(FonteIncompleta):
        _fonte(_Camara(historico={"dados": [], "links": []})).historico(CELSO_SABINO)


def test_condicao_eleitoral_desconhecida_e_resposta_invalida() -> None:
    historico = copy.deepcopy(HISTORICO)
    historico["dados"][1]["condicaoEleitoral"] = "Efetivo"

    with pytest.raises(RespostaInvalida, match="condicaoEleitoral"):
        _fonte(_Camara(historico=historico)).historico(CELSO_SABINO)


def test_identificador_de_outro_sistema_e_recusado() -> None:
    partido = IdentificadorExterno(SistemaExterno.CAMARA_V2_PARTIDO, "38009")

    with pytest.raises(ValueError, match="camara_v2"):
        _fonte(_Camara()).historico(partido)


def test_nunca_chama_o_endpoint_que_devolve_cpf() -> None:
    camara = _Camara()
    fonte = _fonte(camara)

    fonte.listar_em_exercicio()
    fonte.historico(CELSO_SABINO)

    assert not [p for p in camara.pedidos if re.fullmatch(r"/api/v2/deputados/\d+", p.url.path)]
