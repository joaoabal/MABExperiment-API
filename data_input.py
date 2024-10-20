import requests
import json
from datetime import datetime, timedelta
import random

# Configurações
base_url = 'http://localhost:5001'
headers = {'Content-Type': 'application/json'}

# 1. Criar um experimento

experiment_name = "Teste de Otimização de CTR"

end_date = datetime.now()  # Data atual
start_date = end_date - timedelta(days=7)  # 7 dias atrás

start_date_str = start_date.strftime('%Y-%m-%d')
end_date_str = end_date.strftime('%Y-%m-%d')

experiment_data = {
    "name": experiment_name,
    "start_date": start_date_str,
    "end_date": end_date_str
}

response = requests.post(f"{base_url}/experiments", headers=headers, json=experiment_data)
if response.status_code == 201:
    experiment_id = response.json()['experiment_id']
    print(f"Experimento criado com ID: {experiment_id}")
else:
    print("Erro ao criar o experimento:")
    print(response.text)
    exit()

# 2. Criar variantes
variant_names = ['A', 'B']

for variant_name in variant_names:
    variant_data = {
        "name": variant_name
    }
    response = requests.post(f"{base_url}/experiments/{experiment_id}/variants", headers=headers, json=variant_data)
    if response.status_code == 201:
        print(f"Variante '{variant_name}' criada com sucesso.")
    else:
        print(f"Erro ao criar a variante '{variant_name}':")
        print(response.text)
        exit()

# 3. Gerar dados de entrada utilizando o nome da variante
num_records_per_variant = 5000
start_time = datetime.now() - timedelta(days=90)  # Início da série temporal (30 dias atrás)
time_interval = timedelta(minutes=60)  # Intervalo de tempo entre os registros

# Lista para armazenar todos os registros
data = []

# Gerar dados para cada variante
for variant_name in variant_names:
    timestamp = start_time
    for _ in range(num_records_per_variant):
        # Gerar valores aleatórios para impressões e cliques
        impressions = random.randint(50, 200)
        clicks = random.randint(0, impressions)  # Cliques não podem exceder impressões

        # Criar o registro
        record = {
            "experiment_id": experiment_id,
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

# 4. Enviar os dados para o endpoint de inserção de dados do experimento
# Novo endpoint: /experiment_data
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

# Opcional: Salvar os dados enviados em um arquivo JSON
with open('add_experiment_data.json', 'w') as f:
    json.dump(data, f, indent=2)
