import requests
import json
from datetime import datetime, timedelta
import random

# Configurações
base_url = 'http://localhost:5001'
headers = {'Content-Type': 'application/json'}

# 1. Definir o intervalo de tempo
end_date = datetime.now()  # Data atual
start_date = end_date - timedelta(days=90)  # 90 dias atrás

start_time = start_date  # Início da série temporal
time_interval = timedelta(minutes=60)  # Intervalo de tempo entre os registros

# Variantes e dados
variant_names = ['A', 'B', 'C', 'D']
num_records_per_variant = 5000  # Número de registros por variante

# Lista para armazenar todos os registros
data = []

# 2. Gerar dados de entrada para cada variante
for variant_name in variant_names:
    timestamp = start_time
    for _ in range(num_records_per_variant):
        # Gerar valores aleatórios para impressões e cliques
        impressions = random.randint(50, 200)
        clicks = random.randint(0, impressions)  # Cliques não podem exceder impressões

        # Criar o registro
        record = {
            "name": variant_name,
            "timestamp": timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            "impressions": impressions,
            "clicks": clicks
        }

        data.append(record)

        # Incrementar o timestamp
        timestamp += time_interval

# Embaralhar os dados para misturar as variantes
random.shuffle(data)

# 3. Enviar os dados para o endpoint de inserção de dados do experimento
url = f"{base_url}/experiment_data"

# Enviar os dados em lotes menores para evitar sobrecarga
batch_size = 100  # Ajuste conforme necessário
for i in range(0, len(data), batch_size):
    batch = data[i:i + batch_size]
    response = requests.post(url, headers=headers, json=batch)

    if response.status_code == 201:
        print(f"Lote {i // batch_size + 1}: {len(batch)} registros adicionados com sucesso.")
    else:
        print(f"Erro no lote {i // batch_size + 1}: {response.status_code}")
        print("Resposta do servidor:")
        print(response.text)
        break  # Opcional: interromper em caso de erro

# 4. Opcional: Salvar os dados enviados em um arquivo JSON
with open('add_experiment_data.json', 'w') as f:
    json.dump(data, f, indent=2)
