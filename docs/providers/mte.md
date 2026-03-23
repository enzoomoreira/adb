# MTE - Ministerio do Trabalho e Emprego

Microdados de emprego formal do Novo CAGED (Cadastro Geral de Empregados e Desempregados).

## Visao Geral

| Caracteristica | Valor |
|----------------|-------|
| Fonte | FTP do Ministerio do Trabalho |
| Dados | Admissoes e desligamentos (emprego formal) |
| Periodo | 2020 ate presente (Novo CAGED) |
| Atualizacao | Mensal (aproximadamente 2 meses de atraso) |
| Volume | 500MB a 1GB por mes |

O CAGED registra todas as movimentacoes de emprego formal no Brasil: contratacoes, demissoes, transferencias. Os dados sao liberados mensalmente pelo MTE.

---

## Datasets Disponiveis

| Dataset | Descricao |
|---------|-----------|
| `cagedmov` | Movimentacoes (admissoes e desligamentos) - dataset principal |
| `cagedfor` | Declaracoes fora do prazo |
| `cagedexc` | Exclusoes de movimentacoes |

Para a maioria dos casos de uso, `cagedmov` e suficiente.

---

## Exemplos de Uso

### Coletar Dados

```python
import adb

# Coleta todos os datasets, todos os periodos disponiveis
adb.caged.collect()

# Coleta apenas o dataset principal
adb.caged.collect(indicators='cagedmov')

# Coleta multiplos datasets
adb.caged.collect(indicators=['cagedmov', 'cagedfor'])

# Ajustar velocidade de download (mais threads = mais rapido)
adb.caged.collect(max_workers=8)
```

### Leitura de Microdados

```python
import adb

# Leitura basica (ano e obrigatorio)
df = adb.caged.read(year=2024)                    # Ano inteiro
df = adb.caged.read(year=2024, month=6)           # Junho/2024
df = adb.caged.read(year=2024, uf=35)             # Sao Paulo (codigo IBGE)
df = adb.caged.read(year=2024, dataset='cagedfor') # Outro dataset

# Otimizando consultas (evita carregar tudo na memoria)
df = adb.caged.read(year=2024, columns=['uf', 'saldomovimentacao'])
df = adb.caged.read(year=2024, where="saldomovimentacao > 0")
```

### Agregacoes Pre-Definidas

Para analises comuns, use os metodos de agregacao:

```python
import adb

# Saldo de empregos por mes
df = adb.caged.saldo_mensal(year=2024)
# Retorna: ano, mes, saldo, registros

# Saldo de empregos por UF
df = adb.caged.saldo_por_uf(year=2024)
# Retorna: uf, saldo, registros

# Saldo de empregos por setor economico (CNAE)
df = adb.caged.saldo_por_setor(year=2024)
# Retorna: setor, saldo, registros

# Combinando filtros
df = adb.caged.saldo_mensal(year=2024, uf=35)                  # Saldo mensal de SP
df = adb.caged.saldo_por_setor(year=2024, month=6, uf=33)      # Setor, Jun/2024, RJ
```

### Consultas e Status

```python
import adb

# Periodos disponiveis localmente
periodos = adb.caged.available_periods()
# [(2020, 1), (2020, 2), ..., (2024, 10)]

periodos = adb.caged.available_periods('cagedfor')  # Outro dataset

# Status detalhado dos arquivos
status = adb.caged.get_status()
# DataFrame com: arquivo, subdir, registros, colunas, primeira_data, ultima_data, status

# Informacoes dos datasets
adb.caged.info()           # Todos os datasets
adb.caged.info('cagedmov') # Detalhes de um dataset
```

---

## Arquivos Gerados

Apos a coleta, os dados sao salvos em:

```
data/mte/caged/
    cagedmov_2020-01.parquet
    cagedmov_2020-02.parquet
    ...
    cagedmov_2024-10.parquet
    cagedfor_2020-01.parquet
    ...
```

Cada arquivo contem os microdados de um mes. O formato Parquet permite leituras rapidas e eficientes.

---

## Notas Importantes

### Volume de Dados

O CAGED tem **milhoes de registros por mes**. Sempre use filtros para evitar problemas de memoria:

```python
# Ruim: carrega tudo na memoria
df = adb.caged.read(year=2024)

# Bom: filtra por UF
df = adb.caged.read(year=2024, uf=35)

# Melhor: filtra e seleciona colunas
df = adb.caged.read(year=2024, uf=35, columns=['saldomovimentacao', 'cnae'])
```

### Codigos de UF

Use codigos IBGE para filtrar por estado:

| UF | Codigo |
|----|--------|
| SP | 35 |
| RJ | 33 |
| MG | 31 |
| RS | 43 |
| PR | 41 |

### Coluna de Competencia

A coluna `competenciamov` indica o mes de referencia no formato YYYYMM:
- `202401` = Janeiro de 2024
- `202312` = Dezembro de 2023

Use para filtros SQL:

```python
df = adb.caged.read(year=2024, where="competenciamov >= 202406")  # Junho em diante
```

### Primeira Coleta

A coleta inicial pode demorar bastante devido ao volume de dados. Use `max_workers` para acelerar:

```python
# Download mais rapido (usa mais banda de rede)
adb.caged.collect(max_workers=8)
```

Apos a primeira coleta, apenas meses novos sao baixados (atualizacao incremental).
