"""Seleção do deputado exibido na F2 (FR-006, research §4).

Regra objetiva, sem escolha pessoal (princípio II): o primeiro, entre os em
exercício, pelo nome parlamentar em minúsculas e sem acento. A normalização usa
unicodedata, independente do locale da máquina.
"""

import unicodedata
from collections.abc import Sequence
from typing import Protocol


class _ComNome(Protocol):
    @property
    def nome_parlamentar(self) -> str: ...


def normalizar_nome(nome: str) -> str:
    decomposto = unicodedata.normalize("NFKD", nome)
    return "".join(c for c in decomposto if not unicodedata.combining(c)).lower()


def selecionar_deputado[T: _ComNome](deputados: Sequence[T]) -> T:
    """Empate no nome normalizado fica com o primeiro na ordem recebida."""
    if not deputados:
        raise ValueError("nenhum deputado em exercício para selecionar")
    return min(deputados, key=lambda deputado: normalizar_nome(deputado.nome_parlamentar))
