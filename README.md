# r1 — Dashboard de migração de renda (HRP5 vs HRP5_1B)

Dashboard interativo (ECharts) que compara duas medidas de renda por indivíduo, gerando matriz de migração entre faixas e KPIs de variação. Os dados podem vir de um CSV escolhido pelo usuário ou ser embutidos pelo Python em uma versão totalmente estática.

## Arquivos

- `gerar_csv.py` — gera `dados_renda.csv` fictício com 2000 linhas (`NDOC;HRP5;HRP5_1B;ASSALARIADO`).
- `dados_renda.csv` — exemplo já gerado.
- `dash.html` — dashboard interativo com upload de CSV (abra direto no navegador ou sirva via HTTP).
- `gerar_dash_estatico.py` — lê o CSV e gera `dash_estatico.html` com os dados embutidos (sem input de arquivo).
- `dash_estatico.html` — versão estática pronta para abrir com duplo-clique.

## Faixas

`[0, 1000, 2000, 3000, 5000, 10000, 20000, 100000]`

## Funcionalidades

- Filtro por `ASSALARIADO`: Total / S / N.
- Matriz de migração com 4 modos: contagem, % por linha (origem), % por coluna (destino), % sobre total.
- KPIs: médias, diferença de médias, % variação da média, % aumentou/diminuiu/manteve, % manteve/subiu/desceu de faixa, diferença média com sinal, em módulo e em módulo onde |dif|>0.
- Gráficos: distribuição por faixa, direção da variação (pizza), média por faixa de origem.

## Como gerar o estático

```bash
python gerar_csv.py                      # opcional: gera dados_renda.csv
python gerar_dash_estatico.py            # gera dash_estatico.html
# ou: python gerar_dash_estatico.py meu.csv saida.html
```
