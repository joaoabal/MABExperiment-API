/*TABELAS INPUT */

/* Armazena informações sobre cada experimento que você está conduzindo.*/
CREATE TABLE IF NOT EXISTS experiments (
    experiment_id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    start_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    end_date TIMESTAMP NULL
);

/* Armazena as diferentes variantes (ou "braços" no contexto MAB) de cada experimento.*/
CREATE TABLE IF NOT EXISTS variants (
    experiment_id INTEGER NOT NULL REFERENCES experiments(experiment_id),
    name VARCHAR(50) NOT NULL,
    UNIQUE (experiment_id, name)
);

CREATE TABLE IF NOT EXISTS experiment_data (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    impressions INTEGER NOT NULL,
    clicks INTEGER NOT NULL
);

/*TABELAS OUTPUT */ 

/* Armazena os resultados de alocação de tráfego para cada experimento em um determinado momento. */
CREATE TABLE IF NOT EXISTS allocations (
    allocation_id SERIAL PRIMARY KEY,
    experiment_id INTEGER NOT NULL REFERENCES experiments(experiment_id),
    allocation_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    allocation_percentage NUMERIC(5, 2) NOT NULL
);
