# IPEA

O IPEA (Instituto de Pesquisa Economica Aplicada) fornece series temporais agregadas via IPEADATA. O foco principal e em dados de emprego (CAGED, PNAD).

## Por que usar IPEA?

- Dados agregados prontos para uso (saldo, admissoes, desligamentos)
- Nao requer processamento de microdados
- Complementa os dados do CAGED com visao macro
- Inclui taxa de desemprego da PNAD Continua

---

## Indicadores Disponiveis

### Emprego (CAGED Agregado) - Mensal

| Chave | Codigo IPEADATA | Nome | Unidade |
|-------|-----------------|------|---------|
| `caged_saldo` | CAGED12_SALDON12 | Saldo do Novo CAGED | pessoas |
| `caged_admissoes` | CAGED12_ADMISN12 | Admissoes CAGED | pessoas |
| `caged_desligamentos` | CAGED12_DESLIGN12 | Desligamentos CAGED | pessoas |

### Desemprego (PNAD) - Mensal

| Chave | Codigo IPEADATA | Nome | Unidade |
|-------|-----------------|------|---------|
| `taxa_desemprego` | PNADC12_TDESOC12 | Taxa de Desocupacao | % |

---

## Exemplos de Uso

### Leitura de Dados

```python
import adb

# Leitura simples
df = adb.ipea.read('caged_saldo')

# Com filtro de data
df = adb.ipea.read('caged_saldo', start='2020')

# Multiplos indicadores
df = adb.ipea.read('caged_saldo', 'taxa_desemprego')
```

### Coleta de Dados

```python
import adb

# Coletar todos os indicadores
adb.ipea.collect()

# Coletar um indicador especifico
adb.ipea.collect('caged_saldo')

# Coletar uma lista de indicadores
adb.ipea.collect(['caged_saldo', 'caged_admissoes', 'taxa_desemprego'])
```

### Explorando Indicadores

```python
import adb

# Listar todos os indicadores disponiveis
adb.ipea.available()

# Filtrar por frequencia
adb.ipea.available(frequency='monthly')

# Obter informacoes de um indicador
adb.ipea.info('caged_saldo')

# Verificar status dos arquivos coletados
adb.ipea.get_status()
```

---

## Arquivos Gerados

Apos a coleta, os dados sao salvos em:

```
data/
└── ipea/
    └── monthly/
        ├── caged_saldo.parquet
        ├── caged_admissoes.parquet
        ├── caged_desligamentos.parquet
        └── taxa_desemprego.parquet
```

Os arquivos sao salvos no formato Parquet, organizados por frequencia.
