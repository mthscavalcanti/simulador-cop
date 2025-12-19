# 🎯 Otimizador de Videomonitoramento - COP Recife

Sistema de otimização inteligente para posicionamento de câmeras de segurança em Recife, utilizando **Índice de Priorização Espacial (IPE)** e análise de cobertura estratégica baseada em dados geoespaciais e indicadores urbanos.

<div align="center">
  
  [![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
  [![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-FF4B4B.svg)](https://streamlit.io)
  [![License](https://img.shields.io/badge/License-Proprietário-red.svg)]()
  
</div>

---

## 📋 Índice

- [Sobre o Projeto](#-sobre-o-projeto)
- [Principais Funcionalidades](#-principais-funcionalidades)
- [Tecnologias Utilizadas](#-tecnologias-utilizadas)
- [Estrutura do Projeto](#-estrutura-do-projeto)
- [Instalação](#-instalação)
- [Uso](#-uso)
- [Metodologia](#-metodologia)
- [Arquivos de Dados](#-arquivos-de-dados)
- [Configuração](#-configuração)
- [Contribuindo](#-contribuindo)
- [Autores](#-autores)
- [Licença](#-licença)

---

## 🎯 Sobre o Projeto

O **Otimizador de Videomonitoramento** é uma ferramenta desenvolvida pela IGMA Tech para auxiliar o Centro de Operações (COP) de Recife na tomada de decisão sobre o posicionamento estratégico de câmeras de segurança na cidade.

### Problema

Como distribuir câmeras de segurança de forma otimizada considerando:
- Priorização de áreas críticas (segurança, mobilidade, lazer/cultura, comércio)
- Restrições de distância mínima entre câmeras
- Maximização da cobertura com recursos limitados
- Integração com equipamentos existentes
- Análise de pontos de risco (alagamentos, sinistros, crimes)

### Solução

Sistema de otimização que utiliza algoritmos de cobertura geográfica e cálculo de IPE (Índice de Prioridade) para selecionar os melhores pontos para instalação de câmeras, considerando múltiplos eixos estratégicos e aplicando a **regra dos 50%** para cobertura ajustada por logradouro.

---

## ✨ Principais Funcionalidades

### 🗺️ Visualização Geoespacial
- Mapa interativo com limites de bairros de Recife
- Visualização de pontos selecionados (obrigatórios e otimizados via IPE)
- Máscara de foco na área de Recife

### 🎛️ Controles de Otimização
- **Modo de Limite**: Cobertura Alvo (%) ou Quantidade de Câmeras
- **Distância Mínima**: Controle de espaçamento entre câmeras (200-500m)
- **Pesos dos Eixos IPE**: Ajuste personalizado (Segurança, LCT, Comercial, Mobilidade)
- **Inclusão de Câmeras RED**: Pontos de relógios digitais (concessão)

### 📊 Análise de Cobertura
- Cobertura por eixo estratégico (Segurança, LCT, Comercial, Mobilidade)
- Cobertura de pontos de alagamento
- Cobertura de sinistros de trânsito
- Cobertura de CVP (Crimes Violentos contra o Patrimônio)
- Cobertura de vias prioritárias
- Proximidade a equipamentos públicos

### 🧮 Algoritmo Inteligente
- Seleção por ordem de IPE decrescente
- Restrições de distância mínima entre câmeras
- **Regra dos 50%**: Logradouros com ≥50% de IPE coberto contam como 100%
- Distribuição de câmeras: 50% dos pontos = 3 câm, 30% = 2 câm, 20% = 1 câm
- Pontos mínimos obrigatórios prioritários

### 📥 Exportação
- Download de CSV com todos os cruzamentos e selecionados
- Dados formatados com coordenadas e IPE

---

## 🛠️ Tecnologias Utilizadas

### Core
- **Python 3.8+** - Linguagem principal
- **Streamlit 1.28+** - Framework de interface web
- **Pandas** - Manipulação de dados
- **NumPy** - Operações numéricas

### Geoespacial
- **Folium** - Mapas interativos
- **Shapely** - Operações geométricas
- **streamlit-folium** - Integração Folium + Streamlit

### Análise de Dados
- **Openpyxl** - Leitura de arquivos Excel
- **JSON** - Processamento de GeoJSON

---

## 📁 Estrutura do Projeto

```
otimizador-videomonitoramento/
│
├── simulador.py                 # Aplicação principal
├── README.md                    # Este arquivo
├── requirements.txt             # Dependências Python
│
├── data/                        # Dados de entrada
│   ├── Cruzamentos.xlsx         # Cruzamentos e logradouros
│   ├── Prioridades.xlsx         # Pontos mínimos obrigatórios
│   ├── Equipamentos.xlsx        # Equipamentos públicos existentes
│   ├── bairros.geojson          # Limites dos bairros de Recife
│   ├── Alagamentos.xlsx         # Pontos de alagamento
│   ├── Sinistros.xlsx           # Sinistros de trânsito por logradouro
│   ├── Vias Prioritarias.xlsx   # Vias prioritárias
│   ├── CVP.xlsx                 # Crimes Violentos contra Patrimônio
│   └── cop_aquila.png           # Logo do sistema
│
└── .gitignore                   # Arquivos ignorados pelo Git
```

---

## 🚀 Instalação

### Pré-requisitos

- Python 3.8 ou superior
- pip (gerenciador de pacotes Python)
- Git

### Passo a Passo

1. **Clone o repositório**
```bash
git clone https://github.com/seu-usuario/otimizador-videomonitoramento.git
cd otimizador-videomonitoramento
```

2. **Crie um ambiente virtual (recomendado)**
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

3. **Instale as dependências**
```bash
pip install -r requirements.txt
```

4. **Prepare os dados**

Certifique-se de que a pasta `data/` contém todos os arquivos necessários:
- Cruzamentos.xlsx
- Prioridades.xlsx
- Equipamentos.xlsx
- bairros.geojson
- Alagamentos.xlsx
- Sinistros.xlsx
- Vias Prioritarias.xlsx
- CVP.xlsx
- cop_aquila.png

---

## 💻 Uso

### Execução Local

```bash
streamlit run simulador.py
```

A aplicação será aberta automaticamente no navegador em `http://localhost:8501`

### Fluxo de Trabalho

1. **Carregamento Automático**: Os dados são carregados automaticamente ao iniciar a aplicação

2. **Configuração dos Parâmetros** (Sidebar):
   - Escolha o modo de limite (Cobertura Alvo ou Quantidade de Câmeras)
   - Ajuste a distância mínima entre câmeras
   - Decida se inclui câmeras de relógios digitais (RED)
   - Configure os pesos dos eixos IPE

3. **Visualização dos Resultados**:
   - Mapa com pontos selecionados
   - Estatísticas de cobertura por eixo
   - Análise de alvos estratégicos (alagamentos, sinistros, CVP, vias)
   - Equipamentos públicos próximos

4. **Exportação**:
   - Download do CSV com todos os cruzamentos e selecionados

---

## 🧮 Metodologia

### Cálculo do IPE (Índice de Prioridade)

O IPE de cada cruzamento é calculado como:

```
IPE_cruzamento = IPE_log1 + IPE_log2

onde:
IPE_log = w_seg × SEG + w_lct × LCT + w_com × COM + w_mob × MOB
```

**Eixos Estratégicos:**
- **SEG**: Segurança
- **LCT**: Lazer, Cultura e Turismo
- **COM**: Comercial
- **MOB**: Mobilidade

### Algoritmo de Otimização

1. **Pontos Mínimos**: Posiciona câmeras em pontos obrigatórios primeiro
2. **Seleção por IPE**: Ordena cruzamentos por IPE decrescente
3. **Restrição de Distância**: Aplica distância mínima entre câmeras do mesmo logradouro
4. **Cálculo de Cobertura**: Raio de 50m para cada câmera
5. **Regra dos 15%**: Logradouros com ≥50% de IPE coberto contam como 100% cobertos
6. **Distribuição de Câmeras**: 
   - Primeiros 50% dos pontos: 3 câmeras
   - Próximos 30% dos pontos: 2 câmeras
   - Últimos 20% dos pontos: 1 câmera

### Cobertura Ajustada

A cobertura ajustada considera que um logradouro está efetivamente coberto quando ≥50% do seu IPE total está monitorado:

```python
se cobertura_logradouro >= 50%:
    cobertura_ajustada = 100%
senão:
    cobertura_ajustada = cobertura_proporcional
```

---

## 📊 Arquivos de Dados

### Cruzamentos.xlsx
**Abas necessárias:**
- `MODELO`: Ranking IPE dos logradouros (colunas: RANKING_IPE, cod_log, nome, seg, lct, com, mob)
- `cruzamentos_100%`: Cruzamentos da cidade (colunas: cod_log1, nome_log1, cod_log2, nome_log2, latitude, longitude)

### Prioridades.xlsx
Pontos mínimos obrigatórios
- **Colunas**: tipo, logradouro, latitude, longitude, prioridade, cameras
- **Tipo RED**: Pontos de relógios digitais (concessão) com 1 câmera sem custo

### Equipamentos.xlsx
Equipamentos públicos existentes
- **Colunas**: EIXO, TIPO DE EQUIPAMENTO, LOG_CORRIGIDO, LATITUDE COM PONTO, LONGITUDE COM PONTO, PESO

### bairros.geojson
Limites geográficos dos bairros de Recife
- **Formato**: GeoJSON com features contendo geometrias dos polígonos

### Alagamentos.xlsx
Pontos de alagamento mapeados
- **Colunas**: id, nome/local, latitude, longitude

### Sinistros.xlsx
Sinistros de trânsito por logradouro
- **Colunas**: id, logradouro, qtd (quantidade de sinistros)

### Vias Prioritarias.xlsx
Vias prioritárias para monitoramento
- **Colunas**: id, logradouro, prioridade (1-5, sendo 1 maior prioridade)

### CVP.xlsx
Crimes Violentos contra o Patrimônio
- **Colunas**: id, logradouro, cvp (quantidade de crimes)

---

## ⚙️ Configuração

### Parâmetros Fixos

```python
# Caminhos
DATA_DIR = Path("data")

# Raios de cobertura
RAIO_COBERTURA_CAMERA = 50  # metros
RAIO_EQUIPAMENTO = 100  # metros

# Câmeras RED
CAMERAS_RED = 107  # Quantidade fixa de câmeras de relógios digitais
```

### Parâmetros Ajustáveis (UI)

- **Distância Mínima**: 200-500m (padrão: 300m)
- **Pesos IPE**: 0-100% para cada eixo (padrão: Seg=15%, LCT=30%, Com=15%, Mob=40%)
- **Limite de Câmeras**: 250-4032 (ajustado conforme inclusão de RED)
- **Cobertura Alvo**: 0-100% (padrão: 80%)

---

## 👥 Autores

**IGMA Tech**
- Desenvolvimento e implementação do algoritmo de otimização
- Interface de usuário e visualizações
- Análise de dados urbanos

**COP Recife**
- Especificação de requisitos
- Dados e informações estratégicas
- Validação e testes

---

## 📄 Licença

Este projeto é proprietário e confidencial. 

**© 2025 IGMA Tech. Todos os direitos reservados.**

O uso, distribuição ou reprodução não autorizados são estritamente proibidos.

---

<div align="center">
  
  [⬆️ Voltar ao topo](#-otimizador-de-videomonitoramento---cop-recife)
  
</div>