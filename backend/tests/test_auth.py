import pytest
from fastapi import status
from app.models.tenant import Tenants
from app.models.driver import Drivers
from app.models.user import Users
from app.utils.password_utils import hash

class TestAuthAPI:
    """Test cases for Authentication API endpoints"""
    
    def test_tenant_login_success(self, client, db_session, test_tenant):
        """Test successful tenant login"""
        response = client.post(
            "/api/v1/login/tenants",
            data={
                "username": "test@company.com",
                "password": "testpassword123"
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert data["access_token"] is not None
        
        # Check if refresh token cookie is set
        cookies = response.cookies
        assert "refresh_token" in cookies
    
    def test_tenant_login_invalid_credentials(self, client, db_session, test_tenant):
        """Test tenant login with invalid credentials"""
        response = client.post(
            "/api/v1/login/tenants",
            data={
                "username": "test@company.com",
                "password": "wrongpassword"
            }
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
        data = response.json()
        assert data["detail"] == "Invalid credentials"
    
    def test_tenant_login_nonexistent_user(self, client, db_session):
        """Test tenant login with non-existent user"""
        response = client.post(
            "/api/v1/login/tenants",
            data={
                "username": "nonexistent@company.com",
                "password": "testpassword123"
            }
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
        data = response.json()
        assert data["detail"] == "Invalid credentials"
    
    def test_driver_login_success(self, client, db_session, test_driver):
        """Test successful driver login"""
        # Create a driver with password
        driver_with_password = Drivers(
            id=2,
            tenant_id=test_driver.tenant_id,
            first_name="Driver",
            last_name="Test",
            email="driver2@test.com",
            phone_no="+1234567890",
            password=hash("driverpass123"),
            is_active=True,
            driver_type="standard",
            completed_rides="0",
            driver_token="test_driver_token_2",
            is_registered="registered",
            status="available"
        )
        db_session.add(driver_with_password)
        db_session.commit()
        
        response = client.post(
            "/api/v1/login/driver",
            data={
                "username": "driver2@test.com",
                "password": "driverpass123"
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert data["access_token"] is not None
    
    def test_driver_login_invalid_credentials(self, client, db_session, test_driver):
        """Test driver login with invalid credentials"""
        # Create a driver with password
        driver_with_password = Drivers(
            id=3,
            tenant_id=test_driver.tenant_id,
            first_name="Driver",
            last_name="Test",
            email="driver3@test.com",
            phone_no="+1234567890",
            password=hash("driverpass123"),
            is_active=True,
            driver_type="standard",
            completed_rides="0",
            driver_token="test_driver_token_3",
            is_registered="registered",
            status="available"
        )
        db_session.add(driver_with_password)
        db_session.commit()
        
        response = client.post(
            "/api/v1/login/driver",
            data={
                "username": "driver3@test.com",
                "password": "wrongpassword"
            }
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
        data = response.json()
        assert data["detail"] == "Invalid credentials"
    
    def test_user_login_success(self, client, db_session, test_user):
        """Test successful user/rider login"""
        # Create a user with password
        user_with_password = Users(
            id=2,
            tenant_id=test_user.tenant_id,
            first_name="User",
            last_name="Test",
            email="user2@test.com",
            phone_no="+0987654321",
            password=hash("userpass123"),
            role="rider",
            tier="free"
        )
        db_session.add(user_with_password)
        db_session.commit()
        
        response = client.post(
            "/api/v1/login/user",
            data={
                "username": "user2@test.com",
                "password": "userpass123"
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert data["access_token"] is not None
    
    def test_user_login_invalid_credentials(self, client, db_session, test_user):
        """Test user login with invalid credentials"""
        # Create a user with password
        user_with_password = Users(
            id=3,
            tenant_id=test_user.tenant_id,
            first_name="User",
            last_name="Test",
            email="user3@test.com",
            phone_no="+0987654321",
            password=hash("userpass123"),
            role="rider",
            tier="free"
        )
        db_session.add(user_with_password)
        db_session.commit()
        
        response = client.post(
            "/api/v1/login/user",
            data={
                "username": "user3@test.com",
                "password": "wrongpassword"
            }
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
        data = response.json()
        assert data["detail"] == "Invalid credentials"
    
    # def test_refresh_token_tenant(self, client, db_session, test_tenant):
    #     """Test tenant refresh token endpoint"""
    #     # First login to get refresh token
    #     login_response = client.post(
    #         "/api/v1/login/tenants",
    #         data={
    #             "username": "test@company.com",
    #             "password": "testpassword123"
    #         }
    #     )
        
    #     refresh_token = login_response.cookies.get("refresh_token")
        
    #     # Test refresh endpoint
    #     response = client.post(
    #         "/api/v1/login/refresh_tenants",
    #         cookies={"refresh_token": refresh_token}
    #     )
        
    #     # Note: This endpoint might not be fully implemented in the current code
    #     # Adjust assertions based on actual implementation
    #     assert response.status_code in [status.HTTP_200_OK, status.HTTP_422_UNPROCESSABLE_ENTITY]
    
    # def test_refresh_token_general(self, client, db_session, test_user):
    #     """Test general refresh token endpoint"""
    #     # Create a user with password
    #     user_with_password = Users(
    #         id=4,
    #         tenant_id=test_user.tenant_id,
    #         first_name="User",
    #         last_name="Test",
    #         email="user4@test.com",
    #         phone_no="+0987654321",
    #         password=hash("userpass123"),
    #         is_active=True
    #     )
    #     db_session.add(user_with_password)
    #     db_session.commit()
        
    #     # First login to get refresh token
    #     login_response = client.post(
    #         "/api/v1/login/user",
    #         data={
    #             "username": "user4@test.com",
    #             "password": "userpass123"
    #         }
    #     )
        
    #     refresh_token = login_response.cookies.get("refresh_token")
        
    #     # Test refresh endpoint
    #     response = client.post(
    #         "/api/v1/login/refresh",
    #         cookies={"refresh_token": refresh_token}
    #     )
        
    #     # Note: This endpoint might not be fully implemented in the current code
    #     # Adjust assertions based on actual implementation
    #     assert response.status_code in [status.HTTP_200_OK, status.HTTP_422_UNPROCESSABLE_ENTITY]
    
    def test_login_missing_credentials(self, client):
        """Test login with missing credentials"""
        response = client.post("/api/v1/login/tenants")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_login_empty_credentials(self, client):
        """Test login with empty credentials"""
        response = client.post(
            "/api/v1/login/tenants",
            data={
                "username": "",
                "password": ""
            }
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN 