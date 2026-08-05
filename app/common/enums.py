import enum

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    ADMIN_DEV = "admin_dev"
    INVESTOR = "investor"

class WalletType(str, enum.Enum):
    USER = "user"
    TREASURY = "treasury"

class TransactionType(str, enum.Enum):
    DEPOSIT = "deposit"
    WITHDRAW = "withdraw"
    TRANSFER = "transfer"
    INVESTMENT = "investment"
    PROFIT_PAYOUT = "profit_payout"
    COMPANY_FEE = "company_fee"

class TransactionStatus(str, enum.Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"

class LedgerEntryType(str, enum.Enum):
    DEBIT = "debit"
    CREDIT = "credit"

class ProjectStatus(str, enum.Enum):
    ACTIVE = "active"
    CLOSED = "closed"
    DISTRIBUTED = "distributed"

class InvestmentRequestStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"