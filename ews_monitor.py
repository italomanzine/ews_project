import time
import docker
import numpy as np
import logging
import pandas as pd
from pyews.server_interface import ewsRESTInterface as eRI
from pyews.global_vars import settings
from tqdm import tqdm

# Configurações do EWS
settings["IP"] = "http://localhost:2011/"

# Configuração do logging
logging.basicConfig(filename='monitor.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

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
        throughput = (net_input + net_output) / (1024 ** 2) - prev_throughput  # Em MB

        logging.info(f"CPU: {cpu_percent:.2f}%, Memória: {mem_usage:.2f}/{mem_limit:.2f} MB, Throughput: {throughput:.2f}MB")
        return cpu_percent, mem_usage, throughput
    except Exception as e:
        logging.error(f"Erro ao obter estatísticas do contêiner: {e}")
        return None, None, None

# Classe para o algoritmo UCB1
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

# Classe para o algoritmo Força Bruta
class BruteForce:
    def __init__(self, n_arms):
        self.current_arm = -1
        self.n_arms = n_arms

    def select_arm(self):
        self.current_arm = (self.current_arm + 1) % self.n_arms
        return self.current_arm

    def update(self, arm, reward):
        pass  # Não é necessário atualizar nada para o Força Bruta

# Classe para o algoritmo Guloso (Greedy)
class Greedy:
    def __init__(self, n_arms):
        self.n_arms = n_arms
        self.rewards = np.zeros(n_arms)
        self.counts = np.zeros(n_arms)
        self.best_arm = None
        self.initial_sampling = True

    def select_arm(self):
        if self.initial_sampling:
            # Amostra cada braço uma vez
            for arm in range(self.n_arms):
                if self.counts[arm] == 0:
                    return arm
            # Após amostrar todos, selecione o melhor
            self.best_arm = np.argmax(self.rewards / self.counts)
            self.initial_sampling = False
            return self.best_arm
        else:
            # Sempre retorna o melhor braço encontrado
            return self.best_arm

    def update(self, arm, reward):
        self.counts[arm] += 1
        self.rewards[arm] += reward

# Função para calcular a recompensa com múltiplas métricas
def calculate_reward(avg_response_time, throughput, cpu_percent, mem_usage):
    weight_response_time = 0.4
    weight_throughput = 0.3
    weight_cpu = 0.2
    weight_mem = 0.1

    # Normalizar as métricas (evitar divisão por zero)
    normalized_response_time = 1 / avg_response_time if avg_response_time else 0
    normalized_throughput = throughput
    normalized_cpu = 1 / cpu_percent if cpu_percent else 0
    normalized_mem = 1 / mem_usage if mem_usage else 0

    # Calcular a recompensa
    reward = (weight_response_time * normalized_response_time +
              weight_throughput * normalized_throughput +
              weight_cpu * normalized_cpu +
              weight_mem * normalized_mem)

    logging.info(f"Recompensa Calculada: {reward:.4f}")
    return reward

def run_algorithm(algorithm_name, selector_class, configs, total_iterations, docker_client):
    # Inicializar o DataFrame para armazenar as métricas ao longo do tempo
    columns = ['iteration', 'time_in_seconds', 'selected_config_idx', 'reward', 'cpu_percent', 'mem_usage', 'throughput', 'response_time']
    reward_timeseries = pd.DataFrame(columns=columns)

    start_time = time.time()
    throughput = 0

    n_arms = len(configs)
    selector = selector_class(n_arms)
    logging.info(f"Iniciando o algoritmo {algorithm_name}")

    try:
        # Barra de progresso
        with tqdm(total=total_iterations, desc=f"Executando {algorithm_name}") as pbar:
            for iteration in range(1, total_iterations + 1):
                # Selecionar a próxima composição com base no algoritmo escolhido
                arm = selector.select_arm()
                selected_config = configs[arm]
                logging.info(f"Iteração {iteration}: Alterando para a configuração {arm}")
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
                metrics = [iteration, elapsed_time, arm, reward, cpu_percent, mem_usage, throughput, avg_response_time]
                reward_timeseries = reward_timeseries.append(pd.Series(metrics, index=reward_timeseries.columns), ignore_index=True)

                # Salvar o DataFrame parcialmente em CSV a cada iteração
                csv_filename = f'reward_timeseries_{algorithm_name}.csv'
                reward_timeseries.to_csv(csv_filename, index=False)

                # Atualizar o algoritmo (se necessário)
                selector.update(arm, reward)

                # Atualizar a barra de progresso
                pbar.update(1)

                # Estimativa de tempo restante
                pbar.set_postfix({'Tempo Restante': f"{((time.time() - start_time) / iteration) * (total_iterations - iteration):.2f} s"})

                # Intervalo entre as iterações
                time.sleep(5)
    except KeyboardInterrupt:
        logging.info(f"Monitoramento interrompido pelo usuário no algoritmo {algorithm_name}.")
    except Exception as e:
        logging.error(f"Erro inesperado no algoritmo {algorithm_name}: {e}")
    finally:
        logging.info(f"Execução do algoritmo {algorithm_name} concluída.")

def main():
    # Número total de iterações
    total_iterations = 500  # Alterado para 500

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

    # Menu para o usuário escolher o algoritmo
    print("Selecione o algoritmo para selecionar a configuração ideal do EWS:")
    print("1. UCB1 (Upper Confidence Bound)")
    print("2. Força Bruta")
    print("3. Algoritmo Guloso (Greedy)")
    print("4. Rodar todos os métodos")
    choice = input("Digite 1, 2, 3 ou 4: ")

    if choice == '1':
        algorithm = 'UCB1'
        logging.info("Algoritmo selecionado: UCB1")
        run_algorithm(algorithm_name=algorithm, selector_class=UCB1, configs=configs, total_iterations=total_iterations, docker_client=docker_client)
    elif choice == '2':
        algorithm = 'BRUTE-FORCE'
        logging.info("Algoritmo selecionado: Força Bruta")
        run_algorithm(algorithm_name=algorithm, selector_class=BruteForce, configs=configs, total_iterations=total_iterations, docker_client=docker_client)
    elif choice == '3':
        algorithm = 'GREEDY'
        logging.info("Algoritmo selecionado: Guloso")
        run_algorithm(algorithm_name=algorithm, selector_class=Greedy, configs=configs, total_iterations=total_iterations, docker_client=docker_client)
    elif choice == '4':
        # Rodar todos os métodos sequencialmente
        algorithms = [
            ('UCB1', UCB1),
            ('BRUTE-FORCE', BruteForce),
            ('GREEDY', Greedy)
        ]
        for algorithm_name, selector_class in algorithms:
            run_algorithm(algorithm_name=algorithm_name, selector_class=selector_class, configs=configs, total_iterations=total_iterations, docker_client=docker_client)
    else:
        print("Escolha inválida. Por favor, execute o script novamente e selecione uma opção válida.")
        return

if __name__ == "__main__":
    main()
