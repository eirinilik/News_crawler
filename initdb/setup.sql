CREATE TABLE IF NOT EXISTS news_sites (
    id INT AUTO_INCREMENT PRIMARY KEY,
    domain VARCHAR(255) NOT NULL UNIQUE,
    start_url VARCHAR(255) NOT NULL,
    last_visited DATETIME NULL,
    active TINYINT(1) DEFAULT 1,
    priority INT DEFAULT 10
);

CREATE TABLE IF NOT EXISTS articles (
    id INT PRIMARY KEY AUTO_INCREMENT,
    site_id INT NOT NULL,
    url VARCHAR(500),
    title TEXT,
    body LONGTEXT,
    image_url TEXT,
    content_hash VARCHAR(32), -- Η στήλη που έλειπε
    scraped_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_cited_date DATETIME,
    FOREIGN KEY(site_id) REFERENCES news_sites(id),
    UNIQUE KEY unique_url_idx (url(255))
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 3. Εισαγωγή των 21 πηγών
INSERT IGNORE INTO news_sites (domain, start_url, active, priority) VALUES
('protothema.gr', 'https://www.protothema.gr', 1, 10),
('newsit.gr', 'https://www.newsit.gr', 1, 9),
('news247.gr', 'https://www.news247.gr', 1, 8),
('iefimerida.gr', 'https://www.iefimerida.gr', 1, 7),
('naftemporiki.gr', 'https://www.naftemporiki.gr', 1, 6),
('efsyn.gr', 'https://www.efsyn.gr', 1, 5),
('in.gr', 'https://www.in.gr', 1, 4),
('kathimerini.gr', 'https://www.kathimerini.gr', 1, 3),
('tanea.gr', 'https://www.tanea.gr', 1, 2),
('tovima.gr', 'https://www.tovima.gr', 1, 1),
('cnn.gr', 'https://www.cnn.gr', 1, 10),
('skai.gr', 'https://www.skai.gr', 1, 10),
('newsbeast.gr', 'https://www.newsbeast.gr', 1, 10),
('newsbomb.gr', 'https://www.newsbomb.gr', 1, 10),
('capital.gr', 'https://www.capital.gr', 1, 10),
('huffingtonpost.gr', 'https://www.huffingtonpost.gr', 1, 10),
('documentonews.gr', 'https://www.documentonews.gr', 1, 10),
('ertnews.gr', 'https://www.ertnews.gr', 1, 7),
('forbesgreece.gr', 'https://www.forbesgreece.gr', 1, 5),
('athensvoice.gr', 'https://www.athensvoice.gr', 1, 5),
('gazzetta.gr', 'https://www.gazzetta.gr', 1, 7);