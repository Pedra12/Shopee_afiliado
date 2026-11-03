from __future__ import annotations

import asyncio
import json
import os
import re
import sqlite3
import sys
from contextlib import asynccontextmanager
from decimal import Decimal, InvalidOperation
from pathlib import Path
from time import time

from dotenv import load_dotenv
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import FileResponse, JSONResponse
from starlette.routing import Route
from uvicorn import run as uvicorn_run

ROOT = Path(__file__).resolve().parent
VENDOR = ROOT / "vendor" / "shopee-br-affiliate-mcp"
sys.path.insert(0, str(VENDOR / "src"))

load_dotenv(ROOT / ".env")
if not os.getenv("SHOPEE_VERIFIED_PROFILE", "").strip():
    os.environ["SHOPEE_VERIFIED_PROFILE"] = str(VENDOR / "examples" / "profile.official.json")
if not os.getenv("SHOPEE_HISTORY_DB", "").strip():
    os.environ["SHOPEE_HISTORY_DB"] = str(ROOT / "data" / "affiliate_history.sqlite3")
_db_setting = os.getenv("SHOPEE_APP_DB", "").strip()
DB_PATH = Path(_db_setting).expanduser() if _db_setting else ROOT / "data" / "products.sqlite3"
TREND_CACHE = {"expires": 0.0, "items": []}


def database():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(DB_PATH)
    db.execute("""
        CREATE TABLE IF NOT EXISTS product_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id TEXT NOT NULL,
            shop_id TEXT NOT NULL,
            keyword TEXT NOT NULL,
            sales TEXT,
            period_start TEXT,
            period_end TEXT,
            observed_at TEXT NOT NULL,
            payload TEXT NOT NULL
        )
    """)
    db.execute("CREATE INDEX IF NOT EXISTS idx_snapshots_product ON product_snapshots(item_id, shop_id, id)")
    return db


def numeric(value):
    if value is None:
        return None
    try:
        number = Decimal(str(value))
        return number if number.is_finite() else None
    except (InvalidOperation, ValueError):
        return None


def record_and_score(offers, keyword):
    db = database()
    output = []
    try:
        for offer in offers:
            item_id, shop_id = str(offer["item_id"]), str(offer["shop_id"])
            period_start = str(offer.get("period_start_raw") or "")
            period_end = str(offer.get("period_end_raw") or "")
            previous = None
            if period_start and period_end:
                previous = db.execute(
                    """SELECT sales FROM product_snapshots
                       WHERE item_id=? AND shop_id=? AND period_start=? AND period_end=?
                       ORDER BY id DESC LIMIT 1""",
                    (item_id, shop_id, period_start, period_end),
                ).fetchone()
            sales = numeric(offer.get("sales"))
            previous_sales = numeric(previous[0]) if previous else None
            delta = (sales - previous_sales) if sales is not None and previous_sales is not None else None
            offer["sales_change_since_last_scan"] = str(delta) if delta is not None else None
            offer["trend_signal"] = (
                "rising" if delta is not None and delta > 0 else
                "falling" if delta is not None and delta < 0 else
                "stable" if delta == 0 else "collecting_history"
            )
            db.execute(
                """INSERT INTO product_snapshots
                   (item_id,shop_id,keyword,sales,period_start,period_end,observed_at,payload)
                   VALUES(?,?,?,?,?,?,?,?)""",
                (item_id, shop_id, keyword, str(sales) if sales is not None else None,
                 period_start, period_end, offer.get("observed_at", ""), json.dumps(offer, ensure_ascii=False)),
            )
            output.append(offer)
        db.commit()
    finally:
        db.close()
    return output


@asynccontextmanager
async def lifespan(app):
    from shopee_mcp.core import LiveProvider, load_service

    mode = os.getenv("SHOPEE_MODE", "").strip().lower()
    if not mode:
        mode = "live" if os.getenv("SHOPEE_APP_ID") and os.getenv("SHOPEE_APP_SECRET") else "fixture"
    if mode not in {"live", "fixture"}:
        raise RuntimeError("SHOPEE_MODE deve ser live ou fixture.")
    service = load_service(mode)
    app.state.service = service
    app.state.mode = mode
    yield
    if isinstance(service.provider, LiveProvider):
        await service.provider.client.close()


async def home(request: Request):
    template = Path(os.getenv("SHOPEE_TEMPLATE_PATH", str(ROOT / "templates" / "index.html")))
    return FileResponse(template)


async def status(request: Request):
    service = request.app.state.service
    try:
        result = await service.call("affiliate_status", {})
        if service.provider.mode == "live":
            probe = await service.call("search_offers", {
                "keyword": "celular", "sort_type": 2, "page": 1, "limit": 1
            })
            count = len(probe["data"]["offers"])
            return JSONResponse({
                **result, "api_tested": True, "api_authenticated": True,
                "probe_products": count,
                "message": "API autenticada e retornou produtos." if count else
                           "Autenticação aceita, mas a busca de teste não retornou ofertas."
            })
        return JSONResponse({**result, "api_tested": False,
                             "message": "Modo demonstração: os produtos são exemplos fictícios."})
    except Exception as exc:
        from shopee_mcp.core import SafeError
        if isinstance(exc, SafeError):
            return JSONResponse({"mode": service.provider.mode, "api_tested": True,
                                 "api_authenticated": False,
                                 "error": {"code": exc.code, "message": exc.message}}, status_code=502)
        return JSONResponse({"mode": service.provider.mode, "api_tested": True,
                             "api_authenticated": False,
                             "error": {"code": type(exc).__name__,
                                       "message": "Falha interna ao consultar a API. Nenhuma credencial foi exibida."}},
                            status_code=502)


