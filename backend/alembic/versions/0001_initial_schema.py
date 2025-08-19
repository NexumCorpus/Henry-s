"""Initial schema with core tables

Revision ID: 0001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create users table
    op.create_table('users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('username', sa.String(length=50), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=False),
        sa.Column('role', sa.Enum('barback', 'bartender', 'manager', 'admin', name='userrole'), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    # Create locations table
    op.create_table('locations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('type', sa.Enum('bar', 'storage', 'kitchen', 'rooftop', name='locationtype'), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_locations_id'), 'locations', ['id'], unique=False)
    op.create_index(op.f('ix_locations_name'), 'locations', ['name'], unique=False)

    # Create suppliers table
    op.create_table('suppliers',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('contact_name', sa.String(length=255), nullable=True),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('phone', sa.String(length=50), nullable=True),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('api_endpoint', sa.String(length=500), nullable=True),
        sa.Column('api_credentials', sa.JSON(), nullable=True),
        sa.Column('payment_terms', sa.String(length=100), nullable=True),
        sa.Column('delivery_schedule', sa.String(length=255), nullable=True),
        sa.Column('minimum_order_amount', sa.String(length=50), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('is_preferred', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_suppliers_id'), 'suppliers', ['id'], unique=False)
    op.create_index(op.f('ix_suppliers_name'), 'suppliers', ['name'], unique=False)

    # Create inventory_items table
    op.create_table('inventory_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('category', sa.Enum('spirits', 'beer', 'wine', 'mixers', 'garnishes', 'food', 'supplies', name='itemcategory'), nullable=False),
        sa.Column('barcode', sa.String(length=100), nullable=True),
        sa.Column('sku', sa.String(length=100), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('unit_of_measure', sa.Enum('bottle', 'case', 'liter', 'gallon', 'ounce', 'pound', 'each', name='unitofmeasure'), nullable=False),
        sa.Column('cost_per_unit', sa.DECIMAL(precision=10, scale=2), nullable=True),
        sa.Column('selling_price', sa.DECIMAL(precision=10, scale=2), nullable=True),
        sa.Column('par_level', sa.Float(), nullable=False),
        sa.Column('reorder_point', sa.Float(), nullable=False),
        sa.Column('supplier_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('expiration_days', sa.Float(), nullable=True),
        sa.Column('is_active', sa.String(length=10), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['supplier_id'], ['suppliers.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_inventory_items_id'), 'inventory_items', ['id'], unique=False)
    op.create_index(op.f('ix_inventory_items_name'), 'inventory_items', ['name'], unique=False)
    op.create_index(op.f('ix_inventory_items_category'), 'inventory_items', ['category'], unique=False)
    op.create_index(op.f('ix_inventory_items_barcode'), 'inventory_items', ['barcode'], unique=True)
    op.create_index(op.f('ix_inventory_items_sku'), 'inventory_items', ['sku'], unique=False)
    op.create_index(op.f('ix_inventory_items_supplier_id'), 'inventory_items', ['supplier_id'], unique=False)
    op.create_index('idx_inventory_category_active', 'inventory_items', ['category', 'is_active'], unique=False)
    op.create_index('idx_inventory_supplier_active', 'inventory_items', ['supplier_id', 'is_active'], unique=False)

    # Create stock_levels table
    op.create_table('stock_levels',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('item_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('location_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('current_stock', sa.Float(), nullable=False),
        sa.Column('reserved_stock', sa.Float(), nullable=False),
        sa.Column('last_counted', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_updated', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['item_id'], ['inventory_items.id'], ),
        sa.ForeignKeyConstraint(['location_id'], ['locations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_stock_levels_id'), 'stock_levels', ['id'], unique=False)
    op.create_index(op.f('ix_stock_levels_item_id'), 'stock_levels', ['item_id'], unique=False)
    op.create_index(op.f('ix_stock_levels_location_id'), 'stock_levels', ['location_id'], unique=False)
    op.create_index('idx_stock_item_location', 'stock_levels', ['item_id', 'location_id'], unique=True)
    op.create_index('idx_stock_location_updated', 'stock_levels', ['location_id', 'last_updated'], unique=False)

    # Create transactions table
    op.create_table('transactions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('item_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('location_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('transaction_type', sa.Enum('sale', 'adjustment', 'receive', 'waste', 'transfer', 'count', name='transactiontype'), nullable=False),
        sa.Column('quantity', sa.Float(), nullable=False),
        sa.Column('unit_cost', sa.DECIMAL(precision=10, scale=2), nullable=True),
        sa.Column('total_cost', sa.DECIMAL(precision=10, scale=2), nullable=True),
        sa.Column('pos_transaction_id', sa.String(length=100), nullable=True),
        sa.Column('reference_number', sa.String(length=100), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['item_id'], ['inventory_items.id'], ),
        sa.ForeignKeyConstraint(['location_id'], ['locations.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_transactions_id'), 'transactions', ['id'], unique=False)
    op.create_index(op.f('ix_transactions_item_id'), 'transactions', ['item_id'], unique=False)
    op.create_index(op.f('ix_transactions_location_id'), 'transactions', ['location_id'], unique=False)
    op.create_index(op.f('ix_transactions_user_id'), 'transactions', ['user_id'], unique=False)
    op.create_index(op.f('ix_transactions_transaction_type'), 'transactions', ['transaction_type'], unique=False)
    op.create_index(op.f('ix_transactions_pos_transaction_id'), 'transactions', ['pos_transaction_id'], unique=False)
    op.create_index(op.f('ix_transactions_timestamp'), 'transactions', ['timestamp'], unique=False)
    op.create_index('idx_transaction_item_date', 'transactions', ['item_id', 'timestamp'], unique=False)
    op.create_index('idx_transaction_location_date', 'transactions', ['location_id', 'timestamp'], unique=False)
    op.create_index('idx_transaction_type_date', 'transactions', ['transaction_type', 'timestamp'], unique=False)
    op.create_index('idx_transaction_user_date', 'transactions', ['user_id', 'timestamp'], unique=False)


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('transactions')
    op.drop_table('stock_levels')
    op.drop_table('inventory_items')
    op.drop_table('suppliers')
    op.drop_table('locations')
    op.drop_table('users')
    
    # Drop enums
    op.execute('DROP TYPE IF EXISTS transactiontype')
    op.execute('DROP TYPE IF EXISTS unitofmeasure')
    op.execute('DROP TYPE IF EXISTS itemcategory')
    op.execute('DROP TYPE IF EXISTS locationtype')
    op.execute('DROP TYPE IF EXISTS userrole')