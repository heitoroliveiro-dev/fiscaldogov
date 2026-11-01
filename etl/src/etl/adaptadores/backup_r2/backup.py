"""Cópia de segurança do banco no R2, conferida (FR-024, FR-026, research §6).

`pg_dump --format=custom` com o papel etl_escrita (a migration 0001 concede a
leitura de que ele precisa), enviado a `diario/AAAA-MM-DD.dump` e, aos domingos,
também a `semanal/AAAA-MM-DD.dump`, pela data de Brasília. Cada objeto enviado é
baixado de volta e conferido com `pg_restore --list`. A retenção (7 e 28 dias)
é regra de ciclo de vida do bucket, não código.

A credencial vai para o pg_dump pelas variáveis da libpq (PGPASSWORD etc.),
nunca na linha de comando: assim ela não aparece em `ps` nem em mensagem de erro.
"""

import os
import shutil
import subprocess
import tempfile
from collections.abc import Callable, Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol
from zoneinfo import ZoneInfo

from sqlalchemy import make_url

BRASILIA = ZoneInfo("America/Sao_Paulo")
DOMINGO = 6
# o fim da saída de erro ajuda o diagnóstico; o começo costuma repetir o comando
TRECHO_DO_ERRO = 500


class BackupInvalido(Exception):
    """O arquivo no destino não é um dump legível: a cópia não serve para restaurar."""


class FalhaNoBackup(Exception):
    """pg_dump ou pg_restore saíram com erro."""


def chaves_do_backup(agora: datetime) -> list[str]:
    if agora.tzinfo is None:
        raise ValueError("horário sem fuso: a data do backup é a de Brasília")
    dia = agora.astimezone(BRASILIA).date()
    chaves = [f"diario/{dia.isoformat()}.dump"]
    if dia.weekday() == DOMINGO:
        chaves.append(f"semanal/{dia.isoformat()}.dump")
    return chaves


class Armazenamento(Protocol):
    def enviar(self, chave: str, arquivo: Path) -> None: ...

    def baixar(self, chave: str, destino: Path) -> None: ...


class ArmazenamentoR2:
    def __init__(self, s3: Any, bucket: str) -> None:
        self._s3 = s3
        self._bucket = bucket

    def enviar(self, chave: str, arquivo: Path) -> None:
        # upload_file divide arquivos grandes em partes sozinho
        self._s3.upload_file(
            str(arquivo), self._bucket, chave, ExtraArgs={"ContentType": "application/octet-stream"}
        )

    def baixar(self, chave: str, destino: Path) -> None:
        self._s3.download_file(self._bucket, chave, str(destino))


class ArmazenamentoEmDisco:
    """Para testes e desenvolvimento, sem credencial do R2."""

    def __init__(self, pasta: Path) -> None:
        self._pasta = pasta.resolve()

    def _caminho(self, chave: str) -> Path:
        caminho = (self._pasta / chave).resolve()
        if not caminho.is_relative_to(self._pasta):
            raise ValueError(f"chave fora da pasta de backup: {chave}")
        return caminho

    def enviar(self, chave: str, arquivo: Path) -> None:
        destino = self._caminho(chave)
        destino.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(arquivo, destino)

    def baixar(self, chave: str, destino: Path) -> None:
        shutil.copyfile(self._caminho(chave), destino)


def ambiente_libpq(url: str, base: Mapping[str, str]) -> dict[str, str]:
    """Variáveis da libpq a partir da URL, sem a senha passar pela linha de comando."""
    partes = make_url(url)
    ambiente = {chave: valor for chave, valor in base.items() if not chave.startswith("PG")}
    campos = {
        "PGHOST": partes.host,
        "PGPORT": partes.port,
        "PGUSER": partes.username,
        "PGPASSWORD": partes.password,
        "PGDATABASE": partes.database,
        "PGSSLMODE": partes.query.get("sslmode"),
    }
    ambiente.update({chave: str(valor) for chave, valor in campos.items() if valor})
    return ambiente


class BackupR2:
    def __init__(
        self,
        url_escrita: str,
        armazenamento: Armazenamento,
        *,
        relogio: Callable[[], datetime] = lambda: datetime.now(UTC),
        pg_dump: str = "pg_dump",
        pg_restore: str = "pg_restore",
    ) -> None:
        self._ambiente = ambiente_libpq(url_escrita, os.environ)
        self._armazenamento = armazenamento
        self._relogio = relogio
        self._pg_dump = pg_dump
        self._pg_restore = pg_restore

    def copiar(self) -> list[str]:
        """Gera, envia e confere; devolve as chaves gravadas."""
        chaves = chaves_do_backup(self._relogio())
        with tempfile.TemporaryDirectory(prefix="backup-") as pasta:
            dump = Path(pasta) / "banco.dump"
            self._rodar([self._pg_dump, "--format=custom", f"--file={dump}"], "pg_dump")
            for chave in chaves:
                self._armazenamento.enviar(chave, dump)
            for chave in chaves:
                conferencia = Path(pasta) / "conferencia.dump"
                self._armazenamento.baixar(chave, conferencia)
                self._conferir(chave, conferencia)
                conferencia.unlink()
        return chaves

    def _conferir(self, chave: str, arquivo: Path) -> None:
        try:
            lista = self._rodar([self._pg_restore, "--list", str(arquivo)], "pg_restore --list")
        except FalhaNoBackup as erro:
            raise BackupInvalido(f"{chave}: {erro}") from erro
        if "TABLE DATA" not in lista:
            raise BackupInvalido(f"{chave}: o dump não tem dados de tabela")

    def _rodar(self, comando: list[str], nome: str) -> str:
        # comando montado aqui, com binário da configuração e caminhos temporários
        resultado = subprocess.run(  # noqa: S603
            comando, env=self._ambiente, capture_output=True, text=True, check=False
        )
        if resultado.returncode != 0:
            raise FalhaNoBackup(
                f"{nome} saiu com código {resultado.returncode}: "
                f"{resultado.stderr.strip()[-TRECHO_DO_ERRO:]}"
            )
        return resultado.stdout
