"""Configuração do ETL (contracts/ambientes-e-segredos.md e contracts/etl-cli.md).

Variável obrigatória ausente ou vazia impede a execução: ConfiguracaoInvalida
nomeia cada variável faltante, e o comando sai com código 2 sem executar nada.
"""

import os
import subprocess
import sys

import pytest

from etl.config import ConfiguracaoInvalida, carregar

OBRIGATORIAS = {
    "DATABASE_URL_ESCRITA": "postgresql://etl_escrita:segredo-banco@db:5432/railway",
    "R2_ACCOUNT_ID": "conta-r2",
    "R2_ACCESS_KEY_ID": "chave-r2",
    "R2_SECRET_ACCESS_KEY": "segredo-r2",
    "R2_BUCKET_BRUTOS": "fiscaldogov-brutos",
    "R2_BUCKET_BACKUP": "fiscaldogov-backup",
    "GITHUB_TOKEN_PUBLICACAO": "segredo-github",
    "GITHUB_REPOSITORIO": "heitoroliveiro-dev/fiscaldogov",
    "ALERTA_TELEGRAM_TOKEN": "segredo-telegram",
    "ALERTA_TELEGRAM_CHAT_ID": "123",
}

SEGREDOS = [valor for valor in OBRIGATORIAS.values() if "segredo" in valor]


def test_carrega_com_padroes_do_contrato() -> None:
    config = carregar(OBRIGATORIAS)

    assert config.database_url_escrita == OBRIGATORIAS["DATABASE_URL_ESCRITA"]
    assert config.camara_api_url == "https://dadosabertos.camara.leg.br/api/v2"
    assert config.tempo_limite_s == 3600


def test_aceita_padroes_sobrescritos() -> None:
    config = carregar(
        {**OBRIGATORIAS, "CAMARA_API_URL": "http://localhost:8000", "ETL_TEMPO_LIMITE_S": "2"}
    )

    assert config.camara_api_url == "http://localhost:8000"
    assert config.tempo_limite_s == 2


@pytest.mark.parametrize("ausente", sorted(OBRIGATORIAS))
@pytest.mark.parametrize("como", ["removida", "vazia"])
def test_obrigatoria_ausente_ou_vazia_nomeia_a_variavel(ausente: str, como: str) -> None:
    ambiente = {nome: valor for nome, valor in OBRIGATORIAS.items() if nome != ausente}
    if como == "vazia":
        ambiente[ausente] = ""

    with pytest.raises(ConfiguracaoInvalida) as erro:
        carregar(ambiente)

    mensagem = str(erro.value)
    assert ausente in mensagem
    assert not [segredo for segredo in SEGREDOS if segredo in mensagem]


def test_nomeia_todas_as_ausentes_de_uma_vez() -> None:
    with pytest.raises(ConfiguracaoInvalida) as erro:
        carregar({})

    assert [nome for nome in OBRIGATORIAS if nome not in str(erro.value)] == []


@pytest.mark.parametrize("valor", ["abc", "0", "-5", "1.5"])
def test_tempo_limite_precisa_ser_inteiro_positivo(valor: str) -> None:
    with pytest.raises(ConfiguracaoInvalida, match="ETL_TEMPO_LIMITE_S"):
        carregar({**OBRIGATORIAS, "ETL_TEMPO_LIMITE_S": valor})


def test_comando_sai_com_codigo_2_sem_configuracao() -> None:
    resultado = subprocess.run(  # noqa: S603 — executa o próprio pacote, sem entrada externa
        [sys.executable, "-m", "etl", "coletar"],
        env={"PATH": os.environ.get("PATH", "")},
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )

    assert resultado.returncode == 2, resultado.stderr
    assert "DATABASE_URL_ESCRITA" in resultado.stdout + resultado.stderr
