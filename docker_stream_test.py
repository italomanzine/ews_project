# DESCONSIDERAR ESSE ARQUIVO - FOI USADO PARA TESTES INICIAIS

import docker

def get_container_metrics(container_name):
    client = docker.from_env()

    try:
        container = client.containers.get(container_name)
        stats = container.stats(stream=False)

        # Extraindo métricas principais
        cpu_percentage = calculate_cpu_percentage(stats)
        memory_usage = stats['memory_stats']['usage']
        memory_limit = stats['memory_stats']['limit']
        memory_percentage = (memory_usage / memory_limit) * 100 if memory_limit > 0 else 0
        net_io = stats['networks']
        block_io = stats['blkio_stats']['io_service_bytes_recursive']
        pids = stats['pids_stats']['current']

        # Calculando o tráfego de rede
        net_input = sum([net['rx_bytes'] for net in net_io.values()])
        net_output = sum([net['tx_bytes'] for net in net_io.values()])

        # Mostrando as métricas
        print(f"Container: {container_name}")
        print(f"CPU %: {cpu_percentage:.2f}%")
        print(f"MEM USAGE / LIMIT: {memory_usage / (1024 ** 2):.2f}MB / {memory_limit / (1024 ** 2):.2f}MB")
        print(f"MEM %: {memory_percentage:.2f}%")
        print(f"NET I/O: {net_input / (1024 ** 2):.2f}MB / {net_output / (1024 ** 2):.2f}MB")
        print(f"BLOCK I/O: {block_io}")
        print(f"PIDs: {pids}")
    except docker.errors.NotFound:
        print(f"Container {container_name} not found.")
    except KeyError as e:
        print(f"KeyError: {e} not found in stats.")

def calculate_cpu_percentage(stats):
    cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage'] - stats['precpu_stats']['cpu_usage']['total_usage']
    system_cpu_delta = stats['cpu_stats']['system_cpu_usage'] - stats['precpu_stats']['system_cpu_usage']

    # Verificar se 'online_cpus' existe e usar essa métrica
    num_cpus = stats['cpu_stats'].get('online_cpus', 1)

    if system_cpu_delta > 0.0 and cpu_delta > 0.0:
        cpu_percentage = (cpu_delta / system_cpu_delta) * num_cpus * 100.0
    else:
        cpu_percentage = 0.0
    return cpu_percentage

# Substitua 'ews' pelo nome ou ID do container que você deseja monitorar
get_container_metrics('ews')
