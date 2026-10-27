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

## Ficha completa

Una ficha está **completa** cuando todos los casilleros clave que se ven arriba en la ficha tienen dato (cualquier estado menos `SIN DATO`). Si falta alguno, la web la muestra **en investigación** y dice cuántos tiene: «4 de 6 datos clave». No hace falta tocar nada en el panel: se calcula sola en cada publicación.

| Serie | Casilleros clave |
|---|---|
| 02 Colectivos | Carrocería · Chasis · Motor · Potencia · Medidas · Ejemplar |
| 03 Trenes | Fabricante · Fabricación · Líneas · Flota · Operador · Ejemplar |
| 04 Camiones | Motor · Potencia · Producción · Origen |
| 05 Particulares | Producción · Motor · Unidades · Planta |
| 06 Estatales | Modelo · Uso · Años |

## Cómo se carga una ficha

Cada ficha es un archivo en `datos/fichas/`, con el código como nombre (`02-12.yaml` es la 02.12):

```yaml
codigo: '02.12'
serie: '02'
tipo: Ficha
titulo: Mercedes-Benz OF 1214
periodo: 1983–1994   # los años, como se leen en la tarjeta
estado: en investigación      # en las fichas de vehículos lo decide la web: ver «Ficha completa»
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

## Guía rápida: qué va en cada casillero

En «Datos», el **nombre del campo** decide en qué casillero de la ficha aparece. Tiene que **empezar** con uno de estos nombres («Fabricante» entra; «Empresa fabricante» no). Lo que no coincide igual se ve en «Todos los datos y sus fuentes».

| Serie | Casilleros (nombre del campo) |
|---|---|
| Trenes y subtes | Fabricante · Fabricación · Línea · Flota · Operador · Ejemplar |
| Colectivos | Carrocería · Chasis · Motor · Potencia · Largo · Ejemplar |
| Camiones | Motor · Potencia · Producción · Origen |
| Particulares | Producción · Motor · Unidades · Planta |
| Estatales | Modelo · Uso · Años |

- **Flota** es cuántas unidades hubo. **Ejemplar** es la unidad que se ve en la imagen («Coche 1212»).
- Si dos renglones van al mismo casillero, gana el de más arriba.
- **Imagen principal**: la grande de la ficha. **Portada**: la tarjeta de la grilla. **Pie**: el texto debajo de la principal.
- **Galería**: la leyenda elige el grupo. Con «Plano» → Planos · con «Folleto» o «Publicidad» → Publicidad y folletos · con «Foto de», «Fotograma» o «En uso» → En uso · cualquier otra → Vistas.
- **Años**: `1995–2012`, `Desde 1995`, `2013–hoy` o `2007–Actualidad`.

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
