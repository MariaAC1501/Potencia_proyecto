---
source: "Proyecto_Programación_y_Análsisi_de_Flujos_de_Potencia_con_el_uso_de_una_red_estándar_de_118_barras_II_SEMESTRE_2026.pdf"
title: "Especificaciones del proyecto: Programación y Análsisi de Flujos de Potencia con el uso de una red estándar de 118 barras"
converted_at: "2026-08-21T10:09:27-06:00"
---

# Especificaciones del proyecto: Programación y Análsisi de Flujos de Potencia con el uso de una red estándar de 118 barras

**Instituto Tecnológico de Costa Rica**  
**Escuela de Ingeniería Electromecánica**  
**Curso:** MI-5215 Análisis de Sistemas Eléctricos de Potencia  
**II SEMESTRE DE 2026**  
**Profesor del curso:** Ing. Greivin Barahona Guzmán

**Integrantes por proyecto:** Máximo 4 o 5 estudiantes.

## Objetivo general y alcance

Diseñar empleando tres diferentes técnicas numéricas programables (obligatorio Newton Rapson y Gauss Seidel) que resuelva de manera eficaz y efectiva los flujos de potencia de redes eléctricas de potencia, que permita datos para análisis y toma de decisiones en el estudio de las redes.

El diseño desarrollado debe ser validado a través de redes estándar IEEE donde se dispongan literatura, con una limitante en barras no inferior a 118 (Se recomienda utilizar el caso base de estudio de la IEEE 118 barras), el cual puede ser descargado en:

- <https://matpower.org/docs/ref/matpower5.0/case118.html>
- <http://www.ee.washington.edu/research/pstca/>
- <https://egriddata.org/dataset/ieee-118-bus-case/resource/a0dae646-9bde-4bb5-b73b-259c8deea969>

## Detalles del proyecto

- El programa de cómputo desarrollado para el análisis de flujos de potencia, deben pensarse para un número finito de barras, que se define según los datos de entrada.
- El flujo de datos para alimentar el programa debe ser importados desde Excel y los datos finales para el análisis deben ser exportados a Excel.
- Deben búsqueda información de un caso base (no inferior a 118) en artículos de la IEEE, para la validación del (o los) programas a desarrollar.
- El programa debe ser versátil con respecto al número de barras del sistema de potencia que pueda manejar, es decir el programa debe poder analizar redes muy pequeñas (9, 14 barras), o bien; tan grande como sistema de potencia de una región (caso real).
- Deben emplear al menos tres métodos numéricos (puede ser en archivos diferentes) en la solución de los flujos de potencia.
- Crear un informe del proyecto donde se documente una comparativa de los diferentes métodos y junto con un caso base estándar de la IEEE en un sistema no inferior a 118 barras, que permita generar conclusiones al respecto.
- El informe debe realizarse en Word con: portada, introducción, desarrollo, recomendaciones, conclusiones, anexos, apéndices del proyecto de diseño realizado.
- Desarrollar dentro del informe un apartado de marco teórico, donde documente los diferentes métodos desarrollados para el análisis de flujos de potencia, así como también la documentación del caso base empleado para la validación.
- Presentar un avance impreso del informe desarrollado a la semanas 7 del semestre en curso.
- Preparar un archivo en Power Point el cual será utilizado para exponer ante la clase el trabajo realizado.
- Según cronograma del semestre, realizar ante la clase una exposición con un máximo de 40 minutos donde se detalle el trabajo realizado y los hallazgos encontrados. Durante la exposición se debe realizar una corrida de los programas realizados.
- La entrega total del trabajo se debe hacer por evaluaciones del TEC DIGITAL, en el apartado para tal fin, un día antes de la exposición ante la clase.

## Evaluación del proyecto

### Entregables del trabajo (70%)

Recepción de archivos del trabajo (Programada y Word).

| Criterio | Porcentaje |
|---|---:|
| Formato y estructura del documento (portada, índice, desarrollo, etc.) | 5% |
| Contenido Técnico y Teórico del trabajo realizado | 25% |
| Análisis de los diferentes métodos realizados con el caso base | 25% |
| Conclusiones alcanzadas | 15% |

### Exposición del trabajo ante la clase (30%)

| Criterio | Porcentaje |
|---|---:|
| Formato y estructura de la presentación (Power Point) | 5% |
| Presentación ante la clase (aproximadamente 30 a 40 minutos) | 25% |

La nota definitiva del proyecto será pondera por cada estudiante de cada grupo según el promedio de las evaluaciones obtenidas por cada uno, según la nota secreta que cada compañero de grupo le haya asignado por su labor en el proyecto.

## Rúbrica de evaluación del proyecto

