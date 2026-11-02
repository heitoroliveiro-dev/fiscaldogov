"""Cópia de segurança conferida (T078, FR-024, FR-026, research §6).

O pg_dump roda com o papel etl_escrita, o mesmo da produção: prova que as
permissões da migration 0001 bastam. O que foi enviado é baixado de volta e
conferido com pg_restore --list. Backup que falha não derruba a coleta: vira
`com_pendencias`, com alerta, e a publicação segue.

Precisa de pg_dump e pg_restore da mesma major do servidor (18): no PATH ou em
PG_BIN_DIR. Sem eles, o teste é pulado; com ETL_EXIGIR_INTEGRACAO=1, falha.
"""

import os
import shutil
import subprocess
from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest
from apoio_coleta import CELSO, HISTORICO, AlertadorFalso, PublicadorFalso, banco_limpo

from etl.adaptadores.backup_r2.backup import ArmazenamentoEmDisco, BackupInvalido, BackupR2
from etl.adaptadores.brutos_r2.armazem import ArmazemDeBrutos, GravadorEmDisco
from etl.adaptadores.persistencia.banco import Banco
from etl.adaptadores.persistencia.execucoes import Execucoes
from etl.adaptadores.persistencia.repositorio import Repositorio
from etl.pipeline.coletar import Coleta
from etl.portas import Gatilho, StatusExecucao

DOMINGO_AS_3_EM_BRASILIA = datetime(2026, 11, 1, 6, 0, tzinfo=UTC)
MAJOR_DO_SERVIDOR = "18"


def _binario(nome: str) -> str:
    pasta = os.environ.get("PG_BIN_DIR")
    caminho = str(Path(pasta) / nome) if pasta else shutil.which(nome)
    if not caminho or not Path(caminho).exists():
        mensagem = f"{nome} não encontrado (PATH ou PG_BIN_DIR)"
        if os.environ.get("ETL_EXIGIR_INTEGRACAO") == "1":
            pytest.fail(f"{mensagem}. ETL_EXIGIR_INTEGRACAO=1 proíbe pular.", pytrace=False)
        pytest.skip(mensagem)
    # binário do PATH ou de PG_BIN_DIR, configuração do teste
    versao = subprocess.run(  # noqa: S603
        [caminho, "--version"], capture_output=True, text=True, check=True
    )
    major = versao.stdout.split()[-1].split(".")[0]
    assert major == MAJOR_DO_SERVIDOR, f"{nome} {versao.stdout.strip()}: precisa ser da major 18"
    return caminho


@pytest.fixture(scope="module")
def binarios() -> dict[str, str]:
    return {"pg_dump": _binario("pg_dump"), "pg_restore": _binario("pg_restore")}


def _backup(url: str, pasta: Path, binarios: dict[str, str], armazenamento: Any = None):
    return BackupR2(
        url,
        armazenamento or ArmazenamentoEmDisco(pasta / "bucket"),
        relogio=lambda: DOMINGO_AS_3_EM_BRASILIA,
        **binarios,
    )


def test_dump_com_etl_escrita_e_conferido_no_destino(
    url_escrita: str, tmp_path: Path, binarios: dict[str, str]
) -> None:
    chaves = _backup(url_escrita, tmp_path, binarios).copiar()

    assert chaves == ["diario/2026-11-01.dump", "semanal/2026-11-01.dump"]
    for chave in chaves:
        arquivo = tmp_path / "bucket" / chave
        lista = subprocess.run(  # noqa: S603 — binário conferido em _binario
            [binarios["pg_restore"], "--list", str(arquivo)],
            capture_output=True,
            text=True,
            check=True,
        )
        assert "TABLE DATA public parlamentar" in lista.stdout
        assert "TABLE DATA public execucao_etl" in lista.stdout


class _ArmazenamentoQueCorrompe(ArmazenamentoEmDisco):
    def enviar(self, chave: str, arquivo: Path) -> None:
        corrompido = arquivo.with_suffix(".corrompido")
        corrompido.write_bytes(b"PGDMP" + b"\x00" * 64)
        super().enviar(chave, corrompido)


def test_arquivo_corrompido_no_destino_e_backup_invalido(
    url_escrita: str, tmp_path: Path, binarios: dict[str, str]
) -> None:
    armazenamento = _ArmazenamentoQueCorrompe(tmp_path / "bucket")

    with pytest.raises(BackupInvalido):
        _backup(url_escrita, tmp_path, binarios, armazenamento).copiar()


class _BackupQueFalha:
    def __init__(self, erro: Exception) -> None:
        self._erro = erro

    def copiar(self) -> list[str]:
        raise self._erro


@pytest.fixture
def banco(url_escrita: str) -> Iterator[Banco]:
    with banco_limpo(url_escrita) as banco:
        yield banco


class _Fonte:
    def listar_em_exercicio(self) -> list:
        return [CELSO]

    def historico(self, parlamentar: Any) -> Any:
        return HISTORICO


@pytest.mark.parametrize(
    "erro",
    [ConnectionError("R2 fora do ar"), BackupInvalido("pg_restore --list recusou o arquivo")],
    ids=["envio", "conferencia"],
)
def test_falha_do_backup_vira_pendencia_com_alerta_e_publica(
    banco: Banco, tmp_path: Path, erro: Exception
) -> None:
    publicador, alertador = PublicadorFalso(), AlertadorFalso()
    coleta = Coleta(
        criar_fonte=lambda *_: _Fonte(),
        repositorio=Repositorio(banco),
        brutos=ArmazemDeBrutos(banco, GravadorEmDisco(tmp_path)),
        execucoes=Execucoes(banco),
        backup=_BackupQueFalha(erro),
        publicador=publicador,
        alertador=alertador,
        versao_codigo="teste",
    )

    resultado = coleta.executar(Gatilho.MANUAL)

    assert resultado.status is StatusExecucao.COM_PENDENCIAS
    assert publicador.disparos == [resultado.execucao_id]
    (alerta,) = alertador.textos
    assert "coleta com pendências" in alerta
    assert f"- backup: {type(erro).__name__}" in alerta
