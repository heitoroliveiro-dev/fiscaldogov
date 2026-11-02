"""Alerta de falha da publicação (scripts/alerta-publicacao.sh, T073, FR-029, FR-020a).

O script roda no passo `if: failure()` do publicar.yml e lê os logs do build e do
deploy para nomear a credencial recusada. Sem ALERTA_TELEGRAM_TOKEN ele só
imprime a mensagem: é assim que o teste o exercita, sem rede.
"""

import os
import shutil
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parents[3] / "scripts" / "alerta-publicacao.sh"
BASH = shutil.which("bash") or "/bin/bash"
LINK = "https://github.com/heitoroliveiro-dev/fiscaldogov/actions/runs/1"


def _alerta(pasta: Path, *, build: str = "", deploy: str = "", execucao: str = "42") -> str:
    (pasta / "build.log").write_text(build, encoding="utf-8")
    (pasta / "deploy.log").write_text(deploy, encoding="utf-8")
    ambiente = {
        "PATH": os.environ["PATH"],
        "EXECUCAO_ID": execucao,
        "LINK_DA_EXECUCAO": LINK,
    }
    # script do próprio repositório, sem entrada externa
    resultado = subprocess.run(  # noqa: S603
        [BASH, str(SCRIPT), str(pasta)],
        env=ambiente,
        capture_output=True,
        text=True,
        check=True,
    )
    return resultado.stdout


def test_senha_do_banco_recusada_nomeia_database_url_leitura(tmp_path: Path) -> None:
    texto = _alerta(tmp_path, build='Error: password authentication failed for user "site_leitura"')

    assert texto.splitlines() == [
        "fiscaldogov: publicação com falha",
        "execução 42",
        "- falha de autenticação: DATABASE_URL_LEITURA (papel site_leitura)",
        LINK,
    ]


@pytest.mark.parametrize(
    "log",
    ["Authentication error [code: 10000]", "Invalid API Token", "status code 401"],
)
def test_token_da_cloudflare_recusado_nomeia_cloudflare_api_token(tmp_path: Path, log: str) -> None:
    texto = _alerta(tmp_path, deploy=f"✘ [ERROR] A request to the Cloudflare API failed.\n{log}")

    assert "- falha de autenticação: CLOUDFLARE_API_TOKEN" in texto


def test_falha_comum_sem_execucao_so_tem_titulo_e_link(tmp_path: Path) -> None:
    texto = _alerta(tmp_path, build="Type error: x", execucao="")

    assert texto.splitlines() == ["fiscaldogov: publicação com falha", LINK]


def test_sem_logs_o_alerta_sai_mesmo_assim(tmp_path: Path) -> None:
    # falha antes do build (ex.: npm ci): não há log, mas o alerta não pode depender dele
    ambiente = {"PATH": os.environ["PATH"], "EXECUCAO_ID": "7", "LINK_DA_EXECUCAO": LINK}
    resultado = subprocess.run(  # noqa: S603
        [BASH, str(SCRIPT), str(tmp_path)],
        env=ambiente,
        capture_output=True,
        text=True,
        check=False,
    )

    assert resultado.returncode == 0
    assert resultado.stdout.splitlines() == [
        "fiscaldogov: publicação com falha",
        "execução 7",
        LINK,
    ]
