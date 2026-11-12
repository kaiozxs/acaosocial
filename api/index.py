import json

from config.wsgi import app as _django


def app(environ, start_response):
    # diagnóstico temporário: mostra por onde a Vercel entrega o pedido (sem dados secretos)
    if "__diag=1" in environ.get("QUERY_STRING", ""):
        chaves = ("PATH_INFO", "SCRIPT_NAME", "REQUEST_URI", "RAW_URI", "QUERY_STRING", "REQUEST_METHOD", "SERVER_NAME")
        d = {k: str(environ.get(k)) for k in chaves}
        d["headers"] = {k: str(v)[:120] for k, v in environ.items() if k.startswith("HTTP_X_") or k in ("HTTP_HOST",)}
        corpo = json.dumps(d, indent=1).encode()
        start_response("200 OK", [("Content-Type", "application/json"), ("Content-Length", str(len(corpo)))])
        return [corpo]
    return _django(environ, start_response)
