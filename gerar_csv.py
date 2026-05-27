"""Gera CSV ficticio com 2000 linhas: NDOC, HRP5, HRP5_1B, ASSALARIADO."""
import csv
import random

random.seed(42)
N = 2000
FAIXAS = [0, 1000, 2000, 3000, 5000, 10000, 20000, 100000]


def sortear_renda():
    # distribuicao enviesada para faixas mais baixas
    r = random.random()
    if r < 0.25:
        return random.uniform(0, 1000)
    if r < 0.55:
        return random.uniform(1000, 2000)
    if r < 0.75:
        return random.uniform(2000, 3000)
    if r < 0.88:
        return random.uniform(3000, 5000)
    if r < 0.96:
        return random.uniform(5000, 10000)
    if r < 0.995:
        return random.uniform(10000, 20000)
    return random.uniform(20000, 100000)


def perturbar(valor, assalariado):
    # cria HRP5_1B como variacao da HRP5 (algumas migram, outras mantem)
    r = random.random()
    if r < 0.20:
        return valor  # mantem
    if assalariado == "S":
        fator = random.gauss(1.08, 0.18)  # tende a subir
    else:
        fator = random.gauss(0.98, 0.30)  # mais volatil
    novo = max(0, valor * fator + random.gauss(0, 200))
    # de vez em quando salta de faixa
    if random.random() < 0.05:
        novo = sortear_renda()
    return novo


with open("dados_renda.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f, delimiter=";")
    w.writerow(["NDOC", "HRP5", "HRP5_1B", "ASSALARIADO"])
    for i in range(1, N + 1):
        assal = "S" if random.random() < 0.6 else "N"
        hrp5 = sortear_renda()
        hrp5_1b = perturbar(hrp5, assal)
        w.writerow([i, f"{hrp5:.2f}", f"{hrp5_1b:.2f}", assal])

print(f"Gerado dados_renda.csv com {N} linhas.")
