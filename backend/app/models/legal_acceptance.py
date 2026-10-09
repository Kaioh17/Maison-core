from app.models.base import Base
from sqlalchemy import Column, Integer, String, TIMESTAMP, ForeignKey, UniqueConstraint
from sqlalchemy.sql.expression import text


class LegalAcceptance(Base):
    """Append-only consent log: one row per operator per legal document version."""
    __tablename__ = "legal_acceptances"

    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    version = Column(String(40), nullable=False)
    source = Column(String(20), nullable=False)  # 'login' | 'signup' | 'gate'
    ip_address = Column(String(64), nullable=True)
    user_agent = Column(String(400), nullable=True)
    accepted_on = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))

    __table_args__ = (UniqueConstraint('tenant_id', 'version', name='uq_legal_tenant_version'),)
