"""Adaptador da API v2 de Dados Abertos da Câmara (contracts/fonte-camara-api-v2.md).

Traduz as respostas para as entidades do domínio. Cada resposta é sanitizada e
entregue a ao_receber antes da validação, para ficar guardada para diagnóstico
mesmo quando é inválida. GET /deputados/{id} nunca é chamado: devolve CPF.

Novas tentativas (5xx, 429, rede) entram na T067; aqui, um erro HTTP propaga.
"""

from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any
from zoneinfo import ZoneInfo

import httpx

from etl.adaptadores.camara.sanitizacao import sanitizar
from etl.dominio.entidades import (
    Condicao,
    EventoHistorico,
    Historico,
    IdentificadorExterno,
    Origem,
    Parlamentar,
    Partido,
    SistemaExterno,
)
from etl.portas import FonteIncompleta, RespostaInvalida

USER_AGENT = "fiscaldogov-etl (+https://github.com/heitoroliveiro-dev/fiscaldogov)"
TEMPO_LIMITE_S = 30
MAXIMO_SIMULTANEAS = 4
ITENS_POR_PAGINA = 100
MINIMO_EM_EXERCICIO = 500  # a Câmara tem 513 cadeiras (FR-007b)
SEM_PARTIDO = "S.PART."
# dataHora vem sem fuso; a Câmara registra no horário de Brasília (contrato da fonte)
FUSO_DA_FONTE = ZoneInfo("America/Sao_Paulo")
_CONDICOES = {"Titular": Condicao.TITULAR, "Suplente": Condicao.SUPLENTE}


def criar_cliente(url_base: str, transporte: httpx.BaseTransport | None = None) -> httpx.Client:
    return httpx.Client(
        base_url=url_base,
        headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
        timeout=TEMPO_LIMITE_S,
        limits=httpx.Limits(max_connections=MAXIMO_SIMULTANEAS),
        transport=transporte,
    )


def _campo(registro: Any, nome: str, tipo: type, url: str, *, opcional: bool = False) -> Any:
    if not isinstance(registro, dict) or nome not in registro:
        raise RespostaInvalida(f"campo {nome} ausente em {url}")
    valor = registro[nome]
    if valor is None and opcional:
        return None
    # bool é subclasse de int, mas nunca é um id ou uma legislatura
    if not isinstance(valor, tipo) or isinstance(valor, bool):
        raise RespostaInvalida(f"campo {nome} com tipo inesperado em {url}")
    return valor


def _id_na_uri(uri: str, nome: str, url: str) -> str:
    valor = uri.rstrip("/").rsplit("/", 1)[-1]
    if not valor.isdigit():
        raise RespostaInvalida(f"campo {nome} sem identificador numérico em {url}")
    return valor


