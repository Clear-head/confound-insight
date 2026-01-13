CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    product_name VARCHAR(255) NOT NULL,
    permit_number VARCHAR(50) UNIQUE NOT NULL,
    manufacturer VARCHAR(255),
    is_combination BOOLEAN DEFAULT FALSE,
    source VARCHAR(50) DEFAULT 'MFDS',
    last_synced_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE IF NOT EXISTS compounds (
    id SERIAL PRIMARY KEY,
    standard_name VARCHAR(255) UNIQUE NOT NULL,
    cid BIGINT UNIQUE,
    smiles TEXT,
    inchi TEXT,
    inchi_key VARCHAR(27),
    molecular_formula VARCHAR(100),
    molecular_weight NUMERIC(12, 4),
    iupac_name TEXT,
    fingerprint_morgan BYTEA,
    fingerprint_type VARCHAR(50) DEFAULT 'Morgan_r2_2048',
    is_valid BOOLEAN DEFAULT TRUE,
    validation_error TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    pubchem_last_fetched TIMESTAMP
);



CREATE TABLE IF NOT EXISTS product_ingredients (
    id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    compound_id INTEGER REFERENCES compounds(id) ON DELETE SET NULL,
    raw_ingredient_name VARCHAR(255) NOT NULL,
    content VARCHAR(100),
    unit VARCHAR(20),
    is_main_active BOOLEAN DEFAULT TRUE,
    ingredient_type VARCHAR(50) DEFAULT 'ACTIVE',
    normalization_status VARCHAR(20) DEFAULT 'PENDING',
    normalization_error TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(product_id, raw_ingredient_name)
);


CREATE TABLE IF NOT EXISTS product_ingredients (
    id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    compound_id INTEGER REFERENCES compounds(id) ON DELETE SET NULL,
    raw_ingredient_name VARCHAR(255) NOT NULL,
    content VARCHAR(100),
    unit VARCHAR(20),
    is_main_active BOOLEAN DEFAULT TRUE,
    ingredient_type VARCHAR(50) DEFAULT 'ACTIVE',
    normalization_status VARCHAR(20) DEFAULT 'PENDING',
    normalization_error TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(product_id, raw_ingredient_name)
);