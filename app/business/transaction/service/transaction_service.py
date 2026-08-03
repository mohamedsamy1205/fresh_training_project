from app.business.transaction.repository.transaction_repository import TransactionRepository
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.business.transaction.schema.transaction_schema import TransactionCreate
class TransactionService():
    def __init__(self, repo:TransactionRepository):
        self.repo = repo

    def create(self, data: TransactionCreate):
        return self.repo.create({
            "wallet_id": data.wallet_id,
            "amount": data.amount,
            "type": data.type,
            "status": data.status,
            "sender_id": data.sender_id,
            "description": data.description
        })

    def find_by_senderId(self, sender_id: UUID):
        return self.repo.find_by_senderId(sender_id)

    def find_by_walletId(self, wallet_id: UUID):
        return self.repo.find_by_walletId(wallet_id)

    