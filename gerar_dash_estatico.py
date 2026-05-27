"""Gera HTML estatico com APENAS as estatisticas agregadas embutidas.

Uso:
    python gerar_dash_estatico.py [csv] [saida]

Defaults: csv=dados_renda.csv, saida=dash_estatico.html

Estrategia: o Python le o CSV uma vez, agrega tudo (matriz NFxNF, distribuicoes,
medias por faixa, contagens de direcao e KPIs) para os 3 grupos T/S/N, e injeta
o objeto resultante como window.__EMBED_AGG__. Tamanho do payload nao cresce
com o numero de linhas (so com o numero de faixas).
"""
import csv
import json
from pathlib import Path

FAIXAS = [0, 1000, 2000, 3000, 5000, 10000, 20000, 100000]
NF = len(FAIXAS) - 1


def faixa(v: float) -> int:
    for i in range(NF):
        if FAIXAS[i] <= v < FAIXAS[i + 1]:
            return i
    return NF - 1 if v >= FAIXAS[NF] else -1


def empty_group() -> dict:
    return {
        "n": 0,
        "M": [[0] * NF for _ in range(NF)],
        "distH1": [0] * NF,
        "distH2": [0] * NF,
        "_sumH1": [0.0] * NF,
        "_sumH2": [0.0] * NF,
        "_cntO": [0] * NF,
        "dir": {"aum": 0, "dim": 0, "mant": 0},
        "_s1": 0.0,
        "_s2": 0.0,
        "_dif": 0.0,
        "_absDif": 0.0,
        "_absDifNZ": 0.0,
        "_nz": 0,
        "_mantF": 0,
        "_subF": 0,
        "_descF": 0,
    }


def push(g: dict, h1: float, h2: float) -> None:
    g["n"] += 1
    fa, fb = faixa(h1), faixa(h2)
    if fa >= 0 and fb >= 0:
        g["M"][fa][fb] += 1
    if fa >= 0:
        g["distH1"][fa] += 1
        g["_sumH1"][fa] += h1
        g["_sumH2"][fa] += h2
        g["_cntO"][fa] += 1
    if fb >= 0:
        g["distH2"][fb] += 1
    d = h2 - h1
    g["_s1"] += h1
    g["_s2"] += h2
    g["_dif"] += d
    g["_absDif"] += abs(d)
    if d != 0:
        g["_absDifNZ"] += abs(d)
        g["_nz"] += 1
    if d > 0:
        g["dir"]["aum"] += 1
    elif d < 0:
        g["dir"]["dim"] += 1
    else:
        g["dir"]["mant"] += 1
    if fa == fb:
        g["_mantF"] += 1
    elif fb > fa:
        g["_subF"] += 1
    else:
        g["_descF"] += 1


def finalize(g: dict) -> dict:
    n = g["n"]
    g["meanH1"] = [round(g["_sumH1"][i] / g["_cntO"][i]) if g["_cntO"][i] else 0 for i in range(NF)]
    g["meanH2"] = [round(g["_sumH2"][i] / g["_cntO"][i]) if g["_cntO"][i] else 0 for i in range(NF)]
    if n:
        m1, m2 = g["_s1"] / n, g["_s2"] / n
        g["kpis"] = {
            "n": n,
            "media1": m1,
            "media2": m2,
            "difMedias": m2 - m1,
            "pctVarMedia": (100 * (m2 - m1) / m1) if m1 else 0,
            "pctAumentou": 100 * g["dir"]["aum"] / n,
            "pctDiminuiu": 100 * g["dir"]["dim"] / n,
            "pctManteve": 100 * g["dir"]["mant"] / n,
            "pctMantFaixa": 100 * g["_mantF"] / n,
            "pctSubFaixa": 100 * g["_subF"] / n,
            "pctDescFaixa": 100 * g["_descF"] / n,
            "difMediaPP": g["_dif"] / n,
            "difMediaAbs": g["_absDif"] / n,
            "difMediaAbsNZ": (g["_absDifNZ"] / g["_nz"]) if g["_nz"] else 0,
        }
    else:
        g["kpis"] = None
    # remove campos intermediarios
    for k in [k for k in g if k.startswith("_")]:
        del g[k]
    return g


def detect_sep(linha: str) -> str:
    return max([";", ",", "\t", "|"], key=lambda c: linha.count(c))


def _agregar(csv_path: Path) -> dict:
    txt = csv_path.read_text(encoding="utf-8-sig")
    linhas = txt.splitlines()
    if not linhas:
        raise SystemExit("CSV vazio.")
    sep = detect_sep(linhas[0])
    reader = csv.DictReader(linhas, delimiter=sep)
    fns = reader.fieldnames or []
    cols = {k.lower(): k for k in fns}

    def find(*needles):
        for n in needles:
            for k in cols:
                if n in k:
                    return cols[k]
        return None

    c_hrp5 = next((cols[k] for k in cols if k == "hrp5"), None)
    c_hrp5_1b = find("hrp5_1b", "hrp5 1b", "hrp51b")
    c_assal = find("assal")
    if not (c_hrp5 and c_hrp5_1b and c_assal):
        raise SystemExit(f"Colunas obrigatorias nao encontradas em {fns}")

    groups = {"T": empty_group(), "S": empty_group(), "N": empty_group()}
    for r in reader:
        try:
            h1 = float(str(r[c_hrp5]).replace(",", "."))
            h2 = float(str(r[c_hrp5_1b]).replace(",", "."))
        except (ValueError, TypeError):
            continue
        assal = (r.get(c_assal, "") or "").strip().upper()
        push(groups["T"], h1, h2)
        if assal == "S":
            push(groups["S"], h1, h2)
        elif assal == "N":
            push(groups["N"], h1, h2)
    for k in groups:
        finalize(groups[k])
    return {"groups": groups, "nTotal": groups["T"]["n"], "faixas": FAIXAS}


def dash(csv_path: str, template_path: str, out_path: str) -> None:
    """Gera HTML estatico embutindo as estatisticas agregadas do CSV.

    Todos os argumentos sao strings; o Path() e feito aqui dentro.
    """
    csv_p = Path(csv_path)
    template_p = Path(template_path)
    out_p = Path(out_path)
    if not template_p.exists():
        raise SystemExit(f"Template nao encontrado: {template_p}")

    agg = _agregar(csv_p)
    payload = json.dumps(agg, ensure_ascii=False, separators=(",", ":"))
    html = template_p.read_text(encoding="utf-8")
    injecao = (
        f"<script>window.__EMBED_AGG__ = {payload};"
        f"window.__EMBED_SOURCE__ = {json.dumps(csv_p.name)};</script>\n</body>"
    )
    if "</body>" not in html:
        raise SystemExit("Template sem </body>.")
    html_final = html.replace("</body>", injecao, 1).replace(
        "<title>Dashboard de Migracao de Renda - HRP5 vs HRP5_1B</title>",
        "<title>Dashboard de Migracao de Renda (estatico) - HRP5 vs HRP5_1B</title>",
        1,
    )
    out_p.parent.mkdir(parents=True, exist_ok=True)
    out_p.write_text(html_final, encoding="utf-8")
    size_kb = len(payload) / 1024
    print(f"Gerado {out_p} (N={agg['nTotal']}, payload agregado={size_kb:.1f} KB).")


if __name__ == "__main__":
    dash("dados_renda.csv", "dash.html", "dash_estatico.html")
