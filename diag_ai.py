# Network diagnosis for the AI Parts chat panel (plan 0.2a). Prints no key values; makes no model call
# (GET /v1/models only lists models and costs no tokens).
#   python diag_ai.py
import os
import socket
import ssl
import sys
import traceback

print("python", sys.version.split()[0], sys.executable)
for k in ("ANTHROPIC_API_KEY", "DEEPSEEK_API_KEY"):
    v = os.environ.get(k)
    note = ""
    if v:
        note = f"(length {len(v)}" + (", STILL THE PLACEHOLDER sk-ant-..." if "..." in v else "") \
            + (", has spaces or quotes" if v != v.strip().strip('"') else "") + ")"
    print(k, "set" if v else "NOT set", note)
for k in ("HTTPS_PROXY", "HTTP_PROXY", "ALL_PROXY", "NO_PROXY", "SSL_CERT_FILE", "REQUESTS_CA_BUNDLE",
          "ANTHROPIC_BASE_URL", "FAP_AI_PROVIDER", "FAP_AI_REGION"):
    for name in (k, k.lower()):
        if os.environ.get(name):
            print("env", name, "=", os.environ[name] if "KEY" not in name else "(set)")
print("ssl default cafile:", ssl.get_default_verify_paths().cafile, "| openssl", ssl.OPENSSL_VERSION)
try:
    import certifi
    print("certifi:", certifi.where(), os.path.exists(certifi.where()))
except Exception as e:  # noqa: BLE001
    print("certifi missing:", e)

host = "api.anthropic.com"
try:
    print("dns", host, sorted({a[4][0] for a in socket.getaddrinfo(host, 443)}))
    with socket.create_connection((host, 443), timeout=10) as s:
        print("tcp 443 ok")
        ctx = ssl.create_default_context()
        try:
            import certifi
            ctx.load_verify_locations(certifi.where())
        except Exception:  # noqa: BLE001
            pass
        with ctx.wrap_socket(s, server_hostname=host) as t:
            print("tls ok", t.version(), "issuer", dict(x[0] for x in t.getpeercert()["issuer"]).get("organizationName"))
except Exception:
    print("LOW-LEVEL FAILURE:")
    traceback.print_exc()

try:
    import httpx

    r = httpx.get(f"https://{host}/v1/models", timeout=20,
                  headers={"x-api-key": os.environ.get("ANTHROPIC_API_KEY", ""), "anthropic-version": "2023-06-01"})
    print("httpx GET /v1/models ->", r.status_code, r.text[:200].replace("\n", " "))
except Exception:
    print("HTTPX FAILURE:")
    traceback.print_exc()
