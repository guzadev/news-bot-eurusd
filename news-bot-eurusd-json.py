# news.py — Prealertas 30' antes (EUR/USD) + "no hay noticias" (digest) usando el feed semanal
# --------------------------------------------------------------------------------------------
# - Lee el JSON semanal (sin scraping).
# - Prealerta: si 'ahora' ∈ [evento-30', evento-30'+window], envía Telegram (alto impacto, USD/EUR, HOY BA).
# - Digest "no hay noticias": si HOY no hay USD/EUR de alto impacto, envía 1 vez a una hora exacta BA (p. ej. 03:00).
# - Diseñado para cron cada 5'. Usar window≈330s (5' + margen) para cubrir jitter.
# --------------------------------------------------------------------------------------------

import os, sys, json, html, requests
from pathlib import Path
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
from dotenv import load_dotenv

# ---------- Config base ----------
FEED_URL = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"
TZ_BA = ZoneInfo("America/Argentina/Buenos_Aires")

# Diccionarios para fecha en español (encabezado)
DIAS_ES = {
    "Monday":"Lunes","Tuesday":"Martes","Wednesday":"Miércoles","Thursday":"Jueves",
    "Friday":"Viernes","Saturday":"Sábado","Sunday":"Domingo"
}
MESES_ES = {
    "January":"Enero","February":"Febrero","March":"Marzo","April":"Abril","May":"Mayo","June":"Junio",
    "July":"Julio","August":"Agosto","September":"Septiembre","October":"Octubre","November":"Noviembre","December":"Diciembre"
}

# Emoji por moneda (lo que pediste: 💵 USD / 💶 EUR)
CURRENCY_EMOJI = {"USD":"💵", "EUR":"💶"}

def encabezado_hoy_ba() -> str:
    """Devuelve 'Viernes 27 de Junio' según la fecha actual en BA."""
    hoy = datetime.now(TZ_BA)
    dia = DIAS_ES.get(hoy.strftime("%A"), hoy.strftime("%A"))
    mes = MESES_ES.get(hoy.strftime("%B"), hoy.strftime("%B"))
    return f"{dia} {hoy.day} de {mes}"

# ---------- .env / credenciales ----------
if Path(".env").exists():
    load_dotenv()

def env(name: str) -> str:
    v = os.getenv(name)
    if not v:
        raise ValueError(f"Falta env {name}")
    return v

TELEGRAM_TOKEN = env("TELEGRAM_TOKEN")
TELEGRAM_CHAT_IDS = [x.strip() for x in env("TELEGRAM_CHAT_IDS").split(",") if x.strip()]

# ---------- Envío a Telegram ----------
def send_telegram_html(message: str) -> None:
    """Envía un mensaje HTML (parse_mode=HTML) a todos los chat IDs."""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    for chat_id in TELEGRAM_CHAT_IDS:
        try:
            requests.post(
                url,
                data={
                    "chat_id": chat_id,
                    "text": message,
                    "parse_mode": "HTML",
                    "disable_web_page_preview": True,
                },
                timeout=10,
            )
        except Exception as e:
            print(f"[WARN] Telegram a {chat_id}: {e}", flush=True)

# ---------- Lectura del feed ----------
def fetch_week():
    """Descarga y devuelve el JSON semanal."""
    r = requests.get(FEED_URL, timeout=20)
    r.raise_for_status()
    return r.json()

# ---------- Helpers de normalización ----------
def is_high_impact(evt) -> bool:
    """Detecta 'alto impacto' (acepta string 'High' o escala numérica >=3)."""
    imp = evt.get("impact")
    if isinstance(imp, str):
        return "high" in imp.lower()
    if isinstance(imp, (int, float)):
        return imp >= 3
    imp2 = evt.get("impactDescription") or evt.get("impact_label")
    return isinstance(imp2, str) and "high" in imp2.lower()

def get_currency(evt) -> str:
    """Obtiene la moneda (USD/EUR). Se normaliza a MAYÚSCULAS."""
    return (evt.get("currency") or evt.get("country") or evt.get("cur") or "").upper().strip()

def get_title(evt) -> str:
    """Obtiene el título del evento."""
    return (evt.get("title") or evt.get("event") or evt.get("name") or "").strip()

def get_ts_utc(evt):
    """
    Devuelve epoch (segundos) en UTC.
    Soporta:
      - timestamp en s o ms (key 'timestamp')
      - ISO-8601 en key 'date' (p. ej. '2025-10-27T05:00:00-04:00')
      - fallback: date+time separados (raro en este feed)
    """
    ts = evt.get("timestamp")
    if isinstance(ts, (int, float)):
        if ts > 1e12:  # ms -> s
            ts = ts / 1000.0
        return int(ts)

    d = evt.get("date")
    if isinstance(d, str) and d:
        try:
            dt = datetime.fromisoformat(d)           # respeta el offset del string (ej. -04:00)
            dt_utc = dt.astimezone(timezone.utc)
            return int(dt_utc.timestamp())
        except Exception:
            pass

    ds, ts_ = evt.get("date"), evt.get("time")
    if ds and ts_:
        for fmt in ("%Y-%m-%d %H:%M", "%d-%m-%Y %H:%M", "%Y/%m/%d %H:%M"):
            try:
                dt_naive = datetime.strptime(f"{ds} {ts_}", fmt)
                return int(dt_naive.replace(tzinfo=timezone.utc).timestamp())
            except Exception:
                continue
    return None


