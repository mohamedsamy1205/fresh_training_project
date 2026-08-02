from app.business.wallet.repository.wallet_repository import WalletRepository
from app.business.wallet.schema.wallet_schema import WalletCreate, WalletUpdate
from sqlalchemy.dialects.postgresql import UUID

class WalletService:
    def __init__(self, repo: WalletRepository):
        self.repo = repo

    def create(self, data: WalletCreate):

        return self.repo.create({
            "user_id": data.user_id,
            "name": data.name
        })

    def update_balance(self, data: WalletUpdate):
        return self.repo.update_balance({
            "Wallet_id": data.Wallet_id,
            "new_balance": data.new_balance
        })

    def get_by_user_id(self, user_id: UUID):
        return self.repo.get_by_user_id(user_id)