| Criterio de evaluación | Peso | Excelente (100%) | Muy Bueno (85%) | Bueno (70%) | Regular (50%) | Insuficiente (0%) |
|---|---:|---|---|---|---|---|
| Formato y Estructura del Informe | 5% | Incluye todas las secciones requeridas (portada, intro, desarrollo, recomendaciones, conclusiones, anexos/apéndices) con excelente redacción y orden. | Incluye todas las secciones, pero con detalles menores de formato o redacción. | Faltan una o dos secciones secundarias o el formato es inconsistente. | Estructura desordenada y faltan secciones clave del informe. | El informe no sigue el formato solicitado o es ilegible. |
| Contenido Técnico y Teórico | 25% | Implementa correctamente al menos 3 métodos numéricos (obligatorios Newton-Raphson y Gauss-Seidel). El programa es versátil para cualquier número de barras y maneja importación/exportación con Excel de forma óptima. Marco teórico completo. | Implementa los 3 métodos con éxito, pero la versatilidad o la integración con Excel presenta fallos menores. Marco teórico adecuado. | Implementa solo 2 métodos o la integración con Excel es limitada. Marco teórico superficial. | Solo implementa un método o presenta errores graves en la lógica de programación. | No implementa los métodos requeridos o el código no funciona. |
| Análisis de Métodos con Caso Base | 25% | Análisis comparativo profundo entre los métodos usando un caso IEEE de al menos 118 barras. Los resultados están validados con literatura estándar de forma precisa. | Comparativa clara entre métodos usando el caso de 118 barras, pero con poca profundidad en la discusión de resultados. | El análisis comparativo es breve o se usó un sistema de menos de 118 barras para la validación principal. | No hay una comparación clara entre los métodos o los datos no coinciden con el caso base. | Ausencia de análisis o uso de un caso base no válido. |
| Conclusiones | 15% | Genera conclusiones robustas y fundamentadas en los resultados del análisis comparativo y la eficiencia de los métodos. | Conclusiones claras basadas en los resultados, aunque podrían ser más específicas. | Conclusiones generales que no se derivan directamente de los datos obtenidos en el proyecto. | Conclusiones muy breves o que no guardan relación con los objetivos del diseño. | No incluye conclusiones o son totalmente erróneas. |
| Estructura de la Presentación (PPT) | 5% | Diapositivas profesionales, con apoyo visual claro y resumen efectivo de los hallazgos encontrados. | Presentación bien estructurada, pero con exceso de texto o pocas gráficas de resultados. | Presentación básica que cumple con mostrar el trabajo, pero carece de dinamismo. | Presentación desordenada o que no incluye los puntos clave del desarrollo técnico. | No se preparó el archivo de Power Point. |
| Exposición y Corrida del Programa | 25% | Exposición fluida dentro del tiempo (30-40 min), demostrando dominio total. La corrida en vivo funciona perfectamente para diversos sistemas. Realiza de manera precisa y ejecutiva del análisis de sus resultados según los publicados a nivel de artículos. | Exposición clara, aunque con ligeros problemas de tiempo o dudas menores en preguntas. El programa corre el caso base con éxito. | La exposición es aceptable, pero la demostración del programa presenta errores técnicos durante la corrida en vivo. | Exposición confusa o el programa no logra completar una corrida exitosa frente a la clase. | No se realizó la exposición o el programa no funciona en absoluto. |

Cada grupo de trabajo puede ponerse de acuerdo y solicitar al profesor con la entrega del proyecto, una ponderación de la nota anterior con la entrega de una coevaluación según el uso del siguiente formulario de coevaluación grupal:

## Formulario de coevaluación grupal

Se le enviará en la fecha de entrega de los proyectos, un formulario donde usted debe evaluar a sus compañeros de grupo individualmente según el desempeño y compromiso que mostraron con el trabajo grupal. Usted no debe asignarse ninguna nota (no se autoevalúe).

La información que se reciba de formulario es confidencial y será revisada únicamente por el profesor y tomada en cuenta para ponderar la nota individual de cada uno de sus compañeros de trabajo de grupo.

De una manera general el formulario le solicitará lo siguiente:

**Nombre del estudiante Evaluador:** _____________________________  
**Carné:** _________  
_(Escriba aquí su nombre)_

**Nombre del proyecto Evaluado:** ______________________________________________.

| # | Nombre de su compañero | Carné de su compañero | Calificación asignada |
|---:|---|---|---|
| 1 |  |  |  |
| 2 |  |  |  |
| 3 |  |  |  |
| 4 |  |  |  |

**Atención:** En caso de no entregar esta información el día de entrega del proyecto, el profesor asumirá que la asignación para cada uno de sus compañeros de grupo de parte suya es de un 100.
