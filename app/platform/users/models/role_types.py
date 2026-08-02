import enum

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    INVESTOR = "investor"