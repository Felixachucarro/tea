# Cómo trabajamos en archivo.tea

## Las reglas

1. **No inventamos datos.** Si no hay fuente, el dato va como `SIN DATO`. Decir lo que no sabemos también es parte del archivo.
2. **Cada dato lleva su estado:**

   | Estado | Qué significa |
   |---|---|
   | `DATO` | Confirmado en al menos dos fuentes, o en una fuente oficial (CNRT, fabricante, Boletín Oficial) |
   | `DATO1` | Confirmado en una sola fuente, que nombramos (se ve como DATO¹) |
   | `VERIFICAR` | Hay una pista, pero falta confirmarla o las fuentes no coinciden |
   | `ESTIMACION` | Una cuenta nuestra, con los supuestos a la vista |
   | `SIN DATO` | No encontramos fuente. Lo decimos y preguntamos |

3. **Toda imagen lleva crédito.** Las reconstruidas o adaptadas se rotulan «Reconstrucción IA» o «Foto adaptada con IA · original de…».
4. **Siempre «archivo.tea»**, nunca «TEA» solo.
5. **La voz:** español rioplatense, con voseo, en primera persona del plural. El dato primero, sin emojis.
6. **Hablamos de los vehículos, no juzgamos a quienes los usan.**

## Qué NO va en este repo

Todo lo que está acá se puede leer. No subimos:

- contactos de fuentes o entrevistados;
- testimonios crudos, audios o transcripciones sin editar;
- permisos y acuerdos de uso de imágenes;
- borradores con fecha de salida acordada;
- contraseñas o claves.

Eso vive en el Drive de dirección.

## Cómo se carga una ficha

Cada ficha es un archivo en `datos/fichas/`, con el código como nombre (`02-12.yaml` es la 02.12):

```yaml
codigo: '02.12'
serie: '02'
tipo: Ficha
titulo: Mercedes-Benz OF 1214
periodo: 1983–1994   # los años, como se leen en la tarjeta
estado: en investigación      # o: publicada
imagen: img/0212-01.jpg       # la imagen principal
portada: img/c0212.jpg        # la de la tarjeta en la grilla
pie: Línea 68, frente · Reconstrucción IA
busqueda: of 1214 mercedes motor delantero
galeria:
- imagen: img/0212-f3.jpg
  leyenda: 02 · Folleto: el chasis
  ancha: true                 # opcional: ocupa todo el ancho
datos:
- campo: Fabricación
  valor: 1983–1994
  estado: DATO1
  fuente: Camión Argentino
  url: https://camionargentino.blogspot.com/2012/03/mercedes-benz-of-1214.html
```

En la galería, la leyenda decide el grupo: si dice «Plano» va a **Planos**; si dice «Folleto» o «Publicidad», a **Publicidad y folletos**; si dice «Fotograma» o «Foto de», a **En uso**. Todo lo demás va a **Vistas**.

## Imágenes y direcciones

- **Las fotos se suben como estén.** Al armar la web, el script hace una copia liviana de cada imagen (WebP, hasta 1600 px). El original queda intacto en `img/`.
- **Cada ficha tiene su página**: la 03.15 queda en `archivotea.ar/archivo/03-15/`. Esa es la dirección para compartir y la que encuentra Google. Por eso el código de cada ficha tiene que ser único: si se repite, el armado se frena y la web no se actualiza hasta corregirlo.
- **El ruido analógico** sobre los vehículos se ajusta en `plantilla/index.html`, en la variable `--ruido-op` (intensidad; `0` lo apaga).

## Cómo se carga una nota

Cada nota es un archivo en `notas/`, con la fecha adelante: `2026-10-18-dia-de-la-madre-ana-rossi.md`.

```markdown
---
titulo: Día de la Madre: Ana Rossi
fecha: '2026-10-18'
serie: '02'
estado: publicada       # borrador | revisión | publicada (solo «publicada» sale en la web)
imagenes:
- img/blog/madre-01.jpg
---
El texto de la nota.
```

## Quién publica

- **Dirección** (Félix y Milagros): aprueban y publican.
- **Colaboradores:** proponen cambios en una rama o con un *pull request*. Una persona de dirección los revisa (fuentes, créditos, estados) antes de que lleguen a `main`.
