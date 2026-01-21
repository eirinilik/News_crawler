# # import pandas as pd
# # import json
# # import re
# # import os
# # import sys
# # from sklearn.ensemble import RandomForestClassifier
# # from sklearn.preprocessing import LabelEncoder
# # import joblib
# # from urllib.parse import urlparse
# # from typing import Dict, List, Any
# #
# # # --- CRITICAL PATH FIX FOR DATABASE MANAGER ---
# # # 1. Define the directory containing core modules (database_manager.py)
# # # This directory is one level up from 'scripts/' (i.e., news_crawler/).
# # CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
# # CRAWLER_DIR = os.path.dirname(CURRENT_DIR)
# # ROOT_DIR = os.path.dirname(CRAWLER_DIR)
# #
# # if CRAWLER_DIR not in sys.path:
# #     sys.path.append(CRAWLER_DIR)
# #
# # try:
# #     import database_manager as db
# # except ImportError as e:
# #     sys.stderr.write(f"❌ CRITICAL: Could not import database_manager: {e}\n")
# #     sys.exit(1)
# #
# # MODELS_DIR = os.path.join(CRAWLER_DIR, "models")
# # OUTPUT_DIR = os.path.join(ROOT_DIR, "predictions")
# #
# # # CRITICAL: This feature list must match exactly the features used during training.
# # REQUIRED_FEATURES = [
# #     "url_length", "url_depth", "title_length", "text_length", "text_density", "has_date_pattern_in_url",
# #     "xpath_depth", "xpath_contains_article", "xpath_contains_main_content", "xpath_contains_story",
# #     "is_article_in_category",
# #     # Note: 'has_trafilatura_meta' is handled as an optional feature in fillna logic
# # ]
# #
# #
# # # This function extracts features from an XPath.
# # def extract_xpath_features(xpath: str) -> Dict[str, Any]:
# #     """Extracts structural features from an XPath string."""
# #     features = {
# #         'xpath_depth': 0,
# #         'xpath_contains_article': False,
# #         'xpath_contains_main_content': False,
# #         'xpath_contains_story': False
# #     }
# #
# #     if xpath and isinstance(xpath, str):
# #         # FIX: XPath depth calculation (number of slashes minus initial ones)
# #         # Using count('/') is generally sufficient for relative path depth.
# #         features['xpath_depth'] = xpath.count('/')
# #
# #         if re.search(r'\b(article)\b', xpath, re.IGNORECASE):
# #             features['xpath_contains_article'] = True
# #         if re.search(r'\b(main|content)\b', xpath, re.IGNORECASE):
# #             features['xpath_contains_main_content'] = True
# #         if re.search(r'\b(story)\b', xpath, re.IGNORECASE):
# #             features['xpath_contains_story'] = True
# #
# #     return features
# #
# #
# # def extract_content_features(text_length: int, is_category_link: bool) -> Dict[str, Any]:
# #     """
# #     Extracts content-based features.
# #     NOTE: The core logic for is_article_in_category is now defined in the spider,
# #     but this function ensures the necessary feature is constructed consistently.
# #     """
# #     # This logic is maintained here for consistency with the original training features
# #     features = {
# #         # This feature relies on preliminary length checks done in the spider.
# #         'is_article_in_category': (is_category_link and text_length and text_length > 100)
# #     }
# #     return features
# #
# #
# # def process_single_file(input_file_path: str):
# #     """Loads data, performs prediction, and saves results to JSON/DB."""
# #
# #     os.makedirs(OUTPUT_DIR, exist_ok=True)
# #
# #     # 1. Load the pre-trained model and label encoder
# #     try:
# #         # FIX: MODELS_DIR is now correctly calculated (news_crawler/models)
# #         clf = joblib.load(os.path.join(MODELS_DIR, "link_classifier.pkl"))
# #         label_encoder = joblib.load(os.path.join(MODELS_DIR, "label_encoder.pkl"))
# #         print(f"✅ Model and Encoder loaded successfully.")
# #     except FileNotFoundError:
# #         print(f"❌ Model or Encoder not found in {MODELS_DIR}. Please run the training script first.")
# #         sys.exit(1)
# #     except Exception as e:
# #         print(f"❌ Error loading model/encoder: {e}")
# #         sys.exit(1)
# #
# #
# #     # 2. Process the input file (Scraped raw data)
# #     try:
# #         # Regex to find a clean JSON object: starts with { and ends with }
# #         json_object_regex = re.compile(r'(\{.*?\})')
# #
# #         unlabeled_data = []
# #
# #         with open(input_file_path, "r", encoding="utf-8") as f:
# #             for line in f:
# #                 line = line.strip()
# #                 if not line:
# #                     continue
# #
# #                 match = json_object_regex.search(line)
# #
# #                 if match:
# #                     json_string = match.group(1)
# #                     try:
# #                         # Each line should be a valid JSON object
# #                         unlabeled_data.append(json.loads(json_string))
# #                     except json.JSONDecodeError:
# #                         sys.stderr.write(
# #                             f"❌ Warning: Could not decode JSON line in {input_file_path}. Line start: {json_string[:50]}...\n")
# #                         continue
# #                 else:
# #                     # Skips lines that are just brackets: ][, [, ], etc.
# #                     if len(line) > 1:
# #                         sys.stderr.write(f"❌ Warning: Line skipped (not a valid object): {line[:30]}...\n")
# #                     continue
# #
# #         df_unlabeled = pd.DataFrame(unlabeled_data)
# #
# #     except FileNotFoundError:
# #         print(f"❌ Prediction input file not found: {input_file_path}. Skipping.")
# #         return
# #     except Exception as e:
# #         sys.stderr.write(f"❌ Critical Error reading data from file {input_file_path}: {e}\n")
# #         sys.exit(1)
# #
# #     if df_unlabeled.empty:
# #         print(f"❗ No data to predict in file {input_file_path}.")
# #         return
# #
# #     # 3. Feature Extraction & Cleaning (For model prediction)
# #
# #     # Extract XPath features
# #     xpath_features_unlabeled = df_unlabeled.get('source_xpath', pd.Series([])).apply(extract_xpath_features)
# #     df_xpath_unlabeled = pd.DataFrame(xpath_features_unlabeled.tolist())
# #
# #     # Extract Content features
# #     content_features_unlabeled = df_unlabeled.apply(
# #         lambda row: extract_content_features(row.get('text_length', 0), row.get('is_category_link', False)), axis=1
# #     )
# #
# #     # Re-insert 'is_article_in_category' (optional, but ensures presence)
# #     df_unlabeled['is_article_in_category'] = [f['is_article_in_category'] for f in content_features_unlabeled]
# #
# #     df_unlabeled = pd.concat([
# #         df_unlabeled.reset_index(drop=True),
# #         df_xpath_unlabeled.reset_index(drop=True),
# #     ], axis=1)
# #
# #     # 4. Prepare features for the model
# #
# #     # Add missing columns with zero fill to match training data structure
# #     for feature in REQUIRED_FEATURES:
# #         if feature not in df_unlabeled.columns:
# #             df_unlabeled[feature] = 0
# #
# #     try:
# #         # Ensure all features are numeric (Float) and not Booleans/Objects
# #         X_unlabeled = df_unlabeled[REQUIRED_FEATURES].astype(float).fillna(0)
# #     except KeyError as e:
# #         sys.stderr.write(f"❌ CRITICAL: Missing required feature column after processing: {e}.\n")
# #         sys.exit(1)
# #     except Exception as e:
# #         sys.stderr.write(f"❌ CRITICAL: Error preparing features for model: {e}\n")
# #         sys.exit(1)
# #
# #     # 5. Predict labels and add them to the DataFrame
# #     try:
# #         clf = joblib.load(os.path.join(MODELS_DIR, "link_classifier.pkl"))
# #         y_pred_encoded = clf.predict(X_unlabeled)
# #         label_encoder = joblib.load(os.path.join(MODELS_DIR, "label_encoder.pkl"))
# #         y_pred = label_encoder.inverse_transform(y_pred_encoded)
# #         df_unlabeled['predicted_label'] = y_pred
# #         print(f"✅ Prediction completed successfully.")
# #     except ValueError as e:
# #         sys.stderr.write(f"❌ Prediction Error: {e}. Check if features columns match the training data (e.g., column count).\n")
# #         sys.exit(1)
# #
# #     # 6. Save prediction JSON & Save to DB (The Unified Output)
# #
# #     if df_unlabeled.empty:
# #         return
# #
# #     first_url = df_unlabeled.iloc[0]["url"]
# #     domain_netloc = urlparse(first_url).netloc
# #
# #     # 6.1. Save Prediction JSON
# #     domain_safe = domain_netloc.replace('.', '_')
# #     output_filename = os.path.join(OUTPUT_DIR, f"predictions_{domain_safe}.json")
# #
# #     df_unlabeled.to_json(
# #         output_filename,
# #         orient="records",
# #         indent=2,
# #         force_ascii=False
# #     )
# #     print(f"\n Predictions for {domain_netloc} saved successfully to {output_filename}")
# #
# #     # 6.2. SAVE TO MYSQL/DB
# #
# #     try:
# #         # Load site mapping once for performance
# #         site_rows = db.get_active_sites()
# #         domain_to_id = {db.normalize_domain(s["domain"]): s["id"] for s in site_rows}
# #     except Exception as e:
# #         sys.stderr.write(f"❌ Error loading site mapping for DB Save: {e}\n")
# #         return
# #
# #     normalized_domain = db.normalize_domain(domain_netloc)
# #     site_id = domain_to_id.get(normalized_domain)
# #
# #     if site_id is None:
# #         sys.stderr.write(f"⚠️ Warning: Site ID not found for {domain_netloc} (or {normalized_domain}). Skipping DB save.\n")
# #         return
# #
# #     articles_saved = 0
# #     # The hashlib module is imported at the top of database_manager.py
# #     for index, row in df_unlabeled.iterrows():
# #         # Only process items predicted as 'article'
# #         if row['predicted_label'] == "article":
# #             body_content = row.get("article_body") or ""
# #             title_content = row.get("title") or "No Title Found"
# #
# #
# #             db.save_article(
# #                 site_id=site_id,
# #                 url=row["url"],
# #                 title=title_content,
# #                 body=body_content,
# #                 image_url=(row.get("image_urls") or [None])[0],
# #             )
# #             articles_saved += 1
# #
# #     print(f"✅ DB Save Complete: {articles_saved} articles inserted/updated for {domain_netloc}")
# #
# #
# # if __name__ == "__main__":
# #
# #     # --- REQUIRED: Get the path of the input file from the args ---
# #     if len(sys.argv) < 2:
# #         sys.stderr.write("Usage: python predict_new_site.py <path_to_input_json_file>\n")
# #         sys.exit(1)
# #
# #     input_file_path = sys.argv[1]
# #
# #     # Check if the provided path is absolute or relative
# #     base_dir_for_rel_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# #
# #     if not os.path.isabs(input_file_path):
# #         # Correct the relative path
# #         input_file_path = os.path.join(base_dir_for_rel_path, input_file_path)
# #
# #     if not os.path.exists(input_file_path):
# #         sys.stderr.write(f"❌ Input file not found: {input_file_path}\n")
# #         sys.exit(1)
# #
# #     process_single_file(input_file_path)
# import pandas as pd
# import json
# import re
# import os
# import sys
# import joblib
# from urllib.parse import urlparse
# from typing import Dict, List, Any
#
# # ==============================================================================
# # --- 🛠️ DYNAMIC PATH CONFIGURATION (PROJECT ROOT) ---
# # ==============================================================================
#
# # File location: news_crawler/scripts/
# CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
# CRAWLER_DIR = os.path.dirname(CURRENT_DIR)
# ROOT_DIR = os.path.dirname(CRAWLER_DIR)
#
# # Add project root to sys.path to enable core module imports
# if CRAWLER_DIR not in sys.path:
#     sys.path.append(CRAWLER_DIR)
#
# try:
#     import database_manager as db
# except ImportError as e:
#     print(f"❌ CRITICAL: Could not import database_manager: {e}")
#     sys.exit(1)
#
# # Directory Definitions
# MODELS_DIR = os.path.join(CRAWLER_DIR, "models")
# OUTPUT_DIR = os.path.join(ROOT_DIR, "predictions")
#
# # Feature list must match training data exactly
# REQUIRED_FEATURES = [
#     "url_length", "url_depth", "title_length", "text_length", "text_density", "has_date_pattern_in_url",
#     "xpath_depth", "xpath_contains_article", "xpath_contains_main_content", "xpath_contains_story",
#     "is_article_in_category"
# ]
#
#
# def extract_xpath_features(xpath: str) -> Dict[str, Any]:
#     """Extracts structural features from an XPath string."""
#     features = {
#         'xpath_depth': 0,
#         'xpath_contains_article': False,
#         'xpath_contains_main_content': False,
#         'xpath_contains_story': False
#     }
#     if xpath and isinstance(xpath, str):
#         features['xpath_depth'] = xpath.count('/')
#         if re.search(r'\b(article)\b', xpath, re.IGNORECASE): features['xpath_contains_article'] = True
#         if re.search(r'\b(main|content)\b', xpath, re.IGNORECASE): features['xpath_contains_main_content'] = True
#         if re.search(r'\b(story)\b', xpath, re.IGNORECASE): features['xpath_contains_story'] = True
#     return features
#
#
# def process_single_file(input_file_path: str):
#     """Loads scraped data, performs ML prediction, and syncs results to DB."""
#     os.makedirs(OUTPUT_DIR, exist_ok=True)
#     domain_safe = "unknown_domain"
#
#     # 1. Load ML Model and Encoder
#     try:
#         clf = joblib.load(os.path.join(MODELS_DIR, "link_classifier.pkl"))
#         label_encoder = joblib.load(os.path.join(MODELS_DIR, "label_encoder.pkl"))
#         print(f"✅ Model/Encoder loaded from {MODELS_DIR}")
#     except Exception as e:
#         print(f"❌ Error loading model: {e}")
#         return
#
#     # 2. Robust Data Parsing (Supports both JSON Arrays and JSON Lines)
#     try:
#         with open(input_file_path, 'r', encoding='utf-8', errors='replace') as f:
#             data = json.load(f)
#
#         df = pd.DataFrame(data)
#     except Exception as e:
#         print(f"❌ Failed to read or parse file: {e}")
#         return
#
#         df = pd.DataFrame(data)
#     except Exception as e:
#         print(f"❌ Failed to read or parse file: {e}")
#         return
#
#     # Check for valid data
#     if df.empty or 'url' not in df.columns:
#         print(f"❗ No valid records with 'url' found in {input_file_path}")
#         return
#
#     # Clean empty URLs
#     df = df[df['url'].notna()]
#
#     # Extract domain for safe file naming
#     try:
#         first_url = df.iloc[0]["url"]
#         domain_safe = urlparse(first_url).netloc.replace('.', '_')
#     except Exception:
#         pass
#
#     print(f"📊 Processing {len(df)} records for {domain_safe}...")
#
#     # 3. Feature Engineering Layer
#     # Determine the correct XPath column (legacy support for 'source_xpath')
#     xpath_col = 'xpath' if 'xpath' in df.columns and df['xpath'].notna().any() else 'source_xpath'
#     xpath_series = df.get(xpath_col, pd.Series([""] * len(df)))
#     xpath_features = xpath_series.apply(lambda x: extract_xpath_features(x if isinstance(x, str) else ""))
#     df_xpath = pd.DataFrame(xpath_features.tolist())
#
#     # Concatenate extracted features with the original data
#     df = pd.concat([df.reset_index(drop=True), df_xpath.reset_index(drop=True)], axis=1)
#
#     # Ensure all required model features exist (fill with 0 if missing)
#     for feature in REQUIRED_FEATURES:
#         if feature not in df.columns:
#             df[feature] = 0
#
#     # 4. Model Prediction (Random Forest)
#     try:
#         # Cast features to float and handle missing values
#         X = df[REQUIRED_FEATURES].astype(float).fillna(0)
#         df['predicted_label'] = label_encoder.inverse_transform(clf.predict(X))
#
#         # Log distribution for verification
#         counts = df['predicted_label'].value_counts()
#         print(f"📈 Prediction distribution: {counts.to_dict()}")
#     except Exception as e:
#         print(f"❌ Prediction Error: {e}")
#         return
#
#     # 5. Export Predictions to JSON
#     output_filename = os.path.join(OUTPUT_DIR, f"predictions_{domain_safe}.json")
#     df.to_json(output_filename, orient="records", indent=2, force_ascii=False)
#
#     # 6. Database Synchronization Layer
#     try:
#         # Load active sites from DB for mapping
#         site_rows = db.get_active_sites()
#         domain_to_id = {db.normalize_domain(s["domain"]): s["id"] for s in site_rows}
#
#         articles_saved = 0
#         for _, row in df.iterrows():
#             # Process only records predicted as 'article'
#             if str(row.get('predicted_label', '')).lower() == "article":
#                 url = row.get("url")
#                 normalized_domain = db.normalize_domain(urlparse(url).netloc)
#                 site_id = domain_to_id.get(normalized_domain)
#
#                 if site_id:
#                     # Convert image list to single string for the database
#                     img_list = row.get("image_urls", [])
#                     final_img = img_list[0] if isinstance(img_list, list) and len(img_list) > 0 else None
#
#                     # Persistence via MD5 deduplication logic
#                     db.save_article(
#                         site_id=site_id,
#                         url=url,
#                         title=row.get("title") or "No Title",
#                         body=row.get("article_body") or "",
#                         image_url=final_img
#                     )
#                     articles_saved += 1
#
#         print(f"✅ DB Sync Complete: {articles_saved} articles saved for {domain_safe}")
#     except Exception as e:
#         print(f"❌ DB Sync Error: {e}")
#
#
# if __name__ == "__main__":
#     if len(sys.argv) > 1:
#         process_single_file(sys.argv[1])
#     else:
#         print("Usage: python predict_new_site.py <path_to_json_file>")

