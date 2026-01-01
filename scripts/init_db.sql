-- 1. 의약품 제품 정보 테이블 (식약처 데이터 기반)
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    product_name VARCHAR(255) NOT NULL,          -- 제품명
    permit_number VARCHAR(50) UNIQUE NOT NULL,   -- 품목기준코드 (식약처 고유번호)
    manufacturer VARCHAR(255),                   -- 업체명 (제조/수입사)
    is_combination BOOLEAN DEFAULT FALSE,       -- 복합제 여부
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. 정규화된 화합물/주성분 정보 테이블 (PubChem 데이터 기반)
CREATE TABLE compounds (
    id SERIAL PRIMARY KEY,
    standard_name VARCHAR(255) UNIQUE NOT NULL,  -- 정규화된 성분명 (영문/국문 표준)
    cid INTEGER UNIQUE,                          -- PubChem Compound ID
    smiles TEXT,                                 -- Canonical SMILES (구조 정보)
    molecular_formula VARCHAR(100),              -- 분자식
    molecular_weight NUMERIC(10, 4),             -- 분자량
    iupac_name TEXT,                             -- IUPAC 명칭
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 3. 제품과 성분 사이의 매핑 테이블 (N:M 관계 해소)
-- 식약처 제품명에서 추출된 성분이 어떤 표준 화합물(Compound)과 매칭되는지 기록
CREATE TABLE product_ingredients (
    id SERIAL PRIMARY KEY,
    product_id INTEGER REFERENCES products(id) ON DELETE CASCADE,
    compound_id INTEGER REFERENCES compounds(id) ON DELETE SET NULL,
    raw_ingredient_name VARCHAR(255) NOT NULL,   -- 정규화 전 원재료명
    content VARCHAR(100),                        -- 함량 (예: 500mg)
    is_main_active BOOLEAN DEFAULT TRUE          -- 주성분 여부
);

-- 4. 화합물 간 구조 유사도 분석 결과 테이블 (RDKit 분석 기반)
CREATE TABLE compound_similarities (
    id SERIAL PRIMARY KEY,
    target_compound_id INTEGER REFERENCES compounds(id) ON DELETE CASCADE,
    comparison_compound_id INTEGER REFERENCES compounds(id) ON DELETE CASCADE,
    similarity_score NUMERIC(5, 4) CHECK (similarity_score >= 0 AND similarity_score <= 1), -- Tanimoto Score
    analysis_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_similarity_pair UNIQUE (target_compound_id, comparison_compound_id)
);