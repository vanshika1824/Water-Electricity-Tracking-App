"""
AquaWatt Phase 2: Dataset Acquisition and Integrity Verification Script.
Downloads verified public benchmark datasets for electricity and water tracking,
computes SHA-256 checksums, preserves untouched raw archives,
and extracts inspection copies.
"""

import hashlib
import json
import os
import shutil
import time
import urllib.request
import zipfile

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(BASE_DIR, "data")
RAW_ELE_DIR = os.path.join(DATA_DIR, "raw", "electricity")
RAW_WAT_DIR = os.path.join(DATA_DIR, "raw", "water")
EXT_ELE_DIR = os.path.join(DATA_DIR, "extracted", "electricity")
EXT_WAT_DIR = os.path.join(DATA_DIR, "extracted", "water")

UCI_URL = "https://archive.ics.uci.edu/static/public/235/individual+household+electric+power+consumption.zip"
ZENODO_ZIP_URL = "https://zenodo.org/api/records/22076411/files/HSB_Living_Lab_Data_Package.zip/content"
ZENODO_VERIFY_PY = "https://zenodo.org/api/records/22076411/files/verify_R5.py/content"
ZENODO_VERIFY_JSON = "https://zenodo.org/api/records/22076411/files/verified_numbers_R5.json/content"


def compute_sha256(filepath: str) -> str:
    """Compute SHA-256 hash of a file."""
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            sha256.update(chunk)
    return sha256.hexdigest()


def download_file(url: str, dest_path: str, user_agent: str = "AquaWatt-Research-Agent/1.0"):
    """Download a file with streaming chunks and progress display."""
    print(f"Downloading from: {url}")
    print(f"Saving to: {dest_path}")
    req = urllib.request.Request(url, headers={"User-Agent": user_agent})
    start_time = time.time()
    
    with urllib.request.urlopen(req) as response, open(dest_path, "wb") as out_file:
        total_size = response.headers.get("Content-Length")
        total_size = int(total_size) if total_size else None
        downloaded = 0
        chunk_size = 65536
        
        while True:
            chunk = response.read(chunk_size)
            if not chunk:
                break
            out_file.write(chunk)
            downloaded += len(chunk)
            if total_size:
                pct = (downloaded / total_size) * 100
                print(f"\r  Downloaded: {downloaded / 1024 / 1024:.2f} MB / {total_size / 1024 / 1024:.2f} MB ({pct:.1f}%)", end="")
            else:
                print(f"\r  Downloaded: {downloaded / 1024 / 1024:.2f} MB", end="")
        print()
    elapsed = time.time() - start_time
    size_mb = os.path.getsize(dest_path) / (1024 * 1024)
    print(f"Completed in {elapsed:.2f}s ({size_mb:.2f} MB, {size_mb / max(elapsed, 0.01):.2f} MB/s)")


def extract_archive(zip_path: str, extract_to: str):
    """Safely extract a ZIP archive into destination folder."""
    print(f"\nExtracting: {zip_path} -> {extract_to}")
    os.makedirs(extract_to, exist_ok=True)
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(extract_to)
        print(f"Extracted {len(zf.namelist())} entries.")


def inspect_extracted_folder(folder_path: str) -> list:
    """Walk through extracted folder and inspect all files."""
    results = []
    for root, dirs, files in os.walk(folder_path):
        for f in files:
            full_p = os.path.join(root, f)
            rel_p = os.path.relpath(full_p, folder_path)
            size = os.path.getsize(full_p)
            sha = compute_sha256(full_p)
            
            # Count lines if text/csv
            line_count = None
            sample_header = None
            if f.endswith((".txt", ".csv", ".json", ".py", ".md")):
                try:
                    with open(full_p, "r", encoding="utf-8", errors="replace") as tf:
                        first_line = tf.readline().strip()
                        sample_header = first_line[:150]
                        # count lines
                        count = 1
                        for _ in tf:
                            count += 1
                        line_count = count
                except Exception as e:
                    sample_header = f"Read error: {str(e)}"

            results.append({
                "relative_path": rel_p,
                "file_name": f,
                "size_bytes": size,
                "size_mb": round(size / (1024 * 1024), 2),
                "sha256": sha,
                "line_count": line_count,
                "header_sample": sample_header
            })
    return results


