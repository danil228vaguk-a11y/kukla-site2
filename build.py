#!/usr/bin/env python3
"""Генератор статичных страниц: каталог (с пагинацией) и анкеты моделей.
Запуск: python3 build.py  ->  ../dist/
"""
import html, json, math, os, shutil, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from data import SITE, CATEGORIES, SERVICES, MODELS, DESC

HERE = os.path.dirname(os.path.abspath(__file__))
DIST = os.path.join(HERE, "..", "dist")
E = html.escape
CAT = dict(CATEGORIES)
NOINDEX = '<meta name="robots" content="noindex,nofollow">' if SITE.get("noindex", True) else ""
WM_TEXT = SITE["name"]
WM_SITE = SITE["domain"].split("//")[-1]

M = [dict(slug=m[0], name=m[1], age=m[2], bust=m[3][0], waist=m[3][1], hips=m[3][2],
          height=m[4], weight=m[5], price=m[6], cats=m[7], hue=m[8],
          size=max(1, int((m[3][0] - 76) / 4))) for m in MODELS]
BY = {m["slug"]: m for m in M}


def money(v):
    return f"{v:,}".replace(",", " ") + " ₽"


# ---------- заглушки фото (SVG) ----------
def placeholder(m, n):
    sh = 0.9 + (m["hue"] % 7) / 40  # небольшая вариативность силуэта
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 800">
<defs><radialGradient id="g" cx=".5" cy=".55" r=".6"><stop offset="0" stop-color="#3a0b08"/><stop offset="1" stop-color="#000"/></radialGradient>
<linearGradient id="d" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#e8321e" stop-opacity=".55"/><stop offset=".35" stop-color="#1b1b1d"/><stop offset="1" stop-color="#0b0b0c"/></linearGradient></defs>
<rect width="600" height="800" fill="url(#g)"/>
<g transform="translate(300 24) scale({sh:.2f}) translate(-300 0)">
<path d="M262 120c-10 70-8 150 6 205M338 120c10 70 8 150-6 205" stroke="#1d1213" stroke-width="20" fill="none" stroke-linecap="round"/>
<ellipse cx="300" cy="122" rx="34" ry="44" fill="#2a1a1c"/>
<rect x="288" y="160" width="24" height="40" fill="#2a1a1c"/>
<path d="M236 214c20-10 44-14 64-14s44 4 64 14l-10 26c-14 40-12 86-6 124-8 40-8 72 0 100 30 120 70 240 110 340H78c40-100 80-220 110-340 8-28 8-60 0-100 6-38 8-84-6-124z" fill="url(#d)"/>
<path d="M236 214c26 22 68 22 128 0" stroke="#e8321e" stroke-opacity=".55" stroke-width="2" fill="none"/></g>
<text x="300" y="770" text-anchor="middle" font-family="Arial,sans-serif" font-size="20" fill="#fff" opacity=".45">{E(m["name"])} · фото {n}</text>
<defs><pattern id="wm" width="260" height="190" patternUnits="userSpaceOnUse" patternTransform="rotate(-28)">
<text x="0" y="60" font-family="Georgia,serif" font-size="34" font-weight="700" fill="#fff" fill-opacity=".14">{WM_TEXT}</text>
<text x="130" y="155" font-family="Georgia,serif" font-size="34" font-weight="700" fill="#fff" fill-opacity=".14">{WM_TEXT}</text></pattern></defs>
<rect width="600" height="800" fill="url(#wm)"/>
<text x="580" y="740" text-anchor="end" font-family="Arial,sans-serif" font-size="22" font-weight="700" fill="#fff" fill-opacity=".7" stroke="#000" stroke-opacity=".35" stroke-width=".8">{WM_SITE}</text></svg>'''
    return svg


def has_real(m, n):
    return os.path.exists(os.path.join(HERE, "photos", f"{m['slug']}-{n}.jpg"))


def photo_url(m, n, depth):
    ext = "jpg" if has_real(m, n) else "svg"
    return "../" * depth + f"img/{m['slug']}-{n}.{ext}"


def watermark_jpg(src, dst):
    """Накладывает диагональный полупрозрачный знак и подпись домена. Нужен Pillow."""
    from PIL import Image, ImageDraw, ImageFont
    im = Image.open(src).convert("RGBA")
    w, h = im.size
    fs = max(18, w // 16)
    try:
        font = ImageFont.truetype("DejaVuSerif-Bold.ttf", fs)
        fsm = ImageFont.truetype("DejaVuSans-Bold.ttf", max(14, w // 28))
    except OSError:
        font = fsm = ImageFont.load_default()
    d = max(w, h) * 2
    lay = Image.new("RGBA", (d, d), (0, 0, 0, 0)); dr = ImageDraw.Draw(lay)
    stepx, stepy = int(fs * 5.2), int(fs * 3.4)
    for row, y in enumerate(range(0, d, stepy)):
        for x in range(-stepx, d, stepx):
            dr.text((x + (stepx // 2 if row % 2 else 0), y), WM_TEXT, font=font, fill=(255, 255, 255, 46))
    lay = lay.rotate(28, resample=Image.BICUBIC)
    l, t = (d - w) // 2, (d - h) // 2
    im.alpha_composite(lay.crop((l, t, l + w, t + h)))
    dd = ImageDraw.Draw(im)
    tw = dd.textlength(WM_SITE, font=fsm)
    dd.text((w - tw - w * .03, h - fsm.size * 1.8), WM_SITE, font=fsm, fill=(255, 255, 255, 190), stroke_width=1, stroke_fill=(0, 0, 0, 90))
    im.convert("RGB").save(dst, "JPEG", quality=86, optimize=True)


# ---------- общие куски ----------
def tags_html(items, base, depth, limit, all_label, ident):
    pre = "../" * depth
    out = ['<div class="tags" data-tags>']
    for i, (slug, label) in enumerate(items):
        hid = " is-extra" if i >= limit else ""
        out.append(f'<a class="tag{hid}" href="{pre}{slug}/">{E(label)}</a>')
    out.append(f'<button type="button" class="tag tag--more" data-expand aria-expanded="false" '
               f'data-more="{E(all_label)}" data-less="Свернуть">{E(all_label)}</button></div>')
    return "\n".join(out)


IC_WA = ('<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
         '<path d="M3.5 20.5l1.3-4.4A8.5 8.5 0 1 1 8 19.3z"/><path d="M9 8.5c0 3.5 3 6.5 6.5 6.5l1.3-1.6-2.2-1.2-1 .8a4.5 4.5 0 0 1-2-2l.8-1-1.2-2.2z"/></svg>')
IC_TG = ('<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
         '<path d="M21.5 3.5L2.8 10.8l6.4 2.3 2.3 6.4z"/><path d="M9.2 13.1l12.3-9.6"/></svg>')
MESS = (f'<a class="ico" href="https://wa.me/" aria-label="WhatsApp" rel="noopener">{IC_WA}</a>'
        f'<a class="ico" href="https://t.me/" aria-label="Telegram" rel="noopener">{IC_TG}</a>')


def header(depth):
    p = "../" * depth
    cats = "".join(f'<a href="{p}{s}/">{E(l)}</a>' for s, l in CATEGORIES)
    svcs = "".join(f'<a href="{p}{s}/">{E(l)}</a>' for s, l in SERVICES)
    return f'''<header class="hdr" id="top">
