"""Starts the Shopee dashboard inside the Android app process."""
import os, threading, time

def start_server(app_id, app_secret, account_reference, app_files, template_file):
    os.environ["SHOPEE_APP_ID"] = app_id or ""
    os.environ["SHOPEE_APP_SECRET"] = app_secret or ""
    os.environ["SHOPEE_ACCOUNT_REFERENCE"] = account_reference or ""
    os.environ["SHOPEE_MODE"] = "live" if app_id and app_secret else "fixture"
    os.environ["SHOPEE_APP_DB"] = os.path.join(app_files, "products.sqlite3")
    os.environ["SHOPEE_HISTORY_DB"] = os.path.join(app_files, "affiliate_history.sqlite3")
    os.environ["SHOPEE_VERIFIED_PROFILE"] = os.path.join(app_files, "profile.official.json")
    os.environ["SHOPEE_TEMPLATE_PATH"] = template_file
    import uvicorn
    import app as dashboard
    server = uvicorn.Server(uvicorn.Config(dashboard.app, host="127.0.0.1", port=5000, log_level="error", access_log=False))
    threading.Thread(target=server.run, name="ShopeeLocalApi", daemon=True).start()
    for _ in range(100):
        if server.started: return True
        time.sleep(0.1)
    raise RuntimeError("O serviço local não iniciou dentro do tempo esperado.")
