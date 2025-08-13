
"""
Ride Sharing System CLI Tool
A comprehensive command-line interface to simulate frontend interactions
with the ride-sharing backend API.
"""

import requests
import json
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Any
import getpass
from urllib.parse import urljoin
import sys
import os
from dataclasses import dataclass
from enum import Enum
import re

class UserRole(Enum):
    RIDER = "rider"
    DRIVER = "driver"
    TENANT = "tenant"
    ADMIN = "admin"

class ServiceType(Enum):
    AIRPORT = "airport"
    HOURLY = "hourly"
    DROP_OFF = "dropoff"

class PaymentType(Enum):
    CASH = "cash"
    CARD = "card"
    ZELLE = "zelle"

class DriverType(Enum):
    OUTSOURCED = "outsourced"
    IN_HOUSE = "in_house"

@dataclass
class CurrentUser:
    email: str
    role: str
    id: Optional[int] = None
    tenant_id: Optional[int] = None
    full_name: Optional[str] = None

class RideBookingAPI:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.current_user: Optional[CurrentUser] = None
        self.access_token: Optional[str] = None
        
    def set_auth_token(self, token: str):
        """Set authentication token for API calls"""
        self.access_token = token
        self.session.headers.update({"Authorization": f"Bearer {token}"})
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Make HTTP request with error handling"""
        url = urljoin(f"{self.base_url}/", endpoint.lstrip('/'))
        try:
            response = self.session.request(method, url, **kwargs)
            return response
        except requests.exceptions.RequestException as e:
            raise Exception(f"Network error: {e}")
    
    def login(self, email: str, password: str, role: str) -> Dict:
        """Login user based on role"""
        login_endpoints = {
            "rider": "/api/v1/login/user",
            "driver": "/api/v1/login/driver", 
            "tenant": "/api/v1/login/tenants"
        }
        
        endpoint = login_endpoints.get(role.lower())
        if not endpoint:
            raise ValueError(f"Invalid role: {role}")
            
        data = {
            "username": email,
            "password": password
        }
        
        response = self._make_request("POST", endpoint, data=data)
        if response.status_code == 200:
            result = response.json()
            self.set_auth_token(result["access_token"])
            self.current_user = CurrentUser(email=email, role=role)
            return result
        else:
            raise Exception(f"Login failed: {response.status_code} - {response.text}")
    
    # Tenant operations
    def create_tenant(self, tenant_data: Dict) -> Dict:
        """Create new tenant"""
        response = self._make_request("POST", "/api/v1/tenant/add", json=tenant_data)
        if response.status_code == 201:
            return response.json()
        else:
            raise Exception(f"Failed to create tenant: {response.status_code} - {response.text}")
    
    def get_tenant_info(self) -> Dict:
        """Get current tenant information"""
        response = self._make_request("GET", "/api/v1/tenant/")
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to get tenant info: {response.status_code} - {response.text}")
    
    def get_tenant_drivers(self) -> List[Dict]:
        """Get all drivers for current tenant"""
        response = self._make_request("GET", "/api/v1/tenant/drivers")
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to get drivers: {response.status_code} - {response.text}")
    
    def get_tenant_vehicles(self, driver_id: Optional[int] = None, assigned_only: bool = False) -> List[Dict]:
        """Get vehicles for current tenant"""
        params = {}
        if driver_id:
            params["driver_id"] = driver_id
        if assigned_only:
            params["assigned_drivers"] = True
            
        response = self._make_request("GET", "/api/v1/tenant/vehicles", params=params)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to get vehicles: {response.status_code} - {response.text}")
    
    def get_tenant_bookings(self, status: Optional[str] = None) -> List[Dict]:
        """Get bookings for current tenant"""
        params = {}
        if status:
            params["booking_status"] = status
            
        response = self._make_request("GET", "/api/v1/tenant/bookings", params=params)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to get bookings: {response.status_code} - {response.text}")
    
    def onboard_driver(self, driver_data: Dict) -> Dict:
        """Onboard new driver"""
        response = self._make_request("POST", "/api/v1/tenant/onboard", json=driver_data)
        if response.status_code == 201:
            return response.json()
        else:
            raise Exception(f"Failed to onboard driver: {response.status_code} - {response.text}")
    
    def assign_driver_to_ride(self, rider_id: int, driver_id: int) -> Dict:
        """Assign driver to a ride"""
        payload = {"driver_id": driver_id}
        response = self._make_request("PATCH", f"/api/v1/tenant/assign_driver/{rider_id}", json=payload)
        if response.status_code == 202:
            return response.json()
        else:
            raise Exception(f"Failed to assign driver: {response.status_code} - {response.text}")
    
    def assign_driver_to_vehicle(self, vehicle_id: int, driver_id: int) -> Dict:
        """Assign driver to a vehicle"""
        payload = {"driver_id": driver_id}
        response = self._make_request("PATCH", f"/api/v1/tenant/assign_driver_vehicle/{vehicle_id}", json=payload)
        if response.status_code == 202:
            return response.json()
        else:
            raise Exception(f"Failed to assign driver to vehicle: {response.status_code} - {response.text}")
    
    # User operations
    def create_user(self, user_data: Dict) -> Dict:
        """Create new user/rider"""
        response = self._make_request("POST", "/api/v1/users/add", json=user_data)
        if response.status_code == 201:
            return response.json()
        else:
            raise Exception(f"Failed to create user: {response.status_code} - {response.text}")
    
    def get_user_info(self) -> Dict:
        """Get current user information"""
        response = self._make_request("GET", "/api/v1/users/")
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to get user info: {response.status_code} - {response.text}")
    
    # Driver operations
    def register_driver(self, driver_data: Dict) -> Dict:
        """Register driver with token"""
        response = self._make_request("PATCH", "/api/v1/driver/register", json=driver_data)
        if response.status_code == 202:
            return response.json()
        else:
            raise Exception(f"Failed to register driver: {response.status_code} - {response.text}")
    
    def get_driver_info(self) -> Dict:
        """Get current driver information"""
        response = self._make_request("GET", "/api/v1/driver/info")
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to get driver info: {response.status_code} - {response.text}")
    
    def get_available_rides(self, status: str = "pending") -> List[Dict]:
        """Get available rides for driver"""
        params = {"booking_status": status}
        response = self._make_request("GET", "/api/v1/driver/rides/available", params=params)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to get available rides: {response.status_code} - {response.text}")
    
    def respond_to_ride(self, booking_id: int, action: str) -> Dict:
        """Confirm or cancel a ride"""
        params = {"action": action}
        response = self._make_request("PATCH", f"/api/v1/driver/ride/{booking_id}/decision", params=params)
        if response.status_code == 202:
            return response.json()
        else:
            raise Exception(f"Failed to respond to ride: {response.status_code} - {response.text}")
    
    # Booking operations
    def book_ride(self, booking_data: Dict) -> Dict:
        """Book a ride"""
        response = self._make_request("POST", "/api/v1/bookings/set", json=booking_data)
        if response.status_code == 201:
            return response.json()
        else:
            raise Exception(f"Failed to book ride: {response.status_code} - {response.text}")
    
    def get_user_bookings(self) -> List[Dict]:
        """Get user's bookings"""
        response = self._make_request("GET", "/api/v1/bookings/")
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to get bookings: {response.status_code} - {response.text}")
    
    # Vehicle operations
    def get_vehicles(self) -> List[Dict]:
        """Get available vehicles"""
        response = self._make_request("GET", "/api/v1/vehicles/")
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to get vehicles: {response.status_code} - {response.text}")
    
    def add_vehicle(self, vehicle_data: Dict) -> Dict:
        """Add new vehicle"""
        response = self._make_request("POST", "/api/v1/vehicles/add", json=vehicle_data)
        if response.status_code == 201:
            return response.json()
        else:
            raise Exception(f"Failed to add vehicle: {response.status_code} - {response.text}")
    
    def set_vehicle_rates(self, rate_data: Dict) -> Dict:
        """Set vehicle category rates"""
        response = self._make_request("PATCH", "/api/v1/vehicles/set_rates", json=rate_data)
        if response.status_code == 201:
            return response.json()
        else:
            raise Exception(f"Failed to set vehicle rates: {response.status_code} - {response.text}")
    
    def get_vehicle_rates(self) -> List[Dict]:
        """Get vehicle category rates"""
        response = self._make_request("GET", "/api/v1/vehicles/vehicle_rates")
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to get vehicle rates: {response.status_code} - {response.text}")