<div class="wrap hdr__in">
<a class="logo" href="{p or './'}" aria-label="Kukla">Kukla</a>
<button class="burger" type="button" aria-label="Меню" aria-expanded="false" data-burger><i></i><i></i><i></i></button>
<nav class="nav" data-nav aria-label="Основное меню">
<a href="{p}catalog/">Каталог моделей</a>
<div class="dd"><button type="button" class="dd__b" aria-expanded="false">Анкеты моделей</button><div class="dd__m">{cats}</div></div>
<div class="dd"><button type="button" class="dd__b" aria-expanded="false">Услуги</button><div class="dd__m">{svcs}</div></div>
<a href="{p}price/">Цены</a><a href="{p}o-nas/">О нас</a><a href="{p}blog/">Блог</a>
<a href="{p}contacts/">Контакты</a><a href="{p}work/">Работа</a>
</nav>
<div class="hdr__r"><div class="mess">{MESS}</div>
<a class="btn btn--sm" href="#order" data-open-order>Заказ</a>
<a class="lang" href="#" hreflang="en">EN</a></div>
</div></header>'''


def form(idx, title="Заказать звонок"):
    return f'''<form class="cb" data-cb novalidate>
<div class="cb__t">{title}</div>
<label class="fld"><span>Имя</span><input name="name" type="text" autocomplete="given-name" placeholder="Как к вам обращаться" required></label>
<label class="fld"><span>Номер телефона</span><input name="phone" type="tel" inputmode="tel" autocomplete="tel" placeholder="+7 (___) ___-__-__" required></label>
<button class="btn" type="submit">Заказать звонок</button>
<p class="cb__ok" hidden>Спасибо! Мы перезвоним в ближайшее время.</p>
<p class="cb__note">Нажимая кнопку, вы соглашаетесь с обработкой персональных данных.</p>
</form>'''


def footer(depth):
    p = "../" * depth
    nav = [("", "Главная"), ("catalog/", "Каталог моделей"), ("services/", "Услуги"), ("price/", "Цены"),
           ("o-nas/", "О нас"), ("blog/", "Блог"), ("contacts/", "Контакты"), ("work/", "Работа")]
    links = "".join(f'<a href="{p}{u}">{l}</a>' for u, l in nav)
    return f'''<footer class="ftr" id="order"><div class="wrap ftr__in">
