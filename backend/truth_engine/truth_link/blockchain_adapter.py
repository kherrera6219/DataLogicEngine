"""
Blockchain Adapter
-----------------
Implements Merkle Tree hashing and blockchain anchoring for immutable audit trails.
"""
import hashlib
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, UTC

logger = logging.getLogger(__name__)

class MerkleTree:
    """
    Merkle Tree implementation for creating tamper-proof audit trails.
    """
    
    def __init__(self, data_blocks: List[str]):
        self.leaves = [self._hash(block) for block in data_blocks]
        self.root = self._build_tree(self.leaves)
    
    def _hash(self, data: str) -> str:
        """Create SHA-256 hash of data."""
        return hashlib.sha256(data.encode('utf-8')).hexdigest()
    
    def _build_tree(self, nodes: List[str]) -> str:
        """Recursively build Merkle tree and return root hash."""
        if len(nodes) == 0:
            return self._hash("")
        if len(nodes) == 1:
            return nodes[0]
        
        # Pair up nodes and hash them together
        next_level = []
        for i in range(0, len(nodes), 2):
            left = nodes[i]
            right = nodes[i + 1] if i + 1 < len(nodes) else nodes[i]
            combined = left + right
            next_level.append(self._hash(combined))
        
        return self._build_tree(next_level)
    
    def get_root(self) -> str:
        """Return the Merkle root hash."""
        return self.root


class BlockchainAdapter:
    """
    Adapter for anchoring audit trails to blockchain networks.
    """
    
    def __init__(self, network: str = "ethereum-testnet"):
        self.network = network
        self.anchored_hashes: List[Dict[str, Any]] = []
        logger.info(f"BlockchainAdapter initialized for {network}")
    
    def create_audit_hash(self, trace_events: List[Dict[str, Any]]) -> str:
        """
        Create a Merkle root hash from trace events.
        """
        # Convert trace events to strings
        event_strings = [
            f"{e.get('timestamp')}:{e.get('stage')}:{e.get('data')}"
            for e in trace_events
        ]
        
        tree = MerkleTree(event_strings)
        root_hash = tree.get_root()
        
        logger.info(f"Created Merkle root: {root_hash[:16]}...")
        return root_hash
    
    async def anchor_to_blockchain(self, merkle_root: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Anchor a Merkle root hash to the blockchain.
        In production: This would submit a transaction to Ethereum/Hyperledger.
        """
        # Mock implementation
        anchor_record = {
            "merkle_root": merkle_root,
            "network": self.network,
            "timestamp": datetime.now(UTC).isoformat(),
            "block_number": len(self.anchored_hashes) + 1000000,  # Mock block number
            "transaction_hash": f"0x{hashlib.sha256(merkle_root.encode()).hexdigest()}",
            "metadata": metadata
        }
        
        self.anchored_hashes.append(anchor_record)
        logger.info(f"Anchored hash to {self.network} at block {anchor_record['block_number']}")
        
        return anchor_record
    
    def verify_audit_trail(self, merkle_root: str) -> Optional[Dict[str, Any]]:
        """
        Verify if a Merkle root exists in the blockchain.
        """
        for record in self.anchored_hashes:
            if record['merkle_root'] == merkle_root:
                return record
        return None

# Global Instance
blockchain_adapter = BlockchainAdapter()
