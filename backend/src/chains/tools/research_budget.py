
from threading import Lock
from urllib.parse import urlsplit, urlunsplit


class ResearchBudget:
    """Controla os limites de pesquisa de uma execução da Pesquisadora."""

    def __init__(
        self,
        max_buscas_por_dia: int = 2,
        max_leituras_por_dia: int = 2,
    ):
        self.max_buscas_por_dia = max_buscas_por_dia
        self.max_leituras_por_dia = max_leituras_por_dia

        self._buscas_por_dia: dict[int, int] = {}
        self._leituras_por_dia: dict[int, int] = {}

        self._consultas_realizadas: set[str] = set()
        self._urls_tentadas: set[str] = set()

        self._lock = Lock()

    @staticmethod
    def _normalizar_consulta(query: str) -> str:
        return " ".join(query.casefold().split())

    @staticmethod
    def _normalizar_url(url: str) -> str:
        partes = urlsplit(url.strip())

        esquema = partes.scheme.lower()
        hostname = (partes.hostname or "").lower()

        if not esquema or not hostname:
            return url.strip()

        porta = partes.port

        if porta and not (
            (esquema == "https" and porta == 443)
            or (esquema == "http" and porta == 80)
        ):
            hostname = f"{hostname}:{porta}"

        caminho = partes.path.rstrip("/") or "/"

        return urlunsplit(
            (
                esquema,
                hostname,
                caminho,
                partes.query,
                "",
            )
        )

    def reservar_busca(
        self,
        dia: int,
        query: str,
    ) -> tuple[bool, str]:

        consulta = self._normalizar_consulta(query)

        with self._lock:
            if consulta in self._consultas_realizadas:
                return False, "Esta consulta já foi realizada nesta execução."

            quantidade = self._buscas_por_dia.get(dia, 0)

            if quantidade >= self.max_buscas_por_dia:
                return False, (
                    f"Limite de {self.max_buscas_por_dia} buscas "
                    f"atingido no dia {dia}."
                )

            self._consultas_realizadas.add(consulta)
            self._buscas_por_dia[dia] = quantidade + 1

            return True, "Busca autorizada."

    def reservar_leitura(
        self,
        dia: int,
        url: str,
    ) -> tuple[bool, str]:

        endereco = self._normalizar_url(url)

        with self._lock:
            if endereco in self._urls_tentadas:
                return False, "Esta URL já foi consultada nesta execução."

            quantidade = self._leituras_por_dia.get(dia, 0)

            if quantidade >= self.max_leituras_por_dia:
                return False, (
                    f"Limite de {self.max_leituras_por_dia} leituras "
                    f"atingido no dia {dia}."
                )

            self._urls_tentadas.add(endereco)
            self._leituras_por_dia[dia] = quantidade + 1

            return True, "Leitura autorizada."

    def resumo(self) -> dict:
        with self._lock:
            return {
                "buscas_por_dia": dict(self._buscas_por_dia),
                "leituras_por_dia": dict(self._leituras_por_dia),
                "total_buscas": sum(self._buscas_por_dia.values()),
                "total_leituras": sum(self._leituras_por_dia.values()),
                "urls_tentadas": len(self._urls_tentadas),
            }
