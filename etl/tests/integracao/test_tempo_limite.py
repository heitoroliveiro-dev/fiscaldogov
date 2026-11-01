"""Vigia de tempo da coleta (T064, FR-013a, research §5).

Com tempo limite de 2 s, uma fonte ou uma gravação que demora é interrompida:
a execução termina `falha` com motivo "tempo esgotado", nada fica gravado e a
execução seguinte roda (não sobra em_andamento bloqueando).
"""

import signal
import time
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from apoio_coleta import (
    CELSO,
    HISTORICO,
    AlertadorFalso,
    BackupFalso,
    banco_limpo,
    contar,
    linhas,
    montar_coleta,
)
from sqlalchemy import Connection

from etl.adaptadores.brutos_r2.armazem import ArmazemDeBrutos, GravadorEmDisco
from etl.adaptadores.persistencia.banco import Banco
from etl.adaptadores.persistencia.execucoes import Execucoes
from etl.adaptadores.persistencia.repositorio import Repositorio
from etl.dominio.entidades import Historico
from etl.pipeline.coletar import Coleta
from etl.portas import Gatilho, StatusExecucao


@pytest.fixture
def banco(url_escrita: str) -> Iterator[Banco]:
    with banco_limpo(url_escrita) as banco:
        yield banco


class _Fonte:
    def __init__(self, demora_s: float = 0) -> None:
        self._demora_s = demora_s

    def listar_em_exercicio(self) -> list:
        time.sleep(self._demora_s)
        return [CELSO]

    def historico(self, parlamentar: Any) -> Historico:
        return HISTORICO


class _RepositorioLento(Repositorio):
    """Grava o primeiro parlamentar e trava dentro da mesma transação."""

    def _gravar_um(self, conexao: Connection, dados: Any) -> None:
        super()._gravar_um(conexao, dados)
        time.sleep(10)


def _erros(banco: Banco, execucao_id: int) -> Any:
    (linha,) = linhas(
        banco, "SELECT status, erros FROM execucao_etl WHERE id = :id", id=execucao_id
    )
    return linha


def test_fonte_que_demora_e_interrompida_como_tempo_esgotado(banco: Banco, tmp_path: Path) -> None:
    alertador = AlertadorFalso()
    parlamentares_antes = contar(banco, "parlamentar")
    inicio = time.monotonic()

    resultado = montar_coleta(
        banco, tmp_path, lambda *_: _Fonte(demora_s=10), alertador=alertador, tempo_limite_s=2
    ).executar(Gatilho.MANUAL)

    assert time.monotonic() - inicio < 6
    assert resultado.status is StatusExecucao.FALHA
    execucao = _erros(banco, resultado.execucao_id)
    assert execucao.status == "falha"
    assert execucao.erros == [
        {"etapa": "vigia", "tipo": "TempoEsgotado", "mensagem": "tempo esgotado (2 s)"}
    ]
    assert contar(banco, "parlamentar") == parlamentares_antes
    assert any("tempo esgotado" in texto for texto in alertador.textos)
    assert signal.alarm(0) == 0  # o vigia foi desarmado


def test_gravacao_interrompida_no_meio_e_desfeita(banco: Banco, tmp_path: Path) -> None:
    parlamentares_antes = contar(banco, "parlamentar")
    coleta = Coleta(
        criar_fonte=lambda *_: _Fonte(),
        repositorio=_RepositorioLento(banco),
        brutos=ArmazemDeBrutos(banco, GravadorEmDisco(tmp_path)),
        execucoes=Execucoes(banco),
        backup=BackupFalso(),
        publicador=_SemPublicar(),
        alertador=AlertadorFalso(),
        versao_codigo="teste",
        tempo_limite_s=2,
    )

    resultado = coleta.executar(Gatilho.MANUAL)

    assert resultado.status is StatusExecucao.FALHA
    assert _erros(banco, resultado.execucao_id).erros[0]["tipo"] == "TempoEsgotado"
    assert contar(banco, "parlamentar") == parlamentares_antes
    periodos_do_celso = (
        "SELECT 1 FROM periodo_exercicio pe JOIN mandato m ON m.id = pe.mandato_id "
        "JOIN parlamentar p ON p.id = m.parlamentar_id WHERE p.nome_parlamentar = 'Celso Sabino'"
    )
    assert linhas(banco, periodos_do_celso) == []


def test_depois_do_tempo_esgotado_a_execucao_seguinte_roda(banco: Banco, tmp_path: Path) -> None:
    montar_coleta(banco, tmp_path, lambda *_: _Fonte(demora_s=10), tempo_limite_s=2).executar(
        Gatilho.MANUAL
    )

    seguinte = montar_coleta(banco, tmp_path, lambda *_: _Fonte()).executar(Gatilho.MANUAL)

    assert seguinte.status is StatusExecucao.SUCESSO
    assert linhas(banco, "SELECT 1 FROM parlamentar WHERE nome_parlamentar = 'Celso Sabino'")


class _SemPublicar:
    def disparar(self, execucao_id: int) -> None:
        raise AssertionError("não publica depois de falha")
