"""Respostas brutas: chave, compactação, hash e envio (FR-011, research §6, T026).

A deduplicação consulta coleta_bruta no banco e por isso é testada em
tests/integracao/test_armazem_brutos.py.
"""

import gzip
import hashlib
import json
from pathlib import Path

import pytest

from etl.adaptadores.brutos_r2.armazem import (
    GravadorEmDisco,
    GravadorR2,
    chave_do_bruto,
    criar_cliente_r2,
    empacotar,
)

BASE = "https://dadosabertos.camara.leg.br/api/v2"
CONTEUDO = {"dados": [{"id": 204496, "nome": "Celso Sabino"}], "links": []}


def test_hash_e_do_json_canonico_e_ignora_a_ordem_das_chaves() -> None:
    reordenado = {"links": [], "dados": [{"nome": "Celso Sabino", "id": 204496}]}

    pacote = empacotar(CONTEUDO)

    assert pacote.sha256 == empacotar(reordenado).sha256
    assert pacote.sha256 == hashlib.sha256(pacote.json).hexdigest()
    assert json.loads(pacote.json) == CONTEUDO


def test_conteudo_compactado_volta_ao_json_original() -> None:
    pacote = empacotar(CONTEUDO)

    assert json.loads(gzip.decompress(pacote.compactado)) == CONTEUDO
    assert pacote.bytes == len(pacote.compactado)


def test_compactacao_e_deterministica() -> None:
    # sem data no cabeçalho do gzip: o mesmo conteúdo gera o mesmo objeto
    assert empacotar(CONTEUDO).compactado == empacotar(CONTEUDO).compactado


def test_texto_com_acento_vai_em_utf8() -> None:
    assert "UNIÃO".encode() in empacotar({"siglaPartido": "UNIÃO"}).json


@pytest.mark.parametrize(
    ("url", "caminho"),
    [
        (f"{BASE}/deputados?itens=100&pagina=1", "deputados"),
        (f"{BASE}/deputados?pagina=2&itens=100", "deputados"),
        (f"{BASE}/deputados/204496/historico", "deputados/204496/historico"),
    ],
)
def test_chave_segue_o_caminho_da_api(url: str, caminho: str) -> None:
    sha = "a" * 64

    assert chave_do_bruto(url, sha) == f"camara/api-v2/{caminho}/{sha}.json.gz"


def test_url_fora_da_api_v2_e_recusada() -> None:
    with pytest.raises(ValueError, match="api/v2"):
        chave_do_bruto("https://www.camara.leg.br/deputados/204496", "a" * 64)


def test_gravador_em_disco_escreve_na_chave(tmp_path: Path) -> None:
    pacote = empacotar(CONTEUDO)
    chave = chave_do_bruto(f"{BASE}/deputados/204496/historico", pacote.sha256)

    GravadorEmDisco(tmp_path).enviar(chave, pacote.compactado)

    assert (tmp_path / chave).read_bytes() == pacote.compactado


class _S3Falso:
    def __init__(self) -> None:
        self.envios: list[dict] = []

    def put_object(self, **parametros: object) -> None:
        self.envios.append(parametros)


def test_gravador_r2_envia_ao_bucket_com_tipo_e_compactacao() -> None:
    s3 = _S3Falso()

    GravadorR2(s3, "fiscaldogov-brutos").enviar("camara/api-v2/x/y.json.gz", b"gz")

    assert s3.envios == [
        {
            "Bucket": "fiscaldogov-brutos",
            "Key": "camara/api-v2/x/y.json.gz",
            "Body": b"gz",
            "ContentType": "application/json",
            "ContentEncoding": "gzip",
        }
    ]


def test_cliente_r2_usa_o_endpoint_s3_da_conta() -> None:
    cliente = criar_cliente_r2("conta123", "chave", "segredo")

    assert cliente.meta.endpoint_url == "https://conta123.r2.cloudflarestorage.com"
    assert cliente.meta.region_name == "auto"
