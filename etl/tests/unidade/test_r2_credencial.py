"""Credencial do R2 recusada é nomeada no alerta (FR-020a).

O boto3 devolve ClientError com o código do S3; os que significam chave
inválida ou sem permissão viram CredencialInvalida, no envio dos brutos e no
envio e na conferência do backup.
"""

from pathlib import Path

import pytest
from boto3.exceptions import S3UploadFailedError
from botocore.exceptions import ClientError

from etl.adaptadores.backup_r2.backup import ArmazenamentoR2
from etl.adaptadores.brutos_r2.armazem import CREDENCIAL_R2, GravadorR2, traduzir_erro_do_r2
from etl.portas import CredencialInvalida


def _erro(codigo: str, http: int) -> ClientError:
    return ClientError(
        {"Error": {"Code": codigo, "Message": "x"}, "ResponseMetadata": {"HTTPStatusCode": http}},
        "PutObject",
    )


@pytest.mark.parametrize(
    ("codigo", "http"),
    [
        ("InvalidAccessKeyId", 403),
        ("SignatureDoesNotMatch", 403),
        ("AccessDenied", 403),
        ("Unauthorized", 401),
    ],
)
def test_chave_recusada_vira_credencial_invalida(codigo: str, http: int) -> None:
    traduzido = traduzir_erro_do_r2(_erro(codigo, http))

    assert isinstance(traduzido, CredencialInvalida)
    assert traduzido.credencial == CREDENCIAL_R2
    assert "R2_ACCESS_KEY_ID" in CREDENCIAL_R2


@pytest.mark.parametrize(("codigo", "http"), [("NoSuchBucket", 404), ("InternalError", 500)])
def test_outros_erros_do_r2_passam_como_estao(codigo: str, http: int) -> None:
    erro = _erro(codigo, http)

    assert traduzir_erro_do_r2(erro) is erro


class _S3QueRecusa:
    def put_object(self, **_: object) -> None:
        raise _erro("InvalidAccessKeyId", 403)

    def upload_file(self, *_: object, **__: object) -> None:
        # como o boto3 real: o ClientError vem embrulhado
        try:
            raise _erro("SignatureDoesNotMatch", 403)
        except ClientError as erro:
            raise S3UploadFailedError("Failed to upload") from erro

    def download_file(self, *_: object) -> None:
        raise _erro("AccessDenied", 403)


def test_gravador_dos_brutos_nomeia_a_credencial() -> None:
    with pytest.raises(CredencialInvalida):
        GravadorR2(_S3QueRecusa(), "fiscaldogov-brutos").enviar("chave", b"{}")


def test_armazenamento_do_backup_nomeia_a_credencial(tmp_path: Path) -> None:
    armazenamento = ArmazenamentoR2(_S3QueRecusa(), "fiscaldogov-backup")
    arquivo = tmp_path / "banco.dump"
    arquivo.write_bytes(b"x")

    with pytest.raises(CredencialInvalida):
        armazenamento.enviar("diario/x.dump", arquivo)
    with pytest.raises(CredencialInvalida):
        armazenamento.baixar("diario/x.dump", tmp_path / "volta.dump")
