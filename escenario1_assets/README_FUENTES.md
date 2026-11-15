# Diagrama unifilar publicado

`IEEE118_unifilar_UW.png` es conversión sin anotaciones del escaneo TIFF de 600 DPI distribuido por R. Christie, University of Washington, *Power Systems Test Case Archive: 118 Bus Power Flow Test Case*, mayo de 1993. El diagrama original corresponde al sistema AEP de diciembre de 1962.

- Página: https://labs.ece.uw.edu/pstca/pf118/pg_tca118bus.htm
- TIFF original: https://labs.ece.uw.edu/pstca/pf118/118bus6.tif
- Original conservado: `IEEE118_unifilar_UW.tif`.
- Fuente, hash y advertencias: `fuente_unifilar.json`.

**Identificación verificada contra el CDF original UW** (`.web-content/ieee118cdf_original.txt`): **barra 26 = TannrsCk V1 / Tanners Creek 345 kV; barra 30 = Sorenson V1 / Sorenson 345 kV**. No confundir barra 26 con W. Kamm: esa identificación sería errónea. El recorte `unifilar_region_26_30.png` abarca Sorenson arriba y Tanners Creek abajo. La línea es el enlace vertical de 345 kV entre ambos, no la rama diagonal de W. Kamm. El CDF usa códigos V1/V2; los kV se verifican en `IEEE118.xlsx`.

Este sí es un diagrama tomado de literatura/archivo publicado, a diferencia de los diagramas de topología propios generados en `presentacion_assets/`. Para exposición mostrar el unifilar y ampliar la región de barras 26 y 30; confirmar identificadores y datos contra MATPOWER case118. La fuente advierte que el escaneo histórico puede ser poco legible y que los límites térmicos no son datos históricos verificados.
