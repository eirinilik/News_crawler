News Crawler Pipeline: Intelligent Data Acquisition 

An advanced, scalable news crawling and classification pipeline. The system automates the collection of news articles from diverse Greek web sources, utilizing Machine Learning to filter out "noise" (boilerplate) and ensure high-quality data for business intelligence reporting . 

System Architecture

The project implements a 4-layer sequential data pipeline:

    Acquisition: Hybrid crawling using Scrapy for speed and Playwright for full JavaScript rendering (mitigating data loss by up to 33.8%) .

    Preprocessing: Boilerplate removal via Trafilatura and site-specific Regex rules .

    Classification: A Random Forest model (97% accuracy) classifies pages into Article, Category, or Other .

    Persistence: Structured storage in MySQL with MD5 Hashing for deduplication (64.6% storage efficiency).
### Project Structure

```text
.
├── docker-compose.yaml      # Orchestrates Crawler and MySQL services
├── Dockerfile               # Builds the Python environment with Playwright
├── initdb/                  # SQL scripts for database initialization
├── news_crawler/            # Main application package
│   ├── config/              # Configuration & Site-Specific Rules
│   │   └── boilerplate_rules.json # Custom Regex rules per domain
│   ├── concurrent_runner.py # Entry point for parallel crawling
│   ├── database_manager.py  # MySQL schema and connection logic
│   ├── spiders/             # Scrapy spider definitions
│   ├── models/              # Trained ML models (.pkl files)
│   ├── data/                # Training datasets
│   └── settings.py          # Scrapy configuration
├── logs/                    # Execution logs
├── results/                 # Exported crawl results
└── requirements.txt         # Python dependencies

```
Quick Start (Docker)
1. Configure Credentials

The .env file is already included in the repository. Open it and update the following variables with your local database settings:
Code snippet


Update these with your specific values

# Database Configuration
DB_NAME=news_crawler_db

DB_USER=crawler_user

DB_PASSWORD=your_secure_password

DB_ROOT_PASSWORD=your_root_password

DB_HOST=db

2. Launch the Pipeline

Deploy the entire stack (Database + Crawler) using Docker Compose:
Bash

docker-compose up --build

Note: The crawler will automatically wait for the MySQL healthcheck before starting.
 Performance Metrics

    Throughput: ~87.5 pages per minute.

    Classification: 0.99 F1-Score for the Article class.

    Deduplication: 64.6% reduction in redundant I/O operations.