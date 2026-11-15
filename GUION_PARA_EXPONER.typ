// Relato común: tools/presentation_story.py. GUION_PARA_EXPONER.md es generado.
// Generar imágenes y compilar: python tools/build_oral_script.py
#set document(title: "Guion — IEEE118, escenario 1: línea26–30", author: "MI-5215 · Nombres reales pendientes")
#set page(
  paper: "a4",
  margin: (x: 1.9cm, top: 1.8cm, bottom: 1.8cm),
  header: text(size: 8pt, fill: rgb("#64748b"))[GUION DE EXPOSICIÓN · MI-5215],
  footer: align(center)[
    #text(size: 9pt, fill: rgb("#64748b"))[
      #context counter(page).display("1 / 1", both: true)
    ]
  ],
)
#set text(size: 12pt, lang: "es", fill: rgb("#1b3049"))
#set par(justify: false, leading: 0.4em, spacing: 0.5em)
#set heading(numbering: none)
#show heading.where(level: 1): set text(size: 16pt, hyphenate: false, fill: rgb("#10263f"))
#show raw: set text(size: 8pt)

#let data = json("guion_assets/guion.json")
#let two(value) = {
  let digits = str(value)
  if digits.len() < 2 { "0" + digits } else { digits }
}
#let clock(seconds) = two(calc.floor(seconds / 60)) + ":" + two(calc.rem(seconds, 60))
#let muted = rgb("#64748b")
#let accent = rgb("#008878")

#v(1.0cm)
#text(size: 28pt, weight: "bold", fill: rgb("#10263f"))[Guion para exponer]
#v(0.35cm)
#text(size: 17pt)[Programación y análisis de flujos de potencia]
#parbreak()
#text(size: 14pt, fill: accent)[IEEE118 · Escenario 1: retiro de línea 26–30]
#v(0.7cm)
#block(width: 100%, inset: 12pt, fill: rgb("#eff5f7"), radius: 4pt)[
  #strong[Qué contiene este documento]

  Discurso para #data.main_slides diapositivas, con notas sincronizadas y acciones en pantalla. Orden: 0 presentación; 1 configuración; 2 red IEEE118; 3 corrida base; 4 escenario línea26–30; 5 conclusiones. Cada página incluye una miniatura estática de referencia, no una grabación.
]
#v(0.45cm)
#strong[Cómo usarlo]
#enum(
  [Ensaya el discurso con tus propias palabras; no necesitas memorizarlo literalmente.],
  [Lee únicamente el apartado *Qué decir*. Los recuadros de apoyo son indicaciones para quien expone.],
  [En la demostración, ejecuta y comprueba el programa antes de describir los resultados en pantalla.],
  [Completa TODOS los nombres reales y asigna las voces. Cada nueva voz dice su nombre antes de iniciar su parte; no se suponen seis integrantes.],
)
#v(0.35cm)
#strong[Duración orientativa: #clock(data.total_seconds)]

Presupuesto: 0=1:30; 1=9:00; 2=3:30; 3=7:30; 4=11:00; 5=2:30. Incluye código, Excel y corridas, no solo lectura. Ensayar para confirmar 30–40min. Video real MP4 mínimo1080p, voces e identidades pendientes. Grabar cada corrida completa, sin cortes ni acelerado, desde ejecutar hasta exportar; logs y PDF NO sustituyen la toma.
#v(0.35cm)
#strong[Lectura de símbolos y unidades]
#table(
  columns: (0.8fr, 2.2fr),
  stroke: 0.4pt + rgb("#d7e0ea"),
  inset: 6pt,
  [*pu*], [Por unidad.],
  [*MW*], [Megavatios; potencia activa.],
  [*MVA*], [Megavoltamperios; potencia aparente.],
  [*10⁻⁸*], [Diez a la menos ocho.],
  [*Ybus*], [I griega bus; matriz de admitancias nodales.],
  [*B' / B''*], [B prima / B doble prima.],
)
#v(0.35cm)
#text(size: 9pt, fill: muted)[
  Correspondencia: PRESENTACION.pptx/pdf y GUION_PARA_EXPONER.md. Fuente común: tools/presentation_story.py. Procedimiento y fuentes: PRESENTACION.md. Cifras de los Excel disponibles; los tiempos son de una sola corrida técnica, no de un video ya grabado.
]

#for slide in data.slides {
  pagebreak()
  text(size: 10pt, weight: "bold", fill: accent)[DIAPOSITIVA #slide.number]
  heading(level: 1, slide.title)
  text(size: 9pt, fill: muted)[Voz: #slide.voice · #slide.section]
  v(0.1cm)
  grid(
    columns: (100mm, 1fr),
    gutter: 6mm,
    image("guion_assets/" + slide.image, width: 100mm),
    block(inset: 7pt, fill: rgb("#eff5f7"), radius: 3pt)[
      #if slide.appendix {
        text(size: 12pt, weight: "bold", fill: accent)[Respaldo opcional]
        parbreak()
        text(size: 9.5pt, fill: muted)[Fuera del recorrido principal. Consultar solo si surge una pregunta.]
      } else {
        text(size: 9.5pt, fill: muted)[Tiempo sugerido]
        parbreak()
        text(size: 15pt, weight: "bold", fill: accent)[#clock(slide.seconds)]
        v(0.25cm)
        text(size: 9.5pt, fill: muted)[Tramo de la exposición]
        parbreak()
        text(size: 10pt)[#clock(slide.start_seconds) – #clock(slide.end_seconds)]
      }
    ],
  )
  v(0.35cm)
  text(size: 11pt, weight: "bold", fill: accent)[QUÉ DECIR]
  v(0.1cm)
  for paragraph in slide.speech {
    text(paragraph)
    parbreak()
  }
  if slide.code != "" {
    block(width: 100%, inset: 7pt, fill: rgb("#f1f5f9"), radius: 3pt)[
      #text(size: 9pt, weight: "bold")[COMANDOS REALES — CAPTURA CONTINUA, NO LEER]
      #raw(slide.code, lang: "matlab", block: true)
    ]
  }
  if slide.cues.len() > 0 {
    block(width: 100%, inset: 8pt, fill: rgb("#f1f5f9"), radius: 3pt, breakable: false)[
      #set text(size: 9.5pt, fill: muted)
      #set par(leading: 0.45em, spacing: 0.5em)
      #strong[APOYO VISUAL — NO LEER EN VOZ ALTA]
      #for cue in slide.cues {
        parbreak()
        text(cue)
      }
    ]
  }
}
