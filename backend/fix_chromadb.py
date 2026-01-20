"""
ChromaDB Troubleshooting and Repair Script

This script helps diagnose and fix common ChromaDB issues, particularly
the "Could not connect to tenant default_tenant" error.
"""

import os
import shutil
import sys

# Add backend to path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

def check_chroma_directories():
    """Check if ChromaDB directories exist and their status"""
    print("=" * 60)
    print("Checking ChromaDB directories...")
    print("=" * 60)
    
    shard_dirs = []
    for i in range(3):  # NUM_SHARDS = 3
        shard_dir = os.path.join(BASE_DIR, f"chroma_db_shard_{i}")
        exists = os.path.exists(shard_dir)
        shard_dirs.append((shard_dir, exists))
        
        if exists:
            size = sum(os.path.getsize(os.path.join(dirpath, filename))
                      for dirpath, dirnames, filenames in os.walk(shard_dir)
                      for filename in filenames)
            print(f"✅ Shard {i}: EXISTS ({size / 1024 / 1024:.2f} MB)")
        else:
            print(f"❌ Shard {i}: MISSING")
    
    return shard_dirs

def backup_chroma_directories():
    """Backup existing ChromaDB directories"""
    print("\n" + "=" * 60)
    print("Creating backup of ChromaDB directories...")
    print("=" * 60)
    
    import time
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    backup_dir = os.path.join(BASE_DIR, f"chroma_backup_{timestamp}")
    
    os.makedirs(backup_dir, exist_ok=True)
    
    for i in range(3):
        shard_dir = os.path.join(BASE_DIR, f"chroma_db_shard_{i}")
        if os.path.exists(shard_dir):
            backup_shard = os.path.join(backup_dir, f"chroma_db_shard_{i}")
            shutil.copytree(shard_dir, backup_shard)
            print(f"✅ Backed up shard {i}")
    
    print(f"\n📁 Backup created at: {backup_dir}")
    return backup_dir

def reset_chroma_directories():
    """Delete and recreate ChromaDB directories"""
    print("\n" + "=" * 60)
    print("Resetting ChromaDB directories...")
    print("=" * 60)
    
    for i in range(3):
        shard_dir = os.path.join(BASE_DIR, f"chroma_db_shard_{i}")
        if os.path.exists(shard_dir):
            shutil.rmtree(shard_dir)
            print(f"🗑️  Deleted shard {i}")
        
        os.makedirs(shard_dir, exist_ok=True)
        print(f"✅ Created fresh shard {i}")

def test_chroma_initialization():
    """Test if ChromaDB can be initialized properly"""
    print("\n" + "=" * 60)
    print("Testing ChromaDB initialization...")
    print("=" * 60)
    
    try:
        import core
        print("Loading embedding model...")
        core.get_embedding_function()
        print("✅ Embedding model loaded")
        
        print("\nInitializing database shards...")
        dbs = core.get_dbs()
        print(f"✅ Successfully initialized {len(dbs)} shards")
        
        # Test adding a document
        print("\nTesting document addition...")
        from langchain_core.documents import Document
        test_doc = Document(page_content="Test document", metadata={"test": True})
        
        ids = dbs[0].add_documents([test_doc])
        print(f"✅ Successfully added test document (ID: {ids[0]})")
        
        # Test search
        print("\nTesting search...")
        results = dbs[0].similarity_search("test", k=1)
        print(f"✅ Search successful, found {len(results)} results")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("\n" + "=" * 60)
    print("ChromaDB Troubleshooting Script")
    print("=" * 60)
    
    # Step 1: Check directories
    shard_dirs = check_chroma_directories()
    
    # Step 2: Ask user what to do
    print("\n" + "=" * 60)
    print("What would you like to do?")
    print("=" * 60)
    print("1. Test ChromaDB initialization (recommended first)")
    print("2. Backup existing ChromaDB directories")
    print("3. Reset ChromaDB (delete and recreate - DESTRUCTIVE)")
    print("4. Backup AND reset ChromaDB")
    print("5. Exit")
    
    choice = input("\nEnter your choice (1-5): ").strip()
    
    if choice == "1":
        success = test_chroma_initialization()
        if success:
            print("\n✅ ChromaDB is working correctly!")
        else:
            print("\n❌ ChromaDB has issues. Consider option 4 (backup and reset)")
    
    elif choice == "2":
        backup_dir = backup_chroma_directories()
        print(f"\n✅ Backup complete: {backup_dir}")
    
    elif choice == "3":
        confirm = input("\n⚠️  This will DELETE all ChromaDB data. Are you sure? (yes/no): ")
        if confirm.lower() == "yes":
            reset_chroma_directories()
            print("\n✅ Reset complete. Run batch_ingest.py to re-index your documents.")
        else:
            print("❌ Reset cancelled")
    
    elif choice == "4":
        confirm = input("\n⚠️  This will BACKUP then DELETE all ChromaDB data. Continue? (yes/no): ")
        if confirm.lower() == "yes":
            backup_dir = backup_chroma_directories()
            reset_chroma_directories()
            print(f"\n✅ Backup created at: {backup_dir}")
            print("✅ Reset complete. Run batch_ingest.py to re-index your documents.")
        else:
            print("❌ Operation cancelled")
    
    elif choice == "5":
        print("Exiting...")
    
    else:
        print("Invalid choice")

if __name__ == "__main__":
    main()
