"""Convierte el caso IEEE 300-bus de PSTCA/CDF a Excel del repositorio.

Entrada esperada: data/ieee300cdf.txt descargado desde
https://labs.ece.uw.edu/pstca/pf300/ieee300cdf.txt

Salida: data/IEEE300.xlsx con hojas config, bus, gen y branch.
"""
from __future__ import annotations

from pathlib import Path
import re
from openpyxl import Workbook

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "data" / "ieee300cdf.txt"
OUTPUT = ROOT / "data" / "IEEE300.xlsx"


def field(line: str, start: int, end: int) -> str:
    """Campo fijo CDF, columnas 1-indexadas e inclusivas."""
    if len(line) < end:
        line = line.ljust(end)
    return line[start - 1 : end].strip()


def to_float(line: str, start: int, end: int) -> float:
    value = field(line, start, end)
    return float(value) if value else 0.0


def to_int(line: str, start: int, end: int) -> int:
    value = field(line, start, end)
    return int(value) if value else 0


def parse_base_mva(lines: list[str]) -> float:
    for line in lines[:5]:
        match = re.search(r"\b(\d+\.\d+)\b", line)
        if match:
            return float(match.group(1))
    return 100.0


def parse_cdf(path: Path):
    lines = path.read_text(encoding="latin1").splitlines()
    base_mva = parse_base_mva(lines)

    bus_rows = []
    branch_rows = []

    in_bus = False
    in_branch = False

    for line in lines:
        if line.startswith("BUS DATA"):
            in_bus = True
            in_branch = False
            continue
        if line.startswith("BRANCH DATA"):
            in_branch = True
            in_bus = False
            continue

        if in_bus:
            if field(line, 1, 4) == "-999":
                in_bus = False
                continue
            if not line.strip():
                continue

            cdf_type = to_int(line, 25, 26)
            if cdf_type in (0, 1):
                bus_type = 1  # PQ
            elif cdf_type == 2:
                bus_type = 2  # PV
            elif cdf_type == 3:
                bus_type = 3  # Slack
            else:
                raise ValueError(f"Tipo de barra CDF no soportado: {cdf_type}")

            bus_i = to_int(line, 1, 4)
            area = to_int(line, 19, 20) or 1
            zone = to_int(line, 21, 23) or 1
            vm = to_float(line, 28, 33)
            va = to_float(line, 34, 40)
            pd = to_float(line, 41, 49)
            qd = to_float(line, 50, 59)
            pg = to_float(line, 60, 67)
            qg = to_float(line, 68, 75)
            base_kv = to_float(line, 77, 83)
            vg = to_float(line, 85, 90) or vm
            qmax = to_float(line, 91, 98)
            qmin = to_float(line, 99, 106)
            # En CDF los shunts de barra son admitancias en pu. En este
            # repositorio, GS/BS siguen el convenio MATPOWER: MW/MVAr a V=1,
            # por eso se multiplican por baseMVA.
            gs = to_float(line, 107, 114) * base_mva
            bs = to_float(line, 115, 122) * base_mva

            bus_rows.append(
                {
                    "BUS_I": bus_i,
                    "TYPE": bus_type,
                    "PD": pd,
                    "QD": qd,
                    "GS": gs,
                    "BS": bs,
                    "AREA": area,
                    "VM": vm,
                    "VA": va,
                    "BASE_KV": base_kv,
                    "ZONE": zone,
                    "VMAX": 1.10,
                    "VMIN": 0.90,
                    "PG_CDF": pg,
                    "QG_CDF": qg,
                    "QMAX_CDF": qmax,
                    "QMIN_CDF": qmin,
                    "VG_CDF": vg,
                }
            )
            continue

        if in_branch:
            if field(line, 1, 4) == "-999":
                in_branch = False
                continue
            if not line.strip():
                continue

            tap = to_float(line, 77, 82)
            shift = to_float(line, 84, 90)

            branch_rows.append(
                {
                    "F_BUS": to_int(line, 1, 4),
                    "T_BUS": to_int(line, 6, 9),
                    "BR_R": to_float(line, 20, 29),
                    "BR_X": to_float(line, 30, 40),
                    "BR_B": to_float(line, 41, 50),
                    "RATE_A": to_float(line, 51, 55),
                    "RATE_B": to_float(line, 57, 61),
                    "RATE_C": to_float(line, 63, 67),
                    "TAP": tap,
                    "SHIFT": shift,
                    "STATUS": 1,
                    "ANGMIN": -360,
                    "ANGMAX": 360,
                }
            )

    return base_mva, bus_rows, branch_rows


def write_excel(base_mva: float, bus_rows: list[dict], branch_rows: list[dict], output: Path):
    gen_rows = []
    for row in bus_rows:
        has_generator = row["TYPE"] in (2, 3) or abs(row["PG_CDF"]) > 1e-12 or abs(row["QG_CDF"]) > 1e-12
        if not has_generator:
            continue
        gen_rows.append(
            {
                "GEN_BUS": row["BUS_I"],
                "PG": row["PG_CDF"],
                "QG": row["QG_CDF"],
                "QMAX": row["QMAX_CDF"],
                "QMIN": row["QMIN_CDF"],
                "VG": row["VG_CDF"] or row["VM"],
                "MBASE": base_mva,
                "STATUS": 1,
            }
        )

    bus_headers = [
        "BUS_I",
        "TYPE",
        "PD",
        "QD",
        "GS",
        "BS",
        "AREA",
        "VM",
        "VA",
        "BASE_KV",
        "ZONE",
        "VMAX",
        "VMIN",
    ]
    gen_headers = ["GEN_BUS", "PG", "QG", "QMAX", "QMIN", "VG", "MBASE", "STATUS"]
    branch_headers = [
        "F_BUS",
        "T_BUS",
        "BR_R",
        "BR_X",
        "BR_B",
        "RATE_A",
        "RATE_B",
        "RATE_C",
        "TAP",
        "SHIFT",
        "STATUS",
        "ANGMIN",
        "ANGMAX",
    ]

    wb = Workbook()
    ws = wb.active
    ws.title = "config"
    ws.append(["baseMVA"])
    ws.append([base_mva])

    ws = wb.create_sheet("bus")
    ws.append(bus_headers)
    for row in bus_rows:
        ws.append([row[h] for h in bus_headers])

    ws = wb.create_sheet("gen")
    ws.append(gen_headers)
    for row in gen_rows:
        ws.append([row[h] for h in gen_headers])

    ws = wb.create_sheet("branch")
    ws.append(branch_headers)
    for row in branch_rows:
        ws.append([row[h] for h in branch_headers])

    ws = wb.create_sheet("fuente")
    ws.append(["campo", "valor"])
    ws.append(["origen", "Power Systems Test Case Archive (PSTCA), University of Washington"])
    ws.append(["url", "https://labs.ece.uw.edu/pstca/pf300/ieee300cdf.txt"])
    ws.append(["formato_origen", "IEEE Common Data Format"])
    ws.append(["barras", len(bus_rows)])
    ws.append(["generadores", len(gen_rows)])
    ws.append(["ramas", len(branch_rows)])

    output.parent.mkdir(parents=True, exist_ok=True)
    wb.save(output)
    return len(gen_rows)


def main():
    base_mva, bus_rows, branch_rows = parse_cdf(INPUT)
    n_gen = write_excel(base_mva, bus_rows, branch_rows, OUTPUT)
    print(f"Generado: {OUTPUT}")
    print(f"baseMVA={base_mva:g}, barras={len(bus_rows)}, generadores={n_gen}, ramas={len(branch_rows)}")


if __name__ == "__main__":
    main()
