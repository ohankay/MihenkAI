"""Query service for evaluation monitoring list operations."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import EvaluationJob


class EvaluationQueryService:
    """Encapsulates monitoring query/filter/pagination logic for evaluation jobs."""

    @staticmethod
    def _to_utc_naive(value: Optional[datetime]) -> Optional[datetime]:
        if value is None:
            return None
        if value.tzinfo is not None:
            return value.astimezone(timezone.utc).replace(tzinfo=None)
        return value

    async def list_jobs(
        self,
        session: AsyncSession,
        *,
        limit: int,
        offset: int,
        profile_id: Optional[int] = None,
        status: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> tuple[list[EvaluationJob], int]:
        """Return paginated jobs and total count for given filters."""
        start_dt = self._to_utc_naive(start_time)
        end_dt = self._to_utc_naive(end_time)

        filters = []
        if profile_id is not None:
            filters.append(EvaluationJob.profile_id == profile_id)
        if status:
            filters.append(EvaluationJob.status == status)
        if start_dt is not None:
            filters.append(EvaluationJob.created_at >= start_dt)
        if end_dt is not None:
            filters.append(EvaluationJob.created_at <= end_dt)

        base_stmt: Select = select(EvaluationJob)
        count_stmt = select(func.count()).select_from(EvaluationJob)
        if filters:
            base_stmt = base_stmt.where(*filters)
            count_stmt = count_stmt.where(*filters)

        result = await session.execute(
            base_stmt
            .order_by(EvaluationJob.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        rows = result.scalars().all()

        total = int((await session.execute(count_stmt)).scalar_one())
        return rows, total
