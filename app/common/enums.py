import enum

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    ADMIN_DEV = "admin_dev"
    INVESTOR = "investor"

class TransactionType(str, enum.Enum):
    DEPOSIT = "deposit"
    WITHDRAW = "withdraw"
    TRANSFER = "transfer"

class TransactionStatus(str, enum.Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"