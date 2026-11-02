"""Registro de execuções em execucao_etl (T018, FR-010, data-model.md).

O registro usa transação própria: precisa sobreviver ao ROLLBACK da coleta,
senão uma execução com falha some sem deixar rastro (FR-012). Por isso estes
testes gravam de verdade e apagam ao fim só o que criaram.
"""

import threading
from collections.abc import Iterator
from datetime import datetime, timedelta

import pytest
from sqlalchemy import delete, func, select

from etl.adaptadores.persistencia.banco import Banco
from etl.adaptadores.persistencia.execucoes import (
    TRAVA_DO_INICIO,
    ExecucaoNaoEmAndamento,
    Execucoes,
    Gatilho,
    StatusExecucao,
)
from etl.portas import ColetaEmAndamento

VERSAO = "abc1234"


@pytest.fixture
def banco(url_escrita: str) -> Iterator[Banco]:
    banco = Banco.conectar(url_escrita, tempo_limite_s=10)
    tabela = banco.tabelas["execucao_etl"]
    with banco.transacao() as conexao:
        ultimo_id = conexao.execute(select(func.coalesce(func.max(tabela.c.id), 0))).scalar_one()
    yield banco
    with banco.transacao() as conexao:
        conexao.execute(delete(tabela).where(tabela.c.id > ultimo_id))
    banco.fechar()


@pytest.fixture
def execucoes(banco: Banco) -> Execucoes:
    return Execucoes(banco)


def _linha(banco: Banco, execucao_id: int):
    tabela = banco.tabelas["execucao_etl"]
    with banco.transacao() as conexao:
        return conexao.execute(select(tabela).where(tabela.c.id == execucao_id)).one()


def test_iniciar_grava_em_andamento(banco: Banco, execucoes: Execucoes) -> None:
    execucao_id = execucoes.iniciar(Gatilho.AGENDADA, VERSAO)

    linha = _linha(banco, execucao_id)
    assert linha.status == "em_andamento"
    assert linha.gatilho == "agendada"
    assert linha.versao_codigo == VERSAO
    assert linha.iniciada_em is not None
    assert linha.terminada_em is None


def test_inicio_sobrevive_ao_rollback_da_coleta(banco: Banco, execucoes: Execucoes) -> None:
    with pytest.raises(RuntimeError), banco.transacao():
        execucao_id = execucoes.iniciar(Gatilho.MANUAL, VERSAO)
        raise RuntimeError("falha na gravação da coleta")

    assert _linha(banco, execucao_id).status == "em_andamento"


def test_finalizar_grava_status_detalhes_e_termino(banco: Banco, execucoes: Execucoes) -> None:
    execucao_id = execucoes.iniciar(Gatilho.RESERVA, VERSAO)

    execucoes.finalizar(
        execucao_id,
        StatusExecucao.COM_PENDENCIAS,
        contagens={"parlamentar": 1, "periodo_exercicio": 3},
        tentativas=[{"url": "/deputados", "tentativas": 2}],
        erros=[],
        pendencias=[{"etapa": "backup", "motivo": "envio ao R2 falhou"}],
    )

    linha = _linha(banco, execucao_id)
    assert linha.status == "com_pendencias"
    assert linha.contagens == {"parlamentar": 1, "periodo_exercicio": 3}
    assert linha.tentativas == [{"url": "/deputados", "tentativas": 2}]
    assert linha.erros == []
    assert linha.pendencias == [{"etapa": "backup", "motivo": "envio ao R2 falhou"}]
    assert linha.terminada_em is not None
    assert linha.terminada_em >= linha.iniciada_em


def test_finalizar_sem_detalhes_mantem_os_padroes(banco: Banco, execucoes: Execucoes) -> None:
    execucao_id = execucoes.iniciar(Gatilho.RESERVA, VERSAO)

    execucoes.finalizar(execucao_id, StatusExecucao.DISPENSADA)

    linha = _linha(banco, execucao_id)
    assert linha.status == "dispensada"
    assert (linha.contagens, linha.tentativas, linha.erros, linha.pendencias) == ({}, [], [], [])


def test_finalizar_duas_vezes_e_recusado(execucoes: Execucoes) -> None:
    execucao_id = execucoes.iniciar(Gatilho.MANUAL, VERSAO)
    execucoes.finalizar(execucao_id, StatusExecucao.SUCESSO)

    with pytest.raises(ExecucaoNaoEmAndamento):
        execucoes.finalizar(execucao_id, StatusExecucao.FALHA)


def test_finalizar_execucao_inexistente_e_recusado(execucoes: Execucoes) -> None:
    with pytest.raises(ExecucaoNaoEmAndamento):
        execucoes.finalizar(2_000_000_000, StatusExecucao.SUCESSO)


def test_finalizar_como_em_andamento_e_recusado(execucoes: Execucoes) -> None:
    execucao_id = execucoes.iniciar(Gatilho.MANUAL, VERSAO)

    with pytest.raises(ValueError, match="em_andamento"):
        execucoes.finalizar(execucao_id, StatusExecucao.EM_ANDAMENTO)


