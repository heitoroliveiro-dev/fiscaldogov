"""Registro de operação sem segredos (FR-030, constituição princípio VI).

O logger do ETL escreve uma linha JSON por evento; valores de campos cujo nome
indica segredo e senhas dentro de URLs de conexão saem mascarados, em qualquer
parte da linha: mensagem, campos, campos aninhados e erro.
"""

import io
import json
import logging

import pytest

from etl import registro

MASCARA = "***"
SENHA = "s3nh4-n40-p0d3-v4z4r"


@pytest.fixture
def saida() -> io.StringIO:
    buffer = io.StringIO()
    registro.configurar(buffer)
    return buffer


@pytest.fixture
def log() -> logging.Logger:
    return logging.getLogger("etl.teste")


def _unica_linha(saida: io.StringIO) -> dict:
    linhas = saida.getvalue().splitlines()
    assert len(linhas) == 1, linhas
    return json.loads(linhas[0])


def test_linha_json_com_mensagem_nivel_e_campos(saida: io.StringIO, log: logging.Logger) -> None:
    log.info("etapa concluida", extra={"etapa": "coletar", "gravados": 3})

    linha = _unica_linha(saida)

    assert linha["mensagem"] == "etapa concluida"
    assert linha["nivel"] == "INFO"
    assert linha["etapa"] == "coletar"
    assert linha["gravados"] == 3


@pytest.mark.parametrize(
    "campo",
    [
        "GITHUB_TOKEN_PUBLICACAO",
        "ALERTA_TELEGRAM_TOKEN",
        "R2_SECRET_ACCESS_KEY",
        "POSTGRES_PASSWORD",
        "DATABASE_URL_ESCRITA",
        "database_url_leitura",
    ],
)
def test_mascara_valor_de_campo_com_nome_de_segredo(
    saida: io.StringIO, log: logging.Logger, campo: str
) -> None:
    log.info("configuracao lida", extra={campo: SENHA})

    linha = _unica_linha(saida)

    assert linha[campo] == MASCARA
    assert SENHA not in saida.getvalue()


def test_nao_mascara_campo_comum(saida: io.StringIO, log: logging.Logger) -> None:
    log.info("configuracao lida", extra={"R2_BUCKET_BRUTOS": "fiscaldogov-brutos"})

    assert _unica_linha(saida)["R2_BUCKET_BRUTOS"] == "fiscaldogov-brutos"


def test_mascara_campo_de_segredo_aninhado(saida: io.StringIO, log: logging.Logger) -> None:
    log.info("ambiente", extra={"ambiente": {"R2_SECRET_ACCESS_KEY": SENHA, "R2_BUCKET": "b"}})

    assert _unica_linha(saida)["ambiente"] == {"R2_SECRET_ACCESS_KEY": MASCARA, "R2_BUCKET": "b"}


@pytest.mark.parametrize(
    ("url", "mascarada"),
    [
        (
            f"postgresql://etl_escrita:{SENHA}@db.railway.internal:5432/railway",
            "postgresql://etl_escrita:***@db.railway.internal:5432/railway",
        ),
        (
            f"postgresql+psycopg://site_leitura:{SENHA}@proxy.rlwy.net:41234/railway?sslmode=require",
            "postgresql+psycopg://site_leitura:***@proxy.rlwy.net:41234/railway?sslmode=require",
        ),
    ],
)
def test_mascara_senha_de_url_na_mensagem_e_em_campo_comum(
    saida: io.StringIO, log: logging.Logger, url: str, mascarada: str
) -> None:
    log.info("conectando em %s", url, extra={"destino": url})

    linha = _unica_linha(saida)

    assert linha["mensagem"] == f"conectando em {mascarada}"
    assert linha["destino"] == mascarada
    assert SENHA not in saida.getvalue()


@pytest.mark.parametrize(
    "url",
    [
        "https://dadosabertos.camara.leg.br/api/v2/deputados?itens=100&pagina=1",
        # porta seguida de @ no caminho não é senha
        "https://api.exemplo:443/perfil@fulano",
    ],
)
def test_url_sem_senha_fica_intacta(saida: io.StringIO, log: logging.Logger, url: str) -> None:
    log.info("coletando", extra={"url": url})

    assert _unica_linha(saida)["url"] == url


def test_mascara_senha_de_url_no_erro(saida: io.StringIO, log: logging.Logger) -> None:
    try:
        raise ConnectionError(f"falhou em postgresql://etl_escrita:{SENHA}@db:5432/railway")
    except ConnectionError:
        log.exception("coleta falhou")

    linha = _unica_linha(saida)

    assert "postgresql://etl_escrita:***@db:5432/railway" in linha["erro"]
    assert SENHA not in saida.getvalue()
