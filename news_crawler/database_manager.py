import mysql.connector as db_connector
from datetime import datetime
import hashlib
import sys
import os
from typing import Dict, List, Any

# db configuration from environment variables or defaults
MYSQL_CONFIG = {
    'host': os.environ.get('DB_HOST', '127.0.0.1'),
    'user': os.environ.get('DB_USER', 'crawler_user'),
    'password': os.environ.get('DB_PASSWORD', 'eirini2003'),
    'database': os.environ.get('DB_NAME', 'news_crawler_db')
}

def get_connection():
    # returns a connection to the MySQL database
    return db_connector.connect(**MYSQL_CONFIG, charset='utf8mb4')

def initialize_db():
    # Initialize database and tables
    init_config = {k: v for k, v in MYSQL_CONFIG.items() if k != 'database'}
    try:
        conn = db_connector.connect(**init_config)
        cursor = conn.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {MYSQL_CONFIG['database']} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        conn.close()
    except db_connector.Error as err:
        sys.stderr.write(f"CRITICAL CONNECTION ERROR: {err}\n")
        sys.exit(1)

    try:
        conn = get_connection()
        cursor = conn.cursor()

        # news_sites table: Source management
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS news_sites (
            id INT PRIMARY KEY AUTO_INCREMENT,
            domain VARCHAR(255) UNIQUE,
            start_url TEXT,
            last_visited DATETIME,
            active TINYINT DEFAULT 1,
            priority INT DEFAULT 10
        )
        """)

        # articles table: Stores scraped content and metadata
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS articles (
            id INT PRIMARY KEY AUTO_INCREMENT,
            site_id INT NOT NULL,
            url TEXT,
            title TEXT,
            body LONGTEXT,
            image_url TEXT,
            scraped_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            content_hash VARCHAR(32),
            last_cited_date DATETIME,
            FOREIGN KEY(site_id) REFERENCES news_sites(id),
            UNIQUE KEY unique_url_idx (url(255)) 
        )
        """)
        conn.commit()
        conn.close()
        print("Database initialization completed successfully.")
    except db_connector.Error as err:
        sys.stderr.write(f"CRITICAL SCHEMA ERROR: {err}\n")
        sys.exit(1)

def normalize_domain(domain):
    # Removes www. prefix from domain string
    if domain and domain.startswith("www."):
        return domain[4:]
    return domain

def get_active_sites():
    # Fetch all active news sources ordered by priority
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, domain, start_url FROM news_sites WHERE active = 1 ORDER BY priority DESC")
        rows = cursor.fetchall()
        conn.close()
        return rows
    except db_connector.Error as err:
        sys.stderr.write(f"QUERY ERROR (Active Sites): {err}\n")
        return []

def update_last_visited(domain):
    # Logs the timestamp of the last crawler visit per domain
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE news_sites SET last_visited = NOW() WHERE domain = %s", (domain,))
        conn.commit()
        conn.close()
    except Exception as e:
        sys.stderr.write(f" ERROR (last_visited): {e}\n")

def save_article(site_id, url, title, body, image_url):
    # Saves a new article or updates an existing one using MD5 hash comparison
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
    except db_connector.Error as err:
        sys.stderr.write(f"CONNECTION ERROR (save_article): {err}\n")
        return

    title_safe = title or 'No Title'
    body_safe = body or ''
    image_url_safe = image_url or ''
    content_hash = hashlib.md5(body_safe.encode('utf-8')).hexdigest()

    try:
        # Check if URL already exists in database
        cursor.execute("SELECT id, content_hash FROM articles WHERE url = %s", (url,))
        row = cursor.fetchone()

        if row:
            article_id = row['id']
            if row['content_hash'] != content_hash:
                # Content changed, perform update
                cursor.execute("""
                    UPDATE articles
                    SET title = %s, body = %s, image_url = %s, content_hash = %s, 
                        last_cited_date = NOW()
                    WHERE id = %s
                """, (title_safe, body_safe, image_url_safe, content_hash, article_id))
                sys.stdout.write(f"[UPDATED] {url}\n")
            else:
                # Content unchanged, update last seen timestamp
                cursor.execute("UPDATE articles SET last_cited_date = NOW() WHERE id = %s", (article_id,))
                sys.stdout.write(f"[UNCHANGED] {url}\n")
        else:
            # New URL found, perform insert
            cursor.execute("""
                INSERT INTO articles (
                    site_id, url, title, body, image_url, content_hash, last_cited_date
                ) VALUES (%s, %s, %s, %s, %s, %s, NOW())
            """, (site_id, url, title_safe, body_safe, image_url_safe, content_hash))
            sys.stdout.write(f"[NEW] {url}\n")

        conn.commit()
    except Exception as e:
        sys.stderr.write(f"SQL ERROR for {url}: {e}\n")
    finally:
        conn.close()

if __name__ == "__main__":
    initialize_db()