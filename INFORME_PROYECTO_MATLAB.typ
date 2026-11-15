// Fuente del contenido: INFORME_PROYECTO_MATLAB.md.
// Actualizar tablas, gráficas y PDF: python tools/build_report.py
#set document(
  title: "Flujos de potencia IEEE-118 — caso base y escenario 1",
  author: "Proyecto MI-5215",
)
#set page(
  paper: "a4",
  margin: (x: 2cm, top: 2cm, bottom: 2cm),
  header: text(size: 8pt, fill: rgb("#64748b"))[MI-5215 · Flujos de potencia · Implementación MATLAB],
  footer: align(center, text(size: 9pt, fill: rgb("#64748b"))[
    #context counter(page).display("1 / 1", both: true)
  ]),
)
#set text(size: 11pt, lang: "es", fill: rgb("#1b3049"))
#set par(justify: true, leading: 0.6em, spacing: 0.7em)
#set heading(numbering: none)
#set figure(gap: 7pt)
#show heading.where(level: 1): set text(size: 14pt, fill: rgb("#17365d"))
#show heading.where(level: 2): set text(size: 12pt, fill: rgb("#17365d"))
#show heading.where(level: 3): set text(size: 11pt, fill: rgb("#17365d"))
#show raw: set text(size: 8.3pt)
#show figure.caption: set text(size: 9pt, fill: rgb("#526578"))
#show table: set text(size: 8.7pt)
#set table(inset: 4.5pt, stroke: 0.4pt + rgb("#cbd5e1"))

#let inline(source) = {
  let cursor = 0
  for token in source.matches(regex("`[^`]+`|\\*\\*[^*]+\\*\\*|\\*[^*]+\\*")) {
    text(source.slice(cursor, token.start))
    if token.text.starts-with("`") {
      raw(token.text.slice(1, token.text.len()-1))
    } else if token.text.starts-with("**") {
      strong(text(token.text.slice(2, token.text.len()-2)))
    } else {
      emph(text(token.text.slice(1, token.text.len()-1)))
    }
    cursor = token.end
  }
  text(source.slice(cursor))
}

#let cells(line) = {
  let parts = line.trim().split("|")
  parts.slice(1, parts.len()-1).map(value => value.trim())
}

#let horizontal-rule = line

