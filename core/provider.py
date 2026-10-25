"""Official Toolbox adapter. No direct legacy MOTU/FTP endpoints."""
import time
from .catalogue import PRODUCT, DATASETS, select_variables

class ProviderError(Exception):
    def __init__(self, code):
        self.code = code
        super().__init__(code)

def classify(exc):
    # Messages are examined locally for status classification, never exported.
    context = getattr(exc, "__context__", None) or getattr(exc, "__cause__", None)
    response = getattr(exc, "response", None) or getattr(context, "response", None)
    status = getattr(response, "status_code", None)
    name = type(exc).__name__.lower()
    if status in (400, 401, 403):
        return "AUTH"
    if any(v in name for v in ("credential", "unauthorized", "invalidusernameorpassword")):
        return "AUTH"
    if "couldnotconnecttoauthentication" in name:
        return "NETWORK"
    if any(v in name for v in ("datasetnotfound", "datasetversionnotfound", "variablenotfound", "variablesnotfound")):
        return "SCHEMA"
    if status in (408, 429, 500, 502, 503, 504) or any(v in name for v in ("timeout", "connection", "serverdisconnected")):
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
