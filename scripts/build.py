"""Arma la web de archivo.tea a partir de los datos.

    python scripts/build.py

Lee datos/, notas/ y plantilla/, y escribe la web completa en _sitio/ (no se edita a mano).
Netlify corre este mismo script en cada cambio del repo."""
import datetime as dt, json, os, re, shutil
import yaml
from PIL import Image
import numpy as np

R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(R, '_sitio')
MES = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic']
EST = {'publicada': 'Publicado', 'en investigación': 'Próximamente'}


def leer(p):
    with open(os.path.join(R, p), encoding='utf-8') as f:
        return yaml.safe_load(f)


def fecha(s):
    d = dt.date.fromisoformat(str(s)); return f'{d.day} {MES[d.month - 1]} {d.year}'


def decadas(a):
    y = re.findall(r'\d{4}', a or '')
    if y:
        x = int(y[0]); z = int(y[1]) if len(y) > 1 else (2026 if 'hoy' in a else x)
        return list(range(x // 10 * 10, z // 10 * 10 + 1, 10))
    m = re.search(r'[Aa]ños (\d)0', a or '')
    return [1900 + int(m.group(1)) * 10] if m else []


# ---------- fichas ----------
def pieza(f):
    p = {'c': f['codigo'], 's': f['serie'], 't': f['titulo'], 'a': f.get('años') or 'Sin fecha', 'tipo': f.get('tipo', 'Ficha'),
         'est': EST.get(f.get('estado'), f.get('estado', 'Próximamente')), 'sil': 'logo'}
    if f.get('imagen'): p['img'] = f['imagen']
    if f.get('portada'): p['cover'] = f['portada']
    if f.get('pie'): p['ig'] = f['pie']
    if f.get('galeria'):
        p['gal'] = [[g['imagen'], g.get('leyenda', '')] + ([1] if g.get('ancha') else []) for g in f['galeria']]
    if f.get('nota_galeria'): p['galnota'] = f['nota_galeria']
    p['buscar'] = f.get('busqueda', '')
    p['d'] = [[r['campo'], str(r['valor']), r.get('estado', 'SIN DATO'), r.get('fuente', ''), r.get('url', '')] for r in f.get('datos') or []]
    if f.get('linea_de_tiempo'):
        p['tl'] = [[str(r['año']), r['hito'], r.get('detalle', ''), r.get('estado', 'SIN DATO'), r.get('fuente', ''), r.get('url', '')] for r in f['linea_de_tiempo']]
    p['dec'] = f['decadas'] if 'decadas' in f else decadas(p['a'])
    return p


carpeta = os.path.join(R, 'datos', 'fichas')
PIEZAS = [pieza(leer(os.path.join('datos', 'fichas', x))) for x in os.listdir(carpeta) if x.endswith('.yaml')]
PIEZAS.sort(key=lambda p: (p['s'], p['c']))

# ---------- notas y actividad ----------
NOTAS = []
for x in sorted(os.listdir(os.path.join(R, 'notas'))):
    if not x.endswith('.md'): continue
    txt = open(os.path.join(R, 'notas', x), encoding='utf-8').read()
    m = re.match(r'---\n(.*?)\n---\n(.*)', txt, re.S)
    fm = yaml.safe_load(m.group(1)); fm['texto'] = m.group(2).strip()
    if fm.get('estado', 'publicada') == 'publicada': NOTAS.append(fm)
NOTAS.sort(key=lambda n: (str(n['fecha']), -n.get('orden', 0)), reverse=True)
LOG = [(str(a['fecha']), a['area'], a['titulo'], a['detalle']) for a in leer('datos/actividad.yaml')]
SERIES = leer('datos/series.yaml')


def blog():
    hoy = max(dt.date.fromisoformat(f) for f, *_ in LOG)
    cuenta = {}
    for f, *_ in LOG: cuenta[f] = cuenta.get(f, 0) + 1
    ini = dt.date(2026, 10, 12)
    fin = max(dt.date(2027, 1, 3), hoy + dt.timedelta(days=(6 - hoy.weekday())))
    semanas = (fin - ini).days // 7 + 1
    meses = '<tr><th></th>' + ''.join(
        f'<th>{MES[(ini+dt.timedelta(weeks=w)).month-1] if w==0 or (ini+dt.timedelta(weeks=w)).month!=(ini+dt.timedelta(weeks=w-1)).month else ""}</th>' for w in range(semanas)) + '</tr>'
    filas = ''
    for d in range(7):
        etq = {0: 'lun', 2: 'mié', 4: 'vie'}.get(d, '')
        filas += f'<tr><td class="dia">{etq}</td>'
        for w in range(semanas):
            day = ini + dt.timedelta(weeks=w, days=d)
            n = cuenta.get(day.isoformat(), 0)
            cl = 'fut' if day > hoy else (f'n{min(n,4)}' if n else '')
            if day == hoy: cl += ' hoy'
            tip = f'{fecha(day.isoformat())}: {n} {"aporte" if n==1 else "aportes"}' if day <= hoy else fecha(day.isoformat())
            filas += f'<td><i class="{cl}" title="{tip}"></i></td>'
        filas += '</tr>'
    log = ''.join(f'<li><span class="t">{fecha(f)}</span><span class="tag">{tag}</span><div><b>{t}</b><span class="d">{d}</span></div></li>' for f, tag, t, d in reversed(LOG))
    posts = ''
    for p in NOTAS:
        s = SERIES[p['serie']]; col = {'02': '#e2a517', '00': '#68a6d5'}.get(p['serie'], s['color'])
        imgs = ''.join(f'<img src="{u}" alt="{p["titulo"]} · placa {i+1}" loading="lazy">' for i, u in enumerate(p.get('imagenes') or []))
        link = f'<a class="btn sec" href="{p["enlace"]["url"]}" style="text-decoration:none">{p["enlace"]["texto"]}</a>' if p.get('enlace') else ''
        posts += f'''<article class="post-b"><div class="meta"><i style="border-color:{col}"></i><span>{p["serie"]} — {s["nombre"]}</span><span>{fecha(p["fecha"])}</span><span>{len(p.get("imagenes") or [])} placas</span></div>
<h2>{p["titulo"]}</h2><p>{p["texto"]}</p><div class="tira">{imgs}</div>{link}</article>'''
    return f'''<main class="wrap vista" id="v-blog" hidden>
  <section class="b-top"><p class="ante">Blog</p><h1>Lo que vamos publicando</h1>
    <p class="bajada">Las publicaciones de Instagram, completas, y todo lo que se suma al archivo día por día.</p></section>
  <section class="act" aria-labelledby="t-act">
    <div class="act-h"><b id="t-act">{len(LOG)} aportes</b><span>en {len(cuenta)} días de trabajo · desde el 13 de octubre de 2026</span><span><span id="b-piezas">—</span> piezas en el archivo</span></div>
    <div class="cal"><table aria-label="Actividad por día">{meses}{filas}</table></div>
    <div class="ley"><span>Menos</span><i style="background:#eef1f3"></i><i style="background:#c6dcef"></i><i style="background:#93bfe3"></i><i style="background:#68a6d5"></i><i style="background:#2f6f9f"></i><span>Más</span></div>
  </section>
  <section class="b-sec" aria-labelledby="t-pub"><h2 id="t-pub">Publicaciones</h2><div class="posts">{posts}</div></section>
  <section class="b-sec" aria-labelledby="t-log" style="padding-bottom:72px"><h2 id="t-log">Actividad</h2><ol class="log">{log}</ol></section>
</main>
'''


def diario():
    return ''.join(f'<li><span class="t">{fecha(f)}</span><div><b>{t}</b><span>{x}</span></div></li>' for f, _, t, x in list(reversed(LOG))[:6])


def ultimo():
    u = NOTAS[0]
    imgs = ''.join(f'<img src="{x}" alt="{u["titulo"]} · placa {i+1}" loading="lazy">' for i, x in enumerate((u.get('imagenes') or [])[:4]))
    btn = (f'<a class="btn" href="{u["enlace"]["url"]}" style="text-decoration:none">{u["enlace"]["texto"]}</a>' if u.get('enlace')
           else '<a class="btn" href="#blog" style="text-decoration:none">Ver en el blog</a>')
    return f'''<div class="cuerpo">
      <p class="lead">{u["titulo"]}. {u["texto"]}</p>
      <div class="ultimo">{imgs}</div>
      {btn}
    </div>'''


# ---------- portadas parejas: cada vehículo al contorno, misma altura, mismo piso ----------
def portada(src, dst):
    W, H, ALTO, ANCHO, PISO = 800, 1000, 740, 720, 930
    im = Image.open(src).convert('RGB'); a = np.asarray(im)
    ys, xs = np.where(a.min(2) < 236)
    if len(xs) < 50: shutil.copy(src, dst); return
    x0, x1 = np.percentile(xs, [0.2, 99.8]).astype(int); y0, y1 = ys.min(), ys.max()
    v = im.crop((max(0, x0 - 2), max(0, y0 - 2), min(im.width, x1 + 3), min(im.height, y1 + 3)))
    k = min(ALTO / v.height, ANCHO / v.width)
    v = v.resize((max(1, round(v.width * k)), max(1, round(v.height * k))), Image.LANCZOS)
    out = Image.new('RGB', (W, H), 'white'); out.paste(v, ((W - v.width) // 2, PISO - v.height))
    out.save(dst, quality=86)


# ---------- armado ----------
if os.path.exists(OUT): shutil.rmtree(OUT)
shutil.copytree(os.path.join(R, 'img'), os.path.join(OUT, 'img'))
shutil.copytree(os.path.join(R, 'libreas'), os.path.join(OUT, 'libreas'))
os.makedirs(os.path.join(OUT, 'img', 'cv'), exist_ok=True)
for p in PIEZAS:
    c = p.get('cover')
    if p['tipo'] == 'Ficha' and c and os.path.exists(os.path.join(R, c)):
        portada(os.path.join(R, c), os.path.join(OUT, 'img', 'cv', os.path.basename(c)))

html = open(os.path.join(R, 'plantilla', 'index.html'), encoding='utf-8').read()
for k, v in {'__PIEZAS__': json.dumps(PIEZAS, ensure_ascii=False), '__BLOG__': blog(), '__DIARIO__': diario(), '__ULTIMO__': ultimo()}.items():
    assert k in html, k
    html = html.replace(k, v, 1)
open(os.path.join(OUT, 'index.html'), 'w', encoding='utf-8').write(html)
print(f'listo: {len(PIEZAS)} piezas, {len(NOTAS)} notas, {len(LOG)} entradas de actividad → _sitio/')
