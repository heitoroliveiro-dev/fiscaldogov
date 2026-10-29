"""Coleta ponta a ponta contra o banco, com fonte e publicador falsos (T027, contracts/etl-cli.md).

O histórico do 204496 é o real, traduzido pelo adaptador da Câmara a partir da
fixture; os demais parlamentares são sintéticos. A coleta grava de verdade
(COMMIT), então a limpeza apaga, tabela a tabela, só as linhas criadas no teste.
"""

import json
from collections.abc import Callable, Iterator
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import httpx
import pytest
from sqlalchemy import Connection, func, select, text

from etl.adaptadores.brutos_r2.armazem import ArmazemDeBrutos, GravadorEmDisco
from etl.adaptadores.camara.api_v2 import CamaraApiV2, criar_cliente
from etl.adaptadores.persistencia.banco import Banco
from etl.adaptadores.persistencia.execucoes import Execucoes
from etl.adaptadores.persistencia.repositorio import Repositorio
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
from etl.pipeline.coletar import Coleta
from etl.portas import Gatilho, StatusExecucao

FIXTURES = Path(__file__).parents[1] / "fixtures" / "camara"
BASE = "https://dadosabertos.camara.leg.br/api/v2"
URL_LISTA = f"{BASE}/deputados?itens=100&pagina=1"
AGORA = datetime(2026, 10, 28, 6, 0, tzinfo=UTC)
BRASILIA = ZoneInfo("America/Sao_Paulo")
PDT = Partido("PDT", IdentificadorExterno(SistemaExterno.CAMARA_V2_PARTIDO, "36786"))

# ordem de apagar: dependentes antes
TABELAS_DA_COLETA = (
    "coleta_bruta",
    "execucao_etl",
    "periodo_exercicio",
    "filiacao",
    "mandato",
    "identificador_externo",
    "parlamentar",
    "partido",
)


def _ident(valor: str) -> IdentificadorExterno:
    return IdentificadorExterno(SistemaExterno.CAMARA_V2, valor)


def _historico_real_204496() -> Historico:
    conteudo = json.loads(
        (FIXTURES / "historico-204496-2026-10-28.json").read_text(encoding="utf-8")
    )
    transporte = httpx.MockTransport(lambda pedido: httpx.Response(200, json=conteudo))
    camara = CamaraApiV2(criar_cliente(BASE, transporte), lambda *_: None, lambda: AGORA)
    return camara.historico(_ident("204496"))


def _historico_sintetico(valor: str, eventos: list[tuple[str, bool]]) -> Historico:
    return Historico(
        eventos=tuple(
            EventoHistorico(
                data_hora=datetime.fromisoformat(momento).replace(tzinfo=BRASILIA),
                legislatura=57,
                em_exercicio=em_exercicio,
                condicao=Condicao.TITULAR,
                partido=PDT,
                uf="SP",
                descricao="Entrada" if em_exercicio else "Saída",
            )
            for momento, em_exercicio in eventos
        ),
        origem=Origem(f"{BASE}/deputados/{valor}/historico", AGORA),
    )


def _parlamentar(nome: str, valor: str) -> Parlamentar:
    return Parlamentar(nome, _ident(valor), Origem(URL_LISTA, AGORA), f"https://foto/{valor}.jpg")


CELSO = _parlamentar("Celso Sabino", "204496")
ZECA = _parlamentar("Zeca Sintético", "900001")
ABEL = _parlamentar("Abel Sintético", "900002")


class _FonteFalsa:
    """FonteDaCasa em memória que entrega cada resposta bruta, como o adaptador real."""

    def __init__(
        self,
        ao_receber: Callable[[str, Any], None],
        deputados: list[Parlamentar],
        historicos: dict[str, Historico],
        historico_quebrado: str | None = None,
    ) -> None:
        self._ao_receber = ao_receber
        self._deputados = deputados
        self._historicos = historicos
        self._historico_quebrado = historico_quebrado
        self.pedidos: list[str] = []

    def listar_em_exercicio(self) -> list[Parlamentar]:
        self._ao_receber(URL_LISTA, {"dados": [d.nome_parlamentar for d in self._deputados]})
        return self._deputados

    def historico(self, parlamentar: IdentificadorExterno) -> Historico:
        self.pedidos.append(parlamentar.valor)
        historico = self._historicos[parlamentar.valor]
        self._ao_receber(historico.origem.url, {"eventos": len(historico.eventos)})
        if parlamentar.valor == self._historico_quebrado:
            raise httpx.ConnectError("fonte fora do ar")
        return historico