<div><div class="ftr__h">Навигация</div><nav class="ftr__nav">{links}</nav></div>
<div><div class="ftr__h">Контакты</div><div class="mess">{MESS}</div>
<p class="ftr__ph">{SITE["phone"]}</p><p class="muted">Ежедневно, круглосуточно</p></div>
<div>{form("f")}</div></div>
<div class="wrap ftr__bot"><span>© {SITE["name"]}. Сайт предназначен для лиц старше 18 лет.</span><span class="age">18+</span></div></footer>
<div class="lb" data-lb hidden><button class="lb__x" aria-label="Закрыть" data-lb-close>×</button>
<button class="lb__n lb__n--p" aria-label="Назад" data-lb-prev>‹</button><img alt="" data-lb-img>
<button class="lb__n lb__n--n" aria-label="Вперёд" data-lb-next>›</button></div>'''


def head(title, desc, canonical, depth, extra=""):
    p = "../" * depth
    return f'''<!doctype html><html lang="ru"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
{NOINDEX}<title>{E(title)}</title><meta name="description" content="{E(desc)}">
<link rel="canonical" href="{SITE["domain"]}{canonical}">
<meta property="og:title" content="{E(title)}"><meta property="og:description" content="{E(desc)}"><meta property="og:type" content="website">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Tektur:wght@500;700;800&family=Exo+2:wght@400;500;600&family=Cormorant+SC:wght@500;600&family=Kaushan+Script&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{p}assets/style.css">{extra}</head><body>'''


def tail(depth):
    return f'<script src="{"../" * depth}assets/app.js" defer></script></body></html>'


def card(m, depth, lazy=True):
    p = "../" * depth
    return f'''<a class="card" href="{p}{m["slug"]}/">
<span class="card__ph"><img src="{photo_url(m, 1, depth)}" alt="{E(m["name"])}, {m["age"]} лет" width="600" height="800"{' loading="lazy"' if lazy else ''}></span>
<span class="card__b"><span class="card__n">{E(m["name"])}</span>
<span class="card__p">Возраст: {m["age"]}, Размер груди: {m["size"]}, Рост: {m["height"]}, Вес: {m["weight"]}</span>
<span class="card__f"><span class="card__pr">{money(m["price"])} <em>/ час</em></span><span class="btn btn--sm">Заказ</span></span></span></a>'''


