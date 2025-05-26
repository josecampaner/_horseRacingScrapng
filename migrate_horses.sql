-- Crear tabla horses con estructura completa
CREATE TABLE IF NOT EXISTS horses (
    horse_id VARCHAR(255) PRIMARY KEY,
    horse_name VARCHAR(255) NOT NULL,
    horse_name_ipa VARCHAR(255),
    owner VARCHAR(255),
    owner_ipa VARCHAR(255),
    trainer VARCHAR(255),
    trainer_ipa VARCHAR(255),
    breeder VARCHAR(255),
    breeder_ipa VARCHAR(255),
    country VARCHAR(100),
    country_of_birth VARCHAR(100),
    age INTEGER,
    status VARCHAR(100),
    sex VARCHAR(10),
    color VARCHAR(100),
    url TEXT,
    profile_url TEXT,
    last_race_date DATE,
    last_scraped_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Crear índices para mejorar el rendimiento
CREATE INDEX IF NOT EXISTS idx_horses_name ON horses(horse_name);
CREATE INDEX IF NOT EXISTS idx_horses_trainer ON horses(trainer);
CREATE INDEX IF NOT EXISTS idx_horses_owner ON horses(owner);
CREATE INDEX IF NOT EXISTS idx_horses_sex ON horses(sex);
CREATE INDEX IF NOT EXISTS idx_horses_country ON horses(country_of_birth); 