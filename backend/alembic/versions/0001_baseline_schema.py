"""Baseline schema representing existing AquaWatt tables.

Revision ID: 0001_baseline_schema
Revises: None
Create Date: 2026-11-15 20:50:00.000000

STATUS: NOT EXECUTED.
This migration script documents the exact pre-existing schema of the four
active PostgreSQL tables (users, household_profiles, electricity_consumption,
water_consumption) prior to Phase 6 multi-household architecture changes.

IMPORTANT FOR PHASE 6.2B:
Because this database already contains live records (165 users, 80 profiles,
101 electricity records, 100 water records), Phase 6.2B MUST NOT run
`alembic upgrade 0001_baseline_schema` (which would attempt to re-create
existing tables). Instead, Phase 6.2B will establish this baseline using:
    alembic stamp 0001_baseline_schema
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0001_baseline_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create existing four tables if initializing an empty database from scratch."""
    # 1. Table: users
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("full_name", sa.String(length=100), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="users_pkey"),
    )
    op.create_index("ix_users_id", "users", ["id"], unique=False)
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    # 2. Table: household_profiles
    op.create_table(
        "household_profiles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("household_members", sa.Integer(), nullable=False),
        sa.Column("house_type", sa.String(length=50), nullable=False),
        sa.Column("location", sa.String(length=150), nullable=False),
        sa.Column("num_bathrooms", sa.Integer(), nullable=False),
        sa.Column("people_usually_at_home", sa.Integer(), nullable=True),
        sa.Column("unusual_occupancy", sa.String(length=50), server_default="None", nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="household_profiles_user_id_fkey", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="household_profiles_pkey"),
        sa.UniqueConstraint("user_id", name="household_profiles_user_id_key"),
    )
    op.create_index("ix_household_profiles_id", "household_profiles", ["id"], unique=False)

    # 3. Table: electricity_consumption
    op.create_table(
        "electricity_consumption",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("profile_id", sa.Integer(), nullable=False),
        sa.Column("monthly_consumption_kwh", sa.Float(), nullable=False),
        sa.Column("ac_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("fan_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("refrigerator_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("tv_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("geyser_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("washing_machine_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("water_pump_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("other_appliances", sa.String(length=255), nullable=True),
        sa.Column("usage_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["profile_id"], ["household_profiles.id"], name="electricity_consumption_profile_id_fkey", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="electricity_consumption_pkey"),
    )
    op.create_index("ix_electricity_consumption_id", "electricity_consumption", ["id"], unique=False)
    op.create_index("ix_electricity_consumption_profile_id", "electricity_consumption", ["profile_id"], unique=False)

    # 4. Table: water_consumption
    op.create_table(
        "water_consumption",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("profile_id", sa.Integer(), nullable=False),
        sa.Column("monthly_consumption_litres", sa.Float(), nullable=False),
        sa.Column("num_showers", sa.Integer(), server_default="0", nullable=False),
        sa.Column("avg_shower_duration_mins", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("bucket_usage", sa.Integer(), server_default="0", nullable=False),
        sa.Column("washing_machine_usage", sa.String(length=100), nullable=True),
        sa.Column("garden_watering", sa.String(length=100), nullable=True),
        sa.Column("vehicle_washing", sa.String(length=100), nullable=True),
        sa.Column("water_pump_usage", sa.String(length=100), nullable=True),
        sa.Column("other_water_usage", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["profile_id"], ["household_profiles.id"], name="water_consumption_profile_id_fkey", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="water_consumption_pkey"),
    )
    op.create_index("ix_water_consumption_id", "water_consumption", ["id"], unique=False)
    op.create_index("ix_water_consumption_profile_id", "water_consumption", ["profile_id"], unique=False)


def downgrade() -> None:
    """Drop tables in reverse dependency order."""
    op.drop_index("ix_water_consumption_profile_id", table_name="water_consumption")
    op.drop_index("ix_water_consumption_id", table_name="water_consumption")
    op.drop_table("water_consumption")

    op.drop_index("ix_electricity_consumption_profile_id", table_name="electricity_consumption")
    op.drop_index("ix_electricity_consumption_id", table_name="electricity_consumption")
    op.drop_table("electricity_consumption")

    op.drop_index("ix_household_profiles_id", table_name="household_profiles")
    op.drop_table("household_profiles")

    op.drop_index("ix_users_email", table_name="users")
    op.drop_index("ix_users_id", table_name="users")
    op.drop_table("users")

