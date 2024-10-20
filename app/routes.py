from flask import Blueprint, request, jsonify
from db_connection import get_db_connection  # Importa de db_connection.py
from datetime import datetime
import numpy as np
from scipy.stats import beta

main = Blueprint('main', __name__)

@main.route('/')
def index():
    return "API is running!"

def calculate_allocation(experiment_id):
    conn = get_db_connection()
    cur = conn.cursor()

    # Obter as variantes associadas ao experimento
    cur.execute("""
        SELECT v.name
        FROM variants v
        WHERE v.experiment_id = %s
    """, (experiment_id,))
    
    variant_names = cur.fetchall()
    variant_names = [row[0] for row in variant_names]  # Extraindo os nomes das variantes

    if not variant_names:
        conn.close()
        return {}

    # Obter dados agregados de impressões e cliques para cada variante em experiment_data
    cur.execute(f"""
        SELECT
            ed.name AS variant_name,
            SUM(ed.impressions) AS total_impressions,
            SUM(ed.clicks) AS total_clicks
        FROM
            experiment_data ed
        WHERE
            ed.name IN %s
        GROUP BY
            ed.name;
    """, (tuple(variant_names),))

    results = cur.fetchall()
    conn.close()

    if not results:
        return {}

    samples = []
    variant_names_list = []
    for row in results:
        variant_name, impressions, clicks = row
        alpha = clicks + 1
        beta_param = (impressions - clicks) + 1
        sample = np.random.beta(alpha, beta_param)
        samples.append(sample)
        variant_names_list.append(variant_name)

    # Calcular alocação proporcional
    total = sum(samples)
    allocations = {variant_names_list[i]: round((samples[i] / total) * 100, 2) for i in range(len(samples))}

    return allocations

