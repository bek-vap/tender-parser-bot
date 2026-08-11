-- Create tender database for Tender Intelligence Platform
CREATE DATABASE IF NOT EXISTS tender;

-- Connect to tender database
\c tender

-- Create keywords table
CREATE TABLE IF NOT EXISTS keywords (
    id VARCHAR PRIMARY KEY,
    phrase VARCHAR NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create tenders table
CREATE TABLE IF NOT EXISTS tenders (
    id VARCHAR PRIMARY KEY,
    title TEXT,
    description TEXT,
    amount VARCHAR,
    region VARCHAR,
    source VARCHAR,
    url VARCHAR,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create tender_keyword_matches table
CREATE TABLE IF NOT EXISTS tender_keyword_matches (
    id SERIAL PRIMARY KEY,
    tender_id VARCHAR REFERENCES tenders(id),
    keyword_id VARCHAR REFERENCES keywords(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert sample keywords
INSERT INTO keywords (id, phrase, is_active) VALUES
('1', 'теплица', TRUE),
('2', 'issiqxona', TRUE),
('3', 'qurilish', TRUE),
('4', 'rekonstruksiya', TRUE),
('5', 'zavod', TRUE),
('6', 'sex', TRUE),
('7', 'metallkonstruktsiya', TRUE),
('8', 'armatura', TRUE),
('9', 'agroklaster', TRUE),
('10', 'chorva', TRUE),
('11', 'ferma', TRUE),
('12', 'parrandachilik', TRUE),
('13', 'ombor', TRUE),
('14', 'sklad', TRUE),
('15', 'logistika markazi', TRUE),
('16', 'angar', TRUE),
('17', 'tender', TRUE),
('18', 'konkurs', TRUE),
('19', 'zakupka', TRUE),
('20', 'postavka', TRUE);

COMMIT;