def test_sem_execucao_bem_sucedida_devolve_nada(execucoes: Execucoes) -> None:
    execucoes.finalizar(execucoes.iniciar(Gatilho.AGENDADA, VERSAO), StatusExecucao.FALHA)
    execucoes.finalizar(execucoes.iniciar(Gatilho.RESERVA, VERSAO), StatusExecucao.DISPENSADA)

    assert execucoes.ultima_bem_sucedida() is None


def test_ultima_bem_sucedida_ignora_falha_dispensada_e_em_andamento(
    execucoes: Execucoes,
) -> None:
    sucesso = execucoes.iniciar(Gatilho.AGENDADA, VERSAO)
    execucoes.finalizar(sucesso, StatusExecucao.SUCESSO)
    com_pendencias = execucoes.iniciar(Gatilho.MANUAL, VERSAO)
    execucoes.finalizar(com_pendencias, StatusExecucao.COM_PENDENCIAS)
    execucoes.finalizar(execucoes.iniciar(Gatilho.AGENDADA, VERSAO), StatusExecucao.FALHA)
    execucoes.finalizar(execucoes.iniciar(Gatilho.RESERVA, VERSAO), StatusExecucao.DISPENSADA)
    execucoes.iniciar(Gatilho.MANUAL, VERSAO)

    ultima = execucoes.ultima_bem_sucedida()

    assert ultima is not None
    assert ultima.id == com_pendencias
    assert ultima.status is StatusExecucao.COM_PENDENCIAS
    assert ultima.gatilho is Gatilho.MANUAL
    assert ultima.terminada_em is not None


def test_houve_bem_sucedida_desde_conta_sucesso_e_com_pendencias(
    banco: Banco, execucoes: Execucoes
) -> None:
    agora = _agora(banco)
    hora = timedelta(hours=1)
    execucoes.finalizar(execucoes.iniciar(Gatilho.AGENDADA, VERSAO), StatusExecucao.FALHA)
    assert not execucoes.houve_bem_sucedida_desde(agora - hora)

    execucoes.finalizar(execucoes.iniciar(Gatilho.AGENDADA, VERSAO), StatusExecucao.COM_PENDENCIAS)

    assert execucoes.houve_bem_sucedida_desde(agora - hora)
    # iniciada antes do momento consultado não conta (dia anterior em Brasília)
    assert not execucoes.houve_bem_sucedida_desde(agora + hora)


def test_dispensada_nao_conta_como_bem_sucedida(banco: Banco, execucoes: Execucoes) -> None:
    agora = _agora(banco)

    execucao_id = execucoes.registrar_dispensada(VERSAO)

    linha = _linha(banco, execucao_id)
    assert (linha.status, linha.gatilho, linha.versao_codigo) == ("dispensada", "reserva", VERSAO)
    assert linha.terminada_em is not None
    assert not execucoes.houve_bem_sucedida_desde(agora - timedelta(hours=1))


def test_registrar_pendencia_depois_de_finalizada(banco: Banco, execucoes: Execucoes) -> None:
    execucao_id = execucoes.iniciar(Gatilho.MANUAL, VERSAO)
    execucoes.finalizar(execucao_id, StatusExecucao.SUCESSO, pendencias=[])

    execucoes.registrar_pendencia(execucao_id, {"etapa": "publicacao", "tipo": "X"})

    linha = _linha(banco, execucao_id)
    assert (linha.status, linha.pendencias) == (
        "com_pendencias",
        [{"etapa": "publicacao", "tipo": "X"}],
    )


def test_registrar_pendencia_em_falha_e_recusado(execucoes: Execucoes) -> None:
    execucao_id = execucoes.iniciar(Gatilho.MANUAL, VERSAO)
    execucoes.finalizar(execucao_id, StatusExecucao.FALHA)

    with pytest.raises(ValueError, match="dados gravados"):
        execucoes.registrar_pendencia(execucao_id, {"etapa": "publicacao"})


def test_abrir_espera_a_outra_abertura_e_ve_a_coleta_dela(
    banco: Banco, execucoes: Execucoes
) -> None:
    """Outra abertura segura a trava e ainda não fez COMMIT: abrir espera, depois recusa.

    Sem a trava, abrir não veria a em_andamento ainda não confirmada e começaria
    uma segunda coleta junto com a primeira.
    """
    resultado: list[object] = []

    def abrir() -> None:
        try:
            resultado.append(execucoes.abrir(Gatilho.MANUAL, VERSAO))
        except ColetaEmAndamento as erro:
            resultado.append(erro)

    with banco.engine.begin() as outra:
        outra.execute(select(func.pg_advisory_xact_lock(TRAVA_DO_INICIO)))
        tabela = banco.tabelas["execucao_etl"]
        outra.execute(tabela.insert().values(gatilho="agendada", versao_codigo=VERSAO))
        concorrente = threading.Thread(target=abrir)
        concorrente.start()
        concorrente.join(timeout=1)
        assert concorrente.is_alive(), "abrir não esperou pela trava da outra abertura"
    concorrente.join(timeout=30)

    (desfecho,) = resultado
    assert isinstance(desfecho, ColetaEmAndamento)


def _agora(banco: Banco) -> datetime:
    with banco.transacao() as conexao:
        return conexao.execute(select(func.now())).scalar_one()
