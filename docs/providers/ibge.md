# IBGE/SIDRA

O IBGE (Instituto Brasileiro de Geografia e Estatistica) e a principal fonte oficial de dados macroeconomicos brasileiros. O acesso e feito via Sistema SIDRA (Sistema IBGE de Recuperacao Automatica).

## Por que usar IBGE/SIDRA?

- Fonte oficial de indicadores macroeconomicos do Brasil
- Dados de inflacao (IPCA), atividade economica (PIB, PIM, PMC, PMS) e emprego (PNAD)
- Variacoes ja calculadas: MoM, YoY, acumulado 12 meses, YTD
- Series dessazonalizadas disponiveis

---

## Indicadores Disponiveis

### IPCA (Inflacao) - Mensal

| Chave | Tabela | Variavel | Descricao |
|-------|--------|----------|-----------|
| `ipca` | 1737 | 63 | Variacao mensal |
| `ipca_3m` | 1737 | 2263 | Variacao acumulada 3 meses |
| `ipca_6m` | 1737 | 2264 | Variacao acumulada 6 meses |
| `ipca_ytd` | 1737 | 69 | Variacao acumulada no ano |
| `ipca_12m` | 1737 | 2265 | Variacao acumulada 12 meses |
| `ipca_indice` | 1737 | 2266 | Numero-indice (base dez/1993=100) |
| `ipca_grupos` | 7060 | 63 | Variacao mensal por grupos |

### PIB (Atividade) - Trimestral

| Chave | Tabela | Variavel | Descricao |
|-------|--------|----------|-----------|
| `pib` | 1620 | 583 | Serie encadeada |
| `pib_dessaz` | 1621 | 584 | Dessazonalizado |
| `pib_yoy` | 5932 | 6561 | Taxa YoY (trim/trim ano anterior) |
| `pib_qoq` | 5932 | 6564 | Taxa QoQ (trim/trim anterior dessaz) |
| `pib_ytd` | 5932 | 6563 | Taxa acumulada no ano |
| `pib_4q` | 5932 | 6562 | Taxa acumulada 4 trimestres |

### PIM (Producao Industrial) - Mensal

| Chave | Tabela | Variavel | Descricao |
|-------|--------|----------|-----------|
| `pim` | 8888 | 12606 | Industria geral (numero-indice) |
| `pim_dessaz` | 8888 | 12607 | Dessazonalizado |
| `pim_mom` | 8888 | 11601 | Variacao m/m-1 (dessaz) |
| `pim_yoy` | 8888 | 11602 | Variacao m/m-12 |
| `pim_ytd` | 8888 | 11603 | Variacao acumulada no ano |
| `pim_12m` | 8888 | 11604 | Variacao acumulada 12 meses |

### PMC (Comercio Varejista) - Mensal

| Chave | Tabela | Variavel | Descricao |
|-------|--------|----------|-----------|
| `pmc_varejo` | 8880 | 7169 | Varejo (volume de vendas) |
| `pmc_varejo_dessaz` | 8880 | 7170 | Varejo dessazonalizado |
| `pmc_varejo_mom` | 8880 | 11708 | Varejo MoM (dessaz) |
| `pmc_varejo_yoy` | 8880 | 11709 | Varejo YoY |
| `pmc_varejo_ytd` | 8880 | 11710 | Varejo YTD |
| `pmc_varejo_12m` | 8880 | 11711 | Varejo acumulado 12 meses |
| `pmc_ampliado` | 8881 | 7169 | Ampliado (volume de vendas) |
| `pmc_ampliado_dessaz` | 8881 | 7170 | Ampliado dessazonalizado |
| `pmc_ampliado_mom` | 8881 | 11708 | Ampliado MoM (dessaz) |
| `pmc_ampliado_yoy` | 8881 | 11709 | Ampliado YoY |
| `pmc_ampliado_ytd` | 8881 | 11710 | Ampliado YTD |
| `pmc_ampliado_12m` | 8881 | 11711 | Ampliado acumulado 12 meses |

### PMS (Servicos) - Mensal

| Chave | Tabela | Variavel | Descricao |
|-------|--------|----------|-----------|
| `pms` | 5906 | 7167 | Volume de servicos |
| `pms_dessaz` | 5906 | 7168 | Dessazonalizado |
| `pms_mom` | 5906 | 11623 | MoM (dessaz) |
| `pms_yoy` | 5906 | 11624 | YoY |
| `pms_ytd` | 5906 | 11625 | YTD |
| `pms_12m` | 5906 | 11626 | Acumulado 12 meses |

### PNAD (Emprego) - Mensal (Trimestre Movel)

| Chave | Tabela | Variavel | Descricao |
|-------|--------|----------|-----------|
| `pnad_desocupacao` | 6381 | 4099 | Taxa de desocupacao |

---

## Exemplos de Uso

### Leitura de Dados

```python
import adb

# Leitura simples
df = adb.sidra.read('ipca')

# Com filtro de data
df = adb.sidra.read('ipca', start='2020')

# Multiplos indicadores
df = adb.sidra.read('ipca', 'ipca_12m', 'pib_yoy')
```

### Coleta de Dados

```python
import adb

# Coletar todos os indicadores
adb.sidra.collect()

# Coletar um indicador especifico
adb.sidra.collect('ipca')

# Coletar uma lista de indicadores
adb.sidra.collect(['ipca', 'pib', 'pim'])
```

### Explorando Indicadores

```python
import adb

# Listar todos os indicadores disponiveis
adb.sidra.available()

# Filtrar por frequencia
adb.sidra.available(frequency='monthly')
adb.sidra.available(frequency='quarterly')

# Obter informacoes de um indicador
adb.sidra.info('ipca')

# Verificar status dos arquivos coletados
adb.sidra.status()
```

---

## Arquivos Gerados

Apos a coleta, os dados sao salvos em:

```
data/
└── ibge/
    └── sidra/
        ├── monthly/
        │   ├── ipca.parquet
        │   ├── ipca_12m.parquet
        │   ├── pim.parquet
        │   ├── pmc_varejo.parquet
        │   └── pms.parquet
        └── quarterly/
            ├── pib.parquet
            ├── pib_dessaz.parquet
            └── pnad_desocupacao.parquet
```

Os arquivos sao organizados por frequencia (mensal ou trimestral) e salvos no formato Parquet.
