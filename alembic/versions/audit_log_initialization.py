"""Initial migration to establish the audit_logs table."""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'audit_log_initialization'
down_revision = '0001_create_agents'
depends_on = None # No dependencies required for this foundational table creation.

def upgrade() -> None:
    """Create the audit_logs table."""
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('run_id', sa.String(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('component', sa.String(), nullable=False),
        sa.Column('action_type', sa.Enum('START', 'END', 'CALL', 'RETURN', 'ERROR'), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('input_payload', sa.JSON(), nullable=True),
        sa.Column('output_payload', sa.JSON(), nullable=True),
        sa.Column('duration_ms', sa.Float(), nullable=True)
    )
    op.create_index('ix_audit_run_id', 'audit_logs', ['run_id'], unique=False)


def downgrade() -> None:
    """Drops the audit_logs table."""
    op.drop_table('audit_logs')