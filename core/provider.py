"""Official Toolbox adapter. No direct legacy MOTU/FTP endpoints."""
import time
from .catalogue import PRODUCT, DATASETS, select_variables

class ProviderError(Exception):
    def __init__(self, code):
        self.code = code
        super().__init__(code)

def classify(exc):
    # Messages are examined locally for status classification, never exported.
    chain = []
    current = exc
    while current and len(chain) < 10 and current not in chain:
        chain.append(current)
        current = getattr(current, "__context__", None) or getattr(current, "__cause__", None)

    statuses = [getattr(getattr(e, "response", None), "status_code", None) for e in chain]
    names = [type(e).__name__.lower() for e in chain]
    messages = [str(e).lower() for e in chain]

    if any(s in (400, 401, 403) for s in statuses):
        return "AUTH"
    if any(any(v in name for v in ("credential", "unauthorized", "invalidusernameorpassword")) for name in names):
        return "AUTH"
    if any("couldnotconnecttoauthentication" in name for name in names):
        return "NETWORK"
    if any(any(v in name for v in ("datasetnotfound", "datasetversionnotfound", "variablenotfound", "variablesnotfound")) for name in names):
        return "SCHEMA"

    network_name_indicators = (
        "timeout", "connection", "serverdisconnected", "gaierror", "maxretry",
        "network", "connecterror", "readtimeout", "poolerror", "urlerror",
        "httperror", "serviceunavailable", "socket", "sslerror"
    )
    network_msg_indicators = (
        "connection", "timeout", "timed out", "getaddrinfo", "name resolution",
        "unreachable", "disconnected", "offline", "reset by peer",
        "refused", "no internet", "failed to establish a new connection",
        "dns", "network is down", "no route to host"
    )

    if any(s in (408, 429, 500, 502, 503, 504) for s in statuses):
        return "NETWORK"
    if any(any(k in name for k in network_name_indicators) for name in names):
        return "NETWORK"
    if any(any(k in msg for k in network_msg_indicators) for msg in messages):
        return "NETWORK"
    for e in chain:
        if isinstance(e, (ConnectionError, TimeoutError)):
            return "NETWORK"
        if isinstance(e, OSError) and getattr(e, "errno", None) in (11001, 10051, 10053, 10054, 10060, 10061, 10065):
            return "NETWORK"
    return "FAILED"

def retry(operation, emit, key=None, attempts=3, sleep=time.sleep):
    for attempt in range(1, attempts + 1):
        try:
            return operation()
        except ProviderError:
            raise
        except Exception as exc:
            code = classify(exc)
            if code != "NETWORK" or attempt == attempts:
                raise ProviderError(code) from None
            emit("retry", dataset=key, attempt=attempt)
            sleep(min(2 ** attempt, 8))

class MarineProvider:
    def __init__(self, username, password, emit, api=None):
        if not username or not password:
            raise ProviderError("AUTH")
        if api is None:
            import copernicusmarine as api
        self.api = api
        self.auth = dict(username=username, password=password)
        self.emit = emit
        self.variables = {}

    def validate(self):
        self.emit("auth", 3)
        ok = retry(lambda: self.api.login(**self.auth, check_credentials_valid=True), self.emit)
        if not ok:
            raise ProviderError("AUTH")
        self.emit("authenticated", 6)

    def describe(self, key):
        self.emit("catalogue", dataset=key)
        result = retry(lambda: self.api.describe(dataset_id=DATASETS[key][1],
                       disable_progress_bar=True, raise_on_error=True), self.emit, key)
        raw = result.model_dump(mode="json") if hasattr(result, "model_dump") else result
        if not isinstance(raw, dict):
            raise ProviderError("SCHEMA")
        products = raw.get("products", [])
        found = any(p.get("product_id") == PRODUCT and any(
            d.get("dataset_id") == DATASETS[key][1] for d in p.get("datasets", [])) for p in products)
        if not found:
            raise ProviderError("SCHEMA")
        dataset = next(d for p in products if p.get("product_id") == PRODUCT
                       for d in p.get("datasets", []) if d.get("dataset_id") == DATASETS[key][1])
        services = [s for v in dataset.get("versions", []) for part in v.get("parts", [])
                    for s in part.get("services", []) if s.get("service_short_name") == "static-arco"]
        if not services:
            raise ProviderError("SCHEMA")
        try:
            self.variables[key] = select_variables([v["short_name"] for v in services[0].get("variables", [])])
        except (ValueError, KeyError):
            raise ProviderError("SCHEMA") from None
        return raw

    def subset(self, key, bounds, directory):
        if key not in self.variables:
            raise ProviderError("SCHEMA")
        return retry(lambda: self.api.subset(dataset_id=DATASETS[key][1],
            variables=self.variables[key], **bounds.subset_arguments(), **self.auth,
            coordinates_selection_method="inside", output_directory=str(directory),
            output_filename="source.nc", file_format="netcdf", overwrite=True,
            disable_progress_bar=True, netcdf_compression_level=4), self.emit, key)
