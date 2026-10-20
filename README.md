# archivo.tea

Archivo visual e histórico del transporte argentino. Arrancamos por el conurbano bonaerense, de 1983 a hoy.

Cada dato lleva su fuente y su estado: DATO, DATO¹, VERIFICAR, ESTIMACIÓN o SIN DATO. Las imágenes reconstruidas o adaptadas con IA llevan su etiqueta. Proyecto sin fines comerciales.

## Cómo está organizado

| Carpeta | Qué hay | ¿Se edita? |
|---|---|---|
| `datos/fichas/` | Una ficha por archivo: `03-26.yaml` es la ficha 03.26 | Sí, es el corazón del archivo |
| `datos/actividad.yaml` | El registro del blog, día por día | Sí |
| `datos/series.yaml` | Las series (02 Colectivos, 03 Trenes y subtes…) y sus colores | Rara vez |
| `notas/` | Publicaciones y notas, una por archivo, en Markdown | Sí |
| `img/` | Imágenes: originales, galerías, planos, folletos | Sí, se suben acá |
| `libreas/` | Tu bondi (por ahora se arma aparte) | No |
| `plantilla/` | El diseño de la web | Solo para cambios de diseño |
| `scripts/build.py` | Arma la web a partir de todo lo anterior | No |
| `_sitio/` | La web ya armada. Se genera sola y no se sube al repo | No |

## Cómo se publica

Cada cambio que llega a la rama `main` dispara a Netlify: corre `scripts/build.py` y publica `_sitio/`. No hay que armar nada a mano.

Para ver la web en tu computadora antes de subir (opcional, necesita Python):

```
pip install -r requirements.txt
python scripts/build.py
```

y abrís `_sitio/index.html`.

## Cómo se suma algo

Leé [CONTRIBUTING.md](CONTRIBUTING.md): ahí están las reglas del archivo y cómo se carga una ficha o una nota.
