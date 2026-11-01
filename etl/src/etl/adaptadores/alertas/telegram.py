"""Alertas pela API de bots do Telegram (FR-029, research §10, RNF07).

`sendMessage` com uma nova tentativa. Falha no envio só vai para o log e nunca
levanta: o resultado da execução não depende do alerta. O token faz parte da
URL da API, então o log leva só o tipo do erro e o código HTTP, nunca a URL nem
a mensagem do httpx.
"""

import logging
import time
from collections.abc import Callable

import httpx

URL_BASE = "https://api.telegram.org"
TEMPO_LIMITE_S = 15
ESPERA_ANTES_DA_NOVA_TENTATIVA_S = 5

log = logging.getLogger("etl.alertas")


def criar_cliente_telegram(transporte: httpx.BaseTransport | None = None) -> httpx.Client:
    return httpx.Client(base_url=URL_BASE, timeout=TEMPO_LIMITE_S, transport=transporte)


class AlertadorTelegram:
    def __init__(
        self,
        cliente: httpx.Client,
        token: str,
        chat_id: str,
        *,
        esperar: Callable[[float], None] = time.sleep,
    ) -> None:
        self._cliente = cliente
        self._token = token
        self._chat_id = chat_id
        self._esperar = esperar

    def alertar(self, texto: str) -> None:
        for tentativa in (1, 2):
            try:
                resposta = self._cliente.post(
                    f"/bot{self._token}/sendMessage",
                    json={"chat_id": self._chat_id, "text": texto},
                )
                resposta.raise_for_status()
            except httpx.HTTPError as erro:
                codigo = (
                    erro.response.status_code if isinstance(erro, httpx.HTTPStatusError) else None
                )
                if tentativa == 1:
                    self._esperar(ESPERA_ANTES_DA_NOVA_TENTATIVA_S)
                    continue
                log.error(
                    "alerta não enviado",
                    extra={"erro": type(erro).__name__, "http": codigo},
                )
            else:
                log.info("alerta enviado")
            return
