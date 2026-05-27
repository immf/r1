"""Gera um HTML estatico com os dados do CSV embutidos.

Uso:
    python gerar_dash_estatico.py [csv] [saida]

Defaults: csv=dados_renda.csv, saida=dash_estatico.html
Le o template dash.html e injeta window.__EMBED_DATA__ antes do </body>.
O dash.html ja esconde os controles de upload quando esse array existe.
"""
import csv
import json
import sys
from pathlib import Path

CSV_PATH = Path(sys.argv[1] if len(sys.argv) > 1 else "dados_renda.csv")
OUT_PATH = Path(sys.argv[2] if len(sys.argv) > 2 else "dash_estatico.html")
TEMPLATE = Path("dash.html")


def detectar_sep(linha: str) -> str:
    return max([";", ",", "\t", "|"], key=lambda c: linha.count(c))


def carregar(csv_path: Path) -> list[dict]:
    txt = csv_path.read_text(encoding="utf-8-sig")
    primeira = txt.splitlines()[0]
    sep = detectar_sep(primeira)
    rows = []
    reader = csv.DictReader(txt.splitlines(), delimiter=sep)
    cols = {k.lower(): k for k in (reader.fieldnames or [])}

    def find(*needles):
        for n in needles:
            for k in cols:
                if n in k:
                    return cols[k]
        return None

    c_ndoc = find("ndoc")
    c_hrp5 = next((cols[k] for k in cols if k == "hrp5"), None)
    c_hrp5_1b = find("hrp5_1b", "hrp5 1b", "hrp51b")
    c_assal = find("assal")
    if not (c_hrp5 and c_hrp5_1b and c_assal):
        raise SystemExit(
            f"Colunas obrigatorias nao encontradas. Encontradas: {list(cols.values())}"
        )

    for r in reader:
        try:
            hrp5 = float(str(r[c_hrp5]).replace(",", "."))
            hrp5_1b = float(str(r[c_hrp5_1b]).replace(",", "."))
        except (ValueError, TypeError):
            continue
        rows.append(
            {
                "ndoc": r.get(c_ndoc, "") if c_ndoc else "",
                "hrp5": hrp5,
                "hrp5_1b": hrp5_1b,
                "assal": (r.get(c_assal, "") or "").strip().upper(),
            }
        )
    return rows


def main():
    if not TEMPLATE.exists():
        raise SystemExit(f"Template nao encontrado: {TEMPLATE}")
    rows = carregar(CSV_PATH)
    payload = json.dumps(rows, ensure_ascii=False, separators=(",", ":"))
    html = TEMPLATE.read_text(encoding="utf-8")
    injecao = (
        f"<script>window.__EMBED_DATA__ = {payload};"
        f"window.__EMBED_SOURCE__ = {json.dumps(CSV_PATH.name)};</script>\n</body>"
    )
    if "</body>" not in html:
        raise SystemExit("Template sem </body>.")
    html_final = html.replace("</body>", injecao, 1)
    # marca o titulo para deixar claro que e estatico
    html_final = html_final.replace(
        "<title>Dashboard de Migracao de Renda - HRP5 vs HRP5_1B</title>",
        "<title>Dashboard de Migracao de Renda (estatico) - HRP5 vs HRP5_1B</title>",
        1,
    )
    OUT_PATH.write_text(html_final, encoding="utf-8")
    print(f"Gerado {OUT_PATH} com {len(rows)} linhas embutidas (fonte: {CSV_PATH}).")


if __name__ == "__main__":
    main()
