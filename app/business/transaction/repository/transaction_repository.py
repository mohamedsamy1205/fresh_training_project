
from app.business.transaction.model.transaction import Transaction
from sqlalchemy.dialects.postgresql import UUID
import uuid

class TransactionRepository():
    def __init__(self, db):
        self.db = db

    def create(self, data: dict):
        transaction = Transaction(**data)
        self.db.add(transaction)
        self.db.commit()
        self.db.refresh(transaction)
        return transaction
    
    def find_by_walletId(self, wallet_id: UUID):
        return self.db.query(Transaction).filter(Transaction.wallet_id == wallet_id).all()

    def find_by_senderId(self, sender_id: UUID):
        return self.db.query(Transaction).filter(Transaction.sender_id == sender_id).all()

