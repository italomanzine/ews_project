import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import os

# Configurar estilo para gráficos bonitos
sns.set_theme(style="whitegrid")
plt.rcParams['figure.figsize'] = (12, 8)

# Dicionário com os algoritmos e suas respectivas informações
algorithms = {
    'UCB1': {
        'csv_file': 'reward_timeseries_UCB1.csv',
        'output_dir': 'charts/ubc1'
    },
    'BRUTE-FORCE': {
        'csv_file': 'reward_timeseries_BRUTE-FORCE.csv',
        'output_dir': 'charts/brute_force'
    }
}

# Função para gerar gráficos
def plot_metrics(df, output_dir):
    # Certificar-se de que o diretório de saída existe
    os.makedirs(output_dir, exist_ok=True)

    metrics = {
        'reward': ('Recompensa ao Longo do Tempo', 'Recompensa', 'blue'),
        'cpu_percent': ('Uso de CPU ao Longo do Tempo', 'CPU (%)', 'green'),
        'mem_usage': ('Uso de Memória ao Longo do Tempo', 'Memória (MB)', 'orange'),
        'throughput': ('Throughput ao Longo do Tempo', 'Throughput (MB/s)', 'red'),
        'response_time': ('Tempo de Resposta ao Longo do Tempo', 'Tempo de Resposta (ms)', 'purple'),
        'selected_config_idx': ('Configuração Selecionada ao Longo do Tempo', 'Índice da Configuração Selecionada', 'brown')
    }

    for metric, (title, ylabel, color) in metrics.items():
        plt.figure(figsize=(12, 8))
        if metric == 'selected_config_idx':
            sns.scatterplot(x='time_in_minutes', y=metric, data=df, color=color, s=50)
        else:
            sns.lineplot(x='time_in_minutes', y=metric, data=df, color=color)
            # Adicionar linha de tendência tracejada
            z = np.polyfit(df['time_in_minutes'], df[metric], 1)
            p = np.poly1d(z)
            plt.plot(df['time_in_minutes'], p(df['time_in_minutes']), linestyle='--', color='black', alpha=0.7)
        plt.title(title)
        plt.xlabel('Tempo (minutos)')
        plt.ylabel(ylabel)
        plt.tight_layout()
        # Salvar o gráfico no diretório específico
        plt.savefig(os.path.join(output_dir, f'{metric}_ews.png'))
        plt.close()

# Loop para processar cada algoritmo
for algorithm_name, data in algorithms.items():
    csv_file = data['csv_file']
    output_dir = data['output_dir']
    # Verificar se o arquivo CSV existe
    if os.path.exists(csv_file):
        print(f"Processando dados para {algorithm_name}...")
        df = pd.read_csv(csv_file)
        # Converter o tempo em segundos para minutos para melhor visualização
        df['time_in_minutes'] = df['time_in_seconds'] / 60
        # Gerar os gráficos
        plot_metrics(df, output_dir)
    else:
        print(f"Arquivo CSV não encontrado: {csv_file}. Pulando {algorithm_name}.")