class _Publicador:
    def __init__(self, falhar: bool = False) -> None:
        self.disparos: list[int] = []
        self._falhar = falhar

    def disparar(self, execucao_id: int) -> None:
        if self._falhar:
            raise ConnectionError("GitHub fora do ar")
        self.disparos.append(execucao_id)


class _GravadorQuebrado:
    def enviar(self, chave: str, conteudo: bytes) -> None:
        raise ConnectionError("R2 fora do ar")


class _RepositorioQueQuebraNoSegundo(Repositorio):
    def __init__(self, banco: Banco) -> None:
        super().__init__(banco)
        self._gravados = 0

    def _gravar_um(self, conexao: Connection, dados: Any) -> None:
        if self._gravados == 1:
            raise RuntimeError("falha no meio da gravação")
        super()._gravar_um(conexao, dados)
        self._gravados += 1


@pytest.fixture
def banco(url_escrita: str) -> Iterator[Banco]:
    banco = Banco.conectar(url_escrita, tempo_limite_s=30)
    with banco.transacao() as conexao:
        ultimos = {
            nome: conexao.execute(
                select(func.coalesce(func.max(banco.tabelas[nome].c.id), 0))
            ).scalar_one()
            for nome in TABELAS_DA_COLETA
        }
    yield banco
    with banco.transacao() as conexao:
        for nome in TABELAS_DA_COLETA:
            tabela = banco.tabelas[nome]
            conexao.execute(tabela.delete().where(tabela.c.id > ultimos[nome]))
    banco.fechar()


class _Cenario:
    def __init__(self, banco: Banco, pasta: Path) -> None:
        self.banco = banco
        self.pasta = pasta
        self.publicador = _Publicador()
        self.fontes: list[_FonteFalsa] = []

    def coletar(
        self,
        deputados: list[Parlamentar],
        historicos: dict[str, Historico],
        *,
        repositorio: Repositorio | None = None,
        gravador: Any = None,
        historico_quebrado: str | None = None,
    ):
        def criar_fonte(ao_receber: Callable[[str, Any], None]) -> _FonteFalsa:
            fonte = _FonteFalsa(ao_receber, deputados, historicos, historico_quebrado)
            self.fontes.append(fonte)
            return fonte

        coleta = Coleta(
            criar_fonte=criar_fonte,
            repositorio=repositorio or Repositorio(self.banco),
            brutos=ArmazemDeBrutos(self.banco, gravador or GravadorEmDisco(self.pasta)),
            execucoes=Execucoes(self.banco),
            publicador=self.publicador,
            versao_codigo="teste",
        )
        return coleta.executar(Gatilho.MANUAL)

    def contar(self, tabela: str) -> int:
        with self.banco.transacao() as conexao:
            return conexao.execute(
                select(func.count()).select_from(self.banco.tabelas[tabela])
            ).scalar_one()

    def linhas(self, sql: str, **parametros: object) -> list:
        with self.banco.transacao() as conexao:
            return list(conexao.execute(text(sql), parametros))


@pytest.fixture
def cenario(banco: Banco, tmp_path: Path) -> _Cenario:
    return _Cenario(banco, tmp_path)


@pytest.fixture(scope="module")
def historico_celso() -> Historico:
    return _historico_real_204496()


