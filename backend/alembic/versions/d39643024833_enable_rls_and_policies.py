"""enable rls and policies

Revision ID: d39643024833
Revises: fbf18ae585e2
Create Date: 2025-07-22 15:26:33.926156

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd39643024833'
down_revision: Union[str, Sequence[str], None] = 'fbf18ae585e2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    # enable rls for all tables 
    ##USERS TABLE RLS
    op.execute("ALTER TABLE users ENABLE ROW LEVEL SECURITY")
    op.execute("""
        CREATE POLICY allow_login ON users
        FOR SELECT
        USING (current_setting('app.current_tenant_id', true) IS NULL)
    """)
    op.execute("""
        CREATE POLICY tenant_policy ON users
        FOR SELECT 
        USING (tenant_id = current_setting('app.current_tenant_id')::int)
    """)
    
    ##DRIVERS TABLE RLS
    op.execute("ALTER TABLE drivers ENABLE ROW LEVEL SECURITY")
    op.execute("""
        CREATE POLICY allow_login ON drivers
        FOR SELECT
        USING (current_setting('app.current_tenant_id', true) IS NULL)
    """)
    op.execute ("""
        CREATE POLICY tenant_policy ON drivers
        FOR ALL
        USING (tenant_id = current_setting('app.current_tenant_id')::int)
        WITH CHECK(tenant_id = current_setting('app.current_tenant_id')::int)
    """)

    ##TENANTS TABLE RLS 
    op.execute("ALTER TABLE tenants ENABLE ROW LEVEL SECURITY")
    op.execute("""
        CREATE POLICY allow_login ON tenants
        FOR SELECT
        USING (current_setting('app.current_tenant_id', true) IS NULL)
    """)
    op.execute ("""
        CREATE POLICY tenant_policy ON tenants
        FOR ALL
        USING (id = current_setting('app.current_tenant_id')::int)
        WITH CHECK(id = current_setting('app.current_tenant_id')::int)
    """)
    ##BOOKINKGS RLS
    op.execute("ALTER TABLE bookings ENABLE ROW LEVEL SECURITY")
    op.execute("""
        CREATE POLICY tenant_policy ON bookings
        FOR ALL
        USING (tenant_id = current_setting('app.current_tenant_id')::int)
        WITH CHECK(tenant_id = current_setting('app.current_tenant_id')::int)
    """)
 

    
    ##VEHICLES RLS
    op.execute("ALTER TABLE vehicles ENABLE ROW LEVEL SECURITY")
    op.execute("""
        CREATE POLICY tenant_policy ON vehicles
        FOR ALL
        USING (tenant_id = current_setting('app.current_tenant_id')::int)
        WITH CHECK(tenant_id = current_setting('app.current_tenant_id')::int)
    """)

    ##VEHICLE_CONFIG RLS
    op.execute("ALTER TABLE vehicle_config ENABLE ROW LEVEL SECURITY")
    op.execute("""
        CREATE POLICY tenant_policy ON vehicle_config
        FOR ALL
        USING (tenant_id = current_setting('app.current_tenant_id')::int)
        WITH CHECK(tenant_id = current_setting('app.current_tenant_id')::int)
    """)

    ##TENANTS_SETTINGS RLS
    op.execute("ALTER TABLE tenants_settings ENABLE ROW LEVEL SECURITY")
    op.execute("""
        CREATE POLICY tenant_policy ON tenants_settings
        FOR ALL
        USING (tenant_id = current_setting('app.current_tenant_id')::int)
        WITH CHECK(tenant_id = current_setting('app.current_tenant_id')::int)
    """)



def downgrade() -> None:
    """Downgrade schema."""
    pass
