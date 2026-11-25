import json
import re
import sys
from datetime import datetime, timezone

from playwright.sync_api import sync_playwright

URL = "https://eltoque.com/tasas-de-cambio-de-moneda-en-cuba/hoy"
SALIDA = "tasa_usd.json"


def extraer_usd(texto: str):
    # Busca "USD" seguido de un número (ej: "USD 660" o "USD\n660 CUP")
    for m in re.finditer(r"USD[^\d]{0,40}(\d{2,4}(?:[.,]\d{1,2})?)", texto):
        valor = float(m.group(1).replace(",", "."))
        if 100 <= valor <= 5000:  # filtro de sensatez
            return valor
    return None


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
            ),
            locale="es-ES",
        )
        page = context.new_page()
        respuesta = page.goto(URL, wait_until="networkidle", timeout=60000)
        page.wait_for_timeout(5000)
        texto = page.inner_text("body")
        valor = extraer_usd(texto)

        if valor is None:
            print("Código HTTP:", respuesta.status if respuesta else "sin respuesta")
            print("URL final:", page.url)
            print("Título:", page.title())
            print("Largo del texto:", len(texto))
            print("--- PRIMEROS 1500 CARACTERES ---")
            print(texto[:1500])
            page.screenshot(path="debug.png", full_page=True)
            with open("debug.txt", "w", encoding="utf-8") as f:
                f.write(texto)
            browser.close()
            print("No se encontró la tasa USD", file=sys.stderr)
            sys.exit(1)

        browser.close()

    datos = {
        "usd_cup": valor,
        "actualizado_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "fuente": URL,
    }
    with open(SALIDA, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)
    print(f"USD = {valor} CUP")


if __name__ == "__main__":
    main()