def test_coleta_grava_o_selecionado_com_fonte_e_data(
    cenario: _Cenario, historico_celso: Historico
) -> None:
    resultado = cenario.coletar([ZECA, CELSO], {"204496": historico_celso})

    assert resultado.status is StatusExecucao.SUCESSO
    (parlamentar,) = cenario.linhas(
        "SELECT p.nome_parlamentar, p.nome_ordenacao, p.url_foto, p.fonte_url, p.coletado_em "
        "FROM parlamentar p"
    )
    assert parlamentar.nome_parlamentar == "Celso Sabino"
    assert parlamentar.nome_ordenacao == "celso sabino"
    assert parlamentar.fonte_url == URL_LISTA
    assert parlamentar.coletado_em == AGORA

    (identificador,) = cenario.linhas(
        "SELECT valor, legislatura_numero FROM identificador_externo WHERE sistema = 'camara_v2'"
    )
    assert (identificador.valor, identificador.legislatura_numero) == ("204496", None)

    (mandato,) = cenario.linhas("SELECT legislatura_numero, uf FROM mandato")
    assert (mandato.legislatura_numero, mandato.uf) == (57, "PA")

    periodos = cenario.linhas(
        "SELECT inicio, fim, condicao, fonte_url, coletado_em "
        "FROM periodo_exercicio ORDER BY inicio"
    )
    assert len(periodos) == 7
    assert periodos[-1].fim is None
    assert {(p.fonte_url, p.coletado_em) for p in periodos} == {
        (f"{BASE}/deputados/204496/historico", AGORA)
    }

    filiacoes = cenario.linhas(
        "SELECT pa.sigla, f.fim, f.fonte_url FROM filiacao f "
        "JOIN partido pa ON pa.id = f.partido_id ORDER BY f.inicio"
    )
    assert [(f.sigla, f.fim is None) for f in filiacoes] == [("UNIÃO", False), ("PDT", True)]
    assert all(f.fonte_url == f"{BASE}/deputados/204496/historico" for f in filiacoes)

    partidos = cenario.linhas(
        "SELECT pa.sigla, ie.valor FROM partido pa "
        "JOIN identificador_externo ie ON ie.partido_id = pa.id ORDER BY pa.sigla"
    )
    assert [(p.sigla, p.valor) for p in partidos] == [("PDT", "36786"), ("UNIÃO", "38009")]


def test_execucao_termina_sucesso_com_contagens_e_dispara_a_publicacao(
    cenario: _Cenario, historico_celso: Historico
) -> None:
    resultado = cenario.coletar([CELSO], {"204496": historico_celso})

    (execucao,) = cenario.linhas(
        "SELECT status, contagens, terminada_em FROM execucao_etl WHERE id = :id",
        id=resultado.execucao_id,
    )
    assert execucao.status == "sucesso"
    assert execucao.terminada_em is not None
    assert execucao.contagens == {"parlamentar": 1, "periodo_exercicio": 7, "filiacao": 2}
    assert cenario.publicador.disparos == [resultado.execucao_id]


def test_respostas_brutas_ficam_registradas_na_execucao(
    cenario: _Cenario, historico_celso: Historico
) -> None:
    resultado = cenario.coletar([CELSO], {"204496": historico_celso})

    urls = cenario.linhas(
        "SELECT url FROM coleta_bruta WHERE execucao_id = :id ORDER BY id", id=resultado.execucao_id
    )
    assert [u.url for u in urls] == [URL_LISTA, f"{BASE}/deputados/204496/historico"]


def test_nenhuma_coluna_de_cpf_no_banco(cenario: _Cenario, historico_celso: Historico) -> None:
    cenario.coletar([CELSO], {"204496": historico_celso})

    colunas = cenario.linhas(
        "SELECT table_name, column_name FROM information_schema.columns "
        "WHERE table_schema = 'public' AND (column_name ILIKE '%cpf%' OR column_name ILIKE "
        "'%nascimento%' OR column_name ILIKE '%nome_civil%')"
    )
    assert colunas == []


def test_rodar_duas_vezes_produz_o_mesmo_estado(
    cenario: _Cenario, historico_celso: Historico
) -> None:
    cenario.coletar([CELSO], {"204496": historico_celso})
    estado = {tabela: cenario.contar(tabela) for tabela in TABELAS_DA_COLETA[2:]}

    cenario.coletar([CELSO], {"204496": historico_celso})

    assert {tabela: cenario.contar(tabela) for tabela in TABELAS_DA_COLETA[2:]} == estado
    assert estado == {
        "periodo_exercicio": 7,
        "filiacao": 2,
        "mandato": 1,
        "identificador_externo": 3,
        "parlamentar": 1,
        "partido": 2,
    }


