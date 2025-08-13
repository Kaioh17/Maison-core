##Enable RLS(row level security)

ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE tenants ENABLE ROW LEVEL SECURITY;
ALTER TABLE drivers ENABLE ROW LEVEL SECURITY;

##Create policy to permit login using select only if tenant_id is not provided
CREATE POLICY allow_login
ON users
