"""Probe MPSC adv_notification page with Playwright."""

import asyncio
from pathlib import Path

from playwright.async_api import async_playwright

OUT = Path(__file__).resolve().parent / "_probe_out"
OUT.mkdir(exist_ok=True)

URLS = [
    "https://mpsc.gov.in/adv_notification/8",
    "https://mpsc.gov.in/recruitmentNotification/1",
]


async def dump(url: str) -> None:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url, wait_until="networkidle", timeout=90000)
        await page.wait_for_timeout(3000)
        html = await page.content()
        name = url.rstrip("/").split("/")[-2] + "_" + url.rstrip("/").split("/")[-1]
        path = OUT / f"mpsc_{name}.html"
        path.write_text(html, encoding="utf-8", errors="replace")
        # Extract text sample of tables/links
        info = await page.evaluate(
            """() => {
              const tables = document.querySelectorAll('table').length;
              const rows = document.querySelectorAll('table tr').length;
              const links = [...document.querySelectorAll('a')].slice(0, 30).map(a => ({
                t: (a.innerText || '').trim().slice(0, 120),
                h: a.getAttribute('href')
              })).filter(x => x.t.length > 5);
              const bodyText = document.body.innerText.slice(0, 1500);
              return {tables, rows, links, bodyText};
            }"""
        )
        (OUT / f"mpsc_{name}_meta.txt").write_text(
            f"url={url}\ntables={info['tables']} rows={info['rows']}\n"
            f"body=\n{info['bodyText']}\n\nlinks=\n"
            + "\n".join(f"{x['t']} | {x['h']}" for x in info["links"]),
            encoding="utf-8",
            errors="replace",
        )
        print(f"{url}: tables={info['tables']} rows={info['rows']} links={len(info['links'])} html={len(html)}")
        await browser.close()


async def main() -> None:
    for url in URLS:
        await dump(url)


if __name__ == "__main__":
    asyncio.run(main())
