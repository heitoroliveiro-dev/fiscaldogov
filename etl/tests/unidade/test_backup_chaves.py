"""Chaves da cópia de segurança no R2 (T077, FR-024, research §6).

Todo dia: `diario/AAAA-MM-DD.dump`. Aos domingos, também `semanal/AAAA-MM-DD.dump`.
A data é a de Brasília: a retenção (7 dias no diário, 28 no semanal) é feita
por regra de ciclo de vida do R2 sobre esses prefixos, sem código de limpeza.
"""

from datetime import UTC, datetime

import pytest

from etl.adaptadores.backup_r2.backup import chaves_do_backup


@pytest.mark.parametrize(
    ("agora", "chaves"),
    [
        # segunda-feira, 03:00 em Brasília
        (datetime(2026, 11, 2, 6, 0, tzinfo=UTC), ["diario/2026-11-02.dump"]),
        # domingo, 03:00 em Brasília
        (
            datetime(2026, 11, 1, 6, 0, tzinfo=UTC),
            ["diario/2026-11-01.dump", "semanal/2026-11-01.dump"],
        ),
        # segunda 01:00 UTC ainda é domingo 22:00 em Brasília
        (
            datetime(2026, 11, 2, 1, 0, tzinfo=UTC),
            ["diario/2026-11-01.dump", "semanal/2026-11-01.dump"],
        ),
        # domingo 02:30 UTC ainda é sábado 23:30 em Brasília
        (datetime(2026, 11, 8, 2, 30, tzinfo=UTC), ["diario/2026-11-07.dump"]),
    ],
    ids=["segunda", "domingo", "domingo-a-noite-em-utc-segunda", "sabado-a-noite"],
)
def test_chaves_por_dia_de_brasilia(agora: datetime, chaves: list[str]) -> None:
    assert chaves_do_backup(agora) == chaves


def test_horario_sem_fuso_e_recusado() -> None:
    with pytest.raises(ValueError, match="fuso"):
        chaves_do_backup(datetime(2026, 11, 2, 6, 0))
