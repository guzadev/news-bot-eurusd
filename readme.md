# ForexFactory News Alerts — Personal Trading Assistant

📰 **Alertas de noticias económicas de alto impacto (EUR/USD) desde el feed oficial**

---

## 📚 Descripción

Este proyecto Toma el **feed JSON semanal** de [ForexFactory / Faireconomy](https://www.forexfactory.com/calendar) y envía por **Telegram**:

- **Prealertas 30 minutos antes** de cada noticia de **alto impacto** (`High`) para **USD** y **EUR**.
- (Opcional) Un **mensaje único** al inicio del día si **no hay** noticias de alto impacto (EUR/USD).

Pensado para correrse con **cron** (Render/Railway) solo en **franjas horarias útiles** para reducir consumo.

---

## ⚙️ Funcionalidades principales

- 🔗 Lectura del **JSON semanal oficial**: `https://nfs.faireconomy.media/ff_calendar_thisweek.json`.
- ✅ Filtro por **impacto alto** y **monedas USD/EUR**.
- ⏳ **Prealerta** automática **30’ antes** de cada evento (hora **Buenos Aires**).
- 📅 (Opcional) **“Hoy no hay noticias”**: un mensaje único por la mañana si aplica.
- 💬 Envío por **Telegram** (parseo en HTML, seguro).
- 🧪 Diseñado para correr con **cron cada 5 min** y ventana de tolerancia configurable.

---

## 📦 Tecnologías usadas

- [Python 3.12+](https://www.python.org/)
- [Requests](https://pypi.org/project/requests/) (HTTP)
- [tzdata](https://pypi.org/project/tzdata/) + `zoneinfo` (zonas horarias IANA, BA)
- [python-dotenv](https://pypi.org/project/python-dotenv/) (variables de entorno)
- [Telegram Bot API](https://core.telegram.org/bots/api)

---

## 🚀 ¿Cómo funciona?

1) **Carga del feed semanal** (stateless).  
2) Filtra eventos de **hoy (BA)** con **impacto alto** y **monedas EUR/USD**.  
3) En cada ejecución (cron), si la hora actual cae en la ventana **[evento − 30’, evento − 30’ + `WINDOW_SECONDS`]**, **envía la alerta** a Telegram y termina.  
4) (Opcional) A una hora fija BA (por defecto **03:00**), si **no hay** eventos de alto impacto para hoy, envía el mensaje **“Hoy no hay noticias”** **una sola vez**.

### Ejemplo de prealerta (Telegram)

```
📰 Noticias de alto impacto para USD de hoy 👇🏻

📅 Viernes 27 de Junio:

⏳ En 30 minutos:
• ⏰ 09:00 h
• 💵 USD
• 🗂️ Core PCE Price Index m/m

📍 Hora Buenos Aires
🔗 Ver más detalles en ForexFactory

⚡️ Operá con precaución!
```

---

## 🔧 Configuración

### Variables de entorno

- `TELEGRAM_TOKEN` — Token del bot de Telegram.  
- `TELEGRAM_CHAT_IDS` — IDs separados por coma (p. ej. `12345,67890`).

**Opcionales:**

- `LEAD_MINUTES` — Minutos de antelación (default `30`).  
- `WINDOW_SECONDS` — Ventana de tolerancia (default `330` si corrés cron cada 5’).  
- `DIGEST_AT_BA` — Hora BA para el mensaje “no hay noticias” (default `03:00`).

### Requisitos

```
requests
python-dotenv
tzdata
```

---

## ⏱️ Despliegue con Cron (Render/Railway)

Usá **cron cada 5 minutos** en **UTC**. Tres franjas recomendadas (prealertas):

- **EUR** (prealertas 06:00–10:00 UTC):
  ```
  */5 6-10 * * 1-5
  ```

- **USD** (prealertas 11:30–15:30 UTC):
  ```
  */5 11-15 * * 1-5
  ```
  *(Es una franja amplia: el script solo envía cuando corresponde.)*

- **Fed (opcional)** (prealertas 17:30–18:30 UTC):
  ```
  */5 17-18 * * 1-5
  ```

**Comando sugerido:**
```
python -u news.py --prealert --lead 30 --window 330
```

> El script es **stateless**: cada corrida dura segundos; no necesita base de datos ni storage.

---

## 🧩 Estructura del código (resumen)

- `run_prealerts()` — Núcleo que envía las prealertas 30’ antes.  
- `send_no_news_digest_if_applicable()` — Envía **una única vez** el “✅ Hoy no hay noticias…” si aplica (a `DIGEST_AT_BA`, por defecto 03:00 BA).  
- *Helpers* para leer el JSON, normalizar impacto/moneda/horarios y formatear el mensaje.

---

## 📝 Licencia

Uso **personal**. No autorizado para distribución comercial.

```
(c) 2025 - Uso personal.
```

---

# ✅ ¡Listo para operar con alertas puntuales y sin scraping!