import pandas as pd
import json
import re
import os
import sys
import joblib
from urllib.parse import urlparse

import pandas as pd
import json
import re
import os
import sys
import joblib
from urllib.parse import urlparse

# Paths configuration
current_dir = os.path.dirname(os.path.abspath(__file__))
crawler_dir = os.path.dirname(current_dir)
root_dir = os.path.dirname(crawler_dir)

if crawler_dir not in sys.path:
    sys.path.append(crawler_dir)

try:
    import database_manager as db
except ImportError:
    print("Could not import database_manager")
    sys.exit(1)

models_path = os.path.join(crawler_dir, "models")
output_path = os.path.join(root_dir, "predictions")

REQUIRED_FEATURES = [
    "url_length", "url_depth", "title_length", "text_length", "text_density",
    "has_date_pattern_in_url", "xpath_depth", "xpath_contains_article",
    "xpath_contains_main_content", "xpath_contains_story", "is_article_in_category"
]


def get_xpath_features(xpath):
    data = {'xpath_depth': 0, 'xpath_contains_article': 0, 'xpath_contains_main_content': 0, 'xpath_contains_story': 0}
    if xpath and isinstance(xpath, str):
        data['xpath_depth'] = xpath.count('/')
        if re.search(r'article', xpath, re.I): data['xpath_contains_article'] = 1
        if re.search(r'main|content', xpath, re.I): data['xpath_contains_main_content'] = 1
        if re.search(r'story', xpath, re.I): data['xpath_contains_story'] = 1
    return data


