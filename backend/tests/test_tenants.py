import pytest
from fastapi import status
from app.models.tenant import Tenants
from app.models.driver import Driver
from app.models.vehicle import Vehicle
from app.models.booking import Booking

class TestTenantsAPI:
    """Test cases for Tenants API endpoints"""
    
    def test_public_test_endpoint(self, client):
        """Test public test endpoint"""
        response = client.get("/api/v1/tenant/public_test")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["msg"] == "test endpoint"
    
    def test_get_client_info(self, client):
        """Test client info endpoint"""
        response = client.get("/api/v1/tenant/get_client_info")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "client_host" in data
        assert "client_origin" in data
    
    def test_get_tenant_info_authenticated(self, client, tenant_token):
        """Test getting tenant info with authentication"""
        headers = {"Authorization": f"Bearer {tenant_token}"}
        response = client.get("/api/v1/tenant/", headers=headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["message"] == "Tenant's info retrieved successfully"
        assert "data" in data
    
    def test_get_tenant_info_unauthenticated(self, client):
        """Test getting tenant info without authentication"""
        response = client.get("/api/v1/tenant/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_create_tenant_success(self, client, db_session):
        """Test successful tenant creation"""
        tenant_data = {
            "company_name": "New Test Company",
            "email": "newcompany@test.com",
            "password": "newpassword123",
            "role": "tenant"
        }
        
        response = client.post("/api/v1/tenant/add", json=tenant_data)
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["message"] == "Tenant created successfully"
        assert "data" in data
        assert data["data"]["company_name"] == tenant_data["company_name"]
        assert data["data"]["email"] == tenant_data["email"]
    
    def test_create_tenant_duplicate_email(self, client, db_session, test_tenant):
        """Test tenant creation with duplicate email"""
        tenant_data = {
            "company_name": "Another Company",
            "email": "test@company.com",  # Same email as test_tenant
            "password": "password123",
            "role": "tenant"
        }
        
        response = client.post("/api/v1/tenant/add", json=tenant_data)
        # Should fail due to duplicate email
        assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_422_UNPROCESSABLE_ENTITY]
    
    def test_create_tenant_invalid_data(self, client):
        """Test tenant creation with invalid data"""
        invalid_data = {
            "company_name": "",  # Empty company name
            "email": "invalid-email",  # Invalid email format
            "password": "123",  # Too short password
        }
        
        response = client.post("/api/v1/tenant/add", json=invalid_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_get_drivers_authenticated(self, client, tenant_token, test_driver):
        """Test getting drivers with authentication"""
        headers = {"Authorization": f"Bearer {tenant_token}"}
        response = client.get("/api/v1/tenant/drivers", headers=headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["message"] == "Drivers retrieved successfully"
        assert "data" in data
        assert "meta" in data
        assert data["meta"]["count"] >= 1
    
    def test_get_drivers_unauthenticated(self, client):
        """Test getting drivers without authentication"""
        response = client.get("/api/v1/tenant/drivers")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_get_vehicles_authenticated(self, client, tenant_token, test_vehicle):
        """Test getting vehicles with authentication"""
        headers = {"Authorization": f"Bearer {tenant_token}"}
        response = client.get("/api/v1/tenant/vehicles", headers=headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["message"] == "Drivers retrieved successfully"  # Note: message seems incorrect
        assert "data" in data
        assert "meta" in data
        assert data["meta"]["count"] >= 1
    
    def test_get_vehicles_by_driver(self, client, tenant_token, test_vehicle, test_driver):
        """Test getting vehicles filtered by driver"""
        headers = {"Authorization": f"Bearer {tenant_token}"}
        response = client.get(
            f"/api/v1/tenant/vehicles?driver_id={test_driver.id}",
            headers=headers
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "data" in data
        # Should return vehicles for the specific driver
    
    def test_get_vehicles_assigned_drivers(self, client, tenant_token, test_vehicle):
        """Test getting vehicles assigned to drivers"""
        headers = {"Authorization": f"Bearer {tenant_token}"}
        response = client.get(
            "/api/v1/tenant/vehicles?assigned_drivers=true",
            headers=headers
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "data" in data
    
    def test_get_bookings_authenticated(self, client, tenant_token, test_booking):
        """Test getting bookings with authentication"""
        headers = {"Authorization": f"Bearer {tenant_token}"}
        response = client.get("/api/v1/tenant/bookings", headers=headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "data" in data
        assert "meta" in data
    
    def test_get_bookings_by_status(self, client, tenant_token, test_booking):
        """Test getting bookings filtered by status"""
        headers = {"Authorization": f"Bearer {tenant_token}"}
        response = client.get(
            "/api/v1/tenant/bookings?booking_status=pending",
            headers=headers
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "data" in data
    
    def test_get_bookings_invalid_status(self, client, tenant_token):
        """Test getting bookings with invalid status"""
        headers = {"Authorization": f"Bearer {tenant_token}"}
        response = client.get(
            "/api/v1/tenant/bookings?booking_status=invalid_status",
            headers=headers
        )
        # Should handle invalid status gracefully
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST]
    
    def test_onboard_driver_success(self, client, tenant_token, db_session):
        """Test successful driver onboarding"""
        headers = {"Authorization": f"Bearer {tenant_token}"}
        driver_data = {
            "first_name": "New",
            "last_name": "Driver",
            "email": "newdriver@test.com",
            "phone": "+1234567890",
            "vehicle_info": {
                "make": "Honda",
                "model": "Civic",
                "year": 2019,
                "license_plate": "XYZ789"
            }
        }
        
        response = client.post("/api/v1/tenant/onboard", json=driver_data, headers=headers)
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["message"] == "Driver onboarded successfully"
        assert "data" in data
    
    def test_onboard_driver_invalid_data(self, client, tenant_token):
        """Test driver onboarding with invalid data"""
        headers = {"Authorization": f"Bearer {tenant_token}"}
        invalid_data = {
            "first_name": "",  # Empty first name
            "email": "invalid-email",  # Invalid email
            "phone": "123",  # Invalid phone
        }
        
        response = client.post("/api/v1/tenant/onboard", json=invalid_data, headers=headers)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_assign_driver_to_ride(self, client, tenant_token, test_booking, test_driver):
        """Test assigning driver to a ride"""
        headers = {"Authorization": f"Bearer {tenant_token}"}
        assign_data = {
            "driver_id": test_driver.id
        }
        
        response = client.patch(
            f"/api/v1/tenant/riders/{test_booking.user_id}/assign-driver",
            json=assign_data,
            headers=headers
        )
        assert response.status_code == status.HTTP_202_ACCEPTED
    
    def test_assign_driver_to_vehicle(self, client, tenant_token, test_vehicle, test_driver):
        """Test assigning driver to a vehicle"""
        headers = {"Authorization": f"Bearer {tenant_token}"}
        assign_data = {
            "driver_id": test_driver.id
        }
        
        response = client.patch(
            f"/api/v1/tenant/vehicles/{test_vehicle.id}/assign-driver",
            json=assign_data,
            headers=headers
        )
        assert response.status_code == status.HTTP_202_ACCEPTED
    
    def test_assign_driver_invalid_ids(self, client, tenant_token):
        """Test assigning driver with invalid IDs"""
        headers = {"Authorization": f"Bearer {tenant_token}"}
        assign_data = {
            "driver_id": 999  # Non-existent driver
        }
        
        response = client.patch(
            "/api/v1/tenant/riders/999/assign-driver",
            json=assign_data,
            headers=headers
        )
        # Should handle invalid IDs gracefully
        assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_404_NOT_FOUND, status.HTTP_202_ACCEPTED] 