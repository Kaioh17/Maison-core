-- =========================
-- TENANT 1: JANE
-- =========================
BEGIN;

INSERT INTO tenants (
  email, first_name, last_name, password, phone_no, role, is_verified, is_active
)
VALUES (
  'jane@janeskylinechauffeur.com',
  'Jane',
  'Carter',
  '$2b$12$n7itZTycfMEzZyl8BS3R4OBf1HD5GTcMNdyc/G4608judfNWOZ.YS',
  '+13125550101',
  'tenant',
  TRUE,
  TRUE
)
ON CONFLICT (email) DO UPDATE
SET first_name = EXCLUDED.first_name,
    last_name  = EXCLUDED.last_name,
    password   = EXCLUDED.password,
    phone_no   = EXCLUDED.phone_no,
    role       = 'tenant',
    is_active  = TRUE;

INSERT INTO tenants_profile (
  tenant_id, company_name, slug, address, city,
  stripe_customer_id, stripe_account_id, charges_enabled,
  subscription_status, subscription_plan, cur_subscription_id
)
SELECT
  t.id,
  'Jane Skyline Chauffeur LLC',
  'jane-skyline-chauffeur',
  '110 N Wacker Dr, Chicago, IL',
  'Chicago',
  'cus_UGZMTs0OKIxjH7',
  'acct_1TI2E0JbCxEmn3TV',
  FALSE,
  'active',
  'starter',
  'sub_1TI2EhQtWPwjkVcEwD2191tv'
FROM tenants t
WHERE t.email = 'jane@janeskylinechauffeur.com'
ON CONFLICT (tenant_id) DO UPDATE
SET company_name        = EXCLUDED.company_name,
    slug                = EXCLUDED.slug,
    address             = EXCLUDED.address,
    city                = EXCLUDED.city,
    stripe_customer_id  = EXCLUDED.stripe_customer_id,
    stripe_account_id   = EXCLUDED.stripe_account_id,
    subscription_status = EXCLUDED.subscription_status,
    subscription_plan   = EXCLUDED.subscription_plan,
    cur_subscription_id = EXCLUDED.cur_subscription_id;

INSERT INTO tenants_stats (tenant_id, drivers_count, daily_ride_count, total_ride_count)
SELECT t.id, 1, 0, 0
FROM tenants t
WHERE t.email = 'jane@janeskylinechauffeur.com'
ON CONFLICT (tenant_id) DO UPDATE
SET drivers_count = EXCLUDED.drivers_count;

INSERT INTO tenants_settings (tenant_id, rider_tiers_enabled, config)
SELECT
  t.id,
  FALSE,
  '{
    "booking": {
      "allow_guest_bookings": true,
      "show_vehicle_images": false,
      "allowed_payment_method": {
        "cash": {"is_allowed": true},
        "zelle": {"is_allowed": true},
        "stripe": {"is_allowed": true}
      },
      "types": {
        "airport": {"is_deposit_required": false},
        "dropoff": {"is_deposit_required": false},
        "hourly": {"is_deposit_required": false}
      }
    },
    "branding": {"button_radius": 8, "font_family": "DM Sans"},
    "features": {"vip_profiles": true, "show_loyalty_banner": false}
  }'::jsonb
FROM tenants t
WHERE t.email = 'jane@janeskylinechauffeur.com'
ON CONFLICT (tenant_id) DO UPDATE
SET rider_tiers_enabled = EXCLUDED.rider_tiers_enabled,
    config              = EXCLUDED.config;

INSERT INTO tenant_branding (
  tenant_id, theme, primary_color, secondary_color, accent_color,
  background_color, surface_color, text_color, text_muted_color,
  button_text_color, slug, enable_branding
)
SELECT
  t.id, 'dark', '#7c3aed', '#a78bfa', '#6d28d9',
  '#0a0a12', '#13131f', '#ffffff', '#6b7280',
  '#ffffff', 'jane-skyline-chauffeur', FALSE
FROM tenants t
WHERE t.email = 'jane@janeskylinechauffeur.com'
ON CONFLICT (tenant_id) DO UPDATE
SET theme             = EXCLUDED.theme,
    primary_color     = EXCLUDED.primary_color,
    secondary_color   = EXCLUDED.secondary_color,
    accent_color      = EXCLUDED.accent_color,
    background_color  = EXCLUDED.background_color,
    surface_color     = EXCLUDED.surface_color,
    text_color        = EXCLUDED.text_color,
    text_muted_color  = EXCLUDED.text_muted_color,
    button_text_color = EXCLUDED.button_text_color,
    slug              = EXCLUDED.slug,
    enable_branding   = EXCLUDED.enable_branding;

