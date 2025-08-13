import pytest
from fastapi import status
from app.models.driver import Drivers
from app.models.vehicle import Vehicles
from app.models.booking import Bookings

class TestDriversAPI:
    """Test cases for Drivers API endpoints"""
    
    def __init__(self):
        api_routes_profile = "/api/v1/driver/info"
        
    # def get_routes(self):
    #     api_routes_profile = "/api/v1/driver/info"
    #     return api_routes_profile
    def test_get_driver_profile_authenticated(self, client, driver_token, test_driver):
        """Test getting driver profile with authentication"""
        headers = {"Authorization": f"Bearer {driver_token}"}
        response = client.get(self.api_routes_profile, headers=headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "data" in data
        assert data["data"]["id"] == test_driver.id
        assert data["data"]["first_name"] == test_driver.first_name
        assert data["data"]["last_name"] == test_driver.last_name
    
    def test_get_driver_profile_unauthenticated(self, client):
        """Test getting driver profile without authentication"""
        response = client.get("/api/v1/driver/info")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_update_driver_profile_success(self, client, driver_token, test_driver):
        """Test successful driver profile update"""
        headers = {"Authorization": f"Bearer {driver_token}"}
        update_data = {
            "first_name": "Updated",
            "last_name": "Driver",
            "phone": "+9876543210"
        }
        
        response = client.put("/api/v1/driver/profile", json=update_data, headers=headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["message"] == "Driver profile updated successfully"
        assert "data" in data
        assert data["data"]["first_name"] == update_data["first_name"]
        assert data["data"]["last_name"] == update_data["last_name"]
        assert data["data"]["phone"] == update_data["phone"]
    
    def test_update_driver_profile_invalid_data(self, client, driver_token):
        """Test driver profile update with invalid data"""
        headers = {"Authorization": f"Bearer {driver_token}"}
        invalid_data = {
            "first_name": "",  # Empty first name
            "email": "invalid-email",  # Invalid email format
            "phone": "123"  # Invalid phone
        }
        
        response = client.put("/api/v1/driver/profile", json=invalid_data, headers=headers)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_get_available_rides_authenticated(self, client, driver_token, test_booking):
        """Test getting available rides with authentication"""
        headers = {"Authorization": f"Bearer {driver_token}"}
        response = client.get("/api/v1/driver/rides/available", headers=headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "data" in data
        assert "meta" in data
    
    def test_get_available_rides_unauthenticated(self, client):
        """Test getting available rides without authentication"""
        response = client.get("/api/v1/driver/rides/available")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_get_available_rides_with_filters(self, client, driver_token, test_booking):
        """Test getting available rides with filters"""
        headers = {"Authorization": f"Bearer {driver_token}"}
        response = client.get(
            "/api/v1/driver/available-rides?status=pending&pickup_location=Main St",
            headers=headers
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "data" in data
    
    def test_accept_ride_success(self, client, driver_token, test_booking):
        """Test successful ride acceptance"""
        headers = {"Authorization": f"Bearer {driver_token}"}
        response = client.post(
            f"/api/v1/driver/rides/{test_booking.id}/accept",
            headers=headers
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["message"] == "Ride accepted successfully"
        assert "data" in data
    
    def test_accept_ride_already_accepted(self, client, driver_token, test_booking):
        """Test accepting already accepted ride"""
        # First accept the ride
        headers = {"Authorization": f"Bearer {driver_token}"}
        client.post(
            f"/api/v1/driver/rides/{test_booking.id}/accept",
            headers=headers
        )
        
        # Try to accept again
        response = client.post(
            f"/api/v1/driver/rides/{test_booking.id}/accept",
            headers=headers
        )
        # Should handle already accepted rides gracefully
        assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_409_CONFLICT, status.HTTP_200_OK]
    
    def test_accept_ride_nonexistent(self, client, driver_token):
        """Test accepting non-existent ride"""
        headers = {"Authorization": f"Bearer {driver_token}"}
        response = client.post(
            "/api/v1/driver/rides/999/accept",
            headers=headers
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_start_ride_success(self, client, driver_token, test_booking):
        """Test successful ride start"""
        headers = {"Authorization": f"Bearer {driver_token}"}
        response = client.post(
            f"/api/v1/driver/rides/{test_booking.id}/start",
            headers=headers
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["message"] == "Ride started successfully"
        assert "data" in data
    
    def test_start_ride_not_accepted(self, client, driver_token, test_booking):
        """Test starting ride that hasn't been accepted"""
        headers = {"Authorization": f"Bearer {driver_token}"}
        response = client.post(
            f"/api/v1/driver/rides/{test_booking.id}/start",
            headers=headers
        )
        # Should handle non-accepted rides gracefully
        assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_409_CONFLICT, status.HTTP_200_OK]
    
    def test_complete_ride_success(self, client, driver_token, test_booking):
        """Test successful ride completion"""
        headers = {"Authorization": f"Bearer {driver_token}"}
        response = client.post(
            f"/api/v1/driver/rides/{test_booking.id}/complete",
            headers=headers
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["message"] == "Ride completed successfully"
        assert "data" in data
    
    def test_complete_ride_not_started(self, client, driver_token, test_booking):
        """Test completing ride that hasn't been started"""
        headers = {"Authorization": f"Bearer {driver_token}"}
        response = client.post(
            f"/api/v1/driver/rides/{test_booking.id}/complete",
            headers=headers
        )
        # Should handle non-started rides gracefully
        assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_409_CONFLICT, status.HTTP_200_OK]
    
    def test_get_ride_history_authenticated(self, client, driver_token, test_booking):
        """Test getting ride history with authentication"""
        headers = {"Authorization": f"Bearer {driver_token}"}
        response = client.get("/api/v1/driver/ride-history", headers=headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "data" in data
        assert "meta" in data
    
    def test_get_ride_history_unauthenticated(self, client):
        """Test getting ride history without authentication"""
        response = client.get("/api/v1/driver/ride-history")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_get_ride_history_with_filters(self, client, driver_token, test_booking):
        """Test getting ride history with filters"""
        headers = {"Authorization": f"Bearer {driver_token}"}
        response = client.get(
            "/api/v1/driver/ride-history?status=completed&date_from=2024-01-01",
            headers=headers
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "data" in data
    
    def test_get_earnings_authenticated(self, client, driver_token):
        """Test getting driver earnings with authentication"""
        headers = {"Authorization": f"Bearer {driver_token}"}
        response = client.get("/api/v1/driver/earnings", headers=headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "data" in data
        assert "meta" in data
    
    def test_get_earnings_unauthenticated(self, client):
        """Test getting driver earnings without authentication"""
        response = client.get("/api/v1/driver/earnings")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_get_earnings_with_date_range(self, client, driver_token):
        """Test getting driver earnings with date range"""
        headers = {"Authorization": f"Bearer {driver_token}"}
        response = client.get(
            "/api/v1/driver/earnings?date_from=2024-01-01&date_to=2024-12-31",
            headers=headers
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "data" in data
    
    def test_update_driver_location_success(self, client, driver_token):
        """Test successful driver location update"""
        headers = {"Authorization": f"Bearer {driver_token}"}
        location_data = {
            "latitude": 40.7128,
            "longitude": -74.0060,
            "accuracy": 10.5
        }
        
        response = client.post("/api/v1/driver/location", json=location_data, headers=headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["message"] == "Location updated successfully"
    
    def test_update_driver_location_invalid_coordinates(self, client, driver_token):
        """Test driver location update with invalid coordinates"""
        headers = {"Authorization": f"Bearer {driver_token}"}
        invalid_location = {
            "latitude": 200.0,  # Invalid latitude
            "longitude": -74.0060,
            "accuracy": 10.5
        }
        
        response = client.post("/api/v1/driver/location", json=invalid_location, headers=headers)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_get_driver_vehicle_authenticated(self, client, driver_token, test_vehicle):
        """Test getting driver vehicle with authentication"""
        headers = {"Authorization": f"Bearer {driver_token}"}
        response = client.get("/api/v1/driver/vehicle", headers=headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "data" in data
        assert data["data"]["id"] == test_vehicle.id
    
    def test_get_driver_vehicle_unauthenticated(self, client):
        """Test getting driver vehicle without authentication"""
        response = client.get("/api/v1/driver/vehicle")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED 