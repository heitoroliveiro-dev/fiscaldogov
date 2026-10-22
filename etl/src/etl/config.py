"""Configuração do ETL lida do ambiente (contracts/ambientes-e-segredos.md).

Variável vazia vale como ausente. Todas as faltas são relatadas de uma vez, só
pelo nome: a mensagem nunca carrega valor, porque pode ir para o registro.
"""

from collections.abc import Mapping
from dataclasses import dataclass, field

CAMARA_API_URL_PADRAO = "https://dadosabertos.camara.leg.br/api/v2"
TEMPO_LIMITE_PADRAO_S = 3600

OBRIGATORIAS = (
    "DATABASE_URL_ESCRITA",
    "R2_ACCOUNT_ID",
    "R2_ACCESS_KEY_ID",
    "R2_SECRET_ACCESS_KEY",
    "R2_BUCKET_BRUTOS",
    "R2_BUCKET_BACKUP",
    "GITHUB_TOKEN_PUBLICACAO",
    "GITHUB_REPOSITORIO",
    "ALERTA_TELEGRAM_TOKEN",
    "ALERTA_TELEGRAM_CHAT_ID",
)


class ConfiguracaoInvalida(Exception):
    """Variável obrigatória ausente ou valor inválido: nada é executado (código 2)."""


@dataclass(frozen=True)
class Configuracao:
    # segredos fora do repr, para não vazarem num print ou numa mensagem de erro
    database_url_escrita: str = field(repr=False)
    r2_account_id: str
    r2_access_key_id: str = field(repr=False)
    r2_secret_access_key: str = field(repr=False)
    r2_bucket_brutos: str
    r2_bucket_backup: str
    github_token_publicacao: str = field(repr=False)
    github_repositorio: str
    alerta_telegram_token: str = field(repr=False)
    alerta_telegram_chat_id: str
    camara_api_url: str = CAMARA_API_URL_PADRAO
    tempo_limite_s: int = TEMPO_LIMITE_PADRAO_S


def _tempo_limite(valor: str) -> int:
    segundos = int(valor)  # ValueError se não for inteiro
    if segundos <= 0:
        raise ValueError(valor)
    return segundos


def carregar(ambiente: Mapping[str, str]) -> Configuracao:
    def ler(nome: str) -> str:
        return ambiente.get(nome, "").strip()

    problemas = [f"{nome} ausente" for nome in OBRIGATORIAS if not ler(nome)]

    tempo_limite = TEMPO_LIMITE_PADRAO_S
    if ler("ETL_TEMPO_LIMITE_S"):
        try:
            tempo_limite = _tempo_limite(ler("ETL_TEMPO_LIMITE_S"))
        except ValueError:
            problemas.append(
                "ETL_TEMPO_LIMITE_S precisa ser um número inteiro positivo de segundos"
            )

    if problemas:
        raise ConfiguracaoInvalida("configuração inválida: " + "; ".join(problemas))

    return Configuracao(
        **{nome.lower(): ler(nome) for nome in OBRIGATORIAS},
        camara_api_url=ler("CAMARA_API_URL") or CAMARA_API_URL_PADRAO,
        tempo_limite_s=tempo_limite,
    )
