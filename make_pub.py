#!/usr/bin/env python3
"""Собирает ../pub: страницы со встроенными CSS/JS и ссылками вида x/index.html (для просмотра без сервера)."""
import os, re, shutil, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from data import MODELS
H = os.path.dirname(os.path.abspath(__file__)); D = H + "/../dist"; P = H + "/../pub"
shutil.rmtree(P, ignore_errors=True); shutil.copytree(D, P)
css = open(D + "/assets/style.css", encoding="utf8").read(); js = open(D + "/assets/app.js", encoding="utf8").read()
real = {m[0] for m in MODELS} | {"catalog"}
def h(m):
    u = m.group(1)
    if u.startswith(("http", "viber", "#", "mailto")) or u.endswith((".svg", ".jpg", ".css")) or not u.endswith("/"):
        return m.group(0)
    seg = [s for s in u.split("/") if s and s not in (".", "..")]
    if not seg: return f'href="{u}index.html"'
    return f'href="{u}index.html"' if seg[0] in real or seg[0].startswith("page-") else 'href="#"'
for r, _, fs in os.walk(P):
    for f in fs:
        if f != "index.html": continue
        p = os.path.join(r, f); t = open(p, encoding="utf8").read()
        t = re.sub(r'<link rel="stylesheet" href="(?:\.\./)+assets/style.css">', lambda m: "<style>" + css + "</style>", t)
        t = re.sub(r'<script src="(?:\.\./)+assets/app.js" defer></script>', lambda m: "<script>" + js + "</script>", t)
        t = re.sub(r'href="([^"]*)"', h, t)
        open(p, "w", encoding="utf8").write(t)
shutil.rmtree(P + "/assets")
links = "".join(f'<li><a href="{m[0]}/index.html">{m[1]}</a></li>' for m in MODELS)
open(P + "/index.html", "w", encoding="utf8").write(f'''<title>Кукла — макет сайта</title>
<style>:root{{--bg:#000;--tx:#fff;--mut:#b8a7a7;--red:#e8321e;--line:#6b5656}}
body{{background:var(--bg);color:var(--tx);font:17px/1.55 'Exo 2',system-ui,sans-serif;margin:0;padding-inline:max(16px,env(safe-area-inset-left,0px))}}
main{{max-width:760px;margin:0 auto;padding-block:48px}}h1{{font:800 clamp(30px,6vw,52px)/1.05 Tektur,'Exo 2',sans-serif;text-transform:uppercase;margin:0 0 12px}}
p{{color:var(--mut)}}.row{{display:flex;flex-wrap:wrap;gap:12px;margin:24px 0}}
a.b{{padding:13px 26px;border-radius:10px;background:var(--red);color:#fff;text-decoration:none}}
h2{{font:800 22px Tektur,'Exo 2',sans-serif;text-transform:uppercase;margin:32px 0 12px}}ul{{display:flex;flex-wrap:wrap;gap:10px;padding:0;list-style:none}}
li a{{display:block;padding:8px 18px;border:1.5px solid var(--line);border-radius:999px;color:var(--tx);text-decoration:none}}li a:hover{{border-color:#fff}}</style>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Tektur:wght@800&family=Exo+2:wght@400;500&display=swap">
<main><h1>Кукла: каталог и анкета</h1>
<p>Две страницы по ТЗ в стиле действующего сайта. Модели и фото вымышленные, заглушки. Форма звонка пока ничего не отправляет.</p>
<div class="row"><a class="b" href="catalog/index.html">Каталог моделей</a><a class="b" href="anzhela/index.html">Страница анкеты</a></div>
<h2>Все анкеты</h2><ul>{links}</ul></main>''')
print("pub ok")
