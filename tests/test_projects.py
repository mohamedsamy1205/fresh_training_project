import uuid
from unittest.mock import MagicMock
import pytest

from app.business.projects.service.project_service import ProjectService
from app.business.projects.model.project import Project
from app.business.projects.model.investment_request import InvestmentRequest
from app.core.exceptions import ResourceNotFoundException


def test_list_investment_requests_project_not_found():
    db = MagicMock()
    redis = MagicMock()
    service = ProjectService(db, redis)

    project_id = uuid.uuid4()
    db.query.return_value.filter.return_value.first.return_value = None

    with pytest.raises(ResourceNotFoundException):
        service.list_investment_requests(project_id)


def test_list_investment_requests_success():
    db = MagicMock()
    redis = MagicMock()
    service = ProjectService(db, redis)

    project_id = uuid.uuid4()
    mock_project = Project(uuid=project_id, name="Test Project")
    mock_request = InvestmentRequest(uuid=uuid.uuid4(), project_id=project_id, amount=100.0)

    # First query is for Project check, second query is for InvestmentRequest list
    db.query.return_value.filter.return_value.first.return_value = mock_project
    db.query.return_value.filter.return_value.all.return_value = [mock_request]

    result = service.list_investment_requests(project_id)
    assert len(result) == 1
    assert result[0] == mock_request


@pytest.mark.asyncio
async def test_delete_project_not_found():
    db = MagicMock()
    redis = MagicMock()
    service = ProjectService(db, redis)

    project_id = uuid.uuid4()
    db.query.return_value.filter.return_value.first.return_value = None

    with pytest.raises(ResourceNotFoundException):
        await service.delete_project(project_id)


@pytest.mark.asyncio
async def test_delete_project_success():
    db = MagicMock()
    redis = MagicMock()
    service = ProjectService(db, redis)

    project_id = uuid.uuid4()
    mock_project = Project(uuid=project_id, name="Test Project")

    db.query.return_value.filter.return_value.first.return_value = mock_project

    res = await service.delete_project(project_id)
    assert res["success"] is True
    assert str(project_id) in res["message"]


