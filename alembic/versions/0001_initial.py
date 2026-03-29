"""initial

Revision ID: 0001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '0001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

    op.create_table('organisations',
        sa.Column('id', sa.String(), server_default=sa.text("gen_random_uuid()::text"), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table('roles',
        sa.Column('id', sa.String(), server_default=sa.text("gen_random_uuid()::text"), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('permissions', sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )

    op.create_table('sites',
        sa.Column('id', sa.String(), server_default=sa.text("gen_random_uuid()::text"), nullable=False),
        sa.Column('organisation_id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('address', sa.String(), nullable=True),
        sa.Column('allowed_ip_ranges', sa.JSON(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['organisation_id'], ['organisations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table('units',
        sa.Column('id', sa.String(), server_default=sa.text("gen_random_uuid()::text"), nullable=False),
        sa.Column('site_id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['site_id'], ['sites.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table('users',
        sa.Column('id', sa.String(), server_default=sa.text("gen_random_uuid()::text"), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('hashed_password', sa.String(), nullable=False),
        sa.Column('full_name', sa.String(), nullable=True),
        sa.Column('role_id', sa.String(), nullable=True),
        sa.Column('organisation_id', sa.String(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('is_superuser', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['organisation_id'], ['organisations.id'], ),
        sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )

    op.create_table('user_unit_assignments',
        sa.Column('id', sa.String(), server_default=sa.text("gen_random_uuid()::text"), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('unit_id', sa.String(), nullable=False),
        sa.Column('assigned_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('assigned_by_id', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['assigned_by_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['unit_id'], ['units.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'unit_id')
    )

    op.create_table('body_regions',
        sa.Column('id', sa.String(), server_default=sa.text("gen_random_uuid()::text"), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )

    op.create_table('residents',
        sa.Column('id', sa.String(), server_default=sa.text("gen_random_uuid()::text"), nullable=False),
        sa.Column('unit_id', sa.String(), nullable=False),
        sa.Column('first_name', sa.String(), nullable=False),
        sa.Column('last_name', sa.String(), nullable=False),
        sa.Column('dob', sa.Date(), nullable=True),
        sa.Column('nhs_number', sa.String(), nullable=True),
        sa.Column('room_number', sa.String(), nullable=True),
        sa.Column('allergies', sa.JSON(), nullable=True),
        sa.Column('key_risks', sa.JSON(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['unit_id'], ['units.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table('drugs',
        sa.Column('id', sa.String(), server_default=sa.text("gen_random_uuid()::text"), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('generic_name', sa.String(), nullable=True),
        sa.Column('category', sa.String(), nullable=True),
        sa.Column('controlled_drug_schedule', sa.Integer(), nullable=True),
        sa.Column('unit_of_measure', sa.String(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table('medication_orders',
        sa.Column('id', sa.String(), server_default=sa.text("gen_random_uuid()::text"), nullable=False),
        sa.Column('resident_id', sa.String(), nullable=False),
        sa.Column('drug_id', sa.String(), nullable=False),
        sa.Column('prescribed_by', sa.String(), nullable=True),
        sa.Column('dose_amount', sa.Float(), nullable=True),
        sa.Column('dose_unit', sa.String(), nullable=True),
        sa.Column('route', sa.String(), nullable=True),
        sa.Column('mode_of_administration', sa.JSON(), nullable=True),
        sa.Column('frequency_type', sa.String(), nullable=False),
        sa.Column('daily_times', sa.JSON(), nullable=True),
        sa.Column('interval_hours', sa.Integer(), nullable=True),
        sa.Column('start_date', sa.Date(), nullable=True),
        sa.Column('end_date', sa.Date(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('notes', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['drug_id'], ['drugs.id'], ),
        sa.ForeignKeyConstraint(['resident_id'], ['residents.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table('doses_due',
        sa.Column('id', sa.String(), server_default=sa.text("gen_random_uuid()::text"), nullable=False),
        sa.Column('order_id', sa.String(), nullable=False),
        sa.Column('resident_id', sa.String(), nullable=False),
        sa.Column('scheduled_datetime', sa.DateTime(timezone=True), nullable=False),
        sa.Column('window_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('window_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('dose_key', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['order_id'], ['medication_orders.id'], ),
        sa.ForeignKeyConstraint(['resident_id'], ['residents.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('dose_key')
    )

    op.create_table('administration_records',
        sa.Column('id', sa.String(), server_default=sa.text("gen_random_uuid()::text"), nullable=False),
        sa.Column('dose_due_id', sa.String(), nullable=True),
        sa.Column('order_id', sa.String(), nullable=False),
        sa.Column('resident_id', sa.String(), nullable=False),
        sa.Column('administered_by_id', sa.String(), nullable=False),
        sa.Column('administered_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('route_display', sa.String(), nullable=True),
        sa.Column('mode_display', sa.String(), nullable=True),
        sa.Column('notes', sa.String(), nullable=True),
        sa.Column('reason_code', sa.String(), nullable=True),
        sa.Column('client_event_id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['administered_by_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['dose_due_id'], ['doses_due.id'], ),
        sa.ForeignKeyConstraint(['order_id'], ['medication_orders.id'], ),
        sa.ForeignKeyConstraint(['resident_id'], ['residents.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('client_event_id')
    )

    op.create_table('administration_body_regions',
        sa.Column('id', sa.String(), server_default=sa.text("gen_random_uuid()::text"), nullable=False),
        sa.Column('administration_id', sa.String(), nullable=False),
        sa.Column('body_region_id', sa.String(), nullable=False),
        sa.ForeignKeyConstraint(['administration_id'], ['administration_records.id'], ),
        sa.ForeignKeyConstraint(['body_region_id'], ['body_regions.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table('cd_transactions',
        sa.Column('id', sa.String(), server_default=sa.text("gen_random_uuid()::text"), nullable=False),
        sa.Column('transaction_type', sa.String(), nullable=False),
        sa.Column('drug_id', sa.String(), nullable=False),
        sa.Column('resident_id', sa.String(), nullable=True),
        sa.Column('order_id', sa.String(), nullable=True),
        sa.Column('quantity', sa.Float(), nullable=False),
        sa.Column('unit', sa.String(), nullable=True),
        sa.Column('performed_by_id', sa.String(), nullable=False),
        sa.Column('performed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('witnessed_by_id', sa.String(), nullable=True),
        sa.Column('witnessed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('reason', sa.String(), nullable=True),
        sa.Column('client_event_id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['drug_id'], ['drugs.id'], ),
        sa.ForeignKeyConstraint(['order_id'], ['medication_orders.id'], ),
        sa.ForeignKeyConstraint(['performed_by_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['resident_id'], ['residents.id'], ),
        sa.ForeignKeyConstraint(['witnessed_by_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('client_event_id')
    )

    op.create_table('stock_locations',
        sa.Column('id', sa.String(), server_default=sa.text("gen_random_uuid()::text"), nullable=False),
        sa.Column('unit_id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('location_type', sa.String(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(['unit_id'], ['units.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table('stock_items',
        sa.Column('id', sa.String(), server_default=sa.text("gen_random_uuid()::text"), nullable=False),
        sa.Column('location_id', sa.String(), nullable=False),
        sa.Column('drug_id', sa.String(), nullable=False),
        sa.Column('on_hand_qty', sa.Float(), nullable=True),
        sa.Column('reorder_threshold', sa.Float(), nullable=True),
        sa.Column('unit_of_measure', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['drug_id'], ['drugs.id'], ),
        sa.ForeignKeyConstraint(['location_id'], ['stock_locations.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('location_id', 'drug_id')
    )

    op.create_table('stock_transactions',
        sa.Column('id', sa.String(), server_default=sa.text("gen_random_uuid()::text"), nullable=False),
        sa.Column('item_id', sa.String(), nullable=False),
        sa.Column('transaction_type', sa.String(), nullable=False),
        sa.Column('quantity_change', sa.Float(), nullable=False),
        sa.Column('quantity_after', sa.Float(), nullable=True),
        sa.Column('notes', sa.String(), nullable=True),
        sa.Column('performed_by_id', sa.String(), nullable=False),
        sa.Column('client_event_id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['item_id'], ['stock_items.id'], ),
        sa.ForeignKeyConstraint(['performed_by_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('client_event_id')
    )

    op.create_table('stock_alerts',
        sa.Column('id', sa.String(), server_default=sa.text("gen_random_uuid()::text"), nullable=False),
        sa.Column('item_id', sa.String(), nullable=False),
        sa.Column('alert_type', sa.String(), nullable=False),
        sa.Column('triggered_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resolved_by_id', sa.String(), nullable=True),
        sa.Column('notes', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['item_id'], ['stock_items.id'], ),
        sa.ForeignKeyConstraint(['resolved_by_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table('gp_contacts',
        sa.Column('id', sa.String(), server_default=sa.text("gen_random_uuid()::text"), nullable=False),
        sa.Column('site_id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('practice_name', sa.String(), nullable=True),
        sa.Column('email', sa.String(), nullable=True),
        sa.Column('phone', sa.String(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(['site_id'], ['sites.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table('prescription_requests',
        sa.Column('id', sa.String(), server_default=sa.text("gen_random_uuid()::text"), nullable=False),
        sa.Column('resident_id', sa.String(), nullable=False),
        sa.Column('gp_contact_id', sa.String(), nullable=True),
        sa.Column('requested_by_id', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('ai_draft_content', sa.Text(), nullable=True),
        sa.Column('notes', sa.String(), nullable=True),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['gp_contact_id'], ['gp_contacts.id'], ),
        sa.ForeignKeyConstraint(['requested_by_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['resident_id'], ['residents.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table('medication_errors',
        sa.Column('id', sa.String(), server_default=sa.text("gen_random_uuid()::text"), nullable=False),
        sa.Column('administration_id', sa.String(), nullable=True),
        sa.Column('resident_id', sa.String(), nullable=False),
        sa.Column('reported_by_id', sa.String(), nullable=False),
        sa.Column('error_type', sa.String(), nullable=False),
        sa.Column('severity', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('contributing_factors', sa.JSON(), nullable=True),
        sa.Column('actions_taken', sa.Text(), nullable=True),
        sa.Column('closed_by_id', sa.String(), nullable=True),
        sa.Column('closed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['administration_id'], ['administration_records.id'], ),
        sa.ForeignKeyConstraint(['closed_by_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['reported_by_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['resident_id'], ['residents.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table('ingested_events',
        sa.Column('id', sa.String(), server_default=sa.text("gen_random_uuid()::text"), nullable=False),
        sa.Column('organisation_id', sa.String(), nullable=False),
        sa.Column('client_event_id', sa.String(), nullable=False),
        sa.Column('event_type', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('organisation_id', 'client_event_id', name='uq_ingested_event_org_client')
    )
    op.create_index('ix_ingested_events_organisation_id', 'ingested_events', ['organisation_id'], unique=False)

def downgrade() -> None:
    op.drop_index('ix_ingested_events_organisation_id', table_name='ingested_events')
    op.drop_table('ingested_events')
    op.drop_table('medication_errors')
    op.drop_table('prescription_requests')
    op.drop_table('gp_contacts')
    op.drop_table('stock_alerts')
    op.drop_table('stock_transactions')
    op.drop_table('stock_items')
    op.drop_table('stock_locations')
    op.drop_table('cd_transactions')
    op.drop_table('administration_body_regions')
    op.drop_table('administration_records')
    op.drop_table('doses_due')
    op.drop_table('medication_orders')
    op.drop_table('drugs')
    op.drop_table('residents')
    op.drop_table('body_regions')
    op.drop_table('user_unit_assignments')
    op.drop_table('users')
    op.drop_table('units')
    op.drop_table('sites')
    op.drop_table('roles')
    op.drop_table('organisations')