def main():
    os.makedirs(RAW_ELE_DIR, exist_ok=True)
    os.makedirs(RAW_WAT_DIR, exist_ok=True)
    os.makedirs(EXT_ELE_DIR, exist_ok=True)
    os.makedirs(EXT_WAT_DIR, exist_ok=True)

    summary = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "downloads": [],
        "extractions": {}
    }

    # 1. Download UCI Electricity
    print("=" * 60)
    print("STEP 1: UCI Electricity Dataset Download")
    print("=" * 60)
    uci_dest = os.path.join(RAW_ELE_DIR, "individual+household+electric+power+consumption.zip")
    download_file(UCI_URL, uci_dest)
    uci_sha = compute_sha256(uci_dest)
    uci_size = os.path.getsize(uci_dest)
    print(f"UCI Raw Archive SHA-256: {uci_sha}")
    print(f"UCI Raw Archive Size: {uci_size:,} bytes ({uci_size / 1024 / 1024:.2f} MB)")
    
    summary["downloads"].append({
        "dataset": "UCI Individual Household Electric Power Consumption",
        "url": UCI_URL,
        "local_path": uci_dest,
        "size_bytes": uci_size,
        "sha256": uci_sha,
        "license": "CC BY 4.0"
    })

    # 2. Download HSB Living Lab Water
    print("\n" + "=" * 60)
    print("STEP 2: HSB Living Lab Water Dataset Download (Zenodo 22076411)")
    print("=" * 60)
    zenodo_dest = os.path.join(RAW_WAT_DIR, "HSB_Living_Lab_Data_Package.zip")
    download_file(ZENODO_ZIP_URL, zenodo_dest)
    zenodo_sha = compute_sha256(zenodo_dest)
    zenodo_size = os.path.getsize(zenodo_dest)
    print(f"Zenodo Raw Archive SHA-256: {zenodo_sha}")
    print(f"Zenodo Raw Archive Size: {zenodo_size:,} bytes ({zenodo_size / 1024 / 1024:.2f} MB)")

    # Companion files
    v_py_dest = os.path.join(RAW_WAT_DIR, "verify_R5.py")
    download_file(ZENODO_VERIFY_PY, v_py_dest)
    v_json_dest = os.path.join(RAW_WAT_DIR, "verified_numbers_R5.json")
    download_file(ZENODO_VERIFY_JSON, v_json_dest)

    summary["downloads"].append({
        "dataset": "HSB Living Lab Fixture-Level Household Water Consumption Dataset",
        "url": ZENODO_ZIP_URL,
        "local_path": zenodo_dest,
        "size_bytes": zenodo_size,
        "sha256": zenodo_sha,
        "license": "CC BY 4.0",
        "companion_files": [
            {"name": "verify_R5.py", "sha256": compute_sha256(v_py_dest)},
            {"name": "verified_numbers_R5.json", "sha256": compute_sha256(v_json_dest)}
        ]
    })

    # 3. Extract Archives
    print("\n" + "=" * 60)
    print("STEP 3: Safe Extraction of Inspection Copies")
    print("=" * 60)
    extract_archive(uci_dest, EXT_ELE_DIR)
    extract_archive(zenodo_dest, EXT_WAT_DIR)

    # 4. Inspect Extracted Files
    print("\n" + "=" * 60)
    print("STEP 4: Inspection of Extracted File Structures")
    print("=" * 60)
    summary["extractions"]["electricity"] = inspect_extracted_folder(EXT_ELE_DIR)
    summary["extractions"]["water"] = inspect_extracted_folder(EXT_WAT_DIR)

    report_json_path = os.path.join(BASE_DIR, "machine_learning", "acquisition_summary.json")
    with open(report_json_path, "w", encoding="utf-8") as rf:
        json.dump(summary, rf, indent=2)
    print(f"\nSaved acquisition summary JSON to: {report_json_path}")


if __name__ == "__main__":
    main()

