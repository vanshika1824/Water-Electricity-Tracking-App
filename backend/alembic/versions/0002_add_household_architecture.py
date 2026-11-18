"""Add households and household_members with backfill and safety constraints.

Revision ID: 0002_add_household_architecture
Revises: 0001_baseline_schema
Create Date: 2026-11-15 20:55:00.000000

STATUS: NOT EXECUTED.
This migration script represents the authored Phase 6.2A schema upgrade.
It transitions AquaWatt from single-user 1-to-1 profiles to multi-member
collaborative households with Role-Based Access Control (RBAC).

MANDATORY SAFETY SAFEGUARDS EMBEDDED:
- Safeguard A (Consumption Protection):
  Foreign keys on electricity_consumption and water_consumption use
  `ondelete='RESTRICT'` rather than CASCADE. Ordinary account or household
  deletion cannot permanently wipe historical consumption records.
  Soft-deletion is supported via `households.deleted_at`.
- Safeguard B (Secure Invite Codes):
  Plaintext join codes are never stored in the database. Only 64-char
  cryptographic SHA-256 hashes (`invite_code_hash`) are stored.
- Safeguard C (Exactly One Active Owner):
  A PostgreSQL partial unique index (`uq_one_active_owner_per_household`)
  enforces at most one active OWNER per household at the database level.
  Application services enforce the lower bound (at least one active owner).
- Safeguard D (Sequence Synchronization):
  PostgreSQL sequences for `households_id_seq` and `household_members_id_seq`
  are explicitly synchronized to max(id) so subsequent inserts cannot collide.
"""

