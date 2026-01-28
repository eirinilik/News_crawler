import subprocess
import os
import sys
import json
import glob
import time
import shutil
import traceback
import re
from multiprocessing import Pool
from urllib.parse import urlparse
from typing import List, Dict, Any

# Path configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BASE_DIR)
SCRAPY_PYTHON_EXEC = sys.executable

# directory management
RESULTS_DIR = os.path.join(ROOT_DIR, 'results')
PREDICTIONS_DIR = os.path.join(ROOT_DIR, 'predictions')
LOGS_DIR = os.path.join(ROOT_DIR, 'logs')
FINAL_LOG_FILE = os.path.join(LOGS_DIR, 'all_concurrent_unified.log')

# Execution settings
MAX_CONCURRENT_WORKERS = 4

# Ensure required directories exist
os.makedirs(LOGS_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)
os.makedirs(PREDICTIONS_DIR, exist_ok=True)

# Update system path for module discovery
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

try:
    import database_manager as db
except ImportError:
    from news_crawler import database_manager as db


def clear_output_directories():
    for folder in [RESULTS_DIR, PREDICTIONS_DIR]:
        if os.path.exists(folder):
            for filename in os.listdir(folder):
                file_path = os.path.join(folder, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    print(f'Failed to delete {file_path}. Reason: {e}')
        else:
            os.makedirs(folder, exist_ok=True)

    try:
        with open(FINAL_LOG_FILE, 'w', encoding='utf-8') as f:
            f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] STARTING NEW CRAWL SESSION\n")
            f.write("=" * 75 + "\n")
    except Exception as e:
        print(f"Could not initialize log file: {e}")


