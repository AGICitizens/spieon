"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-04-27

Creates the pgvector extension, all eight Spieon tables in FK-dependency order,
and HNSW indexes on the three embedding columns. Vector indexes are written by
hand because Alembic autogenerate does not understand pgvector index methods.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


EMBEDDING_DIM = 1536


def _ts_columns() -> list[sa.Column]:
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    ]


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # ------------------------------------------------------------------ scans
    op.create_table(
        "scans",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("target_url", sa.String(2048), nullable=False),
        sa.Column("operator_address", sa.String(64), nullable=False),
        sa.Column("recipient_pubkey", sa.String(128), nullable=False),
        sa.Column("budget_usdc", sa.Numeric(18, 6), nullable=False),
        sa.Column("bounty_usdc", sa.Numeric(18, 6), nullable=False),
        sa.Column("spent_usdc", sa.Numeric(18, 6), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("consent_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("adapt_iterations", sa.Integer(), nullable=False),
        sa.Column("error", sa.Text(), nullable=True),
        *_ts_columns(),
    )
    op.create_index("ix_scans_target_url", "scans", ["target_url"])
    op.create_index("ix_scans_operator_address", "scans", ["operator_address"])
    op.create_index("ix_scans_status", "scans", ["status"])

    # ---------------------------------------------------------------- modules
    op.create_table(
        "modules",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("module_hash", sa.String(128), nullable=False),
        sa.Column("author_address", sa.String(64), nullable=False),
        sa.Column("author_ens_name", sa.String(255), nullable=True),
        sa.Column("metadata_uri", sa.String(512), nullable=False),
        sa.Column("severity_cap", sa.String(32), nullable=False),
        sa.Column("times_used", sa.Integer(), nullable=False),
        sa.Column("success_count", sa.Integer(), nullable=False),
        sa.Column("owasp_id", sa.String(64), nullable=True),
        sa.Column("atlas_technique_id", sa.String(64), nullable=True),
        sa.Column("registered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
        *_ts_columns(),
        sa.UniqueConstraint("module_hash", name="uq_module_hash"),
    )
    op.create_index("ix_modules_module_hash", "modules", ["module_hash"])
    op.create_index("ix_modules_author_address", "modules", ["author_address"])
    op.create_index("ix_modules_owasp_id", "modules", ["owasp_id"])
    op.create_index("ix_modules_atlas_technique_id", "modules", ["atlas_technique_id"])

    # ------------------------------------------------------------- heuristics
    op.create_table(
        "heuristics",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("heuristic_key", sa.String(128), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("rule", sa.Text(), nullable=False),
        sa.Column("target_type", sa.String(128), nullable=True),
        sa.Column("probe_class", sa.String(128), nullable=True),
        sa.Column("evidence_scan_ids", postgresql.JSONB(), nullable=False),
        sa.Column("evidence_event_ids", postgresql.JSONB(), nullable=False),
        sa.Column("success_count", sa.Integer(), nullable=False),
        sa.Column("sample_size", sa.Integer(), nullable=False),
        sa.Column("success_rate", sa.Float(), nullable=False),
        sa.Column("owasp_id", sa.String(64), nullable=True),
        sa.Column("atlas_technique_id", sa.String(64), nullable=True),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("eas_attestation_uid", sa.String(128), nullable=True),
        sa.Column("attested_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("embedding", Vector(EMBEDDING_DIM), nullable=True),
        *_ts_columns(),
        sa.UniqueConstraint("heuristic_key", "version", name="uq_heuristic_key_version"),
    )
    op.create_index("ix_heuristics_heuristic_key", "heuristics", ["heuristic_key"])
    op.create_index("ix_heuristics_target_type", "heuristics", ["target_type"])
    op.create_index("ix_heuristics_probe_class", "heuristics", ["probe_class"])
    op.create_index("ix_heuristics_content_hash", "heuristics", ["content_hash"])
    op.create_index("ix_heuristics_eas_attestation_uid", "heuristics", ["eas_attestation_uid"])
    op.execute(
        "CREATE INDEX ix_heuristics_embedding_hnsw ON heuristics "
        "USING hnsw (embedding vector_cosine_ops)"
    )

    # ----------------------------------------------------------- memory_items
    op.create_table(
        "memory_items",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("tier", sa.String(32), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("source_event_ids", postgresql.JSONB(), nullable=False),
        sa.Column("usefulness_score", sa.Integer(), nullable=False),
        sa.Column("cycles_unused", sa.Integer(), nullable=False),
        sa.Column("retrieval_count", sa.Integer(), nullable=False),
        sa.Column("last_retrieved", sa.DateTime(timezone=True), nullable=True),
        sa.Column("target_type", sa.String(128), nullable=True),
        sa.Column("probe_class", sa.String(128), nullable=True),
        sa.Column("embedding", Vector(EMBEDDING_DIM), nullable=True),
        *_ts_columns(),
    )
    op.create_index("ix_memory_items_tier", "memory_items", ["tier"])
    op.create_index("ix_memory_items_usefulness_score", "memory_items", ["usefulness_score"])
    op.create_index("ix_memory_items_target_type", "memory_items", ["target_type"])
    op.create_index("ix_memory_items_probe_class", "memory_items", ["probe_class"])
    op.execute(
        "CREATE INDEX ix_memory_items_embedding_hnsw ON memory_items "
        "USING hnsw (embedding vector_cosine_ops)"
    )

    # --------------------------------------------------------------- findings
    op.create_table(
        "findings",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("scan_id", sa.Uuid(), sa.ForeignKey("scans.id"), nullable=False),
        sa.Column("severity", sa.String(32), nullable=False),
        sa.Column("title", sa.String(512), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("module_hash", sa.String(128), nullable=False),
        sa.Column("cost_usdc", sa.Numeric(18, 6), nullable=False),
        sa.Column("owasp_id", sa.String(64), nullable=True),
        sa.Column("atlas_technique_id", sa.String(64), nullable=True),
        sa.Column("maestro_id", sa.String(64), nullable=True),
        sa.Column("encrypted_bundle_uri", sa.String(512), nullable=True),
        sa.Column("ciphertext_sha256", sa.String(64), nullable=True),
        sa.Column("eas_attestation_uid", sa.String(128), nullable=True),
        sa.Column("attested_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("dedup_key", sa.String(128), nullable=False),
        *_ts_columns(),
        sa.UniqueConstraint("scan_id", "dedup_key", name="uq_finding_scan_dedup"),
    )
    op.create_index("ix_findings_scan_id", "findings", ["scan_id"])
    op.create_index("ix_findings_severity", "findings", ["severity"])
    op.create_index("ix_findings_module_hash", "findings", ["module_hash"])
    op.create_index("ix_findings_eas_attestation_uid", "findings", ["eas_attestation_uid"])
    op.create_index("ix_findings_dedup_key", "findings", ["dedup_key"])

    # ------------------------------------------------------------- probe_runs
    op.create_table(
        "probe_runs",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("scan_id", sa.Uuid(), sa.ForeignKey("scans.id"), nullable=False),
        sa.Column("probe_id", sa.String(128), nullable=False),
        sa.Column("engine", sa.String(32), nullable=False),
        sa.Column("params", postgresql.JSONB(), nullable=False),
        sa.Column("response_excerpt", sa.Text(), nullable=True),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("vulnerable", sa.Boolean(), nullable=False),
        sa.Column("cost_usdc", sa.Numeric(18, 6), nullable=False),
        *_ts_columns(),
    )
    op.create_index("ix_probe_runs_scan_id", "probe_runs", ["scan_id"])
    op.create_index("ix_probe_runs_probe_id", "probe_runs", ["probe_id"])
    op.create_index("ix_probe_runs_engine", "probe_runs", ["engine"])
    op.create_index("ix_probe_runs_status", "probe_runs", ["status"])
    op.create_index("ix_probe_runs_vulnerable", "probe_runs", ["vulnerable"])

    # ------------------------------------------------------- narration_events
    op.create_table(
        "narration_events",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("scan_id", sa.Uuid(), sa.ForeignKey("scans.id"), nullable=False),
        sa.Column(
            "probe_run_id", sa.Uuid(), sa.ForeignKey("probe_runs.id"), nullable=True
        ),
        sa.Column("phase", sa.String(32), nullable=False),
        sa.Column("success_signal", sa.Boolean(), nullable=True),
        sa.Column("target_observations", postgresql.JSONB(), nullable=False),
        sa.Column("decision", sa.String(64), nullable=True),
        sa.Column("next_action", sa.String(128), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("context", postgresql.JSONB(), nullable=False),
        *_ts_columns(),
    )
    op.create_index("ix_narration_events_scan_id", "narration_events", ["scan_id"])
    op.create_index(
        "ix_narration_events_probe_run_id", "narration_events", ["probe_run_id"]
    )
    op.create_index("ix_narration_events_phase", "narration_events", ["phase"])
    op.create_index("ix_narration_events_decision", "narration_events", ["decision"])

    # ---------------------------------------------------------- memory_events
    op.create_table(
        "memory_events",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("scan_id", sa.Uuid(), sa.ForeignKey("scans.id"), nullable=False),
        sa.Column(
            "probe_run_id", sa.Uuid(), sa.ForeignKey("probe_runs.id"), nullable=True
        ),
        sa.Column("event_type", sa.String(32), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("target_type", sa.String(128), nullable=True),
        sa.Column("probe_class", sa.String(128), nullable=True),
        sa.Column("embedding", Vector(EMBEDDING_DIM), nullable=True),
        *_ts_columns(),
    )
    op.create_index("ix_memory_events_scan_id", "memory_events", ["scan_id"])
    op.create_index("ix_memory_events_probe_run_id", "memory_events", ["probe_run_id"])
    op.create_index("ix_memory_events_event_type", "memory_events", ["event_type"])
    op.create_index("ix_memory_events_target_type", "memory_events", ["target_type"])
    op.create_index("ix_memory_events_probe_class", "memory_events", ["probe_class"])
    op.execute(
        "CREATE INDEX ix_memory_events_embedding_hnsw ON memory_events "
        "USING hnsw (embedding vector_cosine_ops)"
    )


def downgrade() -> None:
    # Drop in reverse FK-dependency order. Don't drop the vector extension —
    # other databases on the same cluster may share it.
    op.drop_table("memory_events")
    op.drop_table("narration_events")
    op.drop_table("probe_runs")
    op.drop_table("findings")
    op.drop_table("memory_items")
    op.drop_table("heuristics")
    op.drop_table("modules")
    op.drop_table("scans")
