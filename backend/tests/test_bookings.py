import pytest
from fastapi import status
from app.models.booking import Bookings
from app.models.user import Users
from app.models.driver import Drivers


class TestBookingsAPI:
    """Test cases for Bookings API endpoints"""
    
    def test_create_booking_success(self, client, user_token, test_user):
        """Test successful booking creation"""
        headers = {"Authorization": f"Bearer {user_token}"}
        booking_data = {
            "pickup_location": "123 Main Street",
            "dropoff_location": "456 Oak Avenue",
            "pickup_time": "2024-01-15T10:00:00Z",
            "passenger_count": 2,
            "special_requests": "No smoking"
        }
        
        response = client.post("/api/v1/bookings/set", json=booking_data, headers=headers)
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["message"] == "Booking created successfully"
        assert "data" in data
        assert data["data"]["pickup_location"] == booking_data["pickup_location"]
        assert data["data"]["dropoff_location"] == booking_data["dropoff_location"]
    
    def test_create_booking_invalid_data(self, client, user_token):
        """Test booking creation with invalid data"""
        headers = {"Authorization": f"Bearer {user_token}"}
        invalid_data = {
            "pickup_location": "",  # Empty pickup location
            "dropoff_location": "",  # Empty dropoff location
            "passenger_count": -1  # Invalid passenger count
        }
        
        response = client.post("/api/v1/bookings/set", json=invalid_data, headers=headers)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_create_booking_unauthenticated(self, client):
        """Test booking creation without authentication"""
        booking_data = {
            "pickup_location": "123 Main Street",
            "dropoff_location": "456 Oak Avenue",
            "passenger_count": 1
        }
        
        response = client.post("/api/v1/bookings/set", json=booking_data)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_get_user_bookings_authenticated(self, client, user_token, test_booking):
        """Test getting user bookings with authentication"""
        headers = {"Authorization": f"Bearer {user_token}"}
        response = client.get("/api/v1/bookings", headers=headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "data" in data
        assert "meta" in data
        assert len(data["data"]) >= 1
    
    def test_get_user_bookings_unauthenticated(self, client):
        """Test getting user bookings without authentication"""
        response = client.get("/api/v1/bookings")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_get_user_bookings_with_filters(self, client, user_token, test_booking):
        """Test getting user bookings with filters"""
        headers = {"Authorization": f"Bearer {user_token}"}
        response = client.get(
            "/api/v1/bookings?status=pending&date_from=2024-01-01",
            headers=headers
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "data" in data
    
    def test_get_booking_by_id_authenticated(self, client, user_token, test_booking):
        """Test getting specific booking by ID with authentication"""
        headers = {"Authorization": f"Bearer {user_token}"}
        response = client.get(f"/api/v1/bookings/{test_booking.id}", headers=headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "data" in data
        assert data["data"]["id"] == test_booking.id
        assert data["data"]["pickup_location"] == test_booking.pickup_location
    
    def test_get_booking_by_id_unauthenticated(self, client, test_booking):
        """Test getting specific booking by ID without authentication"""
        response = client.get(f"/api/v1/bookings/{test_booking.id}")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_get_booking_by_id_nonexistent(self, client, user_token):
        """Test getting non-existent booking by ID"""
        headers = {"Authorization": f"Bearer {user_token}"}
        response = client.get("/api/v1/bookings/999", headers=headers)
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_update_booking_success(self, client, user_token, test_booking):
        """Test successful booking update"""
        headers = {"Authorization": f"Bearer {user_token}"}
        update_data = {
            "pickup_location": "Updated Pickup Location",
            "special_requests": "Updated special requests"
        }
        
        response = client.put(f"/api/v1/bookings/{test_booking.id}", json=update_data, headers=headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["message"] == "Booking updated successfully"
        assert "data" in data
        assert data["data"]["pickup_location"] == update_data["pickup_location"]
        assert data["data"]["special_requests"] == update_data["special_requests"]
    
    def test_update_booking_invalid_data(self, client, user_token, test_booking):
        """Test booking update with invalid data"""
        headers = {"Authorization": f"Bearer {user_token}"}
        invalid_data = {
            "pickup_location": "",  # Empty pickup location
            "passenger_count": 0  # Invalid passenger count
        }
        
        response = client.put(f"/api/v1/bookings/{test_booking.id}", json=invalid_data, headers=headers)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_update_booking_unauthorized(self, client, driver_token, test_booking):
        """Test booking update by unauthorized user"""
        headers = {"Authorization": f"Bearer {driver_token}"}
        update_data = {
            "pickup_location": "Unauthorized Update"
        }
        
        response = client.put(f"/api/v1/bookings/{test_booking.id}", json=update_data, headers=headers)
        # Should fail due to authorization
        assert response.status_code in [status.HTTP_403_FORBIDDEN, status.HTTP_401_UNAUTHORIZED]
    
    def test_cancel_booking_success(self, client, user_token, test_booking):
        """Test successful booking cancellation"""
        headers = {"Authorization": f"Bearer {user_token}"}
        response = client.delete(f"/api/v1/bookings/{test_booking.id}", headers=headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["message"] == "Booking cancelled successfully"
    
    def test_cancel_booking_nonexistent(self, client, user_token):
        """Test cancelling non-existent booking"""
        headers = {"Authorization": f"Bearer {user_token}"}
        response = client.delete("/api/v1/bookings/999", headers=headers)
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_cancel_booking_unauthorized(self, client, driver_token, test_booking):
        """Test booking cancellation by unauthorized user"""
        headers = {"Authorization": f"Bearer {driver_token}"}
        response = client.delete(f"/api/v1/bookings/{test_booking.id}", headers=headers)
        # Should fail due to authorization
        assert response.status_code in [status.HTTP_403_FORBIDDEN, status.HTTP_401_UNAUTHORIZED]
    
    def test_get_booking_status_authenticated(self, client, user_token, test_booking):
        """Test getting booking status with authentication"""
        headers = {"Authorization": f"Bearer {user_token}"}
        response = client.get(f"/api/v1/bookings/{test_booking.id}/status", headers=headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "data" in data
        assert "status" in data["data"]
    
    def test_get_booking_status_unauthenticated(self, client, test_booking):
        """Test getting booking status without authentication"""
        response = client.get(f"/api/v1/bookings/{test_booking.id}/status")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_get_booking_estimated_fare(self, client, user_token):
        """Test getting estimated fare for a route"""
        headers = {"Authorization": f"Bearer {user_token}"}
        route_data = {
            "pickup_location": "123 Main Street",
            "dropoff_location": "456 Oak Avenue",
            "passenger_count": 2
        }
        
        response = client.post("/api/v1/bookings/estimate-fare", json=route_data, headers=headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "data" in data
        assert "estimated_fare" in data["data"]
    
    def test_get_booking_estimated_fare_invalid_route(self, client, user_token):
        """Test getting estimated fare for invalid route"""
        headers = {"Authorization": f"Bearer {user_token}"}
        invalid_route = {
            "pickup_location": "",  # Empty pickup location
            "dropoff_location": "456 Oak Avenue"
        }
        
        response = client.post("/api/v1/bookings/estimate-fare", json=invalid_route, headers=headers)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_get_booking_driver_info(self, client, user_token, test_booking, test_driver):
        """Test getting driver information for a booking"""
        headers = {"Authorization": f"Bearer {user_token}"}
        response = client.get(f"/api/v1/bookings/{test_booking.id}/driver", headers=headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "data" in data
        # Should contain driver information if assigned
    
    def test_get_booking_vehicle_info(self, client, user_token, test_booking, test_vehicle):
        """Test getting vehicle information for a booking"""
        headers = {"Authorization": f"Bearer {user_token}"}
        response = client.get(f"/api/v1/bookings/{test_booking.id}/vehicle", headers=headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "data" in data
        # Should contain vehicle information if assigned
    
    def test_rate_booking_success(self, client, user_token, test_booking):
        """Test successful booking rating"""
        headers = {"Authorization": f"Bearer {user_token}"}
        rating_data = {
            "rating": 5,
            "comment": "Great ride experience!"
        }
        
        response = client.post(f"/api/v1/bookings/{test_booking.id}/rate", json=rating_data, headers=headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["message"] == "Rating submitted successfully"
    
    def test_rate_booking_invalid_rating(self, client, user_token, test_booking):
        """Test booking rating with invalid rating value"""
        headers = {"Authorization": f"Bearer {user_token}"}
        invalid_rating = {
            "rating": 6,  # Invalid rating (should be 1-5)
            "comment": "Invalid rating"
        }
        
        response = client.post(f"/api/v1/bookings/{test_booking.id}/rate", json=invalid_rating, headers=headers)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_get_booking_receipt(self, client, user_token, test_booking):
        """Test getting booking receipt"""
        headers = {"Authorization": f"Bearer {user_token}"}
        response = client.get(f"/api/v1/bookings/{test_booking.id}/receipt", headers=headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "data" in data
        # Should contain receipt information 