INSERT INTO tenant_pricing (
  tenant_id, base_fare, per_mile_rate, per_minute_rate, per_hour_rate, cancellation_fee, discounts
)
SELECT t.id, 25.0, 5.0, 3.0, 70.0, 0.0, FALSE
FROM tenants t
WHERE t.email = 'jane@janeskylinechauffeur.com'
ON CONFLICT (tenant_id) DO UPDATE
SET base_fare        = EXCLUDED.base_fare,
    per_mile_rate    = EXCLUDED.per_mile_rate,
    per_minute_rate  = EXCLUDED.per_minute_rate,
    per_hour_rate    = EXCLUDED.per_hour_rate,
    cancellation_fee = EXCLUDED.cancellation_fee,
    discounts        = EXCLUDED.discounts;

INSERT INTO tenant_booking_price (
  tenant_id, service_type, stc_rate, gratuity_rate, airport_gate_fee, meet_and_greet_fee, deposit_type, deposit_fee
)
SELECT t.id, 'airport', 0.10, 0.10, 0.0, 0.0, 'percentage', 0.30
FROM tenants t
WHERE t.email = 'jane@janeskylinechauffeur.com'
ON CONFLICT (service_type, tenant_id) DO UPDATE
SET stc_rate           = EXCLUDED.stc_rate,
    gratuity_rate      = EXCLUDED.gratuity_rate,
    airport_gate_fee   = EXCLUDED.airport_gate_fee,
    meet_and_greet_fee = EXCLUDED.meet_and_greet_fee,
    deposit_type       = EXCLUDED.deposit_type,
    deposit_fee        = EXCLUDED.deposit_fee;

INSERT INTO tenant_booking_price (tenant_id, service_type, deposit_type, deposit_fee)
SELECT t.id, 'dropoff', 'percentage', 0.30
FROM tenants t
WHERE t.email = 'jane@janeskylinechauffeur.com'
ON CONFLICT (service_type, tenant_id) DO UPDATE
SET deposit_type = EXCLUDED.deposit_type,
    deposit_fee  = EXCLUDED.deposit_fee;

INSERT INTO tenant_booking_price (tenant_id, service_type, deposit_type, deposit_fee)
SELECT t.id, 'hourly', 'percentage', 0.30
FROM tenants t
WHERE t.email = 'jane@janeskylinechauffeur.com'
ON CONFLICT (service_type, tenant_id) DO UPDATE
SET deposit_type = EXCLUDED.deposit_type,
    deposit_fee  = EXCLUDED.deposit_fee;

INSERT INTO vehicle_category_rate (tenant_id, vehicle_category, vehicle_flat_rate)
SELECT t.id, v.vehicle_category, 0.0
FROM tenants t
CROSS JOIN (VALUES ('Luxury Sedan'), ('Executive SUV'), ('Stretch Limo'), ('Business Van')) AS v(vehicle_category)
WHERE t.email = 'jane@janeskylinechauffeur.com'
  AND NOT EXISTS (
    SELECT 1
    FROM vehicle_category_rate r
    WHERE r.tenant_id = t.id
      AND r.vehicle_category = v.vehicle_category
  );

COMMIT;




-- =========================
-- TENANT 2: ELVIS
-- =========================
BEGIN;

INSERT INTO tenants (email, first_name, last_name, password, phone_no, role, is_verified, is_active)
VALUES (
  'elvis@elvisexecutivecars.com', 'Elvis', 'Monroe',
  '$2b$12$n7itZTycfMEzZyl8BS3R4OBf1HD5GTcMNdyc/G4608judfNWOZ.YS',
  '+13125550102', 'tenant', TRUE, TRUE
)
ON CONFLICT (email) DO UPDATE
SET first_name = EXCLUDED.first_name, last_name = EXCLUDED.last_name, password = EXCLUDED.password, phone_no = EXCLUDED.phone_no, role = 'tenant', is_active = TRUE;

INSERT INTO tenants_profile (
  tenant_id, company_name, slug, address, city, stripe_customer_id, stripe_account_id, charges_enabled, subscription_status, subscription_plan, cur_subscription_id
)
SELECT
  t.id, 'Elvis Executive Cars', 'elvis-executive-cars', '233 S Wacker Dr, Chicago, IL', 'Chicago',
  'cus_UGZFVua6WniSfF', 'acct_1TI1tlQwGWJ2Wn2C', FALSE, 'active', 'starter', 'sub_1TI27jQtWPwjkVcEyEHnayHF'
