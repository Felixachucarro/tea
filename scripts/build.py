"""Arma la web de archivo.tea a partir de los datos.

    python scripts/build.py

Lee datos/, notas/ y plantilla/, y escribe la web completa en _sitio/ (no se edita a mano).
Netlify corre este mismo script en cada cambio del repo.

Además de la portada arma:
  - una página por ficha en /archivo/03-15/, con su título, descripción y datos escritos (para Google y para compartir);
  - imágenes livianas (WebP, máximo 1600 px) a partir de las originales, que quedan intactas en img/;
  - sitemap.xml y robots.txt."""
import datetime as dt, hashlib, html, json, os, re, shutil, subprocess, sys, unicodedata
import yaml
from PIL import Image, ImageOps, ImageDraw, ImageFont
import numpy as np

R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(R, '_sitio')
SITIO = 'https://archivotea.ar'
MES = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic']
EST = {'publicada': 'Publicado', 'en investigación': 'Próximamente'}
ESTADO_TXT = {'DATO': 'DATO', 'DATO1': 'DATO¹', 'VERIFICAR': 'VERIFICAR', 'ESTIMACION': 'ESTIMACIÓN', 'SIN DATO': 'SIN DATO'}
esc = lambda x: html.escape(str(x or ''), quote=True)


def leer(p):
    with open(os.path.join(R, p), encoding='utf-8') as f:
        return yaml.safe_load(f)


def fecha(s):
    d = dt.date.fromisoformat(str(s)); return f'{d.day} {MES[d.month - 1]} {d.year}'


def decadas(a):
    """Décadas que abarca el período. «Desde 1995», «2013–hoy» y «1957-Actualidad» llegan hasta hoy."""
    a = a or ''
    hasta_hoy = re.search(r'hoy|actualidad|presente|desde', a, re.I)
    y = re.findall(r'\d{4}', a)
    if y:
        x = int(y[0]); z = int(y[1]) if len(y) > 1 else (dt.date.today().year if hasta_hoy else x)
        return list(range(x // 10 * 10, z // 10 * 10 + 1, 10))
    m = re.search(r'[Aa]ños (\d)0', a)
    return [1900 + int(m.group(1)) * 10] if m else []


# ---------- imágenes livianas ----------
if os.path.exists(OUT): shutil.rmtree(OUT)
os.makedirs(OUT)
LIVIANAS = {}          # ruta original -> ruta WebP en _sitio
USADAS = set()         # originales que ya tienen versión liviana (no se copian)


def nombre(ruta):
    base = os.path.splitext(os.path.basename(ruta))[0].lower()
    base = re.sub(r'[^a-z0-9]+', '-', base.translate(str.maketrans('áéíóúñü', 'aeiounu'))).strip('-')[:50] or 'img'
    return f'{base}-{hashlib.md5(ruta.encode()).hexdigest()[:6]}'


def liviana(ruta, lado=1600):
    """Devuelve la ruta de una copia WebP liviana. Si la imagen no existe o no se puede abrir, deja la original."""
    if not ruta or not ruta.startswith('img/'): return ruta
    if ruta in LIVIANAS: return LIVIANAS[ruta]
    src = os.path.join(R, ruta)
    if not os.path.exists(src): LIVIANAS[ruta] = ruta; return ruta
    out = f'img/w/{nombre(ruta)}.webp'
    try:
        im = ImageOps.exif_transpose(Image.open(src))
        alfa = im.mode in ('RGBA', 'LA') or (im.mode == 'P' and 'transparency' in im.info)
        im = im.convert('RGBA' if alfa else 'RGB')
        im.thumbnail((lado, lado), Image.LANCZOS)
        os.makedirs(os.path.join(OUT, 'img', 'w'), exist_ok=True)
        im.save(os.path.join(OUT, out), 'WEBP', quality=82, method=4)
    except Exception as e:
        print(f'  aviso: no se pudo optimizar {ruta} ({e}); queda la original')
        LIVIANAS[ruta] = ruta; return ruta
    LIVIANAS[ruta] = out; USADAS.add(ruta)
    return out


def recorte(src):
    """El vehículo recortado a su contorno sobre blanco (para portadas parejas y vistas previas)."""
    im = ImageOps.exif_transpose(Image.open(src))
    if im.mode in ('RGBA', 'LA', 'P'):
        im = im.convert('RGBA'); fondo = Image.new('RGBA', im.size, 'white'); fondo.alpha_composite(im); im = fondo
    im = im.convert('RGB'); a = np.asarray(im)
    ys, xs = np.where(a.min(2) < 236)
    if len(xs) < 50: return im
    x0, x1 = np.percentile(xs, [0.2, 99.8]).astype(int); y0, y1 = ys.min(), ys.max()
    return im.crop((max(0, x0 - 2), max(0, y0 - 2), min(im.width, x1 + 3), min(im.height, y1 + 3)))


def portada(ruta):
    """Tarjeta del archivo: cada vehículo a la misma altura y sobre la misma línea de piso."""
    W, H, ALTO, ANCHO, PISO = 800, 1000, 740, 720, 930
    v = recorte(os.path.join(R, ruta))
    k = min(ALTO / v.height, ANCHO / v.width)
    v = v.resize((max(1, round(v.width * k)), max(1, round(v.height * k))), Image.LANCZOS)
    out = Image.new('RGB', (W, H), 'white'); out.paste(v, ((W - v.width) // 2, PISO - v.height))
    dst = f'img/cv/{nombre(ruta)}.webp'
    os.makedirs(os.path.join(OUT, 'img', 'cv'), exist_ok=True)
    out.save(os.path.join(OUT, dst), 'WEBP', quality=82, method=4)
    return dst


def vista_previa(ruta, codigo):
    """Imagen 1200×630 para WhatsApp, Facebook y Google (JPG, que todos aceptan)."""
    v = recorte(os.path.join(R, ruta))
    k = min(520 / v.height, 1080 / v.width)
    v = v.resize((max(1, round(v.width * k)), max(1, round(v.height * k))), Image.LANCZOS)
    out = Image.new('RGB', (1200, 630), 'white'); out.paste(v, ((1200 - v.width) // 2, (630 - v.height) // 2))
    dst = f'img/og/{codigo}.jpg'
    os.makedirs(os.path.join(OUT, 'img', 'og'), exist_ok=True)
    out.save(os.path.join(OUT, dst), quality=84)
    return dst


# ---------- placas para historias de Instagram (1080×1920) ----------
FUENTES = os.path.join(R, 'scripts', 'fuentes')
H_TINTA, H_GRIS, H_LINEA = (30, 29, 26), (122, 122, 114), (221, 221, 214)
# casilleros clave por serie, en el mismo orden que la ficha (sin «Ejemplar»)
CLAVES = {'02': [('Carrocería', r'^carrocer'), ('Chasis', r'^(chasis|modelo)'), ('Motor', r'^motor'), ('Potencia', r'potencia'), ('Largo', r'(largo|distancia|batalla)')],
          '03': [('Fabricante', r'^(fabricante|modelo|posible modelo|coche motor)'), ('Fabricación', r'^(fabricaci|llegada|primer)'), ('Línea', r'(l[ií]nea|recorrido|servicio)'), ('Flota', r'(flota|^coches|cantidad)'), ('Operador', r'^(operador|organiza)')],
          '04': [('Motor', r'^motor'), ('Potencia', r'potencia'), ('Producción', r'(producci|fabricaci)'), ('Origen', r'(planta|origen)')],
          '05': [('Producción', r'(producci|fabricaci|lanzamiento)'), ('Motor', r'^motor'), ('Unidades', r'(unidades|ventas)'), ('Planta', r'(planta|origen)')],
          '06': [('Modelo', r'(modelo|veh[ií]culo)'), ('Uso', r'(uso|servicio)'), ('Años', r'(a[ñn]os|producci)')]}
_fuentes = {}


def fuente_h(nombre_f, t):
    k = (nombre_f, t)
    if k not in _fuentes: _fuentes[k] = ImageFont.truetype(os.path.join(FUENTES, nombre_f), t)
    return _fuentes[k]


def datos_placa(p):
    """Hasta tres datos para la placa: los casilleros clave que tengan dato; si faltan, el período."""
    vacio = lambda v: not v or v.strip() in ('—', '-', 'Sin fecha') 
    usados, salida = set(), []
    for etiqueta, patron in CLAVES.get(p['s'], []):
        for i, r in enumerate(p['d']):
            if i in usados or r[2] == 'SIN DATO' or vacio(r[1]): continue
            if re.search(patron, r[0].strip().lower()):
                usados.add(i); salida.append((etiqueta, re.sub(r'\s+', ' ', r[1]).strip())); break
    if len(salida) < 3 and not vacio(p['a']) and p['s'] != '06': salida.insert(0, ('Período', p['a']))
    return salida[:3]


def partir_h(t, f, ancho):
    lineas, l = [], ''
    for w in t.split():
        s_ = (l + ' ' + w).strip()
        if f.getlength(s_) > ancho and l: lineas.append(l); l = w
        else: l = s_
    return lineas + [l]


def placa_historia(p, nombre_corto):
    """La placa para compartir: vehículo centrado, nombre corto, hasta tres datos y la firma de archivo.tea."""
    W, H = 1080, 1920
    im = Image.new('RGB', (W, H), 'white'); dr = ImageDraw.Draw(im)
    logo = Image.open(os.path.join(FUENTES, 'logo-tea.png')).convert('RGBA').resize((64, 64), Image.LANCZOS)
    im.paste(logo, ((W - 64) // 2, 1366), logo)
    dr.text((W // 2, 1446), 'Encontrá el tuyo en', font=fuente_h('Inter-Regular.otf', 30), fill=H_GRIS, anchor='mt')
    dr.text((W // 2, 1484), 'archivotea.ar', font=fuente_h('InterDisplay-Bold.otf', 52), fill=H_TINTA, anchor='mt')
    datos = datos_placa(p)
    fv, fe = fuente_h('InterDisplay-SemiBold.otf', 36), fuente_h('Inter-Medium.otf', 20)
    col = (W - 144) // max(1, len(datos))
    filas = []
    for _, v in datos:
        # lo esencial del dato: sin aclaraciones entre paréntesis ni después de «;», y cortando en comas hasta que entre en dos líneas
        v = re.split(r'\s*[(;]', v)[0].strip().rstrip('.,: ') or v
        while len(partir_h(v, fv, col - 24)) > 2 and ',' in v: v = v.rsplit(',', 1)[0].strip()
        f = partir_h(v, fv, col - 24)
        if len(f) > 2: f = f[:2]; f[1] = f[1].rstrip(',;-– ') + '…'
        filas.append(f)
    nmax = max((len(f) for f in filas), default=0)
    alto_datos = nmax * 44 + 40 if datos else 0
    fn = fuente_h('InterDisplay-ExtraBold.otf', 71); lineas = partir_h(nombre_corto, fn, 936)
    if len(lineas) > 2: fn = fuente_h('InterDisplay-ExtraBold.otf', 58); lineas = partir_h(nombre_corto, fn, 936)[:3]
    paso = 80 if fn.size == 71 else 66
    texto = 36 + len(lineas) * paso + (40 + alto_datos if datos else 0)
    z0, z1 = 250, 1325                                     # libre entre las barras de Instagram
    hv = max(300, min(1000, z1 - z0 - texto)); k = hv / 940
    v = Image.open(os.path.join(OUT, p['cv'])).convert('RGB').crop((0, 0, 800, 940)).resize((round(800 * k), hv), Image.LANCZOS)
    a = np.asarray(v).astype(np.float32) / 255                       # el mismo grano que en la web
    g = np.random.default_rng(int(hashlib.md5(p['c'].encode()).hexdigest()[:8], 16)).random(a.shape[:2], dtype=np.float32)[..., None] - .5
    m = 4 * a * (1 - a) * (a.max(2, keepdims=True) < .96)
    v = Image.fromarray(np.clip((a + g * m * 22 / 255 * 4) * 255, 0, 255).astype(np.uint8))
    y = z0 + (z1 - z0 - hv - texto) // 2
    im.paste(v, ((W - v.width) // 2, y)); y += hv + 36
    for li in lineas: dr.text((W // 2, y), li, font=fn, fill=H_TINTA, anchor='mt'); y += paso
    if datos:
        y += 40
        for i, ((e, _), f) in enumerate(zip(datos, filas)):
            cx = 72 + col * i + col // 2; yy = y + (nmax - len(f)) * 44
            for li in f: dr.text((cx, yy), li, font=fv, fill=H_TINTA, anchor='mt'); yy += 44
            dr.text((cx, y + nmax * 44 + 6), e.upper(), font=fe, fill=H_GRIS, anchor='mt')
            if i: dr.line((72 + col * i, y, 72 + col * i, y + alto_datos - 6), fill=H_LINEA, width=2)
    dst = f'img/historias/{p["c"].replace(".", "-")}.jpg'
    os.makedirs(os.path.join(OUT, 'img', 'historias'), exist_ok=True)
    im.save(os.path.join(OUT, dst), quality=88)
    return dst


# ---------- ficha completa: la decide la cantidad de datos, no un casillero del panel ----------
# Los mismos casilleros clave que la ficha muestra arriba (F2K en la plantilla). Una ficha está completa
# cuando todos tienen dato; si falta alguno, sigue «en investigación».
CASILLEROS = {
    '02': [r'^carrocer(ia|a)( |$)', r'^(chasis|modelo)', r'^motor', r'potencia', r'(largo|distancia|batalla)', r'ejemplar'],
    '03': [r'^(fabricante|fabricantes|modelo|posible modelo|coche motor)', r'^(fabricaci|llegada|primer)', r'(l[ií]nea|recorrido|servicio)',
           r'(flota|^coches|cantidad)', r'^(operador|organiza)', r'ejemplar'],
    '04': [r'^motor', r'potencia', r'(producci|fabricaci)', r'(planta|origen)'],
    '05': [r'(producci|fabricaci|lanzamiento)', r'^motor', r'(unidades|ventas)', r'(planta|origen)'],
    '06': [r'(modelo|veh[ií]culo)', r'(uso|servicio)', r'(a[ñn]os|producci)'],
}


def _norm(t):
    return ''.join(c for c in unicodedata.normalize('NFD', str(t)) if unicodedata.category(c) != 'Mn').lower()


def casilleros_llenos(s, filas):
    """Cuenta los casilleros clave con dato, con la misma regla que la ficha en pantalla."""
    claves = CASILLEROS.get(s, CASILLEROS['02']); usados, llenos = set(), 0
    for patron in claves:
        i = next((j for j, r in enumerate(filas) if j not in usados and re.search(patron, _norm(r[0]))), None)
        if i is None or filas[i][2] == 'SIN DATO' or re.fullmatch(r'[—-]?', filas[i][1].strip()): continue
        usados.add(i); llenos += 1
    return llenos, len(claves)


# ---------- fichas ----------
def pieza(f):
    p = {'c': str(f['codigo']), 's': str(f['serie']), 't': str(f['titulo']).strip(), 'a': str(f.get('periodo') or 'Sin fecha').strip(),
         'tipo': f.get('tipo', 'Ficha'), 'est': EST.get(f.get('estado'), f.get('estado', 'Próximamente')), 'sil': 'logo'}
    if f.get('imagen'): p['img'] = liviana(f['imagen'])
    if f.get('portada'): p['cover'] = liviana(f['portada'])
    if f.get('pie'): p['ig'] = f['pie']
    if f.get('galeria'):
        p['gal'] = [[liviana(g['imagen']), g.get('leyenda', '') or ''] + ([1] if g.get('ancha') else []) for g in f['galeria'] if g.get('imagen')]
    if f.get('nota_galeria'): p['galnota'] = f['nota_galeria']
    p['buscar'] = f.get('busqueda', '') or ''
    # renglones vacíos o a medio cargar en el panel: se saltean con un aviso, sin frenar la web
    datos = [r for r in f.get('datos') or [] if isinstance(r, dict) and r.get('campo') and r.get('valor') not in (None, '')]
    hitos = [r for r in f.get('linea_de_tiempo') or [] if isinstance(r, dict) and r.get('fecha') and r.get('hito')]
    if len(datos) < len(f.get('datos') or []) or len(hitos) < len(f.get('linea_de_tiempo') or []):
        print(f"  aviso: {f['_archivo']} tiene renglones vacíos o incompletos; no se muestran")
    p['d'] = [[str(r['campo']).strip(), str(r['valor']).strip(), r.get('estado') or 'SIN DATO', r.get('fuente', '') or '', r.get('url', '') or ''] for r in datos]
    if hitos:
        p['tl'] = [[str(r['fecha']), r['hito'], r.get('detalle', '') or '', r.get('estado') or 'SIN DATO', r.get('fuente', '') or '', r.get('url', '') or ''] for r in hitos]
    p['dec'] = f['decadas'] if f.get('decadas') else decadas(p['a'])
    if p['tipo'] == 'Ficha' and p['s'] in CASILLEROS:
        llenos, total = casilleros_llenos(p['s'], p['d'])
        p['est'] = 'Publicado' if llenos == total else 'Próximamente'
        p['ck'] = [llenos, total]
    orig = f.get('portada') or f.get('imagen')
    if p['tipo'] == 'Ficha' and orig and os.path.exists(os.path.join(R, orig)):
        p['cv'] = portada(orig)
        p['og'] = vista_previa(orig, p['c'].replace('.', '-'))
        corto = str(f.get('nombre_corto') or '').strip() or (p['t'].split(' · ')[0] if ' · ' in p['t'] else p['t'])
        p['hv'] = placa_historia(p, corto)
    p['_archivo'] = f['_archivo']
    return p


carpeta = os.path.join(R, 'datos', 'fichas')
FICHAS = []
for x in sorted(os.listdir(carpeta)):
    if not x.endswith('.yaml'): continue
    f = leer(os.path.join('datos', 'fichas', x)); f['_archivo'] = x; FICHAS.append(f)

repetidos = {}
for f in FICHAS: repetidos.setdefault(str(f['codigo']), []).append(f['_archivo'])
repetidos = {k: v for k, v in repetidos.items() if len(v) > 1}
if repetidos:
    for k, v in repetidos.items(): print(f'ERROR: el código {k} está repetido en {", ".join(v)}. Cada ficha necesita un código propio.')
    sys.exit(1)

PIEZAS = [pieza(f) for f in FICHAS]
PIEZAS.sort(key=lambda p: (p['s'], p['c']))

# ---------- notas y actividad ----------
NOTAS = []
for x in sorted(os.listdir(os.path.join(R, 'notas'))):
    if not x.endswith('.md'): continue
    txt = open(os.path.join(R, 'notas', x), encoding='utf-8').read().replace('\r\n', '\n')
    m = re.match(r'---\n(.*?)\n---\n(.*)', txt, re.S)
    fm = yaml.safe_load(m.group(1)); fm['texto'] = m.group(2).strip()
    fm['imagenes'] = [liviana(u) for u in fm.get('imagenes') or []]
    if fm.get('estado', 'publicada') == 'publicada': NOTAS.append(fm)
NOTAS.sort(key=lambda n: (str(n['fecha']), -n.get('orden', 0)), reverse=True)
MANUAL = [(str(a['fecha']), a['area'], a['titulo'], a['detalle']) for a in leer('datos/actividad.yaml')]


# ---------- actividad automática: sale del historial del repo ----------
AUTO_DESDE = '2026-10-21'   # antes de esta fecha la actividad está escrita a mano en datos/actividad.yaml
TZ = dt.timezone(dt.timedelta(hours=-3))


def lista(nombres, n=5):
    nombres = list(dict.fromkeys(nombres))
    return ', '.join(nombres[:n]) + (f' y {len(nombres) - n} más' if len(nombres) > n else '')


def actividad_git():
    """Resume por día lo que se cargó: fichas nuevas, fichas actualizadas, notas y cambios en la web."""
    try:
        r = subprocess.run(['git', 'log', f'--since={AUTO_DESDE}T00:00:00-03:00', '--name-status', '-M',
                            '--format=@@%cI'], cwd=R, capture_output=True, text=True, timeout=30)
        if r.returncode: return []
    except Exception:
        return []
    por_codigo = {f['_archivo']: f"{f['codigo']} {str(f['titulo']).strip()}" for f in FICHAS}
    dias = {}
    dia = None
    for linea in r.stdout.splitlines():
        if linea.startswith('@@'):
            dia = dt.datetime.fromisoformat(linea[2:]).astimezone(TZ).date().isoformat(); continue
        if not linea.strip() or dia is None or dia < AUTO_DESDE: continue
        partes = linea.split('\t'); tipo, ruta = partes[0][0], partes[-1]
        d = dias.setdefault(dia, {'nuevas': [], 'act': [], 'notas': [], 'web': False})
        if ruta.startswith('datos/fichas/') and ruta.endswith('.yaml'):
            nom = por_codigo.get(os.path.basename(ruta))
            if not nom: continue
            (d['nuevas'] if tipo == 'A' else d['act']).append(nom)
        elif ruta.startswith('notas/') and ruta.endswith('.md') and tipo == 'A':
            d['notas'].append(os.path.basename(ruta)[11:-3].replace('-', ' '))
        elif ruta.startswith(('scripts/', 'plantilla/', '.pages.yml')):
            d['web'] = True
    salida = []
    for dia, d in sorted(dias.items()):
        nuevas = list(dict.fromkeys(d['nuevas'])); act = [x for x in dict.fromkeys(d['act']) if x not in nuevas]
        if d['web']:
            salida.append((dia, 'Web', 'Mejoras en la web', 'Cambios en el diseño, el panel de carga o el armado del sitio.', 1))
        if d['notas']:
            salida.append((dia, 'Blog', 'Nueva publicación' if len(d['notas']) == 1 else f'{len(d["notas"])} publicaciones nuevas', lista(d['notas']) + '.', len(d['notas'])))
        if act:
            salida.append((dia, 'Archivo', '1 ficha actualizada' if len(act) == 1 else f'{len(act)} fichas actualizadas', lista(act) + '.', len(act)))
        if nuevas:
            salida.append((dia, 'Archivo', '1 ficha nueva' if len(nuevas) == 1 else f'{len(nuevas)} fichas nuevas', lista(nuevas) + '.', len(nuevas)))
    return salida


AUTO = actividad_git()
# orden: lo automático primero y lo destacado a mano al final del día, así aparece arriba en el diario
LOG = sorted([x[:4] for x in AUTO] + MANUAL, key=lambda x: x[0])
APORTES = {}
for f, *_ in MANUAL: APORTES[f] = APORTES.get(f, 0) + 1
for f, _, _, _, n in AUTO: APORTES[f] = APORTES.get(f, 0) + n
SERIES = leer('datos/series.yaml')


def blog():
    hoy = max([dt.date.fromisoformat(f) for f, *_ in LOG] + [dt.datetime.now(TZ).date()])
    cuenta = APORTES
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
        imgs = ''.join(f'<img src="{u}" alt="{esc(p["titulo"])} · placa {i+1}" loading="lazy">' for i, u in enumerate(p.get('imagenes') or []))
        link = f'<a class="btn sec" href="{p["enlace"]["url"]}" style="text-decoration:none">{p["enlace"]["texto"]}</a>' if p.get('enlace') else ''
        posts += f'''<article class="post-b"><div class="meta"><i style="border-color:{col}"></i><span>{p["serie"]} — {s["nombre"]}</span><span>{fecha(p["fecha"])}</span><span>{len(p.get("imagenes") or [])} placas</span></div>
<h2>{p["titulo"]}</h2><p>{p["texto"]}</p><div class="tira">{imgs}</div>{link}</article>'''
    return f'''<main class="wrap vista" id="v-blog" hidden>
  <section class="b-top"><p class="ante">Blog</p><h1>Lo que vamos publicando</h1>
    <p class="bajada">Las publicaciones de Instagram, completas, y todo lo que se suma al archivo día por día.</p></section>
  <section class="boleto-w" aria-label="Boleto: cantidad de visitas al archivo">
    <div class="bol"><div class="cu"><div class="ba"></div><div class="t1">ARCHIVO.TEA</div><div class="t2">Archivo visual del transporte argentino</div>
      <div class="pr"><small>Tarifa única</small><b>$0</b><small>Acceso libre</small></div><div class="vi">El archivo<br>lo hacemos<br>entre todos</div></div>
      <div class="nu"><small>PASAJERO N.º</small><b id="pasajero">——————</b></div>
      <img class="se" src="img/sello-tea.png" alt="" width="120" height="120"></div>
    <p class="pie">Conservá este boleto hasta el final del recorrido</p>
  </section>
  <section class="act" aria-labelledby="t-act">
    <div class="act-h"><b id="t-act">{sum(cuenta.values())} aportes</b><span>en {len(cuenta)} días de trabajo · desde el 13 de octubre de 2026</span><span><span id="b-piezas">—</span> piezas en el archivo</span></div>
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
    imgs = ''.join(f'<img src="{x}" alt="{esc(u["titulo"])} · placa {i+1}" loading="lazy">' for i, x in enumerate((u.get('imagenes') or [])[:4]))
    btn = (f'<a class="btn" href="{u["enlace"]["url"]}" style="text-decoration:none">{u["enlace"]["texto"]}</a>' if u.get('enlace')
           else '<a class="btn" href="#blog" style="text-decoration:none">Ver en el blog</a>')
    return f'''<div class="cuerpo">
      <p class="lead">{u["titulo"]}. {u["texto"]}</p>
      <div class="ultimo">{imgs}</div>
      {btn}
    </div>'''


# ---------- cabeceras, datos estructurados y páginas de ficha ----------
def slug(p): return p['c'].replace('.', '-')
def url_ficha(p): return f'{SITIO}/archivo/{slug(p)}/'
def plano(x): return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', str(x))).strip()


def descripcion(p):
    serie = SERIES[p['s']]['nombre']
    datos = [f'{plano(r[0])}: {plano(r[1]).rstrip(".;")}' for r in p['d'] if r[2] != 'SIN DATO' and not re.search(r'ejemplar', r[0], re.I)][:3]
    base = f'{p["t"]} ({p["a"]}). ' if p['a'] != 'Sin fecha' else f'{p["t"]}. '
    txt = base + ('; '.join(datos) + '.' if datos else f'Ficha de {serie.lower()} en el archivo visual del transporte argentino.')
    return txt if len(txt) <= 158 else txt[:155].rsplit(' ', 1)[0] + '…'


def cabecera(titulo, desc, url, imagen, ld):
    return (f'<base href="/"><meta name="description" content="{esc(desc)}">'
            f'<link rel="canonical" href="{url}">'
            f'<meta property="og:type" content="website"><meta property="og:site_name" content="archivo.tea"><meta property="og:locale" content="es_AR">'
            f'<meta property="og:title" content="{esc(titulo)}"><meta property="og:description" content="{esc(desc)}">'
            f'<meta property="og:url" content="{url}"><meta property="og:image" content="{SITIO}/{imagen}">'
            f'<meta name="twitter:card" content="summary_large_image">'
            f'<link rel="icon" href="/img/favicon.svg" type="image/svg+xml"><title>{esc(titulo)}</title>'
            f'<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>')


WEB = {'@type': 'WebSite', '@id': f'{SITIO}/#sitio', 'url': f'{SITIO}/', 'name': 'archivo.tea',
       'alternateName': 'Transporte Enciclopédico Argentino', 'inLanguage': 'es-AR',
       'description': 'Archivo visual e histórico del transporte argentino. Cada dato con su fuente.'}


def ld_ficha(p, desc):
    img = p.get('og') or p.get('cv') or p.get('img')
    obra = {'@type': 'CreativeWork', '@id': url_ficha(p) + '#ficha', 'url': url_ficha(p), 'name': p['t'], 'headline': p['t'],
            'description': desc, 'inLanguage': 'es-AR', 'isPartOf': {'@id': f'{SITIO}/#sitio'},
            'genre': SERIES[p['s']]['nombre'], 'about': {'@type': 'Thing', 'name': p['t']}}
    if p['a'] != 'Sin fecha': obra['temporalCoverage'] = p['a']
    if img:
        obra['image'] = {'@type': 'ImageObject', 'contentUrl': f'{SITIO}/{img}', 'caption': p.get('ig') or p['t'],
                         'creditText': p.get('ig') or 'archivo.tea'}
    migas = {'@type': 'BreadcrumbList', 'itemListElement': [
        {'@type': 'ListItem', 'position': 1, 'name': 'archivo.tea', 'item': f'{SITIO}/'},
        {'@type': 'ListItem', 'position': 2, 'name': SERIES[p['s']]['nombre'], 'item': f'{SITIO}/#archivo'},
        {'@type': 'ListItem', 'position': 3, 'name': p['t'], 'item': url_ficha(p)}]}
    return {'@context': 'https://schema.org', '@graph': [WEB, obra, migas]}


def fuente(f, u):
    if not f and not u: return ''
    enlace = '<a href="' + esc(u) + '" rel="noopener">fuente</a>' if u else ''
    return '<small>' + esc(f) + (' · ' if f and u else '') + enlace + '</small>'


def ficha_escrita(p):
    """El contenido de la ficha escrito en la página: lo que lee Google y lo que ve quien no tiene JavaScript."""
    serie = SERIES[p['s']]['nombre']
    img = p.get('img') or p.get('cover')
    pie = '<figcaption>' + esc(p['ig']) + '</figcaption>' if p.get('ig') else ''
    fig = f'<figure class="fe-fig"><img src="/{img}" alt="{esc(p["t"])}" width="640">{pie}</figure>' if img else ''
    datos = ''.join(f'<div><dt>{esc(r[0])}</dt><dd>{esc(r[1])}<small>{ESTADO_TXT.get(r[2], r[2])}</small>{fuente(r[3], r[4])}</dd></div>' for r in p['d'])
    tl = ''.join(f'<li><b>{esc(r[0])}</b> · {esc(r[1])}{" — " + esc(r[2]) if r[2] else ""}</li>' for r in p.get('tl') or [])
    gal = ''.join(f'<li>{esc(l)}</li>' for _, l, *_ in p.get('gal') or [] if l)
    return (f'<article class="fe" id="ficha-estatica" aria-labelledby="fe-t">'
            f'<p class="fe-meta">{p["c"]} · {esc(serie)} · {esc(p["tipo"])} · {esc(p["est"])}</p>'
            f'<h1 id="fe-t">{esc(p["t"])}</h1><p class="fe-meta">{esc(p["a"])}</p>{fig}'
            + (f'<h2>Datos</h2><dl>{datos}</dl>' if datos else '<p>Ficha en investigación: todavía no hay datos verificados para mostrar.</p>')
            + (f'<h2>Línea del tiempo</h2><ol>{tl}</ol>' if tl else '')
            + (f'<h2>Imágenes</h2><ul>{gal}</ul>' if gal else '')
            + (f'<p class="fe-meta">{esc(p["galnota"])}</p>' if p.get('galnota') else '')
            + (f'<p><a href="/{p["hv"]}">Placa para compartir en historias</a></p>' if p.get('hv') else '')
            + '<p><a href="/#archivo">Ver todo el archivo</a></p></article>')


def fecha_git(ruta):
    try:
        r = subprocess.run(['git', 'log', '-1', '--format=%cs', '--', ruta], cwd=R, capture_output=True, text=True, timeout=10)
        return r.stdout.strip() or None
    except Exception:
        return None


# ---------- armado ----------
plantilla = open(os.path.join(R, 'plantilla', 'index.html'), encoding='utf-8').read()
for k in ('__HEAD__', '__BLOG__', '__DIARIO__', '__ULTIMO__', '__FICHA__'):
    assert k in plantilla, k
base = plantilla.replace('__BLOG__', blog(), 1).replace('__DIARIO__', diario(), 1).replace('__ULTIMO__', ultimo(), 1)


def frente_parejo(m):
    """Frentes de la portada: cada vehículo recortado a su contorno y a la misma altura, para que apoyen parejos."""
    ruta = m.group(1)
    src = os.path.join(R, ruta)
    if not os.path.exists(src): return m.group(0)
    v = recorte(src); k = 460 / v.height
    v = v.resize((max(1, round(v.width * k)), 460), Image.LANCZOS)
    dst = f'img/fr/{nombre(ruta)}.webp'
    os.makedirs(os.path.join(OUT, 'img', 'fr'), exist_ok=True)
    v.save(os.path.join(OUT, dst), 'WEBP', quality=84, method=4)
    return f'src="{dst}"'


i = base.find('class="frentes"'); j = base.find('</div>', i)
if i > 0: base = base[:i] + re.sub(r'src="(img/[^"]+)"', frente_parejo, base[i:j]) + base[j:]

publicas = [{k: v for k, v in p.items() if k != '_archivo'} for p in PIEZAS]
with open(os.path.join(OUT, 'piezas.js'), 'w', encoding='utf-8') as f:
    f.write('window.__PIEZAS=' + json.dumps(publicas, ensure_ascii=False, separators=(',', ':')) + ';\n')

DESC0 = 'Archivo visual e histórico del transporte argentino: colectivos, trenes, subtes, camiones y autos. Cada vehículo con su ficha y cada dato con su fuente.'
TIT0 = 'archivo.tea · Archivo visual del transporte argentino'
inicio = base.replace('__HEAD__', cabecera(TIT0, DESC0, f'{SITIO}/', 'img/libreas-preview.jpg',
                                          {'@context': 'https://schema.org', '@graph': [WEB]}), 1).replace('__FICHA__', '', 1)
open(os.path.join(OUT, 'index.html'), 'w', encoding='utf-8').write(inicio)

mapa = [(f'{SITIO}/', None)]
for p in PIEZAS:
    desc = descripcion(p)
    titulo = f'{p["t"]} · {SERIES[p["s"]]["nombre"]} | archivo.tea'
    pag = base.replace('__HEAD__', cabecera(titulo, desc, url_ficha(p), p.get('og') or 'img/libreas-preview.jpg', ld_ficha(p, desc)), 1)
    pag = pag.replace('__FICHA__', ficha_escrita(p), 1)
    # en la página de una ficha, el archivo es lo visible desde el primer momento (también sin JavaScript)
    pag = pag.replace('<main class="wrap vista" id="v-inicio">', '<main class="wrap vista" id="v-inicio" hidden>', 1)
    pag = pag.replace('<main class="wrap vista" id="v-archivo" hidden>', '<main class="wrap vista" id="v-archivo">', 1)
    d = os.path.join(OUT, 'archivo', slug(p)); os.makedirs(d, exist_ok=True)
    open(os.path.join(d, 'index.html'), 'w', encoding='utf-8').write(pag)
    mapa.append((url_ficha(p), fecha_git(os.path.join('datos', 'fichas', p['_archivo']))))

with open(os.path.join(OUT, 'sitemap.xml'), 'w', encoding='utf-8') as f:
    f.write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
    for u, lm in mapa: f.write(f'  <url><loc>{u}</loc>{f"<lastmod>{lm}</lastmod>" if lm else ""}</url>\n')
    f.write('</urlset>\n')
open(os.path.join(OUT, 'robots.txt'), 'w').write(f'User-agent: *\nAllow: /\n\nSitemap: {SITIO}/sitemap.xml\n')

# originales: se copian solo las que no tienen versión liviana (logos, imágenes fijas de la portada, etc.)
fijas = set(re.findall(r'img/[^"\'\s)]+', plantilla))
def ignorar(d, nombres):
    rel = os.path.relpath(d, R).replace(os.sep, '/')
    return [n for n in nombres if f'{rel}/{n}' in USADAS and f'{rel}/{n}' not in fijas]
shutil.copytree(os.path.join(R, 'img'), os.path.join(OUT, 'img'), ignore=ignorar, dirs_exist_ok=True)
shutil.copytree(os.path.join(R, 'libreas'), os.path.join(OUT, 'libreas'), dirs_exist_ok=True)

print(f'listo: {len(PIEZAS)} piezas ({len(PIEZAS)} páginas de ficha), {len(NOTAS)} notas, {len(MANUAL)} entradas de actividad a mano + {len(AUTO)} automáticas, '
      f'{len(USADAS)} imágenes optimizadas → _sitio/')
