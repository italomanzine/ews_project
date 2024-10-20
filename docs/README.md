
# Projeto de Monitoramento do EWS

Este projeto envolve o monitoramento de um **Emergent Web Server (EWS)** rodando dentro de um contêiner Docker usando um script Python. O script coleta várias métricas, como uso de CPU, uso de memória, throughput e tempo de resposta, e aplica diferentes algoritmos para selecionar a configuração ideal para o EWS. As métricas coletadas são salvas em arquivos CSV e podem ser visualizadas usando os scripts de plotagem fornecidos.

## Índice

- [Pré-requisitos](#pré-requisitos)
- [Estrutura do Projeto](#estrutura-do-projeto)
- [Instruções de Configuração](#instruções-de-configuração)
  - [1. Clonar o Repositório](#1-clonar-o-repositório)
  - [2. Instalar o Docker](#2-instalar-o-docker)
  - [3. Configurar o Ambiente Python](#3-configurar-o-ambiente-python)
- [Executando o Contêiner Docker do EWS](#executando-o-contêiner-docker-do-ews)
  - [1. Baixar a Imagem Docker do EWS](#1-baixar-a-imagem-docker-do-ews)
  - [2. Executar o Contêiner Docker do EWS](#2-executar-o-contêiner-docker-do-ews)
  - [3. Iniciar o EWS Dentro do Contêiner](#3-iniciar-o-ews-dentro-do-contêiner)
  - [4. Gerar Carga no EWS](#4-gerar-carga-no-ews)
- [Executando o Script Python de Monitoramento](#executando-o-script-python-de-monitoramento)
  - [1. Instalar Dependências Python](#1-instalar-dependências-python)
  - [2. Configurar o Script](#2-configurar-o-script)
  - [3. Executar o Script de Monitoramento](#3-executar-o-script-de-monitoramento)
    - [Selecionando o Algoritmo](#selecionando-o-algoritmo)
- [Gerando e Visualizando Métricas](#gerando-e-visualizando-métricas)
  - [Executar o Script de Plotagem](#executar-o-script-de-plotagem)
- [Resolução de Problemas](#resolução-de-problemas)
- [Conclusão](#conclusão)

## Pré-requisitos

Antes de começar, certifique-se de ter o seguinte instalado em seu sistema:

- **Docker**: Para executar o EWS em um contêiner.
- **Python 3.7 ou superior**: Para executar os scripts de monitoramento.
- **pip**: Instalador de pacotes Python.
- **Git**: Para clonar o repositório (opcional).

## Estrutura do Projeto

```
ews_project/
├── ews_monitor.py               # Script principal de monitoramento
├── chart.py                     # Script para gerar gráficos a partir das métricas
├── requirements.txt             # Dependências Python
├── reward_timeseries_UCB1.csv             # Métricas do UCB1
├── reward_timeseries_BRUTE-FORCE.csv      # Métricas do Força Bruta
├── reward_timeseries_GREEDY.csv           # Métricas do Guloso
└── charts/                      # Diretório onde os gráficos gerados são salvos
    ├── ubc1/                    # Gráficos do algoritmo UCB1
    │   ├── reward_ews.png
    │   ├── cpu_percent_ews.png
    │   ├── mem_usage_ews.png
    │   ├── throughput_ews.png
    │   ├── response_time_ews.png
    │   └── selected_config_idx_ews.png
    ├── brute_force/             # Gráficos do algoritmo Força Bruta
    │   └── ...
    └── greedy/                  # Gráficos do algoritmo Guloso
        └── ...
```

## Instruções de Configuração

### 1. Clonar o Repositório

```bash
git clone https://github.com/italomanzine/ews_project.git
cd ews_project
```

*Se você não tem o Git instalado, pode simplesmente criar um diretório chamado `ews_project` e colocar os scripts fornecidos dentro dele.*

### 2. Instalar o Docker

Siga o guia de instalação oficial do Docker para o seu sistema operacional: [Obter o Docker](https://docs.docker.com/get-docker/)

Verifique a instalação executando:

```bash
docker --version
```

### 3. Configurar o Ambiente Python

É recomendado usar um ambiente virtual para gerenciar as dependências Python.

#### Criar um Ambiente Virtual

```bash
python3 -m venv ews_env
```

#### Ativar o Ambiente Virtual

- **No Linux/MacOS:**

  ```bash
  source ews_env/bin/activate
  ```
- **No Windows (Prompt de Comando):**

  ```cmd
  ews_env\Scripts\activate
  ```
- **No Windows (PowerShell):**

  ```powershell
  .\ews_env\Scripts\Activate.ps1
  ```

## Executando o Contêiner Docker do EWS

### 1. Baixar a Imagem Docker do EWS

```bash
docker pull robertovrf/ews:1.0
```

### 2. Executar o Contêiner Docker do EWS

Execute o contêiner com mapeamento de portas e vinculação de volume para acessar os logs:

```bash
docker run --name ews -p 2011:2011 -p 2012:2012 -v ~/ews_logs:/home/dana/emergent_web_server/pal -d robertovrf/ews:1.0
```

- `--name ews`: Nomeia o contêiner como `ews` para fácil referência.
- `-p 2011:2011 -p 2012:2012`: Mapeia as portas do contêiner para o host.
- `-v ~/ews_logs:/home/dana/emergent_web_server/pal`: Vincula o diretório de logs do contêiner a um diretório no host.

*Nota:* Ajuste o caminho do volume (`/home/dana/emergent_web_server/pal`) se sua imagem Docker usar um caminho diferente para os logs.

### 3. Iniciar o EWS Dentro do Contêiner

Acesse o shell do contêiner:

```bash
docker exec -it ews bash
```

Dentro do contêiner, inicie o EWS:

```bash
cd emergent_web_server/pal/
dana -sp ../repository InteractiveEmergentSys.o
```

Aguarde até ver o prompt `sys>`, indicando que o EWS está em execução.

### 4. Gerar Carga no EWS

Abra outro terminal e execute:

```bash
docker exec -it ews bash
```

Dentro do contêiner:

```bash
cd emergent_web_server/ws_clients/
dana ClientTextPattern.o
```

Isso gerará carga no EWS, simulando requisições de clientes.

## Executando o Script Python de Monitoramento

### 1. Instalar Dependências Python

Com o ambiente virtual ativado, instale os pacotes necessários:

```bash
pip install -r requirements.txt
```

**Conteúdo do `requirements.txt`:**

```
requests
docker
numpy
pandas
matplotlib
seaborn
pyews
tqdm
```

*Nota:* Certifique-se de que `pyews` está instalado. Se não estiver disponível via pip, você pode precisar instalá-lo manualmente.

### 2. Configurar o Script

Certifique-se de que o `settings["IP"]` no `ews_monitor.py` aponta para o endereço correto:

```python
settings["IP"] = "http://localhost:2011/"
```

Ajuste o IP e a porta se o seu EWS estiver rodando em um endereço ou porta diferente.

### 3. Executar o Script de Monitoramento

```bash
python ews_monitor.py
```

#### Selecionando o Algoritmo

Ao executar o script, você será apresentado com um menu para selecionar o algoritmo a ser utilizado para selecionar a configuração ideal do EWS:

```
Selecione o algoritmo para selecionar a configuração ideal do EWS:
1. UCB1 (Upper Confidence Bound)
2. Força Bruta
3. Algoritmo Guloso (Greedy)
4. Rodar todos os métodos
Digite 1, 2, 3 ou 4:
```

As opções são:

- **1. UCB1 (Upper Confidence Bound):** Um algoritmo de multi-armed bandit que equilibra exploração e exploração.
- **2. Força Bruta:** Percorre todas as configurações disponíveis de forma sequencial.
- **3. Algoritmo Guloso (Greedy):** Testa cada configuração uma vez e então continua com a melhor encontrada.
- **4. Rodar todos os métodos:** Executa todos os algoritmos sequencialmente.

Após selecionar a opção desejada, o script iniciará a execução para um número fixo de iterações (500). Durante a execução, uma barra de progresso será exibida, mostrando o andamento e o tempo estimado restante.

As métricas coletadas serão salvas em arquivos CSV com nomes correspondentes ao algoritmo utilizado, por exemplo:

- `reward_timeseries_UCB1.csv`
- `reward_timeseries_BRUTE-FORCE.csv`
- `reward_timeseries_GREEDY.csv`

## Gerando e Visualizando Métricas

Após executar o script de monitoramento e coletar métricas, você pode gerar gráficos para visualizar os dados.

### Executar o Script de Plotagem

```bash
python chart.py
```

**O que o Script Faz:**

- Lê os arquivos CSV gerados para cada algoritmo.
- Gera gráficos de linha para as seguintes métricas ao longo do tempo, incluindo o nome do algoritmo no título:

  - Recompensa
  - Uso de CPU (%)
  - Uso de Memória (MB)
  - Throughput (MB/s)
  - Tempo de Resposta (ms)
- Gera um gráfico de dispersão para o índice da configuração selecionada ao longo do tempo.
- Salva os gráficos nos diretórios correspondentes em `charts/`.

**Estrutura dos Gráficos Gerados:**

- `charts/ubc1/`
  - Gráficos gerados para o algoritmo UCB1.
- `charts/brute_force/`
  - Gráficos gerados para o algoritmo Força Bruta.
- `charts/greedy/`
  - Gráficos gerados para o algoritmo Guloso.

Cada gráfico terá um título que inclui o nome do algoritmo, por exemplo:

- **"Uso de CPU ao Longo do Tempo - UCB1"**

## Resolução de Problemas

- **Endpoints do EWS Não Acessíveis:**

  Se você receber um erro `404 Resource Not Found` ao acessar endpoints do EWS, certifique-se de que:

  - O EWS está rodando dentro do contêiner Docker.
  - A API REST está habilitada e configurada corretamente.
  - As portas corretas estão expostas e mapeadas no comando de execução do Docker.
- **Contêiner Docker Não Encontrado:**

  Se você receber um erro de que o contêiner `ews` não foi encontrado, verifique se:

  - O contêiner está em execução (`docker ps`).
  - O nome do contêiner corresponde (`docker ps --format '{{.Names}}'`).
- **Problemas de Permissão com Logs:**

  Certifique-se de que o diretório `~/ews_logs` tem as permissões corretas para leitura e escrita dos logs.
- **Dependências Ausentes:**

  Se encontrar `ModuleNotFoundError`, certifique-se de que todas as dependências estão instaladas em seu ambiente virtual.
- **Tempo de Execução Prolongado:**

  O tempo total de execução pode ser longo, especialmente ao rodar todos os algoritmos. Você pode ajustar o número de iterações no script `ews_monitor.py` modificando a variável `total_iterations`.

## Conclusão

Seguindo os passos descritos neste guia, você deverá ser capaz de configurar o contêiner Docker do EWS, executar o script Python de monitoramento com diferentes algoritmos, coletar métricas de desempenho e visualizar os dados através dos gráficos gerados. Este projeto fornece uma base para monitorar e otimizar servidores web usando algoritmos adaptativos.

Sinta-se à vontade para explorar e modificar os scripts para atender às suas necessidades ou para implementar funcionalidades e análises adicionais.

---

**Nota:** Sempre certifique-se de que seu ambiente (contêineres Docker, versões do Python, dependências) corresponde aos requisitos especificados neste guia. Se encontrar quaisquer problemas não cobertos aqui, considere consultar a documentação do Docker, Python ou das bibliotecas específicas usadas nos scripts.