# ---------- каталог ----------
SEO_CATALOG = '''<h2>Каталог анкет агентства «Кукла»</h2>
<p>В каталоге собраны все актуальные анкеты девушек. Используйте теги категорий и услуг, чтобы быстро найти подходящий вариант, или просмотрите весь список.</p>
<h3>Как выбрать анкету</h3>
<p>Обратите внимание на возраст, параметры и стоимость, а также на описание — в нём указаны особенности и формат встреч.</p>
<ol><li>Выберите категорию или услугу.</li><li>Откройте анкету и изучите фотографии.</li><li>Закажите звонок — администратор ответит на вопросы.</li></ol>
<h4>Проверенные фотографии</h4>
<p>Фотографии в анкетах проверяются администрацией агентства. Подробнее — на странице <a href="../o-nas/">«О нас»</a>.</p>'''


def build_catalog():
    pp = SITE["per_page"]; pages = math.ceil(len(M) / pp)
    for n in range(1, pages + 1):
        depth = 1 if n == 1 else 2
        path = "catalog/" if n == 1 else f"catalog/page-{n}/"
        chunk = M[(n - 1) * pp: n * pp]
        pg = ""
        for i in range(1, pages + 1):
            if i == n:
                pg += f'<span class="pg on" aria-current="page">{i}</span>'
                continue
            if n == 1:
                href = "" if i == 1 else f"page-{i}/"
            else:
                href = "../" if i == 1 else f"../page-{i}/"
            pg += f'<a class="pg" href="{href or "./"}">{i}</a>'
        prev_next = ""
        if pages > 1:
            prev_next = f'<nav class="pager" aria-label="Страницы каталога">{pg}</nav>'
        title = "Анкеты моделей — каталог девушек | Кукла" + (f" — страница {n}" if n > 1 else "")
        desc = "Каталог анкет девушек агентства «Кукла» в Новосибирске: фото, возраст, параметры и стоимость."
        h = head(title, desc, "/" + path, depth)
        body = f'''{header(depth)}
<main>
<section class="hero hero--s"><div class="wrap"><h1>Анкеты моделей</h1>
<p class="lead">Все анкеты агентства в одном месте: фото, возраст, параметры и стоимость. Выберите категорию или услугу либо просмотрите весь каталог.</p></div></section>
<section class="wrap block"><div class="block__h">Категории девушек</div>
{tags_html(CATEGORIES, "", depth, 7, "Все категории", "c")}</section>
<section class="wrap block"><div class="block__h">Услуги</div>
{tags_html(SERVICES, "", depth, 7, "Все услуги", "s")}</section>
<section class="wrap block" aria-label="Анкеты"><div class="hint hint--d">Нажмите на карточку, чтобы открыть анкету</div><div class="grid">
{"".join(card(m, depth) for m in chunk)}</div>{prev_next}</section>
<section class="wrap block"><div class="cta">{form("c")}</div></section>
<section class="wrap block seo">{SEO_CATALOG.replace('href="../o-nas/"', 'href="' + "../" * depth + 'o-nas/"')}</section>
</main>{footer(depth)}{tail(depth)}'''
        out = os.path.join(DIST, path); os.makedirs(out, exist_ok=True)
        open(os.path.join(out, "index.html"), "w", encoding="utf8").write(h + body)


# ---------- анкета ----------
def similar(m):
    sc = []
    for o in M:
        if o["slug"] == m["slug"]:
            continue
        s = len(set(o["cats"]) & set(m["cats"])) * 10 - abs(o["age"] - m["age"])
        sc.append((-s, o["slug"]))
    sc.sort()
    return [BY[s] for _, s in sc[:8]]


