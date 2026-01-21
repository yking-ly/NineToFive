"""
Batch Orchestrator - Parallel Document Ingestion System

This script manages high-performance parallel ingestion of legal documents:
1. Scans input directory for PDF files
2. Uploads each file to Google Drive (via Apps Script)
3. Processes documents in parallel using MasterIngestPipeline
4. Leverages batch LLM enrichment for 5x speedup

Architecture:
- Multi-threaded execution (configurable worker count)
- Drive upload → Master ingestion pipeline
- Automatic type detection (Statute vs Judgment)
- Batch enrichment (5 sections per LLM call)
"""

import os
import sys
import concurrent.futures
import time
import json
import base64
import requests
from typing import Dict, Any
from master_ingest import MasterIngestPipeline

# ============================================================================
# CONFIGURATION
# ============================================================================

INPUT_DIR = "./info"  # Directory containing PDFs to process
MAX_WORKERS = 3  # Adjust based on CPU/RAM (3 is safe for most systems)
UPLOAD_URL = "https://script.google.com/macros/s/AKfycbyV_2016LPBRF4jBzxVLi0LLCYAW6Hh1ET37KeEeF-JtyDe0oh9p0JOO26-g4TlpiSCzQ/exec"

# ============================================================================
# DRIVE UPLOAD FUNCTION
# ============================================================================

def upload_to_drive(file_path: str) -> Dict[str, Any]:
    """
    Uploads a file to Google Drive via Apps Script.
    
    Args:
        file_path: Path to the PDF file
    
    Returns:
        {
            "driveUrl": "https://drive.google.com/...",
            "thumbnail": "https://lh3.googleusercontent.com/...",
            "filename": "BNS.pdf"
        }
    """
    filename = os.path.basename(file_path)
    
    try:
        # Read and encode file
        with open(file_path, "rb") as f:
            file_content = f.read()
            encoded_content = base64.b64encode(file_content).decode('utf-8')
        
        # Prepare payload
        payload = {
            "file": encoded_content,
            "filename": filename,
            "mimetype": "application/pdf"
        }
        
        # Upload to Google Drive
        print(f"  → Uploading to Drive...")
        response = requests.post(UPLOAD_URL, json=payload, timeout=120)
        
        if response.status_code == 200:
            result = response.json()
            print(f"  ✓ Drive upload successful")
            return {
                "driveUrl": result.get('driveUrl'),
                "thumbnail": result.get('lh3Thumbnail'),
                "filename": filename
            }
        else:
            print(f"  ✗ Drive upload failed: {response.status_code}")
            return {"filename": filename}
            
    except Exception as e:
        print(f"  ✗ Drive upload error: {e}")
        return {"filename": filename}


# ============================================================================
# WORKER FUNCTION
# ============================================================================

def process_single_file(file_path: str) -> str:
    """
    The Worker Function. 
    Handles the lifecycle of ONE document from Disk → Drive → DB.
    
    Pipeline:
        1. Upload to Google Drive
        2. Pass to MasterIngestPipeline (auto-detects type)
        3. Batch enrichment + Dual storage
    
    Args:
        file_path: Full path to PDF file
    
    Returns:
        Status string for logging
    """
    filename = os.path.basename(file_path)
    print(f"\n{'='*60}")
    print(f"[{filename}] Starting processing...")
    print(f"{'='*60}")

    try:
        # STEP 1: DRIVE UPLOAD
        print(f"[{filename}] Phase 1: Drive Upload")
        drive_data = upload_to_drive(file_path)
        
        # STEP 2: MASTER INGESTION
        print(f"[{filename}] Phase 2: Master Ingestion Pipeline")
        pipeline = MasterIngestPipeline()
        
        # Run the full pipeline (Type Detection → Smart Split → Enrich → Store)
        result = pipeline.run(
            file_path=file_path,
            original_filename=filename,
            drive_metadata=drive_data
        )
        
        if result.get("success"):
            doc_type = result.get("doc_type", "UNKNOWN")
            chunks = result.get("chunks_created", 0)
            method = result.get("processing_method", "")
            
            print(f"\n[{filename}] ✅ SUCCESS")
            print(f"  Type: {doc_type}")
            print(f"  Chunks: {chunks}")
            print(f"  Method: {method}")
            
            return f"✓ {filename}: {doc_type} ({chunks} chunks)"
        else:
            error = result.get("error", "Unknown error")
            print(f"\n[{filename}] ✗ FAILED: {error}")
            return f"✗ {filename}: {error}"

    except Exception as e:
        print(f"\n[{filename}] ✗ EXCEPTION: {str(e)}")
        import traceback
        traceback.print_exc()
        return f"✗ {filename}: Exception - {str(e)}"


# ============================================================================
# BATCH JOB ORCHESTRATOR
# ============================================================================

def run_batch_job():
    """
    Phase 1: Parallel Orchestration
    
    Workflow:
        1. Scan input directory for PDFs
        2. Launch parallel workers
        3. Each worker: Upload → Ingest → Store
        4. Report final statistics
    """
    print("\n" + "="*70)
    print("BATCH INGESTION ORCHESTRATOR".center(70))
    print("="*70 + "\n")
    
    # 1. Scan Directory
    input_path = os.path.abspath(INPUT_DIR)
    print(f"📁 Scanning directory: {input_path}")
    
    if not os.path.exists(input_path):
        print(f"❌ Error: Directory not found: {input_path}")
        return
    
    all_files = [
        os.path.join(input_path, f) 
        for f in os.listdir(input_path) 
        if f.lower().endswith('.pdf')
    ]
    
    if not all_files:
        print("⚠️  No PDF files found in directory")
        return
    
    print(f"✓ Found {len(all_files)} PDF documents\n")
    for i, f in enumerate(all_files, 1):
        print(f"  {i}. {os.path.basename(f)}")
    
    print(f"\n🚀 Starting parallel processing with {MAX_WORKERS} workers...\n")
    
    # 2. Parallel Execution
    start_time = time.time()
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # Map the processing function to all files
        results = list(executor.map(process_single_file, all_files))
    
    duration = time.time() - start_time
    
    # 3. Report Results
    print("\n" + "="*70)
    print("BATCH JOB COMPLETE".center(70))
    print("="*70)
    print(f"\n⏱️  Total Duration: {duration:.2f} seconds")
    print(f"📊 Average per file: {duration/len(all_files):.2f} seconds\n")
    
    print("📋 Results:")
    for result in results:
        print(f"  {result}")
    
    # Count successes
    successes = sum(1 for r in results if r.startswith("✓"))
    failures = len(results) - successes
    
    print(f"\n✅ Successful: {successes}/{len(results)}")
    if failures > 0:
        print(f"❌ Failed: {failures}/{len(results)}")
    
    print("\n" + "="*70 + "\n")


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    try:
        run_batch_job()
    except KeyboardInterrupt:
        print("\n\n⚠️  Batch job interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
