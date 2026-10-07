import hashlib
import json
from time import time
from typing import List, Dict, Any
import uuid

class Block:
    def __init__(self, index, timestamp, transactions, previous_hash):
        self.index = index
        self.timestamp = timestamp
        self.transactions = transactions
        self.previous_hash = previous_hash
        self.nonce = 0
        self.hash = self.calculate_hash()
    
    def calculate_hash(self):
        block_string = json.dumps({
            'index': self.index,
            'timestamp': self.timestamp,
            'transactions': self.transactions,
            'previous_hash': self.previous_hash,
            'nonce': self.nonce
        }, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()
    
    def mine_block(self, difficulty):
        while self.hash[0:difficulty] != '0' * difficulty:
            self.nonce += 1
            self.hash = self.calculate_hash()
        print(f"Block mined: {self.hash}")

class BlockchainLedger:
    def __init__(self):
        self.chain = [self.create_genesis_block()]
        self.difficulty = 2
        self.pending_transactions = []
        self.all_transactions = []
    
    def create_genesis_block(self):
        return Block(0, time(), ["Genesis Block"], "0")
    
    def get_latest_block(self):
        return self.chain[-1]
    
    def create_transaction(self, transaction):
        """Add a transaction to pending transactions and mine it"""
        transaction_id = str(uuid.uuid4())[:8]
        transaction['transaction_id'] = transaction_id
        
        self.pending_transactions.append(transaction)
        self.all_transactions.append(transaction)
        
        # Mine the block with this transaction
        block = Block(
            len(self.chain),
            time(),
            [transaction],
            self.get_latest_block().hash
        )
        
        block.mine_block(self.difficulty)
        self.chain.append(block)
        
        return {
            'transaction_id': transaction_id,
            'block_index': block.index,
            'block_hash': block.hash,
            'timestamp': block.timestamp
        }
    
    def is_chain_valid(self):
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i-1]
            
            if current_block.hash != current_block.calculate_hash():
                return False
            
            if current_block.previous_hash != previous_block.hash:
                return False
        
        return True
    
    def get_all_transactions(self):
        """Get all transactions for display"""
        blocks_data = []
        for block in self.chain:
            blocks_data.append({
                'index': block.index,
                'timestamp': block.timestamp,
                'transactions': block.transactions,
                'hash': block.hash[:10] + '...',
                'previous_hash': block.previous_hash[:10] + '...'
            })
        return blocks_data


# Shared in-memory ledger used by the app (it resets when the server restarts)
ledger = BlockchainLedger()
