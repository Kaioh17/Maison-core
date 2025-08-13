import pytest
from fastapi import status
from app.models.vehicle import Vehicle
from app.models.driver import Driver

class TestVehiclesAPI:
    """Test cases for Vehicles API endpoints"""
    
    def test_create_vehicle_success(self, client, tenant_token, test_tenant):
        """Test successful vehicle creation"""
        headers = {"Authorization": f"Bearer {tenant_token}"}
        vehicle_data = {
            "make": "Honda",
            "model": "Civic",
            "year": 2021,
            "license_plate": "XYZ789",
            "color": "Blue",
            "vehicle_type": "sedan",
            "capacity": 4,
            "fuel_type": "gasoline"
        }
        
        response = client.post("/api/v1/vehicles", json=vehicle_data, headers=headers)
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["message"] == "Vehicle created successfully"
        assert "data" in data
        assert data["data"]["make"] == vehicle_data["make"]
        assert data["data"]["model"] == vehicle_data["model"]
        assert data["data"]["license_plate"] == vehicle_data["license_plate"]
    
    def test_create_vehicle_invalid_data(self, client, tenant_token):
        """Test vehicle creation with invalid data"""
        headers = {"Authorization": f"Bearer {tenant_token}"}
        invalid_data = {
            "make": "",  # Empty make
            "model": "",  # Empty model
            "year": 1800,  # Invalid year
            "license_plate": "",  # Empty license plate
            "capacity": -1  # Invalid capacity
        }
        
        response = client.post("/api/v1/vehicles", json=invalid_data, headers=headers)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_create_vehicle_unauthenticated(self, client):
        """Test vehicle creation without authentication"""
        vehicle_data = {
            "make": "Toyota",
            "model": "Camry",
            "year": 2020,
            "license_plate": "ABC123"
        }
        
        response = client.post("/api/v1/vehicles", json=vehicle_data)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_create_vehicle_duplicate_license_plate(self, client, tenant_token, test_vehicle):
        """Test vehicle creation with duplicate license plate"""
        headers = {"Authorization": f"Bearer {tenant_token}"}
        duplicate_data = {
            "make": "Ford",
            "model": "Focus",
            "year": 2022,
            "license_plate": "ABC123"  # Same as test_vehicle
        }
        
        response = client.post("/api/v1/vehicles", json=duplicate_data, headers=headers)
        # Should fail due to duplicate license plate
        assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_422_UNPROCESSABLE_ENTITY]
    
    def test_get_vehicles_authenticated(self, client, tenant_token, test_vehicle):
        """Test getting vehicles with authentication"""
        headers = {"Authorization": f"Bearer {tenant_token}"}
        response = client.get("/api/v1/vehicles", headers=headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "data" in data
        assert "meta" in data
        assert len(data["data"]) >= 1
    
    def test_get_vehicles_unauthenticated(self, client):
        """Test getting vehicles without authentication"""
        response = client.get("/api/v1/vehicles")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_get_vehicles_with_filters(self, client, tenant_token, test_vehicle):
        """Test getting vehicles with filters"""
        headers = {"Authorization": f"Bearer {tenant_token}"}
        response = client.get(
            "/api/v1/vehicles?make=Toyota&vehicle_type=sedan&available=true",
            headers=headers
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "data" in data
    
    def test_get_vehicle_by_id_authenticated(self, client, tenant_token, test_vehicle):
        """Test getting specific vehicle by ID with authentication"""
        headers = {"Authorization": f"Bearer {tenant_token}"}
        response = client.get(f"/api/v1/vehicles/{test_vehicle.id}", headers=headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "data" in data
        assert data["data"]["id"] == test_vehicle.id
        assert data["data"]["make"] == test_vehicle.make
        assert data["data"]["model"] == test_vehicle.model
    
    def test_get_vehicle_by_id_unauthenticated(self, client, test_vehicle):
        """Test getting specific vehicle by ID without authentication"""
        response = client.get(f"/api/v1/vehicles/{test_vehicle.id}")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_get_vehicle_by_id_nonexistent(self, client, tenant_token):
        """Test getting non-existent vehicle by ID"""
        headers = {"Authorization": f"Bearer {tenant_token}"}
        response = client.get("/api/v1/vehicles/999", headers=headers)
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_update_vehicle_success(self, client, tenant_token, test_vehicle):
        """Test successful vehicle update"""
        headers = {"Authorization": f"Bearer {tenant_token}"}
        update_data = {
            "color": "Red",
            "capacity": 5,
            "fuel_type": "hybrid"
        }
        
        response = client.put(f"/api/v1/vehicles/{test_vehicle.id}", json=update_data, headers=headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["message"] == "Vehicle updated successfully"
        assert "data" in data
        assert data["data"]["color"] == update_data["color"]
        assert data["data"]["capacity"] == update_data["capacity"]
        assert data["data"]["fuel_type"] == update_data["fuel_type"]
    
    def test_update_vehicle_invalid_data(self, client, tenant_token, test_vehicle):
        """Test vehicle update with invalid data"""
        headers = {"Authorization": f"Bearer {tenant_token}"}
        invalid_data = {
            "year": 1800,  # Invalid year
            "capacity": 0  # Invalid capacity
        }
        
        response = client.put(f"/api/v1/vehicles/{test_vehicle.id}", json=invalid_data, headers=headers)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_update_vehicle_unauthorized(self, client, driver_token, test_vehicle):
        """Test vehicle update by unauthorized user"""
        headers = {"Authorization": f"Bearer {driver_token}"}
        update_data = {
            "color": "Unauthorized Update"
        }
        
        response = client.put(f"/api/v1/vehicles/{test_vehicle.id}", json=update_data, headers=headers)
        # Should fail due to authorization
        assert response.status_code in [status.HTTP_403_FORBIDDEN, status.HTTP_401_UNAUTHORIZED]
    
    def test_delete_vehicle_success(self, client, tenant_token, test_vehicle):
        """Test successful vehicle deletion"""
        headers = {"Authorization": f"Bearer {tenant_token}"}
        response = client.delete(f"/api/v1/vehicles/{test_vehicle.id}", headers=headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["message"] == "Vehicle deleted successfully"
    
    def test_delete_vehicle_nonexistent(self, client, tenant_token):
        """Test deleting non-existent vehicle"""
        headers = {"Authorization": f"Bearer {tenant_token}"}
        response = client.delete("/api/v1/vehicles/999", headers=headers)
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_delete_vehicle_unauthorized(self, client, driver_token, test_vehicle):
        """Test vehicle deletion by unauthorized user"""
        headers = {"Authorization": f"Bearer {driver_token}"}
        response = client.delete(f"/api/v1/vehicles/{test_vehicle.id}", headers=headers)
        # Should fail due to authorization
        assert response.status_code in [status.HTTP_403_FORBIDDEN, status.HTTP_401_UNAUTHORIZED]
    
    def test_assign_driver_to_vehicle_success(self, client, tenant_token, test_vehicle, test_driver):
        """Test successful driver assignment to vehicle"""
        headers = {"Authorization": f"Bearer {tenant_token}"}
        assign_data = {
            "driver_id": test_driver.id
        }
        
        response = client.post(
            f"/api/v1/vehicles/{test_vehicle.id}/assign-driver",
            json=assign_data,
            headers=headers
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["message"] == "Driver assigned to vehicle successfully"
    
    def test_assign_driver_to_vehicle_invalid_driver(self, client, tenant_token, test_vehicle):
        """Test driver assignment with invalid driver ID"""
        headers = {"Authorization": f"Bearer {tenant_token}"}
        assign_data = {
            "driver_id": 999  # Non-existent driver
        }
        
        response = client.post(
            f"/api/v1/vehicles/{test_vehicle.id}/assign-driver",
            json=assign_data,
            headers=headers
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_remove_driver_from_vehicle_success(self, client, tenant_token, test_vehicle):
        """Test successful driver removal from vehicle"""
        headers = {"Authorization": f"Bearer {tenant_token}"}
        response = client.delete(
            f"/api/v1/vehicles/{test_vehicle.id}/driver",
            headers=headers
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["message"] == "Driver removed from vehicle successfully"
    
    def test_get_vehicle_maintenance_history(self, client, tenant_token, test_vehicle):
        """Test getting vehicle maintenance history"""
        headers = {"Authorization": f"Bearer {tenant_token}"}
        response = client.get(f"/api/v1/vehicles/{test_vehicle.id}/maintenance", headers=headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "data" in data
        # Should contain maintenance history
    
    def test_add_vehicle_maintenance_record(self, client, tenant_token, test_vehicle):
        """Test adding vehicle maintenance record"""
        headers = {"Authorization": f"Bearer {tenant_token}"}
        maintenance_data = {
            "service_type": "oil_change",
            "description": "Regular oil change and filter replacement",
            "cost": 45.00,
            "service_date": "2024-01-15",
            "next_service_date": "2024-07-15"
        }
        
        response = client.post(
            f"/api/v1/vehicles/{test_vehicle.id}/maintenance",
            json=maintenance_data,
            headers=headers
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["message"] == "Maintenance record added successfully"
    
    def test_get_vehicle_location(self, client, tenant_token, test_vehicle):
        """Test getting vehicle current location"""
        headers = {"Authorization": f"Bearer {tenant_token}"}
        response = client.get(f"/api/v1/vehicles/{test_vehicle.id}/location", headers=headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "data" in data
        # Should contain location information
    
    def test_update_vehicle_location(self, client, tenant_token, test_vehicle):
        """Test updating vehicle location"""
        headers = {"Authorization": f"Bearer {tenant_token}"}
        location_data = {
            "latitude": 40.7128,
            "longitude": -74.0060,
            "accuracy": 10.5,
            "timestamp": "2024-01-15T10:00:00Z"
        }
        
        response = client.put(
            f"/api/v1/vehicles/{test_vehicle.id}/location",
            json=location_data,
            headers=headers
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["message"] == "Vehicle location updated successfully"
    
    def test_get_vehicle_analytics(self, client, tenant_token, test_vehicle):
        """Test getting vehicle analytics"""
        headers = {"Authorization": f"Bearer {tenant_token}"}
        response = client.get(
            f"/api/v1/vehicles/{test_vehicle.id}/analytics?period=monthly",
            headers=headers
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "data" in data
        # Should contain analytics data
    
    def test_get_vehicle_rates(self, client, tenant_token, test_vehicle):
        """Test getting vehicle rates"""
        headers = {"Authorization": f"Bearer {tenant_token}"}
        response = client.get(f"/api/v1/vehicles/{test_vehicle.id}/rates", headers=headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "data" in data
        # Should contain rate information
    
    def test_update_vehicle_rates(self, client, tenant_token, test_vehicle):
        """Test updating vehicle rates"""
        headers = {"Authorization": f"Bearer {tenant_token}"}
        rates_data = {
            "base_fare": 15.00,
            "per_km_rate": 2.50,
            "per_minute_rate": 0.50,
            "minimum_fare": 10.00
        }
        
        response = client.put(
            f"/api/v1/vehicles/{test_vehicle.id}/rates",
            json=rates_data,
            headers=headers
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["message"] == "Vehicle rates updated successfully" 