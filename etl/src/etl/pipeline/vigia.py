"""Vigia de tempo da coleta (FR-013a, research §5).

`signal.alarm` interrompe a execução depois do tempo limite (padrão 3600 s).
TempoEsgotado herda de BaseException de propósito: nenhum `except Exception`
pelo caminho (ex.: a guarda dos brutos) pode engolir a interrupção. A transação
aberta é desfeita pelo próprio `with engine.begin()`, que faz ROLLBACK com
qualquer exceção. Uma chamada bloqueada na libpq não é interrompida pelo
sinal; para essa, vale o statement_timeout da sessão (banco.py).

Só funciona na thread principal, que é onde a CLI roda.
"""

import signal
from collections.abc import Iterator
from contextlib import contextmanager
from types import FrameType


class TempoEsgotado(BaseException):
    def __init__(self, segundos: int) -> None:
        super().__init__(f"tempo esgotado ({segundos} s)")


@contextmanager
def limite_de_tempo(segundos: int) -> Iterator[None]:
    def estourar(_sinal: int, _quadro: FrameType | None) -> None:
        raise TempoEsgotado(segundos)

    anterior = signal.signal(signal.SIGALRM, estourar)
    signal.alarm(segundos)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, anterior)
