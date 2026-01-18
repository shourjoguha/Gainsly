"""Add goals and biometrics tables

Revision ID: ae12bc34de56
Revises: 9c1a2b3c4d5e
Create Date: 2026-01-18

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "ae12bc34de56"
down_revision: Union[str, Sequence[str], None] = "9c1a2b3c4d5e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    dialect_name = conn.dialect.name

    # Helper to create enum if not exists (PostgreSQL only)
    def create_enum_if_not_exists(name, values):
        if dialect_name != "postgresql":
            return
        has_type = conn.execute(
            sa.text(f"SELECT 1 FROM pg_type WHERE typname = '{name}'")
        ).scalar()
        if not has_type:
            sa.Enum(*values, name=name).create(conn)

    # Define enums
    sex_enum = sa.Enum("FEMALE", "MALE", "INTERSEX", "UNSPECIFIED", name="sex")
    data_source_enum = sa.Enum("MANUAL", "PROVIDER", "ESTIMATED", name="datasource")
    biometric_metric_type_enum = sa.Enum(
        "WEIGHT_KG",
        "BODY_FAT_PERCENT",
        "RESTING_HR",
        "HRV",
        "SLEEP_HOURS",
        "VO2_MAX",
        name="biometricmetrictype",
    )
    goal_type_enum = sa.Enum(
        "PERFORMANCE",
        "BODY_COMPOSITION",
        "SKILL",
        "HEALTH",
        "HABIT",
        "OTHER",
        name="goaltype",
    )
    goal_status_enum = sa.Enum(
        "ACTIVE",
        "PAUSED",
        "COMPLETED",
        "CANCELLED",
        name="goalstatus",
    )

    # Create enums safely
    create_enum_if_not_exists("sex", ["FEMALE", "MALE", "INTERSEX", "UNSPECIFIED"])
    create_enum_if_not_exists("datasource", ["MANUAL", "PROVIDER", "ESTIMATED"])
    create_enum_if_not_exists("biometricmetrictype", [
        "WEIGHT_KG", "BODY_FAT_PERCENT", "RESTING_HR", "HRV", "SLEEP_HOURS", "VO2_MAX"
    ])
    create_enum_if_not_exists("goaltype", [
        "PERFORMANCE", "BODY_COMPOSITION", "SKILL", "HEALTH", "HABIT", "OTHER"
    ])
    create_enum_if_not_exists("goalstatus", [
        "ACTIVE", "PAUSED", "COMPLETED", "CANCELLED"
    ])

    if not inspector.has_table("user_profiles"):
        op.create_table(
            "user_profiles",
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("date_of_birth", sa.Date(), nullable=True),
            sa.Column("sex", sex_enum, nullable=True),
            sa.Column("height_cm", sa.Integer(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
            sa.PrimaryKeyConstraint("user_id"),
        )

    if not inspector.has_table("user_biometrics_history"):
        op.create_table(
            "user_biometrics_history",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("date", sa.Date(), nullable=False),
            sa.Column("metric_type", biometric_metric_type_enum, nullable=False),
            sa.Column("value", sa.Float(), nullable=False),
            sa.Column("source", data_source_enum, nullable=False),
            sa.Column("external_reference", sa.String(length=255), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_user_biometrics_history_date"), "user_biometrics_history", ["date"], unique=False)
        op.create_index(op.f("ix_user_biometrics_history_metric_type"), "user_biometrics_history", ["metric_type"], unique=False)
        op.create_index(op.f("ix_user_biometrics_history_user_id"), "user_biometrics_history", ["user_id"], unique=False)

    if not inspector.has_table("macro_cycles"):
        op.create_table(
            "macro_cycles",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("name", sa.String(length=200), nullable=True),
            sa.Column("start_date", sa.Date(), nullable=False),
            sa.Column("end_date", sa.Date(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_macro_cycles_user_id"), "macro_cycles", ["user_id"], unique=False)

    # Check if programs already has macro_cycle_id
    programs_columns = [c["name"] for c in inspector.get_columns("programs")]
    if "macro_cycle_id" not in programs_columns:
        with op.batch_alter_table("programs") as batch_op:
            batch_op.add_column(sa.Column("macro_cycle_id", sa.Integer(), nullable=True))
            batch_op.create_index(op.f("ix_programs_macro_cycle_id"), ["macro_cycle_id"], unique=False)
            batch_op.create_foreign_key(
                "fk_programs_macro_cycle_id_macro_cycles",
                "macro_cycles",
                ["macro_cycle_id"],
                ["id"],
            )

    if not inspector.has_table("goals"):
        op.create_table(
            "goals",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("macro_cycle_id", sa.Integer(), nullable=True),
            sa.Column("program_id", sa.Integer(), nullable=True),
            sa.Column("goal_type", goal_type_enum, nullable=False),
            sa.Column("target_json", sa.JSON(), nullable=True),
            sa.Column("priority", sa.Integer(), nullable=False),
            sa.Column("status", goal_status_enum, nullable=False),
            sa.Column("effective_from", sa.DateTime(), nullable=False),
            sa.Column("effective_to", sa.DateTime(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(["macro_cycle_id"], ["macro_cycles.id"]),
            sa.ForeignKeyConstraint(["program_id"], ["programs.id"]),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_goals_macro_cycle_id"), "goals", ["macro_cycle_id"], unique=False)
        op.create_index(op.f("ix_goals_program_id"), "goals", ["program_id"], unique=False)
        op.create_index(op.f("ix_goals_user_id"), "goals", ["user_id"], unique=False)

    if not inspector.has_table("goal_checkins"):
        op.create_table(
            "goal_checkins",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("goal_id", sa.Integer(), nullable=False),
            sa.Column("date", sa.Date(), nullable=False),
            sa.Column("value_json", sa.JSON(), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(["goal_id"], ["goals.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_goal_checkins_date"), "goal_checkins", ["date"], unique=False)
        op.create_index(op.f("ix_goal_checkins_goal_id"), "goal_checkins", ["goal_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_goal_checkins_goal_id"), table_name="goal_checkins")
    op.drop_index(op.f("ix_goal_checkins_date"), table_name="goal_checkins")
    op.drop_table("goal_checkins")

    op.drop_index(op.f("ix_goals_user_id"), table_name="goals")
    op.drop_index(op.f("ix_goals_program_id"), table_name="goals")
    op.drop_index(op.f("ix_goals_macro_cycle_id"), table_name="goals")
    op.drop_table("goals")

    with op.batch_alter_table("programs") as batch_op:
        batch_op.drop_constraint("fk_programs_macro_cycle_id_macro_cycles", type_="foreignkey")
        batch_op.drop_index(op.f("ix_programs_macro_cycle_id"))
        batch_op.drop_column("macro_cycle_id")

    op.drop_index(op.f("ix_macro_cycles_user_id"), table_name="macro_cycles")
    op.drop_table("macro_cycles")

    op.drop_index(op.f("ix_user_biometrics_history_user_id"), table_name="user_biometrics_history")
    op.drop_index(op.f("ix_user_biometrics_history_metric_type"), table_name="user_biometrics_history")
    op.drop_index(op.f("ix_user_biometrics_history_date"), table_name="user_biometrics_history")
    op.drop_table("user_biometrics_history")

    op.drop_table("user_profiles")
