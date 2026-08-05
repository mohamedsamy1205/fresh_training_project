from app.business.wallet.model.wallet import Wallet
from app.core.exceptions import ResourceNotFoundException
from sqlalchemy.dialects.postgresql import UUID
import uuid

class WalletRepository:
    def __init__(self, db):
        self.db = db

    def create(self, data: dict):
        
        wallet = Wallet(**data)

        self.db.add(wallet)
        self.db.commit()
        self.db.refresh(wallet)
        return wallet

    def update_balance(self, data: dict):

        wallet = (
            self.db.query(Wallet)
            .filter(
                Wallet.uuid == data["Wallet_id"]
            )
            .first()
        )

        if wallet is None:
            raise ResourceNotFoundException("Wallet not found")



        wallet.balance = data["new_balance"]

        self.db.commit()
        self.db.refresh(wallet)

        return wallet

    def get_by_user_id(
        self,
        user_id: UUID
    ):

        return (
            self.db.query(Wallet)
            .filter(
                Wallet.user_id == user_id
            )
            .all()
        )