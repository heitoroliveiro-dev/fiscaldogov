"""O domínio não conhece as fontes nem o banco (FR-023, ADR-0003).

Nenhum módulo de etl/src/etl/dominio/ importa etl.adaptadores nem bibliotecas
de I/O. A troca de formato de uma API muda o adaptador, nunca a regra de negócio.
"""

import ast
from pathlib import Path

PACOTE = Path(__file__).parents[2] / "src" / "etl"
DOMINIO = PACOTE / "dominio"

PROIBIDOS = ("etl.adaptadores", "httpx", "sqlalchemy", "boto3", "psycopg")


def _pacote_do_modulo(arquivo: Path) -> list[str]:
    partes = list(arquivo.relative_to(PACOTE.parent).with_suffix("").parts)
    # o pacote é a pasta do arquivo, inclusive para __init__.py
    return partes[:-1]


def _importados(fonte: str, pacote: list[str]) -> list[str]:
    modulos = []
    for no in ast.walk(ast.parse(fonte)):
        if isinstance(no, ast.Import):
            modulos.extend(alias.name for alias in no.names)
        elif isinstance(no, ast.ImportFrom):
            base = pacote[: len(pacote) - no.level + 1] if no.level else []
            raiz = ".".join([*base, *([no.module] if no.module else [])])
            modulos.append(raiz)
            # "from .. import adaptadores" importa o subpacote pelo nome
            modulos.extend(f"{raiz}.{alias.name}" for alias in no.names)
    return modulos


def _violacoes(fonte: str, pacote: list[str]) -> list[str]:
    return [
        modulo
        for modulo in _importados(fonte, pacote)
        if any(modulo == p or modulo.startswith(f"{p}.") for p in PROIBIDOS)
    ]


def test_dominio_nao_importa_adaptadores_nem_io() -> None:
    arquivos = sorted(DOMINIO.rglob("*.py"))
    assert arquivos, f"pasta do domínio não encontrada em {DOMINIO}"

    violacoes = {
        str(arquivo.relative_to(PACOTE)): encontrados
        for arquivo in arquivos
        if (encontrados := _violacoes(arquivo.read_text(), _pacote_do_modulo(arquivo)))
    }

    assert violacoes == {}


def test_detector_reconhece_cada_forma_de_import() -> None:
    # Sem isto, um detector quebrado passaria vazio enquanto o domínio está vazio.
    pacote = ["etl", "dominio"]
    fonte = "\n".join(
        [
            "import httpx",
            "import sqlalchemy.engine",
            "from boto3 import client",
            "from psycopg.rows import dict_row",
            "from etl.adaptadores.camara import api_v2",
            "from ..adaptadores import persistencia",
            "from .. import adaptadores",
            "from . import periodos",
            "from etl.portas import FonteDaCasa",
            "import datetime",
        ]
    )

    assert _violacoes(fonte, pacote) == [
        "httpx",
        "sqlalchemy.engine",
        "boto3",
        "boto3.client",
        "psycopg.rows",
        "psycopg.rows.dict_row",
        "etl.adaptadores.camara",
        "etl.adaptadores.camara.api_v2",
        "etl.adaptadores",
        "etl.adaptadores.persistencia",
        "etl.adaptadores",
    ]
