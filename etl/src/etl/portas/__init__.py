"""Portas: o que o pipeline espera de cada adaptador (ADR-0003, typing.Protocol).

O pipeline depende destas interfaces, não das implementações; os erros das
fontes e os estados de uma execução também moram aqui, para que o pipeline os
trate sem conhecer a Câmara nem o banco.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any, Protocol

from etl.dominio.entidades import DadosDoParlamentar, Historico, IdentificadorExterno, Parlamentar


class FonteIncompleta(Exception):
    """A fonte respondeu, mas com menos do que o mínimo plausível: nada é gravado (FR-007b)."""


class RespostaInvalida(Exception):
    """JSON inválido, ou campo usado ausente ou de tipo inesperado: falha fechada."""


class CredencialInvalida(Exception):
    """Um serviço recusou a credencial (401/403): o alerta aponta a causa (FR-020a)."""

    def __init__(self, credencial: str, detalhe: str) -> None:
        super().__init__(f"{credencial} recusado ({detalhe})")
        self.credencial = credencial


class ColetaEmAndamento(Exception):
    """Já há uma coleta em andamento há menos de 60 min: esta não começa (código 3)."""


class StatusExecucao(StrEnum):
    EM_ANDAMENTO = "em_andamento"
    SUCESSO = "sucesso"
    COM_PENDENCIAS = "com_pendencias"
    FALHA = "falha"
    DISPENSADA = "dispensada"


class Gatilho(StrEnum):
    AGENDADA = "agendada"
    RESERVA = "reserva"
    MANUAL = "manual"


class FonteDaCasa(Protocol):
    def listar_em_exercicio(self) -> list[Parlamentar]: ...

    def historico(self, parlamentar: IdentificadorExterno) -> Historico: ...


class RepositorioDeDados(Protocol):
    def parlamentares_armazenados(self) -> list[IdentificadorExterno]: ...

    def gravar(self, todos: Sequence[DadosDoParlamentar]) -> dict[str, int]:
        """Grava tudo numa única transação e devolve as contagens (FR-012)."""
        ...


class ArmazemDeBrutos(Protocol):
    def guardar(self, execucao_id: int, url: str, conteudo: Any) -> bool: ...


@dataclass(frozen=True)
class Abertura:
    execucao_id: int
    # em_andamento com mais de 60 min fechadas agora como falha "interrompida"
    interrompidas: tuple[int, ...]


class RegistroDeExecucoes(Protocol):
    def iniciar(self, gatilho: Gatilho, versao_codigo: str) -> int: ...

    def abrir(self, gatilho: Gatilho, versao_codigo: str) -> Abertura:
        """Fecha as travadas e inicia; ColetaEmAndamento se houver uma recente (FR-013a)."""
        ...

    def houve_bem_sucedida_desde(self, momento: datetime) -> bool: ...

    def registrar_dispensada(self, versao_codigo: str) -> int: ...

    def finalizar(
        self,
        execucao_id: int,
        status: StatusExecucao,
        *,
        contagens: dict[str, Any] | None = None,
        tentativas: list[Any] | None = None,
        erros: list[Any] | None = None,
        pendencias: list[Any] | None = None,
    ) -> None: ...


class Backup(Protocol):
    def copiar(self) -> list[str]:
        """pg_dump enviado e conferido no destino; devolve as chaves (FR-024)."""
        ...


class Publicador(Protocol):
    def disparar(self, execucao_id: int) -> None: ...


class Alertador(Protocol):
    def alertar(self, texto: str) -> None:
        """Envia ao canal do responsável (FR-029). Não levanta: falha só vai para o log."""
        ...
