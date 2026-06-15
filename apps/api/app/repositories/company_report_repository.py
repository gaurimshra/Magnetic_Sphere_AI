import json
import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from app.core.config import Settings
from app.models.domain import CompanyReport, RawCompanySignal, ReportHistoryItem


class CompanyReportRepository:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.sqlite_path = Path(__file__).resolve().parents[2] / "company_reports.db"

    def get_latest(self, key: str, max_age_hours: int = 24) -> CompanyReport | None:
        row = self._get_latest_row(key)
        if not row:
            return None

        generated_at = datetime.fromisoformat(row["generated_at"])
        if generated_at.tzinfo is None:
            generated_at = generated_at.replace(tzinfo=UTC)
        if datetime.now(UTC) - generated_at > timedelta(hours=max_age_hours):
            return None

        report = CompanyReport.model_validate_json(row["payload"])
        return report.model_copy(update={"cached": True})

    def save(self, key: str, report: CompanyReport) -> None:
        payload = report.model_dump_json()
        if self._save_postgres(key, report, payload):
            return
        self._save_sqlite(key, report, payload)

    def previous_report(self, key: str, before_report_id: str | None = None) -> CompanyReport | None:
        row = self._previous_report_postgres(key, before_report_id) or self._previous_report_sqlite(key, before_report_id)
        if not row:
            return None
        return CompanyReport.model_validate_json(row["payload"])

    def history(self, key: str | None = None, limit: int = 20) -> list[ReportHistoryItem]:
        rows = self._history_postgres(key, limit) or self._history_sqlite(key, limit)
        items: list[ReportHistoryItem] = []
        previous_by_domain: dict[str, int] = {}
        for row in reversed(rows):
            report = CompanyReport.model_validate_json(row["payload"])
            previous_score = previous_by_domain.get(report.company.domain)
            delta = 0 if previous_score is None else report.opportunity_score - previous_score
            previous_by_domain[report.company.domain] = report.opportunity_score
            items.append(
                ReportHistoryItem(
                    id=report.id,
                    company_name=report.company.company_name,
                    domain=report.company.domain,
                    generated_at=report.generated_at,
                    opportunity_score=report.opportunity_score,
                    confidence=report.confidence,
                    score_delta=report.score_delta or delta,
                    timeline_delta=report.timeline_delta,
                    alert=report.score_alert,
                )
            )
        return list(reversed(items))

    def save_signals(self, signals: list[RawCompanySignal]) -> None:
        if not signals:
            return
        if self._save_signals_postgres(signals):
            return
        self._save_signals_sqlite(signals)

    def list_signals(self, key: str, limit: int = 50) -> list[RawCompanySignal]:
        rows = self._list_signals_postgres(key, limit) or self._list_signals_sqlite(key, limit)
        return [
            RawCompanySignal(
                id=row["id"],
                company_key=row["company_key"],
                company_name=row["company_name"],
                domain=row["domain"],
                provider=row["provider"],
                signal_type=row["signal_type"],
                source=row["source"],
                title=row["title"],
                url=row["url"] or "",
                raw_snippet=row["raw_snippet"],
                raw_payload=json.loads(row["raw_payload"] or "{}"),
                extracted_entities=json.loads(row["extracted_entities"] or "[]"),
                confidence=int(row["confidence"]),
                occurred_at=row["occurred_at"],
                captured_at=row["captured_at"],
                dedup_key=row["dedup_key"],
                duplicate_of=row["duplicate_of"],
            )
            for row in rows
        ]

    def _get_latest_row(self, key: str) -> dict[str, Any] | None:
        postgres_row = self._get_latest_postgres(key)
        if postgres_row:
            return postgres_row
        return self._get_latest_sqlite(key)

    def _save_postgres(self, key: str, report: CompanyReport, payload: str) -> bool:
        if not self.settings.database_url.startswith("postgres"):
            return False

        try:
            import psycopg
        except ImportError:
            return False

        try:
            with psycopg.connect(self._psycopg_url()) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        CREATE TABLE IF NOT EXISTS company_reports (
                            id TEXT PRIMARY KEY,
                            company_key TEXT NOT NULL,
                            company_name TEXT NOT NULL,
                            domain TEXT NOT NULL,
                            generated_at TIMESTAMPTZ NOT NULL,
                            payload JSONB NOT NULL
                        )
                        """
                    )
                    self._ensure_postgres_signals(cur)
                    cur.execute(
                        """
                        INSERT INTO company_reports
                            (id, company_key, company_name, domain, generated_at, payload)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        ON CONFLICT (id) DO UPDATE SET
                            company_key = EXCLUDED.company_key,
                            company_name = EXCLUDED.company_name,
                            domain = EXCLUDED.domain,
                            generated_at = EXCLUDED.generated_at,
                            payload = EXCLUDED.payload
                        """,
                        (
                            report.id,
                            key,
                            report.company.company_name,
                            report.company.domain,
                            report.generated_at,
                            payload,
                        ),
                    )
                conn.commit()
            return True
        except Exception:
            return False

    def _get_latest_postgres(self, key: str) -> dict[str, Any] | None:
        if not self.settings.database_url.startswith("postgres"):
            return None

    def _previous_report_postgres(self, key: str, before_report_id: str | None) -> dict[str, Any] | None:
        if not self.settings.database_url.startswith("postgres"):
            return None
        try:
            import psycopg
            from psycopg.rows import dict_row
        except ImportError:
            return None
        try:
            with psycopg.connect(self._psycopg_url(), row_factory=dict_row) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT generated_at, payload::text AS payload
                        FROM company_reports
                        WHERE (company_key = %s OR lower(domain) = lower(%s))
                          AND (%s IS NULL OR id <> %s)
                        ORDER BY generated_at DESC
                        LIMIT 1
                        """,
                        (key, key, before_report_id, before_report_id),
                    )
                    row = cur.fetchone()
                    return dict(row) if row else None
        except Exception:
            return None

    def _history_postgres(self, key: str | None, limit: int) -> list[dict[str, Any]]:
        if not self.settings.database_url.startswith("postgres"):
            return []
        try:
            import psycopg
            from psycopg.rows import dict_row
        except ImportError:
            return []
        try:
            with psycopg.connect(self._psycopg_url(), row_factory=dict_row) as conn:
                with conn.cursor() as cur:
                    if key:
                        cur.execute(
                            """
                            SELECT payload::text AS payload
                            FROM company_reports
                            WHERE company_key = %s OR lower(domain) = lower(%s)
                            ORDER BY generated_at DESC
                            LIMIT %s
                            """,
                            (key, key, limit),
                        )
                    else:
                        cur.execute(
                            """
                            SELECT payload::text AS payload
                            FROM company_reports
                            ORDER BY generated_at DESC
                            LIMIT %s
                            """,
                            (limit,),
                        )
                    return [dict(row) for row in cur.fetchall()]
        except Exception:
            return []

        try:
            import psycopg
            from psycopg.rows import dict_row
        except ImportError:
            return None

        try:
            with psycopg.connect(self._psycopg_url(), row_factory=dict_row) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT generated_at, payload::text AS payload
                        FROM company_reports
                        WHERE company_key = %s OR lower(domain) = lower(%s)
                        ORDER BY generated_at DESC
                        LIMIT 1
                        """,
                        (key, key),
                    )
                    row = cur.fetchone()
                    if not row:
                        return None
                    return {
                        "generated_at": row["generated_at"].isoformat(),
                        "payload": row["payload"],
                    }
        except Exception:
            return None

    def _save_sqlite(self, key: str, report: CompanyReport, payload: str) -> None:
        with sqlite3.connect(self.sqlite_path) as conn:
            self._ensure_sqlite(conn)
            conn.execute(
                """
                INSERT OR REPLACE INTO company_reports
                    (id, company_key, company_name, domain, generated_at, payload)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    report.id,
                    key,
                    report.company.company_name,
                    report.company.domain,
                    report.generated_at,
                    payload,
                ),
            )
            conn.commit()

    def _get_latest_sqlite(self, key: str) -> dict[str, Any] | None:
        with sqlite3.connect(self.sqlite_path) as conn:
            conn.row_factory = sqlite3.Row
            self._ensure_sqlite(conn)
            row = conn.execute(
                """
                SELECT generated_at, payload
                FROM company_reports
                WHERE company_key = ? OR lower(domain) = lower(?)
                ORDER BY generated_at DESC
                LIMIT 1
                """,
                (key, key),
            ).fetchone()
            return dict(row) if row else None

    def _previous_report_sqlite(self, key: str, before_report_id: str | None) -> dict[str, Any] | None:
        with sqlite3.connect(self.sqlite_path) as conn:
            conn.row_factory = sqlite3.Row
            self._ensure_sqlite(conn)
            row = conn.execute(
                """
                SELECT generated_at, payload
                FROM company_reports
                WHERE (company_key = ? OR lower(domain) = lower(?))
                  AND (? IS NULL OR id <> ?)
                ORDER BY generated_at DESC
                LIMIT 1
                """,
                (key, key, before_report_id, before_report_id),
            ).fetchone()
            return dict(row) if row else None

    def _history_sqlite(self, key: str | None, limit: int) -> list[dict[str, Any]]:
        with sqlite3.connect(self.sqlite_path) as conn:
            conn.row_factory = sqlite3.Row
            self._ensure_sqlite(conn)
            if key:
                rows = conn.execute(
                    """
                    SELECT payload
                    FROM company_reports
                    WHERE company_key = ? OR lower(domain) = lower(?)
                    ORDER BY generated_at DESC
                    LIMIT ?
                    """,
                    (key, key, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT payload
                    FROM company_reports
                    ORDER BY generated_at DESC
                    LIMIT ?
                    """,
                    (limit,),
                ).fetchall()
            return [dict(row) for row in rows]

    def _ensure_sqlite(self, conn: sqlite3.Connection) -> None:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS company_reports (
                id TEXT PRIMARY KEY,
                company_key TEXT NOT NULL,
                company_name TEXT NOT NULL,
                domain TEXT NOT NULL,
                generated_at TEXT NOT NULL,
                payload TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS company_signals (
                id TEXT PRIMARY KEY,
                company_key TEXT NOT NULL,
                company_name TEXT NOT NULL,
                domain TEXT NOT NULL,
                provider TEXT NOT NULL,
                signal_type TEXT NOT NULL,
                source TEXT NOT NULL,
                title TEXT NOT NULL,
                url TEXT,
                raw_snippet TEXT NOT NULL,
                raw_payload TEXT NOT NULL,
                extracted_entities TEXT NOT NULL,
                confidence INTEGER NOT NULL,
                occurred_at TEXT NOT NULL,
                captured_at TEXT NOT NULL,
                dedup_key TEXT NOT NULL UNIQUE,
                duplicate_of TEXT
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_company_signals_key ON company_signals(company_key, occurred_at)")

    def _ensure_postgres_signals(self, cur: Any) -> None:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS company_signals (
                id TEXT PRIMARY KEY,
                company_key TEXT NOT NULL,
                company_name TEXT NOT NULL,
                domain TEXT NOT NULL,
                provider TEXT NOT NULL,
                signal_type TEXT NOT NULL,
                source TEXT NOT NULL,
                title TEXT NOT NULL,
                url TEXT,
                raw_snippet TEXT NOT NULL,
                raw_payload JSONB NOT NULL,
                extracted_entities JSONB NOT NULL,
                confidence INTEGER NOT NULL,
                occurred_at TIMESTAMPTZ NOT NULL,
                captured_at TIMESTAMPTZ NOT NULL,
                dedup_key TEXT NOT NULL UNIQUE,
                duplicate_of TEXT
            )
            """
        )
        cur.execute("CREATE INDEX IF NOT EXISTS idx_company_signals_key ON company_signals(company_key, occurred_at)")

    def _save_signals_postgres(self, signals: list[RawCompanySignal]) -> bool:
        if not self.settings.database_url.startswith("postgres"):
            return False
        try:
            import psycopg
        except ImportError:
            return False
        try:
            with psycopg.connect(self._psycopg_url()) as conn:
                with conn.cursor() as cur:
                    self._ensure_postgres_signals(cur)
                    for signal in signals:
                        cur.execute(
                            """
                            INSERT INTO company_signals (
                                id, company_key, company_name, domain, provider, signal_type, source, title, url,
                                raw_snippet, raw_payload, extracted_entities, confidence, occurred_at, captured_at,
                                dedup_key, duplicate_of
                            )
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            ON CONFLICT (dedup_key) DO UPDATE SET
                                captured_at = EXCLUDED.captured_at,
                                confidence = GREATEST(company_signals.confidence, EXCLUDED.confidence)
                            """,
                            (
                                signal.id,
                                signal.company_key,
                                signal.company_name,
                                signal.domain,
                                signal.provider,
                                signal.signal_type,
                                signal.source,
                                signal.title,
                                signal.url,
                                signal.raw_snippet,
                                json.dumps(signal.raw_payload),
                                json.dumps(signal.extracted_entities),
                                signal.confidence,
                                signal.occurred_at,
                                signal.captured_at,
                                signal.dedup_key,
                                signal.duplicate_of,
                            ),
                        )
                conn.commit()
            return True
        except Exception:
            return False

    def _save_signals_sqlite(self, signals: list[RawCompanySignal]) -> None:
        with sqlite3.connect(self.sqlite_path) as conn:
            self._ensure_sqlite(conn)
            conn.executemany(
                """
                INSERT OR IGNORE INTO company_signals (
                    id, company_key, company_name, domain, provider, signal_type, source, title, url,
                    raw_snippet, raw_payload, extracted_entities, confidence, occurred_at, captured_at,
                    dedup_key, duplicate_of
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        signal.id,
                        signal.company_key,
                        signal.company_name,
                        signal.domain,
                        signal.provider,
                        signal.signal_type,
                        signal.source,
                        signal.title,
                        signal.url,
                        signal.raw_snippet,
                        json.dumps(signal.raw_payload),
                        json.dumps(signal.extracted_entities),
                        signal.confidence,
                        signal.occurred_at,
                        signal.captured_at,
                        signal.dedup_key,
                        signal.duplicate_of,
                    )
                    for signal in signals
                ],
            )
            conn.commit()

    def _list_signals_postgres(self, key: str, limit: int) -> list[dict[str, Any]]:
        if not self.settings.database_url.startswith("postgres"):
            return []
        try:
            import psycopg
            from psycopg.rows import dict_row
        except ImportError:
            return []
        try:
            with psycopg.connect(self._psycopg_url(), row_factory=dict_row) as conn:
                with conn.cursor() as cur:
                    self._ensure_postgres_signals(cur)
                    cur.execute(
                        """
                        SELECT *, raw_payload::text AS raw_payload, extracted_entities::text AS extracted_entities
                        FROM company_signals
                        WHERE company_key = %s OR lower(domain) = lower(%s)
                        ORDER BY occurred_at DESC, captured_at DESC
                        LIMIT %s
                        """,
                        (key, key, limit),
                    )
                    return [dict(row) for row in cur.fetchall()]
        except Exception:
            return []

    def _list_signals_sqlite(self, key: str, limit: int) -> list[dict[str, Any]]:
        with sqlite3.connect(self.sqlite_path) as conn:
            conn.row_factory = sqlite3.Row
            self._ensure_sqlite(conn)
            rows = conn.execute(
                """
                SELECT *
                FROM company_signals
                WHERE company_key = ? OR lower(domain) = lower(?)
                ORDER BY occurred_at DESC, captured_at DESC
                LIMIT ?
                """,
                (key, key, limit),
            ).fetchall()
            return [dict(row) for row in rows]

    def _psycopg_url(self) -> str:
        return self.settings.database_url.replace("postgresql+psycopg://", "postgresql://", 1)
