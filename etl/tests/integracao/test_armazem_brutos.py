"""Deduplicação e registro das respostas brutas em coleta_bruta (FR-011, FR-012, T026).

O registro usa transação própria, como execucao_etl: a evidência de uma execução
que falhou continua ligada a ela depois do ROLLBACK dos dados. Por isso os testes
gravam de verdade e apagam ao fim só o que criaram.
"""

from collections.abc import Iterator
from pathlib import Path

import pytest
from sqlalchemy import delete, func, select

from etl.adaptadores.brutos_r2.armazem import ArmazemDeBrutos, GravadorEmDisco
from etl.adaptadores.persistencia.banco import Banco
from etl.adaptadores.persistencia.execucoes import Execucoes, Gatilho

BASE = "https://dadosabertos.camara.leg.br/api/v2"
URL = f"{BASE}/deputados/204496/historico"
CONTEUDO = {"dados": [{"situacao": "Exercício"}], "links": []}


@pytest.fixture
def banco(url_escrita: str) -> Iterator[Banco]:
    banco = Banco.conectar(url_escrita, tempo_limite_s=10)
    execucao = banco.tabelas["execucao_etl"]
    coleta = banco.tabelas["coleta_bruta"]
    with banco.transacao() as conexao:
        ultima = conexao.execute(select(func.coalesce(func.max(execucao.c.id), 0))).scalar_one()
    yield banco
    with banco.transacao() as conexao:
        conexao.execute(delete(coleta).where(coleta.c.execucao_id > ultima))
        conexao.execute(delete(execucao).where(execucao.c.id > ultima))
    banco.fechar()


@pytest.fixture
def execucao_id(banco: Banco) -> int:
    return Execucoes(banco).iniciar(Gatilho.MANUAL, "teste")


@pytest.fixture
def armazem(banco: Banco, tmp_path: Path) -> ArmazemDeBrutos:
    return ArmazemDeBrutos(banco, GravadorEmDisco(tmp_path))


def _registros(banco: Banco, execucao_id: int) -> list:
    coleta = banco.tabelas["coleta_bruta"]
    with banco.transacao() as conexao:
        return list(
            conexao.execute(
                select(coleta).where(coleta.c.execucao_id == execucao_id).order_by(coleta.c.id)
            )
        )


def test_primeira_resposta_e_enviada_e_registrada(
    banco: Banco, armazem: ArmazemDeBrutos, execucao_id: int, tmp_path: Path
) -> None:
    assert armazem.guardar(execucao_id, URL, CONTEUDO) is True

    (registro,) = _registros(banco, execucao_id)
    assert registro.fonte == "camara_v2"
    assert registro.url == URL
    assert (
        registro.chave_r2 == f"camara/api-v2/deputados/204496/historico/{registro.sha256}.json.gz"
    )
    assert len(registro.sha256) == 64
    assert registro.bytes == (tmp_path / registro.chave_r2).stat().st_size
    assert registro.coletada_em is not None


def test_conteudo_igual_ao_ultimo_da_mesma_url_nao_e_regravado(
    banco: Banco, armazem: ArmazemDeBrutos, execucao_id: int, tmp_path: Path
) -> None:
    armazem.guardar(execucao_id, URL, CONTEUDO)
    objetos_antes = list(tmp_path.rglob("*.json.gz"))

    assert armazem.guardar(execucao_id, URL, CONTEUDO) is False

    assert len(_registros(banco, execucao_id)) == 1
    assert list(tmp_path.rglob("*.json.gz")) == objetos_antes


def test_conteudo_diferente_e_gravado(
    banco: Banco, armazem: ArmazemDeBrutos, execucao_id: int
) -> None:
    armazem.guardar(execucao_id, URL, CONTEUDO)

    assert armazem.guardar(execucao_id, URL, {"dados": [], "links": []}) is True

    assert len(_registros(banco, execucao_id)) == 2


def test_volta_ao_conteudo_anterior_e_gravada_de_novo(
    banco: Banco, armazem: ArmazemDeBrutos, execucao_id: int
) -> None:
    # a comparação é com a ÚLTIMA coleta da URL, não com qualquer uma
    armazem.guardar(execucao_id, URL, CONTEUDO)
    armazem.guardar(execucao_id, URL, {"dados": [], "links": []})

    assert armazem.guardar(execucao_id, URL, CONTEUDO) is True

    assert len(_registros(banco, execucao_id)) == 3


def test_mesmo_conteudo_em_outra_url_e_gravado(
    banco: Banco, armazem: ArmazemDeBrutos, execucao_id: int
) -> None:
    armazem.guardar(execucao_id, URL, CONTEUDO)

    assert armazem.guardar(execucao_id, f"{BASE}/deputados/999/historico", CONTEUDO) is True


def test_registro_sobrevive_ao_rollback_da_coleta(
    banco: Banco, armazem: ArmazemDeBrutos, execucao_id: int
) -> None:
    with pytest.raises(RuntimeError), banco.transacao():
        armazem.guardar(execucao_id, URL, CONTEUDO)
        raise RuntimeError("falha na gravação dos dados")

    assert len(_registros(banco, execucao_id)) == 1


def test_falha_no_envio_nao_registra(banco: Banco, execucao_id: int) -> None:
    class _GravadorQuebrado:
        def enviar(self, chave: str, conteudo: bytes) -> None:
            raise ConnectionError("R2 fora do ar")

    with pytest.raises(ConnectionError):
        ArmazemDeBrutos(banco, _GravadorQuebrado()).guardar(execucao_id, URL, CONTEUDO)

    assert _registros(banco, execucao_id) == []