async def search(request: Request):
    try:
        body = await request.json()
        keyword = str(body.get("keyword", "")).strip()
        if not keyword or len(keyword) > 120:
            return JSONResponse({"error": {"message": "Digite um termo de busca com até 120 caracteres."}}, status_code=400)
        sort_type = int(body.get("sort_type", 2))
        if sort_type not in {1, 2, 3, 4, 5}:
            sort_type = 2
        args = {"keyword": keyword, "sort_type": sort_type, "page": 1, "limit": 30}
        if body.get("category_id"):
            args["category_id"] = int(body["category_id"])
        result = await request.app.state.service.call("search_offers", args)
        offers = record_and_score(result["data"]["offers"], keyword)
        result["data"]["offers"] = offers
        return JSONResponse(result)
    except json.JSONDecodeError:
        return JSONResponse({"error": {"message": "Requisição inválida."}}, status_code=400)
    except Exception as exc:
        from shopee_mcp.core import SafeError
        if isinstance(exc, SafeError):
            return JSONResponse({"error": {"code": exc.code, "message": exc.message}}, status_code=400)
        return JSONResponse({"error": {"code": type(exc).__name__,
                                       "message": "Falha interna na busca. Nenhuma credencial foi exibida."}}, status_code=502)



async def discover(request: Request):
    # Broad but bounded search set. Each request uses the official affiliate API.
    keywords = ["casa", "beleza", "moda", "cozinha", "pet", "eletrônicos", "fitness", "acessórios"]
    service = request.app.state.service
    found = {}
    errors = []
    for keyword in keywords:
        try:
            result = await service.call("search_offers", {
                "keyword": keyword, "sort_type": 2, "page": 1, "limit": 30
            })
            for offer in result["data"]["offers"]:
                key = (str(offer["item_id"]), str(offer["shop_id"]))
                if key not in found:
                    offer["search_keyword"] = keyword
                    found[key] = offer
        except Exception as exc:
            from shopee_mcp.core import SafeError
            if isinstance(exc, SafeError):
                errors.append({"keyword": keyword, "code": exc.code, "message": exc.message})
            else:
                errors.append({"keyword": keyword, "message": "Consulta indisponível."})

    grouped = {}
    for offer in found.values():
        grouped.setdefault(offer["search_keyword"], []).append(offer)
    scored = []
    for keyword, offers in grouped.items():
        scored.extend(record_and_score(offers, keyword))
    def ranking(offer):
        sales = numeric(offer.get("sales"))
        commission = numeric(offer.get("commission_rate_fraction"))
        return (sales if sales is not None else Decimal("-1"),
                commission if commission is not None else Decimal("-1"))
    scored.sort(key=ranking, reverse=True)
    return JSONResponse({
        "mode": service.provider.mode,
        "synthetic": service.provider.mode == "fixture",
        "data": {
            "offers": scored[:50],
            "keywords_scanned": keywords,
            "unique_products": len(scored),
            "errors": errors,
            "observed_at": str(int(time()))
        }
    })


async def trends(request: Request):
    if os.getenv("GOOGLE_TRENDS_ENABLED", "true").lower() != "true":
        return JSONResponse({"source": "disabled", "trends": [], "message": "Google Trends desativado."})
    if TREND_CACHE["expires"] > time():
        return JSONResponse({"source": "Google Trends RSS", "cached": True, "trends": TREND_CACHE["items"]})
    try:
        from trendspyg import download_google_trends_rss
        envelope = await asyncio.to_thread(download_google_trends_rss, geo="BR", normalize=True)
        items = envelope.get("trends", []) if isinstance(envelope, dict) else []
        TREND_CACHE["items"] = [
            {"keyword": str(item.get("keyword", "")), "rank": item.get("rank"),
             "volume_min": item.get("volume_min"), "news": item.get("news", [])[:2]}
            for item in items if item.get("keyword")
        ]
        TREND_CACHE["expires"] = time() + 1800
        return JSONResponse({"source": "Google Trends RSS", "cached": False, "trends": TREND_CACHE["items"],
                             "notice": "Índice relativo/sinal externo; não representa vendas Shopee."})
    except Exception:
        return JSONResponse({"source": "Google Trends RSS", "trends": [],
                             "message": "Fonte temporariamente indisponível ou limitada. A busca Shopee continua disponível."}, status_code=200)


async def affiliate_link(request: Request):
    try:
        body = await request.json()
        url = str(body.get("product_url", "")).strip()
        if not url.startswith("https://shopee.com.br/") and not url.startswith("https://www.shopee.com.br/"):
            return JSONResponse({"error": {"message": "Use o link HTTPS original de um produto Shopee Brasil."}}, status_code=400)
        account = request.app.state.service.account
        sub_id = re.sub(r"[^A-Za-z0-9_-]", "_", str(body.get("sub_id", "painel")))[:64] or "painel"
        result = await request.app.state.service.call("generate_affiliate_link", {
            "origin_url": url, "sub_ids": [sub_id], "expected_account_reference": account
        })
        return JSONResponse(result)
    except Exception as exc:
        from shopee_mcp.core import SafeError
        if isinstance(exc, SafeError):
            return JSONResponse({"error": {"code": exc.code, "message": exc.message}}, status_code=400)
        return JSONResponse({"error": {"message": "Não foi possível gerar o link de afiliado."}}, status_code=502)


routes = [
    Route("/", home),
    Route("/api/status", status),
    Route("/api/search", search, methods=["POST"]),
    Route("/api/discover", discover, methods=["POST"]),
    Route("/api/trends", trends),
    Route("/api/link", affiliate_link, methods=["POST"]),
]
app = Starlette(debug=False, routes=routes, lifespan=lifespan)


if __name__ == "__main__":
    uvicorn_run(app, host="127.0.0.1", port=int(os.getenv("PORT", "5000")), log_level="warning")
