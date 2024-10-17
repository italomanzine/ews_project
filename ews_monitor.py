# ews_monitor.py

import time
import docker
import numpy as np
import logging
from pyews.server_interface import ewsRESTInterface as eRI
from pyews.global_vars import settings
import pandas as pd



# Configurações do EWS
settings["IP"] = "http://localhost:2011/"

# Configuração do logging
logging.basicConfig(filename='monitor.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Não inicialize o servidor novamente, pois ele já está rodando no Docker
configurations = eRI.get_all_configs()

# Função auxiliar para calcular uso de CPU
def calculate_cpu_percent(stats):
    try:
        cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage'] - stats['precpu_stats']['cpu_usage']['total_usage']
        system_delta = stats['cpu_stats']['system_cpu_usage'] - stats['precpu_stats']['system_cpu_usage']
        num_cpus = stats['cpu_stats'].get('online_cpus', 1)
        if system_delta > 0.0:
            cpu_percent = (cpu_delta / system_delta) * num_cpus * 100.0
        else:
            cpu_percent = 0.0
        return cpu_percent
    except KeyError as e:
        logging.error(f"Erro ao calcular uso de CPU: {e}")
        return 0.0

# Função para obter utilização de recursos do contêiner Docker
def get_container_stats(docker_client, prev_throughput, container_name='ews'):
    try:
        container = docker_client.containers.get(container_name)
        stats = container.stats(stream=False)

        # CPU
        cpu_percent = calculate_cpu_percent(stats)

        # Memória (Exibindo em MB)
        mem_usage = stats['memory_stats']['usage'] / (1024 ** 2)  # Convertendo para MB
        mem_limit = stats['memory_stats']['limit'] / (1024 ** 2)  # Convertendo para MB

        # Net I/O
        net_io = stats['networks']
        net_input = sum([net['rx_bytes'] for net in net_io.values()])
        net_output = sum([net['tx_bytes'] for net in net_io.values()])
        throughput = (net_input + net_output) / (1024 ** 2) - prev_throughput # Em MB

        logging.info(f"CPU: {cpu_percent:.2f}%, Memória: {mem_usage:.2f}/{mem_limit:.2f} MB, Throughput: {throughput:.2f}MB")
        return cpu_percent, mem_usage, throughput
    except Exception as e:
        logging.error(f"Erro ao obter estatísticas do contêiner: {e}")
        return None, None, None

# Trocar o UCB1 pelo Força Bruta
# Classe para o algoritmo UCB1 (Upper Confidence Bound)
# Problema Multi-Armed Bandit
class UCB1:
    def __init__(self, n_arms):
        self.n = np.zeros(n_arms)  # Contador de seleções de cada braço
        self.value = np.zeros(n_arms)  # Valor estimado de cada braço
        self.total_count = 0  # Total de seleções

    def select_arm(self):
        self.total_count += 1
        # Se algum braço ainda não foi selecionado, selecione-o
        for arm in range(len(self.n)):
            if self.n[arm] == 0:
                return arm
        # Caso contrário, use a fórmula UCB1
        ucb_values = self.value + np.sqrt((2 * np.log(self.total_count)) / (self.n + 1e-5))
        return np.argmax(ucb_values)

    def update(self, arm, reward):
        self.n[arm] += 1
        n = self.n[arm]
        value = self.value[arm]
        # Atualização incremental da média
        self.value[arm] = ((n - 1) / n) * value + (1 / n) * reward

# Função para calcular a recompensa com múltiplas métricas
def calculate_reward(avg_response_time, throughput, cpu_percent, mem_usage):
    weight_response_time = 0.4
    weight_throughput = 0.3
    weight_cpu = 0.2
    weight_mem = 0.1

    # Normalizar as métricas (ajuste os limites conforme necessário)
    normalized_response_time = 1 / avg_response_time 
    normalized_throughput = throughput
    normalized_cpu = 1 / cpu_percent
    normalized_mem = 1 / mem_usage

    # Calcular a recompensa
    reward = (weight_response_time * normalized_response_time +
              weight_throughput * normalized_throughput +
              weight_cpu * normalized_cpu +
              weight_mem * normalized_mem)

    logging.info(f"Recompensa Calculada: {reward:.4f}")
    return reward

def main():
    # Inicializar o cliente Docker
    docker_client = docker.from_env()

    # Obter todas as composições disponíveis
    configs = eRI.get_all_configs()
    if not configs:
        logging.error("Nenhuma configuração disponível. Verifique se o EWS está funcionando corretamente.")
        return

    logging.info("Configurações disponíveis:")
    for idx, config in enumerate(configs):
        logging.info(f"ID: {idx}, Descrição: {config.original_json}")

    # Obter a composição atual
    current_config = eRI.get_config()
    if not current_config:
        logging.error("Não foi possível obter a configuração atual.")
    else:
        logging.info(f"Configuração Atual: {current_config.original_json}")

    # Inicializar o algoritmo Upper Confidence Bound (UCB1) 
    n_arms = len(configs)
    ucb1 = UCB1(n_arms)

    # Inicializar o DataFrame para armazenar as métricas ao longo do tempo
    columns = ['time_in_seconds', 'selected_config_idx', 'reward', 'cpu_percent', 'mem_usage', 'throughput', 'response_time']
    reward_timeseries = pd.DataFrame(columns=columns)

    start_time = time.time()

    # Ciclo principal de monitoramento e adaptação
    throughput = 0
    try:
        while True:
            # Selecionar a próxima composição
            arm = ucb1.select_arm()
            selected_config = configs[arm]
            logging.info(f"Alterando para a configuração: {selected_config.original_json}")
            try:
                eRI.change_configuration(selected_config)
            except Exception as e:
                logging.error(f"Falha ao alterar a configuração: {e}")
                continue

            # Tempo para a composição estabilizar
            time.sleep(5)

            # Coletar métricas
            perception = eRI.get_perception()
            avg_response_time = perception.metric_dict.get('response_time').average_value() if perception and 'response_time' in perception.metric_dict else None
            logging.info(f"Avg Response Time: {avg_response_time}")
            cpu_percent, mem_usage, throughput = get_container_stats(docker_client=docker_client, prev_throughput=throughput)

            # Definir a recompensa com base em múltiplas métricas
            if avg_response_time and throughput and cpu_percent is not None and mem_usage is not None:
                reward = calculate_reward(avg_response_time, throughput, cpu_percent, mem_usage)
            else:
                logging.info(f"Alguma métrica não está disponível. Ignorando esta iteração. Verifique os logs para mais detalhes. Avg Response Time: {avg_response_time}, Throughput: {throughput}, CPU: {cpu_percent}, Memória: {mem_usage}")
                reward = 0

            # Adicionar as métricas ao DataFrame
            elapsed_time = time.time() - start_time 
            metrics = [elapsed_time, arm, reward, cpu_percent, mem_usage, throughput, avg_response_time]
            reward_timeseries = reward_timeseries.append(pd.Series(metrics, index=reward_timeseries.columns), ignore_index=True)

            # Salvar o DataFrame parcialmente em CSV a cada iteração
            reward_timeseries.to_csv('reward_timeseries.csv', index=False)

            # Atualizar o algoritmo UCB1
            ucb1.update(arm, reward)

            # Intervalo entre as iterações
            time.sleep(5)
    except KeyboardInterrupt:
        logging.info("Monitoramento interrompido pelo usuário.")

if __name__ == "__main__":
    main()