import pytest
from fastapi import status
from app.models.user import User
from app.utils.password_utils import hash_password

class TestUsersAPI:
    """Test cases for Users API endpoints"""
    
    def test_create_user_success(self, client, db_session):
        """Test successful user creation"""
        user_data = {
            "first_name": "New",
            "last_name": "User",
            "email": "newuser@test.com",
            "phone": "+1234567890",
            "password": "newpassword123"
        }
        
        response = client.post("/api/v1/users", json=user_data)
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["message"] == "User created successfully"
        assert "data" in data
        assert data["data"]["first_name"] == user_data["first_name"]
        assert data["data"]["last_name"] == user_data["last_name"]
        assert data["data"]["email"] == user_data["email"]
        assert data["data"]["phone"] == user_data["phone"]
    
    def test_create_user_invalid_data(self, client):
        """Test user creation with invalid data"""
        invalid_data = {
            "first_name": "",  # Empty first name
            "last_name": "",  # Empty last name
            "email": "invalid-email",  # Invalid email format
            "phone": "123",  # Invalid phone
            "password": "123"  # Too short password
        }
        
        response = client.post("/api/v1/users", json=invalid_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_create_user_duplicate_email(self, client, db_session, test_user):
        """Test user creation with duplicate email"""
        duplicate_data = {
            "first_name": "Another",
            "last_name": "User",
            "email": "user@test.com",  # Same email as test_user
            "phone": "+0987654321",
            "password": "password123"
        }
        
        response = client.post("/api/v1/users", json=duplicate_data)
        # Should fail due to duplicate email
        assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_422_UNPROCESSABLE_ENTITY]
    
    def test_get_user_profile_authenticated(self, client, user_token, test_user):
        """Test getting user profile with authentication"""
        headers = {"Authorization": f"Bearer {user_token}"}
        response = client.get("/api/v1/users/profile", headers=headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "data" in data
        assert data["data"]["id"] == test_user.id
        assert data["data"]["first_name"] == test_user.first_name
        assert data["data"]["last_name"] == test_user.last_name
        assert data["data"]["email"] == test_user.email
    
    def test_get_user_profile_unauthenticated(self, client):
        """Test getting user profile without authentication"""
        response = client.get("/api/v1/users/profile")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_update_user_profile_success(self, client, user_token, test_user):
        """Test successful user profile update"""
        headers = {"Authorization": f"Bearer {user_token}"}
        update_data = {
            "first_name": "Updated",
            "last_name": "User",
            "phone": "+9876543210"
        }
        
        response = client.put("/api/v1/users/profile", json=update_data, headers=headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["message"] == "User profile updated successfully"
        assert "data" in data
        assert data["data"]["first_name"] == update_data["first_name"]
        assert data["data"]["last_name"] == update_data["last_name"]
        assert data["data"]["phone"] == update_data["phone"]
    
    def test_update_user_profile_invalid_data(self, client, user_token):
        """Test user profile update with invalid data"""
        headers = {"Authorization": f"Bearer {user_token}"}
        invalid_data = {
            "first_name": "",  # Empty first name
            "email": "invalid-email",  # Invalid email format
            "phone": "123"  # Invalid phone
        }
        
        response = client.put("/api/v1/users/profile", json=invalid_data, headers=headers)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_update_user_profile_unauthorized(self, client, driver_token):
        """Test user profile update by unauthorized user"""
        headers = {"Authorization": f"Bearer {driver_token}"}
        update_data = {
            "first_name": "Unauthorized Update"
        }
        
        response = client.put("/api/v1/users/profile", json=update_data, headers=headers)
        # Should fail due to authorization
        assert response.status_code in [status.HTTP_403_FORBIDDEN, status.HTTP_401_UNAUTHORIZED]
    
    def test_change_user_password_success(self, client, user_token, test_user):
        """Test successful password change"""
        headers = {"Authorization": f"Bearer {user_token}"}
        password_data = {
            "current_password": "testpassword123",
            "new_password": "newpassword456"
        }
        
        response = client.put("/api/v1/users/change-password", json=password_data, headers=headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["message"] == "Password changed successfully"
    
    def test_change_user_password_wrong_current(self, client, user_token, test_user):
        """Test password change with wrong current password"""
        headers = {"Authorization": f"Bearer {user_token}"}
        password_data = {
            "current_password": "wrongpassword",
            "new_password": "newpassword456"
        }
        
        response = client.put("/api/v1/users/change-password", json=password_data, headers=headers)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "Invalid current password" in data["detail"]
    
    def test_change_user_password_invalid_new_password(self, client, user_token, test_user):
        """Test password change with invalid new password"""
        headers = {"Authorization": f"Bearer {user_token}"}
        password_data = {
            "current_password": "testpassword123",
            "new_password": "123"  # Too short
        }
        
        response = client.put("/api/v1/users/change-password", json=password_data, headers=headers)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_get_user_bookings_authenticated(self, client, user_token, test_booking):
        """Test getting user bookings with authentication"""
        headers = {"Authorization": f"Bearer {user_token}"}
        response = client.get("/api/v1/users/bookings", headers=headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "data" in data
        assert "meta" in data
        assert len(data["data"]) >= 1
    
    def test_get_user_bookings_unauthenticated(self, client):
        """Test getting user bookings without authentication"""
        response = client.get("/api/v1/users/bookings")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_get_user_bookings_with_filters(self, client, user_token, test_booking):
        """Test getting user bookings with filters"""
        headers = {"Authorization": f"Bearer {user_token}"}
        response = client.get(
            "/api/v1/users/bookings?status=completed&date_from=2024-01-01",
            headers=headers
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "data" in data
    
    def test_get_user_payment_methods_authenticated(self, client, user_token):
        """Test getting user payment methods with authentication"""
        headers = {"Authorization": f"Bearer {user_token}"}
        response = client.get("/api/v1/users/payment-methods", headers=headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "data" in data
        # Should contain payment methods
    
    def test_get_user_payment_methods_unauthenticated(self, client):
        """Test getting user payment methods without authentication"""
        response = client.get("/api/v1/users/payment-methods")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_add_user_payment_method_success(self, client, user_token):
        """Test successful payment method addition"""
        headers = {"Authorization": f"Bearer {user_token}"}
        payment_data = {
            "card_number": "4242424242424242",
            "expiry_month": 12,
            "expiry_year": 2025,
            "cvv": "123",
            "cardholder_name": "Test User"
        }
        
        response = client.post("/api/v1/users/payment-methods", json=payment_data, headers=headers)
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["message"] == "Payment method added successfully"
        assert "data" in data
    
    def test_add_user_payment_method_invalid_data(self, client, user_token):
        """Test payment method addition with invalid data"""
        headers = {"Authorization": f"Bearer {user_token}"}
        invalid_data = {
            "card_number": "123",  # Invalid card number
            "expiry_month": 13,  # Invalid month
            "expiry_year": 2020,  # Expired year
            "cvv": "12"  # Invalid CVV
        }
        
        response = client.post("/api/v1/users/payment-methods", json=invalid_data, headers=headers)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_delete_user_payment_method_success(self, client, user_token):
        """Test successful payment method deletion"""
        headers = {"Authorization": f"Bearer {user_token}"}
        response = client.delete("/api/v1/users/payment-methods/1", headers=headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["message"] == "Payment method deleted successfully"
    
    def test_get_user_preferences_authenticated(self, client, user_token):
        """Test getting user preferences with authentication"""
        headers = {"Authorization": f"Bearer {user_token}"}
        response = client.get("/api/v1/users/preferences", headers=headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "data" in data
        # Should contain user preferences
    
    def test_update_user_preferences_success(self, client, user_token):
        """Test successful user preferences update"""
        headers = {"Authorization": f"Bearer {user_token}"}
        preferences_data = {
            "language": "en",
            "timezone": "UTC",
            "notifications": {
                "email": True,
                "sms": False,
                "push": True
            },
            "accessibility": {
                "large_text": False,
                "high_contrast": True
            }
        }
        
        response = client.put("/api/v1/users/preferences", json=preferences_data, headers=headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["message"] == "Preferences updated successfully"
        assert "data" in data
    
    def test_get_user_activity_history_authenticated(self, client, user_token):
        """Test getting user activity history with authentication"""
        headers = {"Authorization": f"Bearer {user_token}"}
        response = client.get("/api/v1/users/activity-history", headers=headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "data" in data
        # Should contain activity history
    
    def test_get_user_activity_history_with_filters(self, client, user_token):
        """Test getting user activity history with filters"""
        headers = {"Authorization": f"Bearer {user_token}"}
        response = client.get(
            "/api/v1/users/activity-history?activity_type=login&date_from=2024-01-01",
            headers=headers
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "data" in data
    
    def test_deactivate_user_account_success(self, client, user_token, test_user):
        """Test successful account deactivation"""
        headers = {"Authorization": f"Bearer {user_token}"}
        response = client.post("/api/v1/users/deactivate", headers=headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["message"] == "Account deactivated successfully"
    
    def test_reactivate_user_account_success(self, client, user_token, test_user):
        """Test successful account reactivation"""
        headers = {"Authorization": f"Bearer {user_token}"}
        response = client.post("/api/v1/users/reactivate", headers=headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["message"] == "Account reactivated successfully"
    
    def test_get_user_support_tickets_authenticated(self, client, user_token):
        """Test getting user support tickets with authentication"""
        headers = {"Authorization": f"Bearer {user_token}"}
        response = client.get("/api/v1/users/support-tickets", headers=headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "data" in data
        # Should contain support tickets
    
    def test_create_user_support_ticket_success(self, client, user_token):
        """Test successful support ticket creation"""
        headers = {"Authorization": f"Bearer {user_token}"}
        ticket_data = {
            "subject": "Payment Issue",
            "description": "I'm having trouble with my payment method",
            "priority": "medium",
            "category": "billing"
        }
        
        response = client.post("/api/v1/users/support-tickets", json=ticket_data, headers=headers)
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["message"] == "Support ticket created successfully"
        assert "data" in data 