def run_prediction(file_path):
    os.makedirs(output_path, exist_ok=True)

    try:
        model = joblib.load(os.path.join(models_path, "link_classifier.pkl"))
        encoder = joblib.load(os.path.join(models_path, "label_encoder.pkl"))
    except Exception as e:
        print(f"Error loading models: {e}")
        return

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)
        df = pd.DataFrame(raw_data)
    except Exception as e:
        print(f"Error reading file: {e}")
        return

    if df.empty: return

    xpath_col = 'xpath' if 'xpath' in df.columns else 'source_xpath'
    xpath_data = df[xpath_col].apply(lambda x: get_xpath_features(x if isinstance(x, str) else ""))
    df_features = pd.DataFrame(xpath_data.tolist())
    df = pd.concat([df.reset_index(drop=True), df_features.reset_index(drop=True)], axis=1)

    for col in REQUIRED_FEATURES:
        if col not in df.columns: df[col] = 0

    try:
        X = df[REQUIRED_FEATURES].astype(float).fillna(0)
        df['predicted_label'] = encoder.inverse_transform(model.predict(X))
    except Exception as e:
        print(f"Prediction failed: {e}")
        return

    # --- ΔΙΟΡΘΩΣΗ 1: ΑΠΟΘΗΚΕΥΣΗ JSON ΜΕ ΚΑΝΟΝΙΚΑ ΕΛΛΗΝΙΚΑ ---
    first_url = df.iloc[0]["url"]
    domain_name = urlparse(first_url).netloc.replace('.', '_')
    output_file = os.path.join(output_path, f"preds_{domain_name}.json")

    # Χρήση force_ascii=False για να μην βλέπουμε \u03b2
    df.to_json(output_file, orient="records", indent=2, force_ascii=False)

    try:
        sites = db.get_active_sites()
        site_map = {db.normalize_domain(s["domain"]): s["id"] for s in sites}

        for _, row in df.iterrows():
            if str(row.get('predicted_label', '')).lower() == "article":
                url = row["url"]
                domain = db.normalize_domain(urlparse(url).netloc)
                sid = site_map.get(domain)

                if sid:
                    imgs = row.get("image_urls", [])
                    img = imgs[0] if isinstance(imgs, list) and len(imgs) > 0 else None

                    # Η save_article θα στείλει τα δεδομένα στη MySQL
                    db.save_article(
                        site_id=sid,
                        url=url,
                        title=row.get("title", "No Title"),
                        body=row.get("article_body", ""),
                        image_url=img
                    )
    except Exception as e:
        print(f"Database error: {e}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        run_prediction(sys.argv[1])
    else:
        print("No input file provided.")