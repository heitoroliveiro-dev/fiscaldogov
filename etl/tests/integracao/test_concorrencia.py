"""Uma coleta por vez, e a travada não bloqueia a seguinte (T063, FR-013, FR-013a).

Com uma em_andamento iniciada há menos de 60 min, coletar é recusada (código 3
na CLI) sem gravar nada. Uma iniciada há mais de 60 min (processo encerrado à
força) é fechada como falha "interrompida", com alerta, e a coleta segue.
"""

from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any

import pytest
from apoio_coleta import AlertadorFalso, banco_limpo, contar, linhas, montar_coleta
from sqlalchemy import text

from etl.adaptadores.persistencia.banco import Banco
from etl.pipeline.coletar import ColetaEmAndamento
from etl.portas import Gatilho


@pytest.fixture
def banco(url_escrita: str) -> Iterator[Banco]:
    with banco_limpo(url_escrita) as banco:
        yield banco


def _em_andamento_ha(banco: Banco, minutos: int) -> int:
    with banco.transacao() as conexao:
        return conexao.execute(
            text(
                "INSERT INTO execucao_etl (status, gatilho, versao_codigo, iniciada_em) "
                "VALUES ('em_andamento', 'agendada', 'teste', now() - make_interval(mins => :m)) "
                "RETURNING id"
            ),
            {"m": minutos},
        ).scalar_one()


class _FonteQueNaoDeveSerChamada:
    def __init__(self) -> None:
        self.chamadas = 0

    def listar_em_exercicio(self) -> list:
        self.chamadas += 1
        raise RuntimeError("fonte fora do ar de propósito")

    def historico(self, parlamentar: Any) -> Any:
        raise AssertionError("não chega aqui")


def _criar(fonte: _FonteQueNaoDeveSerChamada) -> Callable[..., _FonteQueNaoDeveSerChamada]:
    return lambda *_: fonte


def test_com_coleta_recente_em_andamento_nao_comeca_nem_grava(banco: Banco, tmp_path: Path) -> None:
    _em_andamento_ha(banco, 10)
    execucoes_antes = contar(banco, "execucao_etl")
    fonte, alertador = _FonteQueNaoDeveSerChamada(), AlertadorFalso()

    with pytest.raises(ColetaEmAndamento, match="já há uma coleta em andamento"):
        montar_coleta(banco, tmp_path, _criar(fonte), alertador=alertador).executar(Gatilho.MANUAL)

    assert contar(banco, "execucao_etl") == execucoes_antes
    assert fonte.chamadas == 0
    assert alertador.textos == []


def test_coleta_travada_ha_mais_de_60_min_e_fechada_como_interrompida_e_alerta(
    banco: Banco, tmp_path: Path
) -> None:
    travada = _em_andamento_ha(banco, 61)
    fonte, alertador = _FonteQueNaoDeveSerChamada(), AlertadorFalso()

    resultado = montar_coleta(banco, tmp_path, _criar(fonte), alertador=alertador).executar(
        Gatilho.AGENDADA
    )

    (anterior,) = linhas(
        banco, "SELECT status, terminada_em, erros FROM execucao_etl WHERE id = :id", id=travada
    )
    assert anterior.status == "falha"
    assert anterior.terminada_em is not None
    assert anterior.erros == [{"etapa": "vigia", "tipo": "interrompida"}]
    # a coleta seguiu: chamou a fonte e registrou a própria execução
    assert fonte.chamadas == 1
    assert resultado.execucao_id != travada
    assert any(f"execução {travada}" in t and "interrompida" in t for t in alertador.textos)


def test_coleta_com_exatamente_59_min_ainda_e_considerada_viva(
    banco: Banco, tmp_path: Path
) -> None:
    _em_andamento_ha(banco, 59)

    with pytest.raises(ColetaEmAndamento):
        montar_coleta(banco, tmp_path, _criar(_FonteQueNaoDeveSerChamada())).executar(
            Gatilho.MANUAL
        )
