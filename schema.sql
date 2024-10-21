/* Tabela para armazenar os dados de impressões e cliques */
CREATE TABLE IF NOT EXISTS experiment_data (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL,          -- Nome da variante
    timestamp TIMESTAMP NOT NULL,       -- Quando os dados foram registrados
    impressions INTEGER NOT NULL,       -- Número de impressões
    clicks INTEGER NOT NULL             -- Número de cliques
);

/* Tabela para armazenar os resultados de alocação e informacoes do experimento */
CREATE TABLE IF NOT EXISTS allocations (
    allocation_id SERIAL PRIMARY KEY,
    allocation_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,  -- Data da alocação
    variant_name VARCHAR(50) NOT NULL,      -- Nome da variante
    allocation_percentage NUMERIC(5, 2) NOT NULL,  -- Percentual de tráfego alocado
    start_date TIMESTAMP NOT NULL,          -- Data de início do cálculo da alocação
    end_date TIMESTAMP NOT NULL             -- Data de fim do cálculo da alocação
);