class CamaraApiV2:
    def __init__(
        self,
        cliente: httpx.Client,
        ao_receber: Callable[[str, Any], None],
        relogio: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self._cliente = cliente
        self._ao_receber = ao_receber
        self._relogio = relogio

    def _obter(self, url: str, parametros: dict[str, int] | None = None) -> tuple[str, Any]:
        resposta = self._cliente.get(url, params=parametros)
        resposta.raise_for_status()
        url_consultada = str(resposta.request.url)
        try:
            conteudo = sanitizar(resposta.json())
        except ValueError as erro:
            raise RespostaInvalida(f"JSON inválido em {url_consultada}") from erro
        self._ao_receber(url_consultada, conteudo)
        return url_consultada, conteudo

    def listar_em_exercicio(self) -> list[Parlamentar]:
        """GET /deputados sem parâmetro de tempo: os em exercício agora, paginados."""
        deputados: list[Parlamentar] = []
        visitadas: set[str] = set()
        proxima: str | None = "/deputados"
        parametros: dict[str, int] | None = {"itens": ITENS_POR_PAGINA, "pagina": 1}
        while proxima is not None:
            url, conteudo = self._obter(proxima, parametros)
            if url in visitadas:
                raise RespostaInvalida(f"paginação em ciclo em {url}")
            visitadas.add(url)
            origem = Origem(url, self._relogio())
            for item in _campo(conteudo, "dados", list, url):
                deputados.append(self._parlamentar(item, origem))
            proxima, parametros = self._proxima_pagina(conteudo, url), None

        if not deputados:
            raise FonteIncompleta("a fonte devolveu lista vazia de deputados em exercício")
        if len(deputados) < MINIMO_EM_EXERCICIO:
            raise FonteIncompleta(
                f"a fonte devolveu {len(deputados)} deputados em exercício; "
                f"o mínimo plausível é {MINIMO_EM_EXERCICIO}"
            )
        return deputados

    @staticmethod
    def _proxima_pagina(conteudo: Any, url: str) -> str | None:
        for link in _campo(conteudo, "links", list, url):
            if _campo(link, "rel", str, url) == "next":
                return _campo(link, "href", str, url)
        return None

    @staticmethod
    def _parlamentar(item: Any, origem: Origem) -> Parlamentar:
        url = origem.url
        return Parlamentar(
            nome_parlamentar=_campo(item, "nome", str, url),
            identificador=IdentificadorExterno(
                SistemaExterno.CAMARA_V2, str(_campo(item, "id", int, url))
            ),
            origem=origem,
            url_foto=_campo(item, "urlFoto", str, url, opcional=True),
        )

    def historico(self, parlamentar: IdentificadorExterno) -> Historico:
        if parlamentar.sistema is not SistemaExterno.CAMARA_V2:
            raise ValueError(f"esperado identificador camara_v2, recebido {parlamentar.sistema}")
        if not parlamentar.valor.isdigit():
            raise ValueError(f"identificador da Câmara não numérico: {parlamentar.valor!r}")

        url, conteudo = self._obter(f"/deputados/{parlamentar.valor}/historico")
        origem = Origem(url, self._relogio())
        eventos = tuple(self._evento(item, url) for item in _campo(conteudo, "dados", list, url))
        if not eventos:
            raise FonteIncompleta(f"histórico vazio em {url}")
        return Historico(eventos, origem)

    @staticmethod
    def _evento(item: Any, url: str) -> EventoHistorico:
        try:
            data_hora = datetime.fromisoformat(_campo(item, "dataHora", str, url))
        except ValueError as erro:
            raise RespostaInvalida(f"campo dataHora fora do formato ISO em {url}") from erro
        if data_hora.tzinfo is None:
            data_hora = data_hora.replace(tzinfo=FUSO_DA_FONTE)

        situacao = _campo(item, "situacao", str, url, opcional=True)
        condicao_eleitoral = _campo(item, "condicaoEleitoral", str, url, opcional=True)
        if condicao_eleitoral is not None and condicao_eleitoral not in _CONDICOES:
            raise RespostaInvalida(
                f"campo condicaoEleitoral desconhecido ({condicao_eleitoral!r}) em {url}"
            )

        sigla = _campo(item, "siglaPartido", str, url)
        partido = None
        if sigla != SEM_PARTIDO:
            uri_partido = _campo(item, "uriPartido", str, url)
            partido = Partido(
                sigla,
                IdentificadorExterno(
                    SistemaExterno.CAMARA_V2_PARTIDO, _id_na_uri(uri_partido, "uriPartido", url)
                ),
            )

        return EventoHistorico(
            data_hora=data_hora,
            legislatura=_campo(item, "idLegislatura", int, url),
            em_exercicio=None if situacao is None else situacao == "Exercício",
            condicao=_CONDICOES.get(condicao_eleitoral) if condicao_eleitoral else None,
            partido=partido,
            uf=_campo(item, "siglaUf", str, url),
            descricao=_campo(item, "descricaoStatus", str, url),
        )