FROM tenants t WHERE t.email = 'elvis@elvisexecutivecars.com'
ON CONFLICT (tenant_id) DO UPDATE
SET company_name = EXCLUDED.company_name, slug = EXCLUDED.slug, address = EXCLUDED.address, city = EXCLUDED.city,
    stripe_customer_id = EXCLUDED.stripe_customer_id, stripe_account_id = EXCLUDED.stripe_account_id,
    subscription_status = EXCLUDED.subscription_status, subscription_plan = EXCLUDED.subscription_plan,
    cur_subscription_id = EXCLUDED.cur_subscription_id;

INSERT INTO tenants_stats (tenant_id, drivers_count, daily_ride_count, total_ride_count)
SELECT t.id, 1, 0, 0 FROM tenants t WHERE t.email = 'elvis@elvisexecutivecars.com'
ON CONFLICT (tenant_id) DO UPDATE SET drivers_count = EXCLUDED.drivers_count;

INSERT INTO tenants_settings (tenant_id, rider_tiers_enabled, config)
SELECT
  t.id, FALSE,
  '{
    "booking":{"allow_guest_bookings":true,"show_vehicle_images":false,
      "allowed_payment_method":{"cash":{"is_allowed":true},"zelle":{"is_allowed":true},"stripe":{"is_allowed":true}},
      "types":{"airport":{"is_deposit_required":false},"dropoff":{"is_deposit_required":false},"hourly":{"is_deposit_required":false}}
    },
    "branding":{"button_radius":8,"font_family":"DM Sans"},
    "features":{"vip_profiles":true,"show_loyalty_banner":false}
  }'::jsonb
FROM tenants t WHERE t.email = 'elvis@elvisexecutivecars.com'
ON CONFLICT (tenant_id) DO UPDATE
SET rider_tiers_enabled = EXCLUDED.rider_tiers_enabled, config = EXCLUDED.config;

INSERT INTO tenant_branding (
  tenant_id, theme, primary_color, secondary_color, accent_color, background_color, surface_color, text_color, text_muted_color, button_text_color, slug, enable_branding
)
SELECT
  t.id, 'dark', '#7c3aed', '#a78bfa', '#6d28d9', '#0a0a12', '#13131f', '#ffffff', '#6b7280', '#ffffff', 'elvis-executive-cars', FALSE
FROM tenants t WHERE t.email = 'elvis@elvisexecutivecars.com'
ON CONFLICT (tenant_id) DO UPDATE
SET theme = EXCLUDED.theme, primary_color = EXCLUDED.primary_color, secondary_color = EXCLUDED.secondary_color,
    accent_color = EXCLUDED.accent_color, background_color = EXCLUDED.background_color, surface_color = EXCLUDED.surface_color,
    text_color = EXCLUDED.text_color, text_muted_color = EXCLUDED.text_muted_color, button_text_color = EXCLUDED.button_text_color,
    slug = EXCLUDED.slug, enable_branding = EXCLUDED.enable_branding;

INSERT INTO tenant_pricing (tenant_id, base_fare, per_mile_rate, per_minute_rate, per_hour_rate, cancellation_fee, discounts)
SELECT t.id, 25.0, 5.0, 3.0, 70.0, 0.0, FALSE
FROM tenants t WHERE t.email = 'elvis@elvisexecutivecars.com'
ON CONFLICT (tenant_id) DO UPDATE
SET base_fare = EXCLUDED.base_fare, per_mile_rate = EXCLUDED.per_mile_rate, per_minute_rate = EXCLUDED.per_minute_rate,
    per_hour_rate = EXCLUDED.per_hour_rate, cancellation_fee = EXCLUDED.cancellation_fee, discounts = EXCLUDED.discounts;

INSERT INTO tenant_booking_price (tenant_id, service_type, stc_rate, gratuity_rate, airport_gate_fee, meet_and_greet_fee, deposit_type, deposit_fee)
SELECT t.id, 'airport', 0.10, 0.10, 0.0, 0.0, 'percentage', 0.30
FROM tenants t WHERE t.email = 'elvis@elvisexecutivecars.com'
ON CONFLICT (service_type, tenant_id) DO UPDATE
SET stc_rate = EXCLUDED.stc_rate, gratuity_rate = EXCLUDED.gratuity_rate, airport_gate_fee = EXCLUDED.airport_gate_fee,
    meet_and_greet_fee = EXCLUDED.meet_and_greet_fee, deposit_type = EXCLUDED.deposit_type, deposit_fee = EXCLUDED.deposit_fee;

