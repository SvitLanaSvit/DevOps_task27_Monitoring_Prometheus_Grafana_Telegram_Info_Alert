import os
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException, Request

app = FastAPI(title="alertmanager-telegram-webhook")


def _require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def _chunk(text: str, size: int = 3800) -> list[str]:
    # Telegram limit is 4096; keep margin for safety.
    chunks: list[str] = []
    for i in range(0, len(text), size):
        chunks.append(text[i : i + size])
    return chunks or [""]


def _format_alertmanager_payload(payload: dict[str, Any]) -> str:
    status = payload.get("status", "unknown")
    alerts = payload.get("alerts", []) or []

    lines: list[str] = [f"Alertmanager: {status}", ""]

    for alert in alerts:
        labels = alert.get("labels", {}) or {}
        annotations = alert.get("annotations", {}) or {}

        name = labels.get("alertname", "(no alertname)")
        instance = labels.get("instance", "")
        job = labels.get("job", "")
        severity = labels.get("severity", "")

        summary = annotations.get("summary", "")
        description = annotations.get("description", "")

        lines.append(f"• {name} [{severity}]".rstrip())
        meta = " ".join([p for p in [f"job={job}" if job else "", f"instance={instance}" if instance else ""] if p])
        if meta:
            lines.append(f"  {meta}")
        if summary:
            lines.append(f"  summary: {summary}")
        if description:
            lines.append(f"  desc: {description}")
        lines.append("")

    text = "\n".join(lines).strip()
    return text


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/alertmanager")
async def alertmanager_webhook(req: Request) -> dict[str, str]:
    try:
        token = _require_env("TELEGRAM_BOT_TOKEN")
        chat_id = _require_env("TELEGRAM_CHAT_ID")
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))

    payload = await req.json()
    text = _format_alertmanager_payload(payload)

    url = f"https://api.telegram.org/bot{token}/sendMessage"

    async with httpx.AsyncClient(timeout=10) as client:
        for part in _chunk(text):
            resp = await client.post(
                url,
                json={
                    "chat_id": chat_id,
                    "text": part,
                    "disable_web_page_preview": True,
                },
            )
            if resp.status_code >= 400:
                raise HTTPException(status_code=502, detail=f"Telegram API error: {resp.status_code} {resp.text}")

    return {"status": "sent"}
