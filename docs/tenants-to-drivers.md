### Documentation 


##  Logic Flow: Tenant & Driver Onboarding and Registration

### 1. Tenant Creation & Onboarding

**Endpoint:**  
`POST /tenant/add`

**Flow:**
- **Input:** Tenant registration data (company name, email, phone, slug, password, etc.).
- **Process:**
  1. **Uniqueness Checks:**  
     `_check_unique_fields` ensures email, company name, phone, and slug are unique in the database.
  2. **Password Hashing:**  
     The password is securely hashed before storing.
  3. **Tenant Creation:**  
     A new tenant row is created and committed to the database.
  4. **Tenant Settings:**  
     `_set_up_tenant_settings` creates a settings row for the new tenant (logo, slug, etc.).
- **Output:**  
  Returns the created tenant’s information.

---

### 2. Tenant Info Retrieval

**Endpoint:**  
`GET /tenant/`

**Flow:**
- **Input:** Authenticated tenant user.
- **Process:**  
  - Fetches the tenant’s company info by ID.
  - Returns 404 if not found.
- **Output:**  
  Tenant’s company information.

---

### 3. Onboarding a Driver (by Tenant)

**Endpoint:**  
`POST /tenant/onboard`

**Flow:**
- **Input:** Driver onboarding data (name, email, phone, license, etc.).
- **Process:**
  1. **Email Uniqueness:**  
     `_confirm_driver_email_absence` ensures no duplicate driver email for the tenant.
  2. **Onboarding Token:**  
     `_onboarding_token` generates a unique token for the driver.
  3. **Driver Creation:**  
     A new driver row is created with status `is_registered="pending"` and the onboarding token.
- **Output:**  
  Returns the new driver’s onboarding info.

---

### 4. Driver Registration (Self-Service)

**Endpoint:**  
`PATCH /driver/register`

**Flow:**
- **Input:** Driver registration data (token, personal info, password, vehicle info if outsourced).
- **Process:**
  1. **Token & Identity Validation:**  
     `_table_checks_` verifies the token, name, and email match the pending driver row.
  2. **License Uniqueness:**  
     Checks for duplicate license number within the tenant.
  3. **Password Hashing:**  
     Hashes the driver’s password.
  4. **Vehicle Handling (Outsourced Only):**  
     - If the driver is outsourced and provides vehicle data:
       - `_vehicle_exists` checks for duplicate license plate.
       - A new vehicle is created and linked to the driver.
       - `allocate_vehicle_category` assigns vehicle category/config.
       - The driver’s `vehicle_id` is set.
  5. **Driver Update:**  
     - Updates driver info, sets status to `registered`, and commits changes.
- **Output:**  
  Returns the updated driver record, including vehicle info if applicable.

---

### 5. Get All Drivers for a Tenant

**Endpoint:**  
`GET /tenant/drivers`

**Flow:**
- **Input:** Authenticated tenant user.
- **Process:**  
  - Queries all drivers for the tenant.
  - Returns 404 if none found.
- **Output:**  
  List of drivers for the tenant.

---

### 6. Error Handling

- All database operations are wrapped in try/except blocks.
- Common DB errors are handled by a custom handler (`db_exceptions.handle`).
- HTTPExceptions are raised for all validation and uniqueness failures.

---

### 7. Relationships & Data Integrity

- **Tenants** have many **Drivers**.
- **Drivers** may have a linked **Vehicle** (especially for outsourced drivers).
- **Vehicle** uniqueness is enforced by license plate and tenant.
- **Driver** uniqueness is enforced by email, license number, and tenant.

---

### 8. Security

- Passwords are always hashed before storage.
- JWT/OAuth2 authentication is used for protected endpoints.
- Role-based access is enforced via dependencies.

---

### 9. Logging

- Key actions (creation, onboarding, registration, errors) are logged for traceability.

---

**Summary:**  
This flow ensures secure, multi-tenant onboarding and management of drivers and vehicles, with robust validation, error handling, and clear separation of responsibilities between tenants and drivers.