class RideBookingCLI:
    def __init__(self):
        self.api = RideBookingAPI()
        self.running = True
    
    def clear_screen(self):
        """Clear terminal screen"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def print_header(self, title: str):
        """Print formatted header"""
        print("=" * 60)
        print(f" {title.center(56)} ")
        print("=" * 60)
    
    def print_menu(self, options: List[str], title: str = "Menu"):
        """Print menu options"""
        self.print_header(title)
        for i, option in enumerate(options, 1):
            print(f"{i}. {option}")
        print("0. Back/Exit")
        print("-" * 60)
    
    def get_choice(self, max_option: int) -> int:
        """Get user choice with validation"""
        while True:
            try:
                choice = int(input("Enter your choice: "))
                if 0 <= choice <= max_option:
                    return choice
                else:
                    print(f"Please enter a number between 0 and {max_option}")
            except ValueError:
                print("Please enter a valid number")
    
    def get_input(self, prompt: str, required: bool = True) -> str:
        """Get user input with validation"""
        while True:
            value = input(prompt).strip()
            if not required or value:
                return value
            print("This field is required. Please enter a value.")
    
    def get_password(self, prompt: str = "Password: ") -> str:
        """Get password input"""
        return getpass.getpass(prompt)
    
    def validate_email(self, email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def get_email(self, prompt: str = "Email: ") -> str:
        """Get and validate email input"""
        while True:
            email = self.get_input(prompt)
            if self.validate_email(email):
                return email.lower()
            print("Please enter a valid email address")
    
    def get_phone(self, prompt: str = "Phone: ") -> str:
        """Get and validate phone input"""
        while True:
            phone = self.get_input(prompt)
            if re.match(r'^\+?[\d\s\-\(\)]+$', phone):
                return phone
            print("Please enter a valid phone number")
    
    def validate_password(self, password: str) -> bool:
        """Validate password strength"""
        if len(password) < 8:
            return False
        if not re.search(r'[A-Z]', password):
            return False
        if not re.search(r'[a-z]', password):
            return False
        if not re.search(r'\d', password):
            return False
        return True
    
    def get_strong_password(self, prompt: str = "Password: ") -> str:
        """Get password with strength validation"""
        while True:
            password = self.get_password(prompt)
            if self.validate_password(password):
                return password
            print("Password must be at least 8 characters and contain uppercase, lowercase, and number")
    
    def format_datetime(self, dt_str: str) -> str:
        """Format datetime string for display"""
        try:
            dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
            return dt.strftime("%Y-%m-%d %H:%M")
        except:
            return dt_str
    
    def get_datetime_input(self, prompt: str) -> str:
        """Get datetime input from user"""
        print(f"{prompt}")
        print("Format: YYYY-MM-DD HH:MM (e.g., 2024-12-25 14:30)")
        while True:
            dt_str = self.get_input("DateTime: ")
            try:
                # Parse and validate
                dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
                # Return in ISO format
                return dt.isoformat()
            except ValueError:
                print("Invalid format. Please use YYYY-MM-DD HH:MM")
    
    def display_table(self, data: List[Dict], headers: List[str], keys: List[str]):
        """Display data in table format"""
        if not data:
            print("No data available")
            return
        
        # Calculate column widths
        widths = []
        for i, header in enumerate(headers):
            key = keys[i]
            max_width = len(header)
            for item in data:
                value_str = str(item.get(key, ''))
                max_width = max(max_width, len(value_str))
            widths.append(min(max_width, 30))  # Cap at 30 chars
        
        # Print header
        header_row = " | ".join(h.ljust(w) for h, w in zip(headers, widths))
        print(header_row)
        print("-" * len(header_row))
        
        # Print data rows
        for item in data:
            row_data = []
            for i, key in enumerate(keys):
                value = item.get(key, '')
                if 'time' in key.lower() or 'date' in key.lower():
                    value = self.format_datetime(str(value)) if value else ''
                value_str = str(value)[:widths[i]]  # Truncate if too long
                row_data.append(value_str.ljust(widths[i]))
            print(" | ".join(row_data))
    
    def main_menu(self):
        """Display main menu"""
        while self.running:
            self.clear_screen()
            
            if self.api.current_user:
                title = f"Ride Booking System - Logged in as {self.api.current_user.role.title()}"
                options = [
                    "Dashboard",
                    "Logout",
                    "Exit"
                ]
            else:
                title = "Ride Booking System - Welcome"
                options = [
                    "Login",
                    "Register Tenant",
                    "Register User",
                    "Register Driver (with token)",
                    "Exit"
                ]
            
            self.print_menu(options, title)
            choice = self.get_choice(len(options))
            
            if choice == 0 or (choice == len(options) and not self.api.current_user):
                self.running = False
            elif not self.api.current_user:
                if choice == 1:
                    self.login_menu()
                elif choice == 2:
                    self.register_tenant()
                elif choice == 3:
                    self.register_user()
                elif choice == 4:
                    self.register_driver()
            else:
                if choice == 1:
                    self.dashboard()
                elif choice == 2:
                    self.logout()
                elif choice == 3:
                    self.running = False
    
    def login_menu(self):
        """Login menu"""
        self.clear_screen()
        roles = ["Rider", "Driver", "Tenant", "Admin"]
        self.print_menu(roles, "Login - Select Role")
        choice = self.get_choice(len(roles))
        
        if choice == 0:
            return
        
        role = roles[choice - 1].lower()
        if role == "admin":
            print("Admin login not implemented yet")
            input("Press Enter to continue...")
            return
        
        print(f"\nLogin as {role.title()}")
        email = self.get_email()
        password = self.get_password()
        
        try:
            result = self.api.login(email, password, role)
            print(f"Login successful! Welcome {email}")
            input("Press Enter to continue...")
        except Exception as e:
            print(f"Login failed: {e}")
            input("Press Enter to continue...")
    
    def logout(self):
        """Logout current user"""
        self.api.current_user = None
        self.api.access_token = None
        self.api.session.headers.pop("Authorization", None)
        print("Logged out successfully!")
        input("Press Enter to continue...")
    
    def register_tenant(self):
        """Register new tenant"""
        self.clear_screen()
        self.print_header("Register New Tenant")
        
        try:
            tenant_data = {
                "email": self.get_email(),
                "first_name": self.get_input("First Name: "),
                "last_name": self.get_input("Last Name: "),
                "password": self.get_strong_password(),
                "phone_no": self.get_phone(),
                "company_name": self.get_input("Company Name: "),
                "slug": self.get_input("Company Slug (lowercase, hyphens only): "),
                "city": self.get_input("City: "),
                "drivers_count": 0
            }
            
            # Optional fields
            logo_url = self.get_input("Logo URL (optional): ", required=False)
            if logo_url:
                tenant_data["logo_url"] = logo_url
            
            address = self.get_input("Address (optional): ", required=False)
            if address:
                tenant_data["address"] = address
            
            result = self.api.create_tenant(tenant_data)
            print(f"Tenant created successfully! ID: {result['id']}")
            
        except Exception as e:
            print(f"Failed to create tenant: {e}")
        
        input("Press Enter to continue...")
    
    def register_user(self):
        """Register new user"""
        self.clear_screen()
        self.print_header("Register New User")
        
        try:
            tenant_id = int(self.get_input("Tenant ID: "))
            
            user_data = {
                "email": self.get_email(),
                "first_name": self.get_input("First Name: "),
                "last_name": self.get_input("Last Name: "),
                "password": self.get_strong_password(),
                "phone_no": self.get_phone(),
                "tenant_id": tenant_id
            }
            
            # Optional fields
            for field in ["address", "city", "state", "country", "postal_code"]:
                value = self.get_input(f"{field.title()} (optional): ", required=False)
                if value:
                    user_data[field] = value
            
            result = self.api.create_user(user_data)
            print(f"User created successfully! ID: {result['id']}")
            
        except Exception as e:
            print(f"Failed to create user: {e}")
        
        input("Press Enter to continue...")
    
    def register_driver(self):
        """Register driver with token"""
        self.clear_screen()
        self.print_header("Register Driver (with token)")
        
        try:
            driver_data = {
                "driver_token": self.get_input("Driver Token: "),
                "email": self.get_email(),
                "first_name": self.get_input("First Name: "),
                "last_name": self.get_input("Last Name: "),
                "password": self.get_strong_password(),
                "phone_no": self.get_phone(),
                "license_number": self.get_input("License Number: ")
            }
            
            # Optional fields
            state = self.get_input("State (optional): ", required=False)
            if state:
                driver_data["state"] = state
            
            postal_code = self.get_input("Postal Code (optional): ", required=False)
            if postal_code:
                driver_data["postal_code"] = postal_code
            
            # Check if outsourced driver needs vehicle
            add_vehicle = input("Add vehicle for outsourced driver? (y/n): ").lower() == 'y'
            if add_vehicle:
                vehicle_data = {
                    "make": self.get_input("Vehicle Make: "),
                    "model": self.get_input("Vehicle Model: "),
                    "year": int(self.get_input("Vehicle Year: ")),
                    "license_plate": self.get_input("License Plate: "),
                    "color": self.get_input("Color (optional): ", required=False)
                }
                driver_data["vehicle"] = vehicle_data
            
            result = self.api.register_driver(driver_data)
            print(f"Driver registered successfully! ID: {result['id']}")
            
        except Exception as e:
            print(f"Failed to register driver: {e}")
        
        input("Press Enter to continue...")
    
    def dashboard(self):
        """Role-specific dashboard"""
        if not self.api.current_user:
            return
        
        role = self.api.current_user.role
        if role == "tenant":
            self.tenant_dashboard()
        elif role == "driver":
            self.driver_dashboard()
        elif role == "rider":
            self.rider_dashboard()
    
    def tenant_dashboard(self):
        """Tenant dashboard"""
        while True:
            self.clear_screen()
            options = [
                "View Company Info",
                "Manage Drivers",
                "Manage Vehicles", 
                "View Bookings",
                "Onboard New Driver",
                "Vehicle Rate Settings"
            ]
            
            self.print_menu(options, "Tenant Dashboard")
            choice = self.get_choice(len(options))
            
            if choice == 0:
                return
            elif choice == 1:
                self.view_company_info()
            elif choice == 2:
                self.manage_drivers()
            elif choice == 3:
                self.manage_vehicles()
            elif choice == 4:
                self.view_tenant_bookings()
            elif choice == 5:
                self.onboard_driver()
            elif choice == 6:
                self.manage_vehicle_rates()
    
    def view_company_info(self):
        """View company information"""
        self.clear_screen()
        self.print_header("Company Information")
        
        try:
            info = self.api.get_tenant_info()
            
            print(f"Company: {info['company_name']}")
            print(f"Email: {info['email']}")
            print(f"Owner: {info['first_name']} {info['last_name']}")
            print(f"Phone: {info['phone_no']}")
            print(f"City: {info['city']}")
            print(f"Slug: {info['slug']}")
            print(f"Plan: {info['plan']}")
            print(f"Active: {info['is_active']}")
            print(f"Verified: {info['is_verified']}")
            print(f"Drivers Count: {info['drivers_count']}")
            print(f"Created: {self.format_datetime(info['created_on'])}")
            
        except Exception as e:
            print(f"Error: {e}")
        
        input("\nPress Enter to continue...")
    
    def manage_drivers(self):
        """Manage drivers"""
        while True:
            self.clear_screen()
            options = [
                "View All Drivers",
                "Assign Driver to Ride",
                "Assign Driver to Vehicle"
            ]
            
            self.print_menu(options, "Driver Management")
            choice = self.get_choice(len(options))
            
            if choice == 0:
                return
            elif choice == 1:
                self.view_drivers()
            elif choice == 2:
                self.assign_driver_to_ride()
            elif choice == 3:
                self.assign_driver_to_vehicle()
    
    def view_drivers(self):
        """View all drivers"""
        self.clear_screen()
        self.print_header("All Drivers")
        
        try:
            drivers = self.api.get_tenant_drivers()
            
            headers = ["ID", "Name", "Email", "Type", "Status", "Rides", "Active"]
            keys = ["id", "full_name", "email", "driver_type", "status", "completed_rides", "is_active"]
            
            # Add full_name for display
            for driver in drivers:
                driver["full_name"] = f"{driver['first_name']} {driver['last_name']}"
            
            self.display_table(drivers, headers, keys)
            
        except Exception as e:
            print(f"Error: {e}")
        
        input("\nPress Enter to continue...")
    
    def assign_driver_to_ride(self):
        """Assign driver to a ride"""
        self.clear_screen()
        self.print_header("Assign Driver to Ride")
        
        try:
            # Show pending bookings
            bookings = self.api.get_tenant_bookings("pending")
            if not bookings:
                print("No pending bookings found")
                input("Press Enter to continue...")
                return
            
            print("Pending Bookings:")
            headers = ["ID", "Pickup", "Time", "Service"]
            keys = ["id", "pickup_location", "pickup_time", "service_type"]
            self.display_table(bookings, headers, keys)
            
            ride_id = int(self.get_input("\nEnter Ride ID: "))
            
            # Show available drivers
            drivers = self.api.get_tenant_drivers()
            print("\nAvailable Drivers:")
            headers = ["ID", "Name", "Type", "Status"]
            keys = ["id", "full_name", "driver_type", "status"]
            
            for driver in drivers:
                driver["full_name"] = f"{driver['first_name']} {driver['last_name']}"
            
            self.display_table(drivers, headers, keys)
            
            driver_id = int(self.get_input("\nEnter Driver ID: "))
            
            result = self.api.assign_driver_to_ride(ride_id, driver_id)
            print(f"Success: {result['msg']}")
            
        except Exception as e:
            print(f"Error: {e}")
        
        input("\nPress Enter to continue...")
    
    def assign_driver_to_vehicle(self):
        """Assign driver to vehicle"""
        self.clear_screen()
        self.print_header("Assign Driver to Vehicle")
        
        try:
            # Show unassigned vehicles
            vehicles = self.api.get_tenant_vehicles()
            unassigned = [v for v in vehicles if not v.get('driver_id')]
            
            if not unassigned:
                print("No unassigned vehicles found")
                input("Press Enter to continue...")
                return
            
            print("Unassigned Vehicles:")
            headers = ["ID", "Make", "Model", "Year", "Plate"]
            keys = ["id", "make", "model", "year", "license_plate"]
            self.display_table(unassigned, headers, keys)
            
            vehicle_id = int(self.get_input("\nEnter Vehicle ID: "))
            
            # Show available drivers
            drivers = self.api.get_tenant_drivers()
            print(f"Driver {drivers}")
        except Exception as e :
            print(f"Error: {e}")

if __name__ == "__main__":
    cli = RideBookingCLI()
    cli.main_menu()