#let render(source) = {
  let lines = source.split("\n")
  let i = 0
  while i < lines.len() {
    let line = lines.at(i).trim()
    if line == "" or line.starts-with("<!--") {
      i += 1
    } else if line == "---" {
      horizontal-rule(length: 100%, stroke: 0.4pt + rgb("#cbd5e1"))
      i += 1
    } else if line.starts-with("```") {
      let language = line.slice(3).trim()
      let code = ()
      i += 1
      while i < lines.len() and not lines.at(i).trim().starts-with("```") {
        code.push(lines.at(i))
        i += 1
      }
      if language == "math" {
        block(width: 100%)[
          #set text(size: 10.8pt)
          #eval("$ " + code.join("\n") + " $", mode: "markup")
        ]
      } else {
        block(width: 100%, inset: 8pt, fill: rgb("#f4f7fa"),
          stroke: 0.4pt + rgb("#d8e1ea"), radius: 3pt,
          raw(code.join("\n"), block: true, lang: language))
      }
      parbreak()
      i += 1
    } else if line.starts-with("![") {
      let match = line.match(regex("^!\\[(.*)\\]\\((.*)\\)$"))
      assert(match != none, message: "Formato de imagen no reconocido: " + line)
      let path = match.captures.at(1)
      let graphic = if path.contains("IEEE118_unifilar_UW") or path.contains("unifilar_region") {
        image(path, width: 100%, height: 19cm, fit: "contain")
      } else {
        image(path, width: 100%)
      }
      figure(graphic, caption: inline(match.captures.at(0)))
      parbreak()
      i += 1
    } else if line.starts-with("|") {
      let header = cells(line)
      let separators = cells(lines.at(i+1))
      assert(header.len() == separators.len(), message: "Tabla con encabezados inconsistentes")
      let alignments = separators.map(value => if value.ends-with(":") { right } else { left })
      let columns = if header.len() == 2 {
        (1.35fr, 2fr)
      } else if header.len() == 5 and header.at(0) == "Método" {
        (1.5fr, 0.6fr, 1.1fr, 1.1fr, 0.9fr)
      } else if header.len() == 7 {
        (1.25fr, 0.45fr, 0.85fr, 0.95fr, 1fr, 1fr, 1fr)
      } else {
        (1fr,) * header.len()
      }
      let entries = ()
      i += 2
      while i < lines.len() and lines.at(i).trim().starts-with("|") {
        let row = cells(lines.at(i))
        assert(row.len() == header.len(), message: "Fila de tabla con columnas inconsistentes: " + lines.at(i))
        for cell in row { entries.push(inline(cell)) }
        i += 1
      }
      table(columns: columns, align: alignments,
        table.header(..header.map(cell => table.cell(fill: rgb("#eaf0f7"), strong(inline(cell))))),
        ..entries)
      parbreak()
    } else if line.match(regex("^(#{1,6}) (.+)$")) != none {
      let match = line.match(regex("^(#{1,6}) (.+)$"))
      let depth = match.captures.at(0).len()
      if depth > 1 { heading(level: depth - 1, inline(match.captures.at(1))) }
      i += 1
    } else if line.match(regex("^([0-9]+)[.] (.+)$")) != none {
      let start = int(line.match(regex("^([0-9]+)[.] (.+)$")).captures.at(0))
      let items = ()
      while i < lines.len() {
        let match = lines.at(i).trim().match(regex("^([0-9]+)[.] (.+)$"))
        if match == none { break }
        items.push(inline(match.captures.at(1)))
        i += 1
      }
      enum(start: start, ..items)
      parbreak()
    } else if line.starts-with("- ") or line.starts-with("* ") {
      let items = ()
      while i < lines.len() {
        let value = lines.at(i).trim()
        if not (value.starts-with("- ") or value.starts-with("* ")) { break }
        items.push(inline(value.slice(2)))
        i += 1
      }
      list(..items)
      parbreak()
    } else {
      inline(line)
      parbreak()
      i += 1
    }
  }
}

#align(center)[
  #v(1.9cm)
  #text(size: 15pt, weight: "bold")[Instituto Tecnológico de Costa Rica]
  #parbreak()
  #text(size: 12pt)[Escuela de Ingeniería Electromecánica]
  #v(1.6cm)
  #text(size: 25pt, weight: "bold", hyphenate: false, fill: rgb("#17365d"))[
    Programación y análisis\ de flujos de potencia
  ]
  #v(0.65cm)
  #text(size: 18pt, fill: rgb("#008878"))[Implementación independiente en MATLAB]
  #v(0.9cm)
  #text(size: 15pt)[IEEE-118 · Salida de la línea 26–30]
  #parbreak()
  #text(size: 10pt)[IEEE-14: versatilidad · IEEE-300: respaldo opcional]
  #v(1.7cm)
  #text(size: 12pt)[MI-5215 · Análisis de Sistemas Eléctricos de Potencia]
  #parbreak()
  #text(size: 12pt)[II semestre de 2026]
  #v(0.8cm)
  #text(size: 11pt)[Profesor: Ing. Greivin Barahona Guzmán]
  #v(0.8cm)
  #text(size: 11pt)[Integrantes: PENDIENTE completar nombres reales]
  #parbreak()
  #text(size: 9pt)[Video, voces identificadas y entrega: PENDIENTES humanos]
  #v(0.8cm)
  #text(size: 10pt, fill: rgb("#64748b"))[
    Informe técnico ampliado\
    Modelo eléctrico, métodos propios, resultados y validación independiente
  ]
]
#pagebreak()
#outline(title: "Contenido", depth: 1, indent: 10pt)
#pagebreak()
#render(read("INFORME_PROYECTO_MATLAB.md"))