def log_to_unified_file(content):
    """Appends workflow events and technical logs to the main log file."""
    try:
        with open(FINAL_LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {content}\n")
            f.flush()
    except Exception as e:
        print(f"Logging error: {e}")


def run_single_crawl(site_data: Dict[str, str]) -> Dict[str, Any]:
    """Handles the full pipeline for a single domain: Scrape -> Predict -> Database Sync."""
    start_url = site_data['start_url']
    domain = site_data['domain']
    domain_clean = urlparse(start_url).netloc.replace('www.', '').replace('.', '_')
    raw_json_absolute = os.path.join(RESULTS_DIR, f"raw_{domain_clean}.json")

    log_to_unified_file(f"--- Processing Domain: {domain} ---")
    print(f"[WORKER {domain}] Processing...")

    stats = {
        "domain": domain, "total_pages": 0, "predicted_articles": 0,
        "new_count": 0, "unchanged_count": 0, "updated_count": 0,
        "filtering_pct": 0.0, "status": "FAILED"
    }

    try:
        # 1. Scrapy and Playwright Crawling Phase
        command = [
            SCRAPY_PYTHON_EXEC, "-m", "scrapy", "crawl", "universal_scraper",
            "-a", f"start_url={start_url}",
            "-s", "LOG_LEVEL=INFO",
            "-s", "TELNETCONSOLE_ENABLED=False"
        ]
        result = subprocess.run(command, cwd=ROOT_DIR, capture_output=True, text=True, errors='replace')

        # Save detailed Scrapy/Playwright output for debugging
        log_to_unified_file(f"--- Technical Scrapy/Playwright logs for {domain} ---\n{result.stderr}")

        # 2. Raw Data Validation & Page Counting
        if os.path.exists(raw_json_absolute):
            try:
                with open(raw_json_absolute, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    stats["total_pages"] = len(data) if isinstance(data, list) else 1
            except Exception:
                stats["total_pages"] = 0

        # 3 Machine learning classification and database persistence
        if stats["total_pages"] > 0:
            predict_script = os.path.join(BASE_DIR, 'scripts', 'predict_new_site.py')
            predict_cmd = [SCRAPY_PYTHON_EXEC, predict_script, raw_json_absolute]

            # Execute classification script and capture stdout tags
            p_res = subprocess.run(predict_cmd, cwd=BASE_DIR, capture_output=True, text=True, errors='replace')
            pred_output = p_res.stdout

            log_to_unified_file(f"Database Operations for {domain}:\n{pred_output}")

            # Parse results based on status tags printed by database_manager
            stats["new_count"] = pred_output.count("[NEW]")
            stats["unchanged_count"] = pred_output.count("[UNCHANGED]")
            stats["updated_count"] = pred_output.count("[UPDATED]")
            stats["predicted_articles"] = stats["new_count"] + stats["unchanged_count"] + stats["updated_count"]

            if stats["predicted_articles"] > 0:
                print(
                    f"   -> {domain}: Completed. New: {stats['new_count']}, Updated: {stats['updated_count']}, Unchanged: {stats['unchanged_count']}")

        # Finalize metrics
        if stats["total_pages"] > 0:
            noise_pages = stats["total_pages"] - stats["predicted_articles"]
            stats["filtering_pct"] = (noise_pages / stats["total_pages"]) * 100
            stats["status"] = "SUCCESS"

        log_to_unified_file(f"Worker FINISHED: {domain}\n" + "-" * 50)
        return stats

    except Exception as e:
        log_to_unified_file(f"Worker ERROR: {domain} -> {str(e)}")
        return stats


if __name__ == "__main__":
    clear_output_directories()
    active_sites = db.get_active_sites()

    print(f"Initializing concurrent crawl for {len(active_sites)} sources...")

    # Start the parallel processing pool
    with Pool(processes=MAX_CONCURRENT_WORKERS) as pool:
        all_stats = pool.map(run_single_crawl, active_sites)

    #table1: PIPELINE PERFORMANCE SUMMARY
    line_width = 95
    summary = "\n" + "=" * line_width + "\n"
    summary += f"{'Source Domain':<30} | {'Pages':<10} | {'Articles':<10} | {'Noise Filtering %':<20}\n"
    summary += "-" * line_width + "\n"

    total_p, total_a, total_new, total_unchanged, total_updated = 0, 0, 0, 0, 0
    for s in all_stats:
        row = f"{s['domain']:<30} | {s['total_pages']:<10} | {s['predicted_articles']:<10} | {s['filtering_pct']:>18.1f}%\n"
        summary += row
        total_p += s['total_pages']
        total_a += s['predicted_articles']
        total_new += s.get('new_count', 0)
        total_unchanged += s.get('unchanged_count', 0)
        total_updated += s.get('updated_count', 0)

    avg_filt = ((total_p - total_a) / total_p * 100) if total_p > 0 else 0
    summary += "-" * line_width + "\n"
    summary += f"{'TOTAL PIPELINE PERFORMANCE':<30} | {total_p:<10} | {total_a:<10} | {avg_filt:>18.1f}% (AVG)\n"
    summary += "=" * line_width + "\n"

    # table 2: STORAGE/ DATABASE EFFICIENCY
    total_ops = total_new + total_unchanged + total_updated


    def get_pct(val):
        return (val / total_ops * 100) if total_ops > 0 else 0


    efficiency_table = "\n Database & Storage Efficiency Statistics (Deduplication Layer)\n"
    efficiency_table += "+" + "-" * 20 + "+" + "-" * 20 + "+" + "-" * 15 + "+" + "-" * 35 + "+\n"
    efficiency_table += f"| {'Log Status':<18} | {'Operation Count':<18} | {'Percentage (%)':<13} | {'System Impact':<33} |\n"
    efficiency_table += "+" + "-" * 20 + "+" + "-" * 20 + "+" + "-" * 15 + "+" + "-" * 35 + "+\n"

    efficiency_table += f"| [NEW]              | {total_new:<18} | {get_pct(total_new):>10.1f}% | {'Dataset Expansion.':<33} |\n"
    efficiency_table += f"| [UNCHANGED]        | {total_unchanged:<18} | {get_pct(total_unchanged):>10.1f}% | {'Storage & I/O Optimization.':<33} |\n"
    efficiency_table += f"| [UPDATED]          | {total_updated:<18} | {get_pct(total_updated):>10.1f}% | {'Content Freshness Maintenance.':<33} |\n"
    efficiency_table += "+" + "-" * 20 + "+" + "-" * 20 + "+" + "-" * 15 + "+" + "-" * 35 + "+\n"

    # Final Output Rendering
    final_output = summary + efficiency_table
    log_to_unified_file(final_output)
    print(final_output)
    print(f"PIPELINE PROCESS COMPLETED. Detailed logs available at: {FINAL_LOG_FILE}")