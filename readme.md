
# ForexFactory News Scraper — Personal Trading Assistant

📰 **Scraper de noticias económicas FOMC / NFP / CPI** para complementar estrategia de trading PO3 (Post-Asian Session).

---

## 📚 Descripción

Este proyecto es un scraper personal que extrae, filtra y envía por **Telegram** las noticias de **alto impacto** (`High Impact Expected`) publicadas en el calendario de [ForexFactory](https://www.forexfactory.com/calendar), específicamente:

- Noticias de tipo **FOMC**, **NFP** y **CPI**.
- Solo noticias relacionadas con las monedas **USD** y **EUR**.
  
El objetivo es recibir diariamente un resumen claro y preciso de las noticias relevantes que **ya ocurrieron** durante el día, para evaluar su **impacto en el precio** y asi tener información previa a mi operacion, **después de la sesión asiática**, aplicando mi estrategia PO3.

El scraper corre automáticamente a las **00:00 UTC**, de **lunes a viernes**.

---

## ⚙️ Funcionalidades principales

- 🚀 Scraping de ForexFactory usando **Playwright** con simulación de actividad humana.
- ✅ Filtrado de noticias por impacto (**High**) y tipo (**FOMC**, **NFP**, **CPI**).
- 💬 Envío automático de resumen diario a Telegram.
- 🕛 Programado para ejecutarse **diariamente a las 00:00 UTC** (después del cierre operativo de noticias).
- 🔒 Manejo seguro de variables sensibles mediante **Secrets** o **.env**.
- 📂 Generación de un archivo `eventos_scrapeados.json` para debug o revisión manual.

---

## 📦 Tecnologías usadas

- [Python 3.11+](https://www.python.org/)
- [Playwright Python](https://playwright.dev/python/) (scraping dinámico con headless browser)
- [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/bs4/doc/) (parseo HTML)
- [Telegram Bot API](https://core.telegram.org/bots/api) (envío de mensajes)
- [GitHub Actions](https://docs.github.com/en/actions) (automatización de tareas)
- [dotenv](https://pypi.org/project/python-dotenv/) (manejo de variables de entorno)

---

## 🚀 ¿Cómo funciona?

### 1. Scraping

- Navega a [ForexFactory Calendar](https://www.forexfactory.com/calendar).
- Simula actividad humana (User-Agent random, movimientos de mouse, scroll) para evitar bloqueos.
- Extrae todos los eventos del día.
- Filtra noticias con:
  - Impacto: **High Impact Expected**.
  - Tipo: **FOMC**, **NFP**, **CPI**.
  - Moneda: **USD** o **EUR**.

### 2. Envío a Telegram

- Si hay eventos relevantes:
  - Envía un resumen al chat configurado, con fecha, hora, moneda y nombre del evento.
  - Ejemplo:
  
    ```
    📰 Noticias FOMC/NFP/CPI relevantes para EUR/USD de hoy:

    📅 Tue Jun 4 🕒 8:30am — USD — Non-Farm Employment Change (NFP)
    📅 Tue Jun 4 🕒 10:00am — USD — Core CPI (MoM)

    🔗 Ver más detalles en ForexFactory
    ⚡ Operá con precaución!
    ```
- Si no hay eventos:
  - Envía un mensaje indicando que no hubo noticias relevantes.

---


## 📝 Licencia

Uso **personal**. No autorizado para distribución comercial.

```
(c) 2025 - Uso personal para estrategia de trading PO3.
```

---

# ✅ ¡Listo para automatizar y operar más inteligentemente!