INSERT INTO tenant_booking_price (tenant_id, service_type, deposit_type, deposit_fee)
SELECT t.id, 'dropoff', 'percentage', 0.30 FROM tenants t WHERE t.email = 'elvis@elvisexecutivecars.com'
ON CONFLICT (service_type, tenant_id) DO UPDATE SET deposit_type = EXCLUDED.deposit_type, deposit_fee = EXCLUDED.deposit_fee;

INSERT INTO tenant_booking_price (tenant_id, service_type, deposit_type, deposit_fee)
SELECT t.id, 'hourly', 'percentage', 0.30 FROM tenants t WHERE t.email = 'elvis@elvisexecutivecars.com'
ON CONFLICT (service_type, tenant_id) DO UPDATE SET deposit_type = EXCLUDED.deposit_type, deposit_fee = EXCLUDED.deposit_fee;

INSERT INTO vehicle_category_rate (tenant_id, vehicle_category, vehicle_flat_rate)
SELECT t.id, v.vehicle_category, 0.0
FROM tenants t
CROSS JOIN (VALUES ('Luxury Sedan'), ('Executive SUV'), ('Stretch Limo'), ('Business Van')) AS v(vehicle_category)
WHERE t.email = 'elvis@elvisexecutivecars.com'
  AND NOT EXISTS (
    SELECT 1 FROM vehicle_category_rate r WHERE r.tenant_id = t.id AND r.vehicle_category = v.vehicle_category
  );

COMMIT;


-- =========================
-- TENANT 3: MARREEQ
-- =========================
BEGIN;

INSERT INTO tenants (email, first_name, last_name, password, phone_no, role, is_verified, is_active)
VALUES (
  'marreeq@marreeqpremiumtransport.com', 'Marreeq', 'Johnson',
  '$2b$12$n7itZTycfMEzZyl8BS3R4OBf1HD5GTcMNdyc/G4608judfNWOZ.YS',
  '+13125550103', 'tenant', TRUE, TRUE
)
ON CONFLICT (email) DO UPDATE
SET first_name = EXCLUDED.first_name, last_name = EXCLUDED.last_name, password = EXCLUDED.password, phone_no = EXCLUDED.phone_no, role = 'tenant', is_active = TRUE;

INSERT INTO tenants_profile (
  tenant_id, company_name, slug, address, city, stripe_customer_id, stripe_account_id, charges_enabled, subscription_status, subscription_plan, cur_subscription_id
)
SELECT
  t.id, 'Marreeq Premium Transport', 'marreeq-premium-transport', '401 N Michigan Ave, Chicago, IL', 'Chicago',
  'cus_UGZ1SzWoH9nwfF', 'acct_1TFQiUJleQPRCFJ7', FALSE, 'active', 'starter', 'sub_1TI1vyQtWPwjkVcEFhvA23Ds'
FROM tenants t WHERE t.email = 'marreeq@marreeqpremiumtransport.com'
ON CONFLICT (tenant_id) DO UPDATE
SET company_name = EXCLUDED.company_name, slug = EXCLUDED.slug, address = EXCLUDED.address, city = EXCLUDED.city,
    stripe_customer_id = EXCLUDED.stripe_customer_id, stripe_account_id = EXCLUDED.stripe_account_id,
    subscription_status = EXCLUDED.subscription_status, subscription_plan = EXCLUDED.subscription_plan,
    cur_subscription_id = EXCLUDED.cur_subscription_id;

INSERT INTO tenants_stats (tenant_id, drivers_count, daily_ride_count, total_ride_count)
SELECT t.id, 1, 0, 0 FROM tenants t WHERE t.email = 'marreeq@marreeqpremiumtransport.com'
ON CONFLICT (tenant_id) DO UPDATE SET drivers_count = EXCLUDED.drivers_count;

INSERT INTO tenants_settings (tenant_id, rider_tiers_enabled, config)
SELECT
  t.id, FALSE,
  '{
    "booking":{"allow_guest_bookings":true,"show_vehicle_images":false,
      "allowed_payment_method":{"cash":{"is_allowed":true},"zelle":{"is_allowed":true},"stripe":{"is_allowed":true}},
      "types":{"airport":{"is_deposit_required":false},"dropoff":{"is_deposit_required":false},"hourly":{"is_deposit_required":false}}
    },
    "branding":{"button_radius":8,"font_family":"DM Sans"},
    "features":{"vip_profiles":true,"show_loyalty_banner":false}
  }'::jsonb
