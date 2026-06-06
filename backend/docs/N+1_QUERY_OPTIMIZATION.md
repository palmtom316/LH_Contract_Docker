"""
N+1 Query Optimization Guide for Contract Services

The N+1 query problem occurs when listing contracts and their related data.
For example, when listing contracts, accessing total_receivable for each 
contract triggers a separate query, making 1 + N queries total.

SOLUTION: Use selectinload to preload related data in a single query.

Usage Example in Services:
"""

from sqlalchemy.orm import selectinload
from sqlalchemy import select
from app.models.contract_upstream import ContractUpstream

# BAD: N+1 queries (1 for contracts + N for each contract's receivables)
async def list_contracts_bad(db):
    result = await db.execute(select(ContractUpstream))
    contracts = result.scalars().all()
    
    for contract in contracts:
        # This triggers a separate query for EACH contract
        total = contract.total_receivable  # N queries!
   
    return contracts


# GOOD: Eager loading with selectinload (2-3 queries total)
async def list_contracts_optimized(db):
    stmt = select(ContractUpstream).options(
        selectinload(ContractUpstream.receivables),
        selectinload(ContractUpstream.invoices),
        selectinload(ContractUpstream.receipts),
        selectinload(ContractUpstream.settlements)
    )
    
    result = await db.execute(stmt)
    contracts = result.scalars().all()
    
    # Now accessing total_receivable uses preloaded data - No extra queries!
    for contract in contracts:
        total = contract.total_receivable  # Uses cached data
    
    return contracts


# EVEN BETTER: Use subquery for aggregations
async def list_contracts_with_aggregations(db):
    from sqlalchemy import func
    
    stmt = select(
        ContractUpstream,
        func.coalesce(
            func.sum(FinanceUpstreamReceivable.amount), 0
        ).label('total_received')
    ).outerjoin(
        FinanceUpstreamReceivable
    ).group_by(ContractUpstream.id)
    
    result = await db.execute(stmt)
    # Returns tuples: (contract, total_received)
    return result.all()


"""
APPLY TO YOUR SERVICES:

1. In contract_upstream_service.py - list_contracts method:
   Add selectinload options before executing query

2. In contract_downstream_service.py - list_contracts method:
   Add selectinload for upstream_contract relationship

3. In reports.py - any contract queries:
   Use selectinload for all relationships accessed
"""

# Example fix for contract_upstream_service.py:
"""
async def list_contracts(self, page, page_size, keyword, status, start_date, end_date):
    query = select(ContractUpstream).options(
        selectinload(ContractUpstream.receivables),
        selectinload(ContractUpstream.invoices),
        selectinload(ContractUpstream.receipts),
        selectinload(ContractUpstream.settlements)
    )
    
    # Add filtering...
    if keyword:
        query = query.where(...)
    
    # Execute
    result = await self.db.execute(query)
    contracts = result.scalars().all()
    
    return contracts
"""