import hashlib
import secrets
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0002_add_household_architecture"
down_revision: Union[str, None] = "0001_baseline_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # =========================================================================
    # STEP 1: Create 'households' Table
    # =========================================================================
    op.create_table(
        "households",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("household_name", sa.String(length=100), nullable=False),
        sa.Column("address", sa.String(length=255), nullable=False),
        sa.Column("house_type", sa.String(length=50), nullable=False),
        sa.Column("num_bathrooms", sa.Integer(), server_default="1", nullable=False),
        sa.Column("manual_member_count", sa.Integer(), server_default="1", nullable=False),
        sa.Column("people_usually_at_home", sa.Integer(), nullable=True),
        sa.Column("unusual_occupancy", sa.String(length=50), server_default="None", nullable=True),
        sa.Column("invite_code_hash", sa.String(length=64), nullable=False),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], name="fk_households_created_by", ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name="households_pkey"),
    )
    op.create_index("ix_households_id", "households", ["id"], unique=False)
    op.create_index("ix_households_invite_code_hash", "households", ["invite_code_hash"], unique=True)
    op.create_index("ix_households_created_by", "households", ["created_by"], unique=False)

    # =========================================================================
    # STEP 2: Create 'household_members' Table with Role Constraints
    # =========================================================================
    op.create_table(
        "household_members",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("household_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("role", sa.String(length=20), server_default="MEMBER", nullable=False),
        sa.Column("membership_status", sa.String(length=20), server_default="ACTIVE", nullable=False),
        sa.Column("joined_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("role IN ('OWNER', 'ADMIN', 'MEMBER')", name="chk_member_role"),
        sa.CheckConstraint("membership_status IN ('ACTIVE', 'INVITED', 'INACTIVE')", name="chk_membership_status"),
        sa.ForeignKeyConstraint(["household_id"], ["households.id"], name="fk_members_household", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_members_user", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="household_members_pkey"),
        sa.UniqueConstraint("household_id", "user_id", name="uq_household_member"),
    )
    op.create_index("ix_household_members_id", "household_members", ["id"], unique=False)
    op.create_index("ix_household_members_household_id", "household_members", ["household_id"], unique=False)
    op.create_index("ix_household_members_user_id", "household_members", ["user_id"], unique=False)

    # SAFEGUARD C: Partial unique index enforcing AT MOST ONE active OWNER per household
    op.create_index(
        "uq_one_active_owner_per_household",
        "household_members",
        ["household_id"],
        unique=True,
        postgresql_where=sa.text("role = 'OWNER' AND membership_status = 'ACTIVE'"),
    )

    # =========================================================================
    # STEP 3: Add New Columns to Consumption Tables (Nullable initially)
    # =========================================================================
    # SAFEGUARD A: ondelete='RESTRICT' protects consumption history from cascading deletion
    op.add_column("electricity_consumption", sa.Column("household_id", sa.Integer(), nullable=True))
    op.add_column("electricity_consumption", sa.Column("submitted_by_user_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_elec_consumption_household",
        "electricity_consumption",
        "households",
        ["household_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        "fk_elec_consumption_submitted_by",
        "electricity_consumption",
        "users",
        ["submitted_by_user_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_elec_household_created",
        "electricity_consumption",
        ["household_id", "created_at"],
        unique=False,
    )

    op.add_column("water_consumption", sa.Column("household_id", sa.Integer(), nullable=True))
    op.add_column("water_consumption", sa.Column("submitted_by_user_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_water_consumption_household",
        "water_consumption",
        "households",
        ["household_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        "fk_water_consumption_submitted_by",
        "water_consumption",
        "users",
        ["submitted_by_user_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_water_household_created",
        "water_consumption",
        ["household_id", "created_at"],
        unique=False,
    )

    # =========================================================================
    # STEP 4: Transactional Data Backfill & Integrity Verification
    # =========================================================================
    connection = op.get_bind()

    # 4.1 Validate Pre-conditions
    profile_rows = connection.execute(sa.text("""
        SELECT hp.id, hp.user_id, hp.household_members, hp.house_type, hp.location,
               hp.num_bathrooms, hp.people_usually_at_home, hp.unusual_occupancy,
               hp.created_at, hp.updated_at, u.full_name
        FROM household_profiles hp
        LEFT JOIN users u ON hp.user_id = u.id
        ORDER BY hp.id ASC
    """)).fetchall()

    for p in profile_rows:
        if p.full_name is None:
            raise RuntimeError(
                f"Data Backfill Error: HouseholdProfile id={p.id} references user_id={p.user_id} which does not exist in users table."
            )

    # 4.2 Backfill households and OWNER household_members
    # Retain existing profile IDs for seamless 1:1 mapping
    for p in profile_rows:
        # Generate secure random token and its SHA-256 hash
        # Format: AQ-XXXXXX with unambiguous characters
        raw_token = f"AQ-{''.join(secrets.choice('23456789ABCDEFGHJKLMNPQRSTUVWXYZ') for _ in range(6))}"
        token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
        household_title = f"{p.full_name}'s Household" if p.full_name else f"Household #{p.id}"

        connection.execute(sa.text("""
            INSERT INTO households (
                id, household_name, address, house_type, num_bathrooms,
                manual_member_count, people_usually_at_home, unusual_occupancy,
                invite_code_hash, created_by, created_at, updated_at
            ) VALUES (
                :id, :name, :address, :house_type, :num_bathrooms,
                :members, :people_at_home, :occupancy,
                :invite_hash, :created_by, :created_at, :updated_at
            )
        """), {
            "id": p.id,
            "name": household_title,
            "address": p.location,
            "house_type": p.house_type,
            "num_bathrooms": p.num_bathrooms,
            "members": p.household_members,
            "people_at_home": p.people_usually_at_home,
            "occupancy": p.unusual_occupancy or "None",
            "invite_hash": token_hash,
            "created_by": p.user_id,
            "created_at": p.created_at,
            "updated_at": p.updated_at,
        })

        connection.execute(sa.text("""
            INSERT INTO household_members (
                household_id, user_id, role, membership_status, joined_at
            ) VALUES (
                :household_id, :user_id, 'OWNER', 'ACTIVE', :joined_at
            )
        """), {
            "household_id": p.id,
            "user_id": p.user_id,
            "joined_at": p.created_at,
        })

    # 4.3 Backfill electricity_consumption records
    connection.execute(sa.text("""
        UPDATE electricity_consumption ec
        SET household_id = hp.id,
            submitted_by_user_id = hp.user_id
        FROM household_profiles hp
        WHERE ec.profile_id = hp.id
    """))

    # 4.4 Backfill water_consumption records
    connection.execute(sa.text("""
        UPDATE water_consumption wc
        SET household_id = hp.id,
            submitted_by_user_id = hp.user_id
        FROM household_profiles hp
        WHERE wc.profile_id = hp.id
    """))

    # 4.5 Verify Zero Unmapped Consumption Records
    unmapped_elec = connection.execute(sa.text(
        "SELECT count(*) FROM electricity_consumption WHERE household_id IS NULL"
    )).scalar()
    if unmapped_elec > 0:
        raise RuntimeError(f"Backfill Verification Failed: {unmapped_elec} electricity records could not be mapped to a household.")

    unmapped_water = connection.execute(sa.text(
        "SELECT count(*) FROM water_consumption WHERE household_id IS NULL"
    )).scalar()
    if unmapped_water > 0:
        raise RuntimeError(f"Backfill Verification Failed: {unmapped_water} water records could not be mapped to a household.")

    # 4.6 Enforce NOT NULL on household_id now that all rows are populated
    op.alter_column("electricity_consumption", "household_id", nullable=False)
    op.alter_column("water_consumption", "household_id", nullable=False)

    # =========================================================================
    # STEP 5: SAFEGUARD D - PostgreSQL Sequence Synchronization
    # =========================================================================
    connection.execute(sa.text("""
        SELECT setval(
            pg_get_serial_sequence('households', 'id'),
            COALESCE((SELECT MAX(id) FROM households), 1),
            (SELECT MAX(id) FROM households) IS NOT NULL
        )
    """))
    connection.execute(sa.text("""
        SELECT setval(
            pg_get_serial_sequence('household_members', 'id'),
            COALESCE((SELECT MAX(id) FROM household_members), 1),
            (SELECT MAX(id) FROM household_members) IS NOT NULL
        )
    """))


def downgrade() -> None:
    """Revert household architecture changes.

    CAUTION: Downgrade is lossy for any newly added members or multi-member
    households created after the migration. Existing legacy profiles and
    consumption records remain intact via their legacy profile_id links.
    """
    # Remove consumption table additions
    op.drop_index("ix_water_household_created", table_name="water_consumption")
    op.drop_constraint("fk_water_consumption_submitted_by", "water_consumption", type_="foreignkey")
    op.drop_constraint("fk_water_consumption_household", "water_consumption", type_="foreignkey")
    op.drop_column("water_consumption", "submitted_by_user_id")
    op.drop_column("water_consumption", "household_id")

    op.drop_index("ix_elec_household_created", table_name="electricity_consumption")
    op.drop_constraint("fk_elec_consumption_submitted_by", "electricity_consumption", type_="foreignkey")
    op.drop_constraint("fk_elec_consumption_household", "electricity_consumption", type_="foreignkey")
    op.drop_column("electricity_consumption", "submitted_by_user_id")
    op.drop_column("electricity_consumption", "household_id")

    # Drop household_members
    op.drop_index("uq_one_active_owner_per_household", table_name="household_members")
    op.drop_index("ix_household_members_user_id", table_name="household_members")
    op.drop_index("ix_household_members_household_id", table_name="household_members")
    op.drop_index("ix_household_members_id", table_name="household_members")
    op.drop_table("household_members")

    # Drop households
    op.drop_index("ix_households_created_by", table_name="households")
    op.drop_index("ix_households_invite_code_hash", table_name="households")
    op.drop_index("ix_households_id", table_name="households")
    op.drop_table("households")

