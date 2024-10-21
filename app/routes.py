from flask import Blueprint, request, jsonify
from db_connection import get_db_connection  # Importa de db_connection.py
from datetime import datetime
import numpy as np
from scipy.stats import beta

main = Blueprint('main', __name__)

@main.route('/')
def index():
    return "API is running!"


# insere os dados dos experimentos
@main.route('/experiment_data', methods=['POST'])
def add_experiment_data():
    data = request.get_json()

    # Verifica se data é uma lista (múltiplos registros)
    if isinstance(data, list):
        records = data
    else:
        records = [data]

    conn = get_db_connection()
    cur = conn.cursor()

    for item in records:
        # Verificação dos campos obrigatórios
        required_fields = {"timestamp", "name", "impressions", "clicks"}
        if not required_fields.issubset(item):
            conn.rollback()
            cur.close()
            return jsonify({"error": "Missing data in one of the records"}), 400

        # Valida e converte o timestamp
        try:
            timestamp = datetime.strptime(item['timestamp'], '%Y-%m-%d %H:%M:%S')
        except ValueError:
            conn.rollback()
            cur.close()
            return jsonify({"error": "timestamp format should be YYYY-MM-DD HH:MM:SS"}), 400

        name = item['name']  # Nome da variante
        impressions = item['impressions']
        clicks = item['clicks']

        # Inserir dados diretamente na tabela experiment_data
        try:
            cur.execute("""
                INSERT INTO experiment_data (name, timestamp, impressions, clicks)
                VALUES (%s, %s, %s, %s)
            """, (name, timestamp, impressions, clicks))
        except Exception as e:
            conn.rollback()
            cur.close()
            return jsonify({"error": str(e)}), 500

    # Commit das mudanças no banco de dados
    try:
        conn.commit()
    except Exception as e:
        conn.rollback()
        cur.close()
        return jsonify({"error": str(e)}), 500

    # Fechar conexões
    cur.close()
    conn.close()

    return jsonify({"message": f"{len(records)} records added successfully"}), 201


@main.route('/allocations', methods=['POST'])
def calculate_and_save_allocations():
    data = request.get_json()

    # Verificar se os campos necessários estão presentes
    if not all(k in data for k in ("variant_names", "start_date", "end_date")):
        return jsonify({"error": "variant_names, start_date, and end_date are required"}), 400

    variant_names = data['variant_names']
    start_date = data['start_date']
    end_date = data['end_date']

    conn = get_db_connection()
    cur = conn.cursor()

    # Obter dados agregados de impressões e cliques para as variantes dentro do intervalo
    cur.execute("""
        SELECT
            ed.name AS variant_name,
            SUM(ed.impressions) AS total_impressions,
            SUM(ed.clicks) AS total_clicks,
            SUM(ed.impressions) - SUM(ed.clicks) AS total_non_clicks
        FROM
            experiment_data ed
        WHERE
            ed.name IN %s
            AND ed.timestamp BETWEEN %s AND %s
        GROUP BY ed.name;
    """, (tuple(variant_names), start_date, end_date))

    results = cur.fetchall()

    if not results:
        cur.close()
        conn.close()
        return jsonify({"error": "No data found for the specified variants and date range"}), 404

    samples = []
    for row in results:
        variant_name, impressions, clicks, non_clicks = row
        alpha = clicks + 1
        beta_param = non_clicks + 1
        sample = np.random.beta(alpha, beta_param)
        samples.append((variant_name, sample))

    total = sum(sample[1] for sample in samples)
    allocations = {variant_name: round((sample / total) * 100, 2) for variant_name, sample in samples}


    # Inserir as alocações na tabela allocations
    allocation_date = datetime.now()
    try:
        for variant_name, allocation_percentage in allocations.items():
            cur.execute("""
                INSERT INTO allocations (allocation_date, variant_name, allocation_percentage, start_date, end_date)
                VALUES (%s, %s, %s, %s, %s)
            """, (allocation_date, variant_name, allocation_percentage, start_date, end_date))
        conn.commit()
    except Exception as e:
        conn.rollback()
        cur.close()
        conn.close()
        return jsonify({"error": str(e)}), 500

    cur.close()
    conn.close()

    return jsonify({
        "message": "Allocations calculated and saved successfully",
        "allocation_date": allocation_date.strftime('%Y-%m-%d %H:%M:%S'),
        "allocations": allocations,
        "start_date": start_date,
        "end_date": end_date
    }), 201

@main.route('/allocations', methods=['GET'])
def get_allocations():
    conn = get_db_connection()
    cur = conn.cursor()

    # Obter a data mais recente de alocação
    cur.execute("""
        SELECT MAX(allocation_date) FROM allocations;
    """)
    latest_date = cur.fetchone()[0]

    if not latest_date:
        cur.close()
        conn.close()
        return jsonify({"error": "No allocations found"}), 404

    # Obter as alocações mais recentes junto com start_date e end_date
    cur.execute("""
        SELECT variant_name, allocation_percentage, start_date, end_date
        FROM allocations
        WHERE allocation_date = %s;
    """, (latest_date,))

    allocations = cur.fetchall()
    cur.close()
    conn.close()

    allocation_list = [
        {
            "variant_name": row[0],
            "allocation_percentage": float(row[1]),
            "start_date": row[2].strftime('%Y-%m-%d'),
            "end_date": row[3].strftime('%Y-%m-%d')
        }
        for row in allocations
    ]

    return jsonify({
        "allocation_date": latest_date.strftime('%Y-%m-%d %H:%M:%S'),
        "allocations": allocation_list
    }), 200


