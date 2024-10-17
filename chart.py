import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# Configurar estilo para gráficos bonitos
sns.set_theme(style="whitegrid")
plt.rcParams['figure.figsize'] = (12, 8)

# Ler o CSV com os dados das métricas
csv_file = 'reward_timeseries.csv'
df = pd.read_csv(csv_file)

# Converter o tempo em segundos para minutos para melhor visualização
df['time_in_minutes'] = df['time_in_seconds'] / 60

# Função para gerar gráficos
def plot_metrics(df):
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
        plt.savefig(f'charts/{metric}_ews.png')
        plt.close()

# Gerar os gráficos
plot_metrics(df)