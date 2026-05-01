"""Initial schema

Revision ID: 001
Revises:
Create Date: 2024-01-01 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # departments
    op.create_table(
        "departments",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("slug", sa.String(100), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
        sa.UniqueConstraint("slug"),
    )

    # users
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("email", sa.String(300), nullable=False),
        sa.Column("name", sa.String(300), nullable=True),
        sa.Column("role", sa.Enum("admin", "buero", "dozent", name="userrole"), nullable=False),
        sa.Column("department_id", sa.Integer(), nullable=True),
        sa.Column("cognito_sub", sa.String(100), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["department_id"], ["departments.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("cognito_sub"),
    )
    op.create_index("ix_users_email", "users", ["email"])
    op.create_index("ix_users_cognito_sub", "users", ["cognito_sub"])

    # reminder_configs
    op.create_table(
        "reminder_configs",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("department_id", sa.Integer(), nullable=False),
        sa.Column("days_before", sa.String(100), nullable=False, server_default="7,3,1"),
        sa.Column("send_overdue", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("overdue_interval_days", sa.Integer(), nullable=False, server_default="3"),
        sa.ForeignKeyConstraint(["department_id"], ["departments.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("department_id"),
    )

    # email_templates
    op.create_table(
        "email_templates",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("department_id", sa.Integer(), nullable=True),
        sa.Column("type", sa.String(50), nullable=False),
        sa.Column("subject", sa.String(500), nullable=False),
        sa.Column("body_html", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["department_id"], ["departments.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # document_requests
    op.create_table(
        "document_requests",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("department_id", sa.Integer(), nullable=False),
        sa.Column("created_by", sa.Integer(), nullable=False),
        sa.Column("deadline", sa.DateTime(), nullable=False),
        sa.Column("status", sa.Enum(
            "open", "partial", "completed", "overdue", name="requeststatus"
        ), nullable=False, server_default="open"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["department_id"], ["departments.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # request_assignments
    op.create_table(
        "request_assignments",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("request_id", sa.Integer(), nullable=False),
        sa.Column("dozent_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.Enum(
            "pending", "uploaded", "overdue", name="assignmentstatus"
        ), nullable=False, server_default="pending"),
        sa.Column("submitted_at", sa.DateTime(), nullable=True),
        sa.Column("last_reminder_sent_at", sa.DateTime(), nullable=True),
        sa.Column("reminder_count", sa.Integer(), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(["request_id"], ["document_requests.id"]),
        sa.ForeignKeyConstraint(["dozent_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # uploaded_files
    op.create_table(
        "uploaded_files",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("assignment_id", sa.Integer(), nullable=False),
        sa.Column("s3_key", sa.String(1000), nullable=False),
        sa.Column("filename", sa.String(500), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("content_type", sa.String(100), nullable=False, server_default="application/octet-stream"),
        sa.Column("uploaded_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["assignment_id"], ["request_assignments.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("uploaded_files")
    op.drop_table("request_assignments")
    op.drop_table("document_requests")
    op.drop_table("email_templates")
    op.drop_table("reminder_configs")
    op.drop_table("users")
    op.drop_table("departments")
    op.execute("DROP TYPE IF EXISTS userrole")
    op.execute("DROP TYPE IF EXISTS requeststatus")
    op.execute("DROP TYPE IF EXISTS assignmentstatus")
