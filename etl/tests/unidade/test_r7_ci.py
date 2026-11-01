"""Quickstart R7, passo 4: teste que falha de propósito só no CI.

Passa no pre-commit (sem CI=true) para não exigir --no-verify, e fica vermelho
no GitHub Actions, provando que a proteção de branch impede o merge. Este
arquivo vive só na branch chore/r7-pr-com-teste-falhando e nunca é mesclado.
"""

import os


def test_r7_falha_de_proposito_no_ci() -> None:
    assert os.environ.get("CI") != "true", "R7: falha de propósito para provar o bloqueio do merge"
