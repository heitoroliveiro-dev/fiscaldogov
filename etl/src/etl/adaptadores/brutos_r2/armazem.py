"""Respostas brutas sanitizadas no R2 (FR-011, FR-012, research §6).

Chave camara/api-v2/<caminho>/<sha256>.json.gz. O hash é do JSON canônico
(chaves ordenadas), então a mesma resposta sempre dá o mesmo objeto. Só grava
quando o hash difere da última coleta_bruta da mesma URL. O registro em
coleta_bruta usa transação própria, como execucao_etl, para sobreviver ao
ROLLBACK dos dados. A retenção (365 dias) é regra do bucket, não código.
"""

import gzip
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol
from urllib.parse import urlsplit

import boto3
from botocore.config import Config
from sqlalchemy import func, select

from etl.adaptadores.persistencia.banco import Banco

FONTE = "camara_v2"
_PREFIXO_DA_API = "/api/v2/"
_PREFIXO_DA_CHAVE = "camara/api-v2"


@dataclass(frozen=True)
class Pacote:
    json: bytes
    compactado: bytes
    sha256: str

    @property
    def bytes(self) -> int:
        return len(self.compactado)


def empacotar(conteudo: Any) -> Pacote:
    texto = json.dumps(conteudo, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    dados = texto.encode("utf-8")
    # mtime=0: sem data no cabeçalho do gzip, o objeto depende só do conteúdo
    return Pacote(dados, gzip.compress(dados, mtime=0), hashlib.sha256(dados).hexdigest())


def chave_do_bruto(url: str, sha256: str) -> str:
    caminho = urlsplit(url).path
    if _PREFIXO_DA_API not in caminho:
        raise ValueError(f"URL fora da api/v2 da Câmara: {url}")
    relativo = caminho.split(_PREFIXO_DA_API, 1)[1].strip("/")
    return f"{_PREFIXO_DA_CHAVE}/{relativo}/{sha256}.json.gz"


class Gravador(Protocol):
    def enviar(self, chave: str, conteudo: bytes) -> None: ...


def criar_cliente_r2(account_id: str, access_key_id: str, secret_access_key: str) -> Any:
    return boto3.client(
        "s3",
        endpoint_url=f"https://{account_id}.r2.cloudflarestorage.com",
        aws_access_key_id=access_key_id,
        aws_secret_access_key=secret_access_key,
        region_name="auto",
        # checksum só quando a operação exige: o padrão do boto3 desde a 1.36 manda
        # cabeçalhos extras; conferir contra o R2 real na T052
        config=Config(
            request_checksum_calculation="when_required",
            response_checksum_validation="when_required",
        ),
    )


class GravadorR2:
    def __init__(self, s3: Any, bucket: str) -> None:
        self._s3 = s3
        self._bucket = bucket

    def enviar(self, chave: str, conteudo: bytes) -> None:
        self._s3.put_object(
            Bucket=self._bucket,
            Key=chave,
            Body=conteudo,
            ContentType="application/json",
            ContentEncoding="gzip",
        )


class GravadorEmDisco:
    """Para testes e desenvolvimento, sem credencial do R2."""

    def __init__(self, pasta: Path) -> None:
        self._pasta = pasta.resolve()

    def enviar(self, chave: str, conteudo: bytes) -> None:
        destino = (self._pasta / chave).resolve()
        if not destino.is_relative_to(self._pasta):
            raise ValueError(f"chave fora da pasta de brutos: {chave}")
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_bytes(conteudo)


class ArmazemDeBrutos:
    def __init__(self, banco: Banco, gravador: Gravador) -> None:
        self._banco = banco
        self._gravador = gravador
        self._tabela = banco.tabelas["coleta_bruta"]

    def guardar(self, execucao_id: int, url: str, conteudo: Any) -> bool:
        """Envia e registra; False quando igual à última coleta da mesma URL."""
        pacote = empacotar(conteudo)
        if self._ultimo_sha256(url) == pacote.sha256:
            return False

        chave = chave_do_bruto(url, pacote.sha256)
        self._gravador.enviar(chave, pacote.compactado)
        with self._banco.engine.begin() as conexao:
            conexao.execute(
                self._tabela.insert().values(
                    execucao_id=execucao_id,
                    fonte=FONTE,
                    url=url,
                    chave_r2=chave,
                    sha256=pacote.sha256,
                    bytes=pacote.bytes,
                    coletada_em=func.now(),
                )
            )
        return True

    def _ultimo_sha256(self, url: str) -> str | None:
        t = self._tabela
        consulta = (
            select(t.c.sha256)
            .where(t.c.url == url)
            .order_by(t.c.coletada_em.desc(), t.c.id.desc())
            .limit(1)
        )
        with self._banco.engine.connect() as conexao:
            return conexao.execute(consulta).scalar_one_or_none()
