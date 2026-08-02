"""Persistence for discovered opportunities.

Discovered openings are upserted (unique per source + external id) so the
same posting keeps a stable internal id across searches — that id is what
the selection and apply steps reference.
"""
from __future__ import annotations

from typing import Optional

from ..db import get_conn
from ..models import Opportunity, StoredOpportunity

_COLUMNS = (
    "id, source, external_id, title, company, location, posted_date, url, "
    "description, salary_min, salary_max, contract_time, status, discovered_at"
)


def _row_to_model(row) -> StoredOpportunity:
    return StoredOpportunity(
        id=row["id"],
        source=row["source"],
        external_id=row["external_id"],
        title=row["title"],
        company=row["company"],
        location=row["location"],
        posted_date=row["posted_date"],
        url=row["url"],
        description=row["description"],
        salary_min=row["salary_min"],
        salary_max=row["salary_max"],
        contract_time=row["contract_time"],
        status=row["status"],
        discovered_at=row["discovered_at"],
    )


def upsert_many(opportunities: list[Opportunity]) -> list[StoredOpportunity]:
    """Insert new opportunities, refresh existing ones, and return the
    stored rows (with internal ids) in the same order as the input."""
    with get_conn() as conn:
        for opp in opportunities:
            conn.execute(
                """
                INSERT INTO opportunities
                    (source, external_id, title, company, location, posted_date,
                     url, description, salary_min, salary_max, contract_time)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(source, external_id) DO UPDATE SET
                    title=excluded.title,
                    company=excluded.company,
                    location=excluded.location,
                    posted_date=excluded.posted_date,
                    url=excluded.url,
                    description=excluded.description,
                    salary_min=excluded.salary_min,
                    salary_max=excluded.salary_max,
                    contract_time=excluded.contract_time
                """,
                (
                    opp.source,
                    opp.external_id,
                    opp.title,
                    opp.company,
                    opp.location,
                    opp.posted_date.isoformat() if opp.posted_date else None,
                    opp.url,
                    opp.description,
                    opp.salary_min,
                    opp.salary_max,
                    opp.contract_time,
                ),
            )
        # Fetch the stored rows for the given external ids, preserving order.
        stored: list[StoredOpportunity] = []
        for opp in opportunities:
            row = conn.execute(
                f"SELECT {_COLUMNS} FROM opportunities WHERE source=? AND external_id=?",
                (opp.source, opp.external_id),
            ).fetchone()
            if row:
                stored.append(_row_to_model(row))
    return stored


def list_opportunities(status: Optional[str] = None) -> list[StoredOpportunity]:
    query = f"SELECT {_COLUMNS} FROM opportunities"
    params: tuple = ()
    if status:
        query += " WHERE status = ?"
        params = (status,)
    query += " ORDER BY (posted_date IS NULL), posted_date DESC, id DESC"
    with get_conn() as conn:
        rows = conn.execute(query, params).fetchall()
    return [_row_to_model(r) for r in rows]


def get_opportunity(opp_id: int) -> Optional[StoredOpportunity]:
    with get_conn() as conn:
        row = conn.execute(
            f"SELECT {_COLUMNS} FROM opportunities WHERE id = ?", (opp_id,)
        ).fetchone()
    return _row_to_model(row) if row else None


def set_status(opp_id: int, status: str) -> None:
    with get_conn() as conn:
        conn.execute(
            "UPDATE opportunities SET status = ? WHERE id = ?", (status, opp_id)
        )