@pytest.mark.asyncio
async def test_list_all_projects_investor_status():
    from datetime import datetime
    from app.common.enums import UserRole, InvestmentRequestStatus, ProjectStatus

    db = MagicMock()
    redis = MagicMock()
    redis.get = pytest.StashKey() if hasattr(pytest, 'StashKey') else MagicMock(return_value=None)
    
    # Async mock for redis.get
    async def async_redis_get(key):
        return None
    async def async_redis_setex(key, time, value):
        pass
    redis.get = async_redis_get
    redis.setex = async_redis_setex

    service = ProjectService(db, redis)

    project_id = uuid.uuid4()
    mock_project = Project(
        uuid=project_id,
        name="Test Investment Project",
        start_date=datetime.utcnow(),
        end_date=datetime.utcnow(),
        initial_amount=0.0,
        status=ProjectStatus.ACTIVE.value,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

    user_id = uuid.uuid4()
    mock_user = MagicMock()
    mock_user.uuid = user_id
    mock_user.role = UserRole.INVESTOR

    mock_request = InvestmentRequest(
        uuid=uuid.uuid4(),
        user_id=user_id,
        project_id=project_id,
        status=InvestmentRequestStatus.PENDING.value,
        created_at=datetime.utcnow()
    )

    # First query for Project returns [mock_project], second query for InvestmentRequest chain returns [mock_request]
    db.query.return_value.all.return_value = [mock_project]
    db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [mock_request]

    result = await service.list_all_projects(current_user=mock_user)
    assert len(result) == 1
    assert result[0]["uuid"] == str(project_id)
    assert result[0]["user_request_status"] == InvestmentRequestStatus.PENDING.value


@pytest.mark.asyncio
async def test_close_project_records_transaction_and_ledger():
    from decimal import Decimal
    from app.common.enums import ProjectStatus, TransactionType, LedgerEntryType
    from app.business.wallet.model.wallet import Wallet

    db = MagicMock()
    redis = MagicMock()
    async def async_redis_delete(key):
        pass
    redis.delete = async_redis_delete

    service = ProjectService(db, redis)

    project_id = uuid.uuid4()
    mock_project = Project(
        uuid=project_id,
        name="Active Project",
        status=ProjectStatus.ACTIVE.value
    )

    mock_treasury_wallet = Wallet(
        uuid=uuid.uuid4(),
        name="Company Treasury Vault",
        balance=Decimal("1000.00")
    )

    # 1st query: project query -> mock_project
    # 2nd query: count distinct investors -> 2
    # 3rd query: treasury wallet query -> mock_treasury_wallet
    db.query.return_value.filter.return_value.first.side_effect = [
        mock_project,
        mock_treasury_wallet
    ]
    db.query.return_value.filter.return_value.scalar.return_value = 2

    closed_project = await service.close_project(project_id, Decimal("500.00"))

    assert closed_project.status == ProjectStatus.CLOSED.value
    assert closed_project.final_amount == Decimal("500.00")
    assert mock_treasury_wallet.balance == Decimal("1500.00")
    assert db.add.called


@pytest.mark.asyncio
async def test_approve_investment_request_success():
    from decimal import Decimal
    from app.common.enums import ProjectStatus, InvestmentRequestStatus
    from app.business.transaction.model.transaction import Transaction

    db = MagicMock()
    redis = MagicMock()
    async def async_redis_delete(key):
        pass
    redis.delete = async_redis_delete

    mock_money_service = MagicMock()
    mock_tx = Transaction(uuid=uuid.uuid4(), amount=Decimal("250.00"))
    mock_money_service.process_investment.return_value = mock_tx

    service = ProjectService(db, redis, money_movement_service=mock_money_service)

    req_id = uuid.uuid4()
    project_id = uuid.uuid4()
    user_id = uuid.uuid4()
    wallet_id = uuid.uuid4()

    mock_req = InvestmentRequest(
        uuid=req_id,
        user_id=user_id,
        project_id=project_id,
        wallet_id=wallet_id,
        amount=Decimal("250.00"),
        status=InvestmentRequestStatus.PENDING.value
    )
    mock_project = Project(
        uuid=project_id,
        name="Tech Venture",
        status=ProjectStatus.ACTIVE.value,
        initial_amount=Decimal("100.00")
    )

    db.query.return_value.filter.return_value.first.side_effect = [
        mock_req,
        mock_project
    ]

    res = await service.approve_investment_request(req_id, "idemp_key_123")

    assert res["success"] is True
    assert res["is_duplicate"] is False
    assert mock_req.status == InvestmentRequestStatus.APPROVED.value
    assert mock_project.initial_amount == Decimal("350.00")
    mock_money_service.process_investment.assert_called_once_with(
        user_id=user_id,
        wallet_id=wallet_id,
        amount=Decimal("250.00"),
        idempotency_key="idemp_key_123",
        project_name="Tech Venture"
    )


@pytest.mark.asyncio
async def test_distribute_profits_success():
    from decimal import Decimal
    from app.common.enums import ProjectStatus
    from app.business.projects.model.investment import Investment
    from app.business.wallet.model.wallet import Wallet

    db = MagicMock()
    redis = MagicMock()
    async def async_redis_delete(key):
        pass
    redis.delete = async_redis_delete

    mock_money_service = MagicMock()
    mock_treasury = Wallet(uuid=uuid.uuid4(), balance=Decimal("10000.00"))
    mock_money_service.get_treasury_wallet.return_value = mock_treasury

    service = ProjectService(db, redis, money_movement_service=mock_money_service)

    project_id = uuid.uuid4()
    user_id = uuid.uuid4()
    wallet_id = uuid.uuid4()

    mock_project = Project(
        uuid=project_id,
        name="Real Estate Alpha",
        status=ProjectStatus.CLOSED.value,
        initial_amount=Decimal("1000.00"),
        final_amount=Decimal("1500.00")
    )

    mock_investment = Investment(
        uuid=uuid.uuid4(),
        user_id=user_id,
        project_id=project_id,
        wallet_id=wallet_id,
        amount=Decimal("1000.00")
    )

    db.query.return_value.filter.return_value.first.return_value = mock_project
    db.query.return_value.filter.return_value.all.return_value = [mock_investment]

    res = await service.distribute_profits(project_id, "dist_idemp_key")

    assert res["success"] is True
    assert res["is_duplicate"] is False
    assert mock_project.status == ProjectStatus.DISTRIBUTED.value
    assert res["total_profit"] == Decimal("500.00")
    assert res["total_company_fee_collected"] == Decimal("100.00")
    assert res["total_returned_to_investors"] == Decimal("1400.00")
    mock_money_service.process_profit_payout.assert_called_once()




