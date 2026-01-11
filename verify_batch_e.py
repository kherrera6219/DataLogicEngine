from backend.knowledge_algorithm.registry import KARegistry
from backend.knowledge_algorithm import *
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TestBatchE")

def verify_batch_e():
    batch_e_ids = [
        "KA-047", "KA-054", "KA-056", "KA-087", "KA-097", "KA-098", "KA-114"
    ]
    logger.info(f"Verifying {len(batch_e_ids)} Batch E KAs...")
    
    missing = []
    for ka_id in batch_e_ids:
        ka = KARegistry.get_metadata(ka_id)
        if ka:
            logger.info(f"✅ Found {ka_id}: {ka.name}")
        else:
            logger.error(f"❌ Missing {ka_id}")
            missing.append(ka_id)
            
    if missing:
        logger.error("Batch E Verification FAILED.")
        return False
    
    logger.info("Batch E Verification PASSED.")
    return True

if __name__ == "__main__":
    verify_batch_e()
