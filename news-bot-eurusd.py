from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import re
import json
import time
import random
import requests
import os
from dotenv import load_dotenv
from pathlib import Path
from datetime import datetime, timedelta, timezone
import pytz



USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
]



# === INTENTA CARGAR VARIABLES DESDE UN ARCHIVO .ENV ESTANDO EN LOCAL ===
try:
    from dotenv import load_dotenv
    if Path(".env").exists():
        load_dotenv()
        print("[INFO] dotenv cargado (modo local)", flush=True)
    else:
        print("[INFO] No se encontró archivo .env, se usan variables de entorno del sistema", flush=True)
except Exception as e:
    print(f"[INFO] dotenv no disponible: {e}", flush=True)


# === FUNCION SEGURA PARA OBTENER VARIABLES OBLIGATORIAS ===
def get_env_var(name):
    value = os.getenv(name)
    if value is None:
        print(f"[ERROR] La variable de entorno '{name}' no está definida.", flush=True)
        raise ValueError(f"La variable de entorno '{name}' no está definida.")
    return value


# === CONFIGURACION: VARIABLES DE ENTORNO Y SIMBOLO ===
try:
    print("[INFO] Cargando las variables de entorno", flush=True)
    TELEGRAM_TOKEN = get_env_var("TELEGRAM_TOKEN")
    raw_chat_ids = get_env_var("TELEGRAM_CHAT_IDS")
    # print("[DEBUG] raw_chat_ids repr:", repr(raw_chat_ids), flush=True)
    TELEGRAM_CHAT_IDS = [chat_id.strip() for chat_id in raw_chat_ids.split(",")]
except Exception as e:
    print(f"[ERROR] Fallo al cargar variables: {e}", flush=True)
    exit(1)


# === ENVIO DE MENSAJES DE TELEGRAM ===
def send_telegram_message(message):
    print(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] [TELEGRAM] Enviando mensaje: {message}", flush=True)
    for chat_id in TELEGRAM_CHAT_IDS:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'Markdown'
        }
        try:
            response = requests.post(url, data=payload, timeout=10)
            print(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] [TELEGRAM] Mensaje enviado a {chat_id} (estado: {response.status_code})", flush=True)
        except Exception as e:
            print(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] [ERROR] No se pudo enviar mensaje a {chat_id}: {e}", flush=True)

# === SCRAPER ===
def scrape_forex_factory():
    user_agent = random.choice(USER_AGENTS)

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage"
            ]
        )

        page = browser.new_page(
            user_agent=user_agent,
            viewport={"width": 1280, "height": 800}
        )

        page.goto("https://www.forexfactory.com/calendar", timeout=60000)

        # Simular movimiento de mouse y scroll con tiempos random
        page.mouse.move(100, 100)
        time.sleep(random.uniform(0.5, 1.5))
        for x in range(100, 600, 100):
            page.mouse.move(x, 150)
            time.sleep(random.uniform(0.5, 1.5))
        page.mouse.wheel(0, 500)
        time.sleep(random.uniform(1.0, 2.0))

        html = page.content()
        browser.close()

        soup = BeautifulSoup(html, "html.parser")
        all_rows = soup.find_all("tr")

        et = pytz.timezone("America/New_York")
        bsas = pytz.timezone("America/Argentina/Buenos_Aires")
        today_bsas = datetime.now(bsas).date()

        current_date = ""
        events = []

        for row in all_rows:
            classes = row.get("class", [])
            if "calendar__row" not in classes:
                continue

            date_td = row.find("td", class_="calendar__date")
            if date_td:
                current_date = date_td.get_text(separator=" ", strip=True)

            try:
                time_ = row.find("td", class_="calendar__time").text.strip() if row.find("td", class_="calendar__time") else ""
                currency = row.find("td", class_="calendar__currency").text.strip() if row.find("td", class_="calendar__currency") else ""
                event = row.find("td", class_="calendar__event").text.strip() if row.find("td", class_="calendar__event") else ""

                # Impacto
                impact_element = row.find("td", class_="calendar__impact")
                impact_span = impact_element.find("span") if impact_element else None
                impact_title = impact_span.get("title", "").lower() if impact_span else ""

                if "high impact" in impact_title:
                    impact = "High"
                elif "medium impact" in impact_title:
                    impact = "Medium"
                elif "low impact" in impact_title:
                    impact = "Low"
                else:
                    impact = ""

                if impact != "High" or not re.search(r"(FOMC|NFP|CPI)", event, re.IGNORECASE):
                    continue

                if time_ in ["All Day", "Tentative", ""]:
                    continue

                event_dt_str = f"{current_date} {time_}"
                event_dt_naive = datetime.strptime(event_dt_str, "%a %b %d %I:%M%p")
                event_dt_et = et.localize(event_dt_naive.replace(year=datetime.now(timezone.utc).year))
                event_dt_bsas = event_dt_et.astimezone(bsas)

                if event_dt_bsas.date() != today_bsas:
                    continue

                hora_bsas = event_dt_bsas.strftime("%H:%M")

                events.append({
                    "date": current_date,
                    "time": time_,
                    "currency": currency,
                    "event": event,
                    "impact": impact,
                    "hora_bsas": hora_bsas
                })

            except Exception as e:
                print(f"[WARN] Error procesando fila: {e}", flush=True)
                continue

        with open("eventos_scrapeados.json", "w", encoding="utf-8") as f:
            json.dump(events, f, indent=4, ensure_ascii=False)

        return events


def main():
    start_time = time.time()

    events = scrape_forex_factory()

    # Filtrar solo USD o EUR
    relevant_events = [e for e in events if e["currency"] in ["USD", "EUR"]]
    print(f"[INFO] {len(relevant_events)} eventos relevantes encontrados.", flush=True)

    if relevant_events:
        message = f"📰 *Noticias FOMC/NFP/CPI relevantes para EUR/USD de hoy:*\n\n"
        for event in relevant_events:
            message += f"📅 *{event['date']}* 🕒 *{event['hora_bsas']} hs (hora Buenos Aires)* — `{event['currency']}` — {event['event']}\n"
        message += "\n🔗 [Ver más detalles en ForexFactory](https://www.forexfactory.com/calendar)\n"
        message += "\n⚡ *Operá con precaución!*"
    else:
        message = "✅ *Hoy no hay noticias FOMC/NFP/CPI relevantes para EUR/USD.*"

    send_telegram_message(message)
    print(message, flush=True)

    end_time = time.time()  # 🚀 Medir tiempo al terminar
    elapsed_time = end_time - start_time

    # Hora exacta en UTC
    finish_time_utc = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
    
    print(f"[INFO] Scraping completado en {elapsed_time:.2f} segundos.", flush=True)
    print(f"[INFO] Scraping finalizado a {finish_time_utc} UTC.", flush=True)


# === EJECUCION ===
# Ejecutar siempre, sin depender de __name__ (ideal para Render)
print(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] [INFO] Iniciando el scraper", flush=True)
main()