def build_model(i, m):
    depth = 1
    prev = M[(i - 1) % len(M)]; nxt = M[(i + 1) % len(M)]
    cats = "".join(f'<a class="tag" href="../{s}/">{E(CAT[s])}</a>' for s in m["cats"])
    gal = "".join(
        f'<a class="g__i{" g__i--main" if k == 1 else ""}" href="{photo_url(m, k, 1)}" data-lb-item>'
        f'<img src="{photo_url(m, k, 1)}" alt="{E(m["name"])}, фото {k}" width="600" height="800"'
        f'{"" if k == 1 else " loading=\"lazy\""}></a>' for k in range(1, 5))
    desc = " ".join(DESC).replace("{n}", m["name"])
    params = [("Возраст", f'{m["age"]} лет'), ("Параметры", f'{m["bust"]} / {m["waist"]} / {m["hips"]}'),
              ("Рост", f'{m["height"]} см'), ("Вес", f'{m["weight"]} кг')]
    dl = "".join(f"<div><dt>{a}</dt><dd>{b}</dd></div>" for a, b in params)
    title = f'{m["name"]}, {m["age"]} лет — анкета, фото и цены | Кукла'
    mdesc = f'{m["name"]}, {m["age"]} лет, рост {m["height"]} см, параметры {m["bust"]}/{m["waist"]}/{m["hips"]}. Стоимость от {m["price"]} ₽/час. Фото и описание анкеты.'
    ld = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "Главная", "item": SITE["domain"] + "/"},
        {"@type": "ListItem", "position": 2, "name": "Каталог моделей", "item": SITE["domain"] + "/catalog/"},
        {"@type": "ListItem", "position": 3, "name": m["name"], "item": f'{SITE["domain"]}/{m["slug"]}/'}]}
    extra = f'<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>'
    sim = "".join(f'<div class="slide">{card(s, depth)}</div>' for s in similar(m))
    body = f'''{header(depth)}
<main>
<nav class="pn wrap" aria-label="Навигация между анкетами">
<a class="pn__a" href="../{prev["slug"]}/" rel="prev"><span>←</span> Предыдущая девушка</a>
<a class="pn__a pn__a--c" href="../catalog/">Каталог моделей</a>
<a class="pn__a" href="../{nxt["slug"]}/" rel="next">Следующая девушка <span>→</span></a></nav>
<section class="wrap prof">
<div class="g" data-gallery>{gal}</div>
<div class="prof__i">
<h1>{E(m["name"])}</h1>
<div class="tags tags--s">{cats}</div>
<div class="price"><span class="price__l">Стоимость</span><span class="price__v">{money(m["price"])}</span><span class="price__u">за 1 час</span></div>
<dl class="params">{dl}</dl>
<div class="about"><h2>О девушке</h2><p>{E(desc)}</p></div>
<a class="btn btn--w" href="#order" data-open-order>Заказать {E(m["name"])}</a>
</div></section>
<section class="wrap block"><div class="cta">{form("m")}</div></section>
<section class="wrap block"><h2 class="sec">Похожие анкеты</h2><div class="hint">Свайпайте, чтобы увидеть больше моделей</div>
<div class="slider" data-slider><button class="sl__b sl__b--p" type="button" aria-label="Назад" data-sl-prev>‹</button>
<div class="sl__t" data-sl-track>{sim}</div>
<button class="sl__b sl__b--n" type="button" aria-label="Вперёд" data-sl-next>›</button></div></section>
</main>{footer(depth)}{tail(depth)}'''
    out = os.path.join(DIST, m["slug"]); os.makedirs(out, exist_ok=True)
    open(os.path.join(out, "index.html"), "w", encoding="utf8").write(
        head(title, mdesc, f'/{m["slug"]}/', depth, extra) + body)


def main():
    if os.path.exists(DIST):
        shutil.rmtree(DIST)
    os.makedirs(os.path.join(DIST, "img")); os.makedirs(os.path.join(DIST, "assets"))
    for f in ("style.css", "app.js"):
        shutil.copy(os.path.join(HERE, f), os.path.join(DIST, "assets", f))
    for m in M:
        for n in range(1, 5):
            if has_real(m, n):
                watermark_jpg(os.path.join(HERE, "photos", f"{m['slug']}-{n}.jpg"),
                              os.path.join(DIST, "img", f"{m['slug']}-{n}.jpg"))
            else:
                open(os.path.join(DIST, "img", f'{m["slug"]}-{n}.svg'), "w", encoding="utf8").write(placeholder(m, n))
    build_catalog()
    for i, m in enumerate(M):
        build_model(i, m)
    print("OK:", len(M), "анкет ->", os.path.abspath(DIST))


if __name__ == "__main__":
    main()