def test_parlamentares_ja_armazenados_tem_o_historico_atualizado(
    cenario: _Cenario, historico_celso: Historico
) -> None:
    cenario.coletar([CELSO], {"204496": historico_celso})
    # no dia seguinte, Celso sai de exercício e outro nome passa a ser o primeiro
    saida = EventoHistorico(
        data_hora=datetime(2026, 10, 27, 18, 0, tzinfo=BRASILIA),
        legislatura=57,
        em_exercicio=False,
        condicao=Condicao.TITULAR,
        partido=historico_celso.eventos[14].partido,
        uf="PA",
        descricao="Saída - Afastamento",
    )
    celso_atualizado = Historico(historico_celso.eventos + (saida,), historico_celso.origem)
    abel = _historico_sintetico("900002", [("2023-02-01T12:00", True)])

    cenario.coletar([ABEL], {"204496": celso_atualizado, "900002": abel})

    assert sorted(cenario.fontes[-1].pedidos) == ["204496", "900002"]
    abertos = cenario.linhas(
        "SELECT p.nome_parlamentar FROM periodo_exercicio pe "
        "JOIN mandato m ON m.id = pe.mandato_id JOIN parlamentar p ON p.id = m.parlamentar_id "
        "WHERE pe.fim IS NULL"
    )
    assert [a.nome_parlamentar for a in abertos] == ["Abel Sintético"]
    # o cadastro de quem saiu da lista continua o gravado antes
    assert cenario.contar("parlamentar") == 2


def test_erro_na_gravacao_desfaz_os_dados_e_mantem_os_brutos(
    cenario: _Cenario, banco: Banco, historico_celso: Historico
) -> None:
    abel = _historico_sintetico("900002", [("2023-02-01T12:00", True)])
    cenario.coletar([CELSO], {"204496": historico_celso})
    antes = {tabela: cenario.contar(tabela) for tabela in TABELAS_DA_COLETA[2:]}

    resultado = cenario.coletar(
        [ABEL],
        {"204496": historico_celso, "900002": abel},
        repositorio=_RepositorioQueQuebraNoSegundo(banco),
    )

    assert resultado.status is StatusExecucao.FALHA
    assert {tabela: cenario.contar(tabela) for tabela in TABELAS_DA_COLETA[2:]} == antes
    brutos = cenario.linhas(
        "SELECT url FROM coleta_bruta WHERE execucao_id = :id", id=resultado.execucao_id
    )
    assert len(brutos) >= 1
    (execucao,) = cenario.linhas(
        "SELECT status, erros FROM execucao_etl WHERE id = :id", id=resultado.execucao_id
    )
    assert execucao.status == "falha"
    assert "falha no meio da gravação" in json.dumps(execucao.erros, ensure_ascii=False)
    assert len(cenario.publicador.disparos) == 1  # só a primeira coleta publicou


def test_falha_da_fonte_e_falha_sem_gravar_e_com_brutos_para_diagnostico(
    cenario: _Cenario, historico_celso: Historico
) -> None:
    resultado = cenario.coletar([CELSO], {"204496": historico_celso}, historico_quebrado="204496")

    assert resultado.status is StatusExecucao.FALHA
    assert cenario.contar("parlamentar") == 0
    assert cenario.publicador.disparos == []
    brutos = cenario.linhas(
        "SELECT url FROM coleta_bruta WHERE execucao_id = :id", id=resultado.execucao_id
    )
    assert len(brutos) == 2


def test_falha_ao_guardar_bruto_vira_pendencia_e_publica(
    cenario: _Cenario, historico_celso: Historico
) -> None:
    resultado = cenario.coletar([CELSO], {"204496": historico_celso}, gravador=_GravadorQuebrado())

    assert resultado.status is StatusExecucao.COM_PENDENCIAS
    assert cenario.contar("parlamentar") == 1
    assert cenario.publicador.disparos == [resultado.execucao_id]
    (execucao,) = cenario.linhas(
        "SELECT pendencias FROM execucao_etl WHERE id = :id", id=resultado.execucao_id
    )
    assert [p["etapa"] for p in execucao.pendencias] == ["brutos"]


def test_falha_no_disparo_da_publicacao_vira_pendencia(
    cenario: _Cenario, historico_celso: Historico
) -> None:
    cenario.publicador = _Publicador(falhar=True)

    resultado = cenario.coletar([CELSO], {"204496": historico_celso})

    assert resultado.status is StatusExecucao.COM_PENDENCIAS
    assert cenario.contar("parlamentar") == 1
    (execucao,) = cenario.linhas(
        "SELECT pendencias FROM execucao_etl WHERE id = :id", id=resultado.execucao_id
    )
    assert [p["etapa"] for p in execucao.pendencias] == ["publicacao"]