FROM tenants t WHERE t.email = 'marreeq@marreeqpremiumtransport.com'
ON CONFLICT (tenant_id) DO UPDATE
SET rider_tiers_enabled = EXCLUDED.rider_tiers_enabled, config = EXCLUDED.config;

INSERT INTO tenant_branding (
  tenant_id, theme, primary_color, secondary_color, accent_color, background_color, surface_color, text_color, text_muted_color, button_text_color, slug, enable_branding
)
SELECT
  t.id, 'dark', '#7c3aed', '#a78bfa', '#6d28d9', '#0a0a12', '#13131f', '#ffffff', '#6b7280', '#ffffff', 'marreeq-premium-transport', FALSE
FROM tenants t WHERE t.email = 'marreeq@marreeqpremiumtransport.com'
ON CONFLICT (tenant_id) DO UPDATE
SET theme = EXCLUDED.theme, primary_color = EXCLUDED.primary_color, secondary_color = EXCLUDED.secondary_color,
    accent_color = EXCLUDED.accent_color, background_color = EXCLUDED.background_color, surface_color = EXCLUDED.surface_color,
    text_color = EXCLUDED.text_color, text_muted_color = EXCLUDED.text_muted_color, button_text_color = EXCLUDED.button_text_color,
    slug = EXCLUDED.slug, enable_branding = EXCLUDED.enable_branding;

INSERT INTO tenant_pricing (tenant_id, base_fare, per_mile_rate, per_minute_rate, per_hour_rate, cancellation_fee, discounts)
SELECT t.id, 25.0, 5.0, 3.0, 70.0, 0.0, FALSE
FROM tenants t WHERE t.email = 'marreeq@marreeqpremiumtransport.com'
ON CONFLICT (tenant_id) DO UPDATE
SET base_fare = EXCLUDED.base_fare, per_mile_rate = EXCLUDED.per_mile_rate, per_minute_rate = EXCLUDED.per_minute_rate,
    per_hour_rate = EXCLUDED.per_hour_rate, cancellation_fee = EXCLUDED.cancellation_fee, discounts = EXCLUDED.discounts;

INSERT INTO tenant_booking_price (tenant_id, service_type, stc_rate, gratuity_rate, airport_gate_fee, meet_and_greet_fee, deposit_type, deposit_fee)
SELECT t.id, 'airport', 0.10, 0.10, 0.0, 0.0, 'percentage', 0.30
FROM tenants t WHERE t.email = 'marreeq@marreeqpremiumtransport.com'
ON CONFLICT (service_type, tenant_id) DO UPDATE
SET stc_rate = EXCLUDED.stc_rate, gratuity_rate = EXCLUDED.gratuity_rate, airport_gate_fee = EXCLUDED.airport_gate_fee,
    meet_and_greet_fee = EXCLUDED.meet_and_greet_fee, deposit_type = EXCLUDED.deposit_type, deposit_fee = EXCLUDED.deposit_fee;

INSERT INTO tenant_booking_price (tenant_id, service_type, deposit_type, deposit_fee)
SELECT t.id, 'dropoff', 'percentage', 0.30 FROM tenants t WHERE t.email = 'marreeq@marreeqpremiumtransport.com'
ON CONFLICT (service_type, tenant_id) DO UPDATE SET deposit_type = EXCLUDED.deposit_type, deposit_fee = EXCLUDED.deposit_fee;

INSERT INTO tenant_booking_price (tenant_id, service_type, deposit_type, deposit_fee)
SELECT t.id, 'hourly', 'percentage', 0.30 FROM tenants t WHERE t.email = 'marreeq@marreeqpremiumtransport.com'
ON CONFLICT (service_type, tenant_id) DO UPDATE SET deposit_type = EXCLUDED.deposit_type, deposit_fee = EXCLUDED.deposit_fee;

INSERT INTO vehicle_category_rate (tenant_id, vehicle_category, vehicle_flat_rate)
SELECT t.id, v.vehicle_category, 0.0
FROM tenants t
CROSS JOIN (VALUES ('Luxury Sedan'), ('Executive SUV'), ('Stretch Limo'), ('Business Van')) AS v(vehicle_category)
WHERE t.email = 'marreeq@marreeqpremiumtransport.com'
  AND NOT EXISTS (
    SELECT 1 FROM vehicle_category_rate r WHERE r.tenant_id = t.id AND r.vehicle_category = v.vehicle_category
  );

COMMIT;

