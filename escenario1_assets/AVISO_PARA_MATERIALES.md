# Datos verificados para el material de exposición

- **Corrección importante del reconocimiento visual inicial:** barra **26 es Tanners Creek 345 kV**, NO W. Kamm. Barra **30 es Sorenson 345 kV**. Se comprobó contra el CDF original UW, `.web-content/ieee118cdf_original.txt`, filas26 y30. Ver `README_FUENTES.md` y `fuente_unifilar.json`.
- `unifilar_region_26_30_anotado.png` incluye resaltado y etiquetas propios correctos, sobre recorte publicado. El original sin anotaciones se conserva. `unifilar_region_26_30.png` se corrigió para abarcar ambos extremos (Sorenson arriba, Tanners Creek abajo).
- El Excel real contiene niveles **138, 161 y 345 kV**. Mencionar los 138 y345 pedidos por la guía sin ocultar la barra de161 kV.
- Hay91 barras con PD distinto de0 y99 con PD o QD distinto de0; especificar criterio de conteo en vez de atribuir91 a todas las cargas del archivo.
- La comparación técnica ya está en `comparacion_escenario1.xlsx`. Fuera del rango0.95–1.05pu: base3 (53,76,118); escenario6 (20,21,22,53,76,118). El conteo usa margen de redondeo1e-8pu.
- Se conservaron tres métodos también en el escenario, aunque la guía exige al menos NR yGS. NR:3→4 iteraciones; GS:757→909; FDLF:9→11. Pérdidas132.862872→165.8977MW. Usar valores completos del libro, no estos redondeos.
- **Ranking literal de la guía añadido:** `comparacion_escenario1.xlsx` ahora incluye `cambios_top5_total`, con las cinco mayores |ΔMVA| entre TODAS las ramas: **26–30, 26–25, 23–25, 30–17, 25–27**. La retirada encabeza este ranking, −100 %. `cambios_top5` sigue siendo un ranking COMPLEMENTARIO de cinco ramas activas para explicar redistribución (incluye también32–113). Mostrar el ranking global exigido y luego las rutas activas; no confundir los dos.
- Los tiempos nuevos incluyen la impresión por iteración si verbose=true; son una corrida técnica, no benchmark controlado ni video grabado.