# ---------- Carga de eventos de HOY (reutilizable) ----------
def load_events_today_ba_eur_usd_high():
    """
    Devuelve lista de eventos de HOY (BA) para USD/EUR con impacto ALTO.
    Cada item: {timestamp_utc:int, dt_ba:datetime, currency:str, title:str}
    """
    data = fetch_week()
    events = data if isinstance(data, list) else (data.get("events") or data.get("calendar") or [])
    today_ba = datetime.now(TZ_BA).date()
    out = []
    for evt in events:
        try:
            if not is_high_impact(evt):
                continue
            cur = get_currency(evt)
            if cur not in {"USD", "EUR"}:
                continue
            ts = get_ts_utc(evt)
            if not ts:
                continue
            dt_evt_utc = datetime.fromtimestamp(ts, tz=timezone.utc)
            dt_evt_ba = dt_evt_utc.astimezone(TZ_BA)
            if dt_evt_ba.date() != today_ba:
                continue
            out.append({
                "timestamp_utc": int(ts),
                "dt_ba": dt_evt_ba,
                "currency": cur,
                "title": get_title(evt),
            })
        except Exception as e:
            print(f"[WARN] Evento omitido: {e}", flush=True)
    out.sort(key=lambda x: x["timestamp_utc"])
    return out

# ---------- Lógica principal: PREALERTAS ----------
def run_prealerts(lead_minutes=30, window_seconds=330) -> None:
    """
    Ejecutar con cron (p. ej., cada 5 minutos).
    Dispara si 'ahora' ∈ [evento-30', evento-30' + window].
    Con cron de 5', usar window ≈ 330 s para cubrir jitter y evitar duplicados.
    """
    now_utc = datetime.now(timezone.utc)
    events = load_events_today_ba_eur_usd_high()

    for ev in events:
        dt_evt_utc = datetime.fromtimestamp(ev["timestamp_utc"], tz=timezone.utc)
        prealert_utc = dt_evt_utc - timedelta(minutes=lead_minutes)

        # Ventana de disparo (stateless)
        if not (prealert_utc <= now_utc < prealert_utc + timedelta(seconds=window_seconds)):
            continue

        # Armado del mensaje con tu formato
        title = html.escape(ev["title"])
        cur_s = html.escape(ev["currency"])            # moneda escapada para HTML
        hora_ba = ev["dt_ba"].strftime("%H:%M")        # HH:MM en BA
        emoji = CURRENCY_EMOJI.get(ev["currency"], "")
        fecha_es = encabezado_hoy_ba()

        msg = (
            f"📰 <b>Noticias de alto impacto para {cur_s} de hoy 👇🏻</b>\n\n"
            f"📅 <b>{fecha_es}:</b>\n\n"
            f"⏳ <b>En {lead_minutes} minutos:</b>\n"
            f"• ⏰ <b>{hora_ba} h</b>\n"
            f"• {emoji} <code>{cur_s}</code>\n"
            f"• 🗂️ <b>{title}</b>\n\n"
            f"📍 Hora Buenos Aires\n"
            f'🔗 <a href="https://www.forexfactory.com/calendar">Ver más detalles en ForexFactory</a>\n\n'
            f"⚡️ <b>¡Operá con precaución!</b>"
        )
        send_telegram_html(msg)

# ---------- Digest "no hay noticias" 1 vez al día ----------
def send_no_news_digest_if_applicable(digest_at_hhmm_ba: str = "03:00") -> None:
    """
    Envía un mensaje 'Hoy no hay noticias de alto impacto para EUR/USD' **una sola vez al día**,
    chequeando una **hora exacta BA** (por defecto 03:00).
    - No usa archivos/caché para evitar duplicados, se basa en que cron corre cada 5' y
      sólo coincide una vez con el minuto exacto.
    """
    now_ba = datetime.now(TZ_BA)
    # Mandar sólo días hábiles (lun–vie)
    if now_ba.weekday() >= 5:
        return

    # Enviar sólo a la hora exacta solicitada (ej: "03:00")
    if now_ba.strftime("%H:%M") != digest_at_hhmm_ba:
        return

    events = load_events_today_ba_eur_usd_high()
    if events:
        # Hay noticias: no enviamos el digest de "no hay".
        return

    # Construir y enviar digest "no hay noticias"
    fecha_es = encabezado_hoy_ba()
    msg = (
        f"📅 <b>{html.escape(fecha_es)}:</b>\n\n"
        f"✅ <b>Hoy no hay noticias de alto impacto para las monedas EUR y USD</b> 👍🏻\n\n"
        f"📈 Operá con tranquilidad 👌🏻"
    )
    send_telegram_html(msg)

# ---------- (Opcional) Guard por franja horaria ----------
def dentro_de_franja_ba() -> bool:
    """
    Limita corridas a ventanas probables (lun–vie):
    EUR 03:30–07:30, USD 09:00–13:00, Fed 15:00–16:00 (BA).
    Útil si usás un cron amplio; si cron ya acota bien, podés dejarlo desactivado.
    """
    now = datetime.now(TZ_BA)
    if now.weekday() >= 5:  # 0=lun ... 6=dom
        return False
    hhmm = now.hour * 100 + now.minute
    eur = 300 <= hhmm <= 730     # cubre prealertas que arrancan 30' antes
    usd = 830 <= hhmm <= 1230
    fed = 1430 <= hhmm <= 1530
    return eur or usd or fed


# === EJECUCION ===

# 1) Digest "no hay noticias" (una vez al día a la hora exacta BA)
digest_hhmm = os.getenv("DIGEST_AT_BA", "03:00")  # podés setear "07:00" si preferís más tarde
send_no_news_digest_if_applicable(digest_at_hhmm_ba=digest_hhmm)

# 2) Prealertas (lead=30', window=330s por defecto; override con env vars)
lead = int(os.getenv("LEAD_MINUTES", "30"))
window = int(os.getenv("WINDOW_SECONDS", "330"))
run_prealerts(lead_minutes=lead, window_seconds=window)