# registra o experimento a ser realizado
@main.route('/experiments', methods=['POST'])
def create_experiment():
    data = request.get_json()

    if 'name' not in data:
        return jsonify({"error": "Experiment name is required"}), 400

    name = data['name']
    start_date_str = data.get('start_date')
    end_date_str = data.get('end_date')

    if start_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        except ValueError:
            return jsonify({"error": "start_date format should be YYYY-MM-DD"}), 400
    else:
        start_date = datetime.utcnow()

    if end_date_str:
        try:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
        except ValueError:
            return jsonify({"error": "end_date format should be YYYY-MM-DD"}), 400
    else:
        end_date = None

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            INSERT INTO experiments (name, start_date, end_date)
            VALUES (%s, %s, %s)
            RETURNING experiment_id
        """, (name, start_date, end_date))
        experiment_id = cur.fetchone()[0]
        conn.commit()
    except Exception as e:
        conn.rollback()
        cur.close()
        conn.close()
        return jsonify({"error": str(e)}), 500

    cur.close()
    conn.close()

    return jsonify({
        "message": "Experiment created successfully",
        "experiment_id": experiment_id
    }), 201

#registra as variantes relacionadas a experimentos cadastrados
@main.route('/experiments/<int:experiment_id>/variants', methods=['POST'])
def create_variant(experiment_id):
    data = request.get_json()

    if 'name' not in data:
        return jsonify({"error": "Variant name is required"}), 400

    variant_name = data['name']

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT experiment_id FROM experiments WHERE experiment_id = %s", (experiment_id,))
    experiment = cur.fetchone()
    if not experiment:
        cur.close()
        conn.close()
        return jsonify({"error": "Experiment not found"}), 404

    try:
        cur.execute("""
            INSERT INTO variants (experiment_id, name)
            VALUES (%s, %s)
        """, (experiment_id, variant_name))
        conn.commit()
    except Exception as e:
        conn.rollback()
        cur.close()
        conn.close()
        return jsonify({"error": str(e)}), 500

    cur.close()
    conn.close()

    return jsonify({
        "message": "Variant created successfully"
    }), 201

#insere os dados dos experimentos
@main.route('/experiment_data', methods=['POST'])
def add_experiment_data():
    data = request.get_json()

    if isinstance(data, list):
        records = data
    else:
        records = [data]

    conn = get_db_connection()
    cur = conn.cursor()

    for item in records:
        required_fields = {"timestamp", "name", "impressions", "clicks", "experiment_id"}
        if not required_fields.issubset(item):
            conn.rollback()
            cur.close()
            return jsonify({"error": "Missing data in one of the records"}), 400

        try:
            timestamp = datetime.strptime(item['timestamp'], '%Y-%m-%d %H:%M:%S')
        except ValueError:
            conn.rollback()
            cur.close()
            return jsonify({"error": "timestamp format should be YYYY-MM-DD HH:MM:SS"}), 400

        experiment_id = item['experiment_id']
        name = item['name']
        impressions = item['impressions']
        clicks = item['clicks']

        cur.execute("""
            SELECT name FROM variants WHERE experiment_id = %s AND name = %s
        """, (experiment_id, name))
        variant = cur.fetchone()
        if not variant:
            conn.rollback()
            cur.close()
            return jsonify({"error": f"Variant {name} not found for experiment {experiment_id}"}), 404

        try:
            cur.execute("""
                INSERT INTO experiment_data (name, timestamp, impressions, clicks)
                VALUES (%s, %s, %s, %s)
            """, (name, timestamp, impressions, clicks))
        except Exception as e:
            conn.rollback()
            cur.close()
            return jsonify({"error": str(e)}), 500

    try:
        conn.commit()
    except Exception as e:
        conn.rollback()
        cur.close()
        return jsonify({"error": str(e)}), 500

    cur.close()
    conn.close()

    return jsonify({"message": f"{len(records)} records added successfully"}), 201


@main.route('/allocations', methods=['POST'])
def save_allocations():
    data = request.get_json()

    if 'experiment_id' not in data:
        return jsonify({"error": "experiment_id is required"}), 400

    experiment_id = data['experiment_id']

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT experiment_id FROM experiments WHERE experiment_id = %s", (experiment_id,))
    experiment = cur.fetchone()
    if not experiment:
        cur.close()
        conn.close()
        return jsonify({"error": "Experiment not found"}), 404

    # Calcular as alocações utilizando o algoritmo MAB
    allocations = calculate_allocation(experiment_id)

    if not allocations:
        cur.close()
        conn.close()
        return jsonify({"error": "No data available to calculate allocations"}), 400

    try:
        allocation_date = datetime.utcnow()
        for name, allocation_percentage in allocations.items():
            cur.execute("""
                INSERT INTO allocations (experiment_id, allocation_date, allocation_percentage)
                VALUES (%s, %s, %s)
            """, (experiment_id, allocation_date, allocation_percentage))
        conn.commit()
    except Exception as e:
        conn.rollback()
        cur.close()
        conn.close()
        return jsonify({"error": str(e)}), 500

    cur.close()
    conn.close()

    allocation_list = [{"name": name, "allocation_percentage": allocation_percentage} for name, allocation_percentage in allocations.items()]

    return jsonify({
        "message": "Allocations calculated and saved successfully",
        "experiment_id": experiment_id,
        "allocation_date": allocation_date.strftime('%Y-%m-%d %H:%M:%S'),
        "allocations": allocation_list
    }), 201

@main.route('/allocations/<int:experiment_id>', methods=['GET'])
def get_allocations(experiment_id):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT MAX(allocation_date) FROM allocations
        WHERE experiment_id = %s
    """, (experiment_id,))
    result = cur.fetchone()
    latest_date = result[0]

    if not latest_date:
        cur.close()
        conn.close()
        return jsonify({"error": "No allocations found for this experiment"}), 404

    cur.execute("""
        SELECT allocation_percentage
        FROM allocations
        WHERE experiment_id = %s AND allocation_date = %s
    """, (experiment_id, latest_date))

    allocations = cur.fetchall()
    cur.close()
    conn.close()

    allocation_list = [{"allocation_percentage": float(row[0])} for row in allocations]

    return jsonify({
        "experiment_id": experiment_id,
        "allocation_date": latest_date.strftime('%Y-%m-%d %H:%M:%S'),
        "allocations": allocation_list
    }), 200

