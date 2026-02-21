import argparse
import json
import logging
import os
from pathlib import Path
import sys

# Ensure project root is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.embedder import AuraEmbedder
from app.utils.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def build_vector_store(folder_name: str) -> None:
    """
    Reads all processed JSON files from the specified folder.
    Embeds both Index A (Abstracts) and Index B (Body chunks) into ChromaDB.
    """
    input_dir = settings.PROCESSED_DATA_DIR / folder_name
    
    if not input_dir.exists():
        logger.error(f"Input directory does not exist: {input_dir}")
        return
        
    embedder = AuraEmbedder()
    json_files = list(input_dir.glob("*.json"))
    
    if not json_files:
        logger.warning(f"No processed JSON files found in {input_dir}")
        return
        
    logger.info(f"Found {len(json_files)} processed files in {input_dir}. Starting embedding process...")
    
    success_count = 0
    error_count = 0
    skipped_count = 0 # Track skipped files (e.g. ones that were already embedded)
    
    for file_path in json_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                article_data = json.load(f)
                
            # Embedder handles Index A vs B internally and skips duplicates
            success = embedder.ingest_article(article_data)
            
            if success:
                success_count += 1
            else:
                error_count += 1
                
            if (success_count + error_count) % 20 == 0:
                logger.info(f"Processed {success_count + error_count} files so far...")
                
        except Exception as e:
            logger.error(f"Error reading/embedding file {file_path.name}: {e}")
            error_count += 1

    logger.info("====================================")
    logger.info(f"Vector Store Build Complete for '{folder_name}'")
    logger.info(f"Successfully processed: {success_count}")
    logger.info(f"Failed to process: {error_count}")
    logger.info(f"Database Path: {settings.CHROMA_DB_DIR}")
    logger.info("====================================")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Embed processed AuraQuery documents into ChromaDB.")
    parser.add_argument(
        "--folder", 
        type=str, 
        default="hht", 
        help="The name of the subfolder under data/processed/ to embed. Eg: 'hht'."
    )
    
    args = parser.parse_args()
    build_vector_store(folder_name=args.folder)
