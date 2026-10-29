"""Registro de operação: uma linha JSON por evento em stdout, sem segredos (FR-030).

Mascara o valor de todo campo cujo nome indica segredo e a senha de toda URL de
conexão, na mensagem, nos campos (inclusive aninhados) e no texto do erro. O
manipulador fica na raiz, para que avisos de bibliotecas passem pelo mesmo filtro.
"""

import json
import logging
import re
import sys
from datetime import UTC, datetime
from typing import Any, TextIO

MASCARA = "***"
_NOMES_DE_SEGREDO = ("TOKEN", "SECRET", "PASSWORD", "DATABASE_URL")
# esquema://usuario:senha@ — a senha vai até o @, sem atravessar espaço nem barra
# (em URL de conexão ela vem codificada; com barra, é porta seguida de caminho)
_SENHA_EM_URL = re.compile(r"(?P<inicio>\b[a-z][a-z0-9+.-]*://[^\s:/@]*:)[^\s@/]+(?=@)", re.I)
_ATRIBUTOS_DO_LOGGING = {*vars(logging.makeLogRecord({})), "message", "asctime"}


def _mascarar(valor: Any, nome: str = "") -> Any:
    if any(segredo in nome.upper() for segredo in _NOMES_DE_SEGREDO):
        return MASCARA
    if isinstance(valor, str):
        return _SENHA_EM_URL.sub(rf"\g<inicio>{MASCARA}", valor)
    if isinstance(valor, dict):
        return {chave: _mascarar(item, str(chave)) for chave, item in valor.items()}
    if isinstance(valor, list | tuple):
        return [_mascarar(item) for item in valor]
    return valor


def mascarar(valor: Any) -> Any:
    """Mesmo mascaramento do registro, para texto que vai a outro destino (ex.: o banco)."""
    return _mascarar(valor)


class _FormatoJson(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        campos = {
            chave: valor
            for chave, valor in vars(record).items()
            if chave not in _ATRIBUTOS_DO_LOGGING
        }
        linha = {
            **campos,
            "momento": datetime.fromtimestamp(record.created, UTC).isoformat(),
            "nivel": record.levelname,
            "logger": record.name,
            "mensagem": record.getMessage(),
        }
        if record.exc_info:
            linha["erro"] = self.formatException(record.exc_info)
        return json.dumps(_mascarar(linha), ensure_ascii=False, default=str)


class _Manipulador(logging.StreamHandler):
    def __init__(self, saida: TextIO) -> None:
        super().__init__(saida)
        self.setFormatter(_FormatoJson())


def configurar(saida: TextIO | None = None) -> None:
    """Instala o registro; chamar de novo troca a saída sem duplicar linhas."""
    raiz = logging.getLogger()
    for manipulador in [m for m in raiz.handlers if isinstance(m, _Manipulador)]:
        raiz.removeHandler(manipulador)
    raiz.addHandler(_Manipulador(saida or sys.stdout))
    # bibliotecas só a partir de aviso; o ETL registra as etapas em INFO
    raiz.setLevel(logging.WARNING)
    logging.getLogger("etl").setLevel(logging.INFO)
