#!/usr/bin/env python3
"""
CLI tool for testing Ride Booking System API flows
"""

import requests
import json
from datetime import datetime, timedelta
from typing import Dict, Optional, List
import getpass
from urllib.parse import urljoin

class RideBookingAPI:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.current_user = None
        self.access_token = None
        
    def set_auth_token(self, token: str):
        """Set authentication token for API calls"""
        self.access_token = token
        self.session.headers.update({"Authorization": f"Bearer {token}"})
    
    def login(self, email: str, password: str, role: str) -> Dict:
        """Login user based on role"""
        login_endpoints = {
            "rider": "/login/user",
            "driver": "/login/driver", 
            "tenant": "/login/tenants"
        }
        
        endpoint = login_endpoints.get(role.lower())
        if not endpoint:
            raise ValueError(f"Invalid role: {role}")
            
        url = urljoin(self.base_url, endpoint)
        data = {
            "username": email,
            "password": password
        }
        
        response = self.session.post(url, data=data)
        if response.status_code == 200:
            result = response.json()
            self.set_auth_token(result["access_token"])
            return result
        else:
            raise Exception(f"Login failed: {response.status_code} - {response.text}")
    
    def create_tenant(self, tenant_data: Dict) -> Dict:
        """Create new tenant"""
        url = urljoin(self.base_url, "/tenant/add")
        response = self.session.post(url, json=tenant_data)
        if response.status_code == 201:
            return response.json()
        else:
            raise Exception(f"Failed to create tenant: {response.status_code} - {response.text}")
    
    def create_user(self, user_data: Dict) -> Dict:
        """Create new user/rider"""
        url = urljoin(self.base_url, "/users/add")
        response = self.session.post(url, json=user_data)
        if response.status_code == 201:
            return response.json()
        else:
            raise Exception(f"Failed to create user: {response.status_code} - {response.text}")
    
    def create_driver(self, driver_data: Dict) -> Dict:
        """Create new driver"""
        url = urljoin(self.base_url, "/driver/create")
        response = self.session.post(url, json=driver_data)
        if response.status_code == 201:
            return response.json()
        else:
            raise Exception(f"Failed to create driver: {response.status_code} - {response.text}")
    
    def get_vehicles(self) -> List[Dict]:
        """Get available vehicles"""
        url = urljoin(self.base_url, "/vehicles/")
        response = self.session.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to get vehicles: {response.status_code} - {response.text}")
    
    def add_vehicle(self, vehicle_data: Dict) -> Dict:
        """Add new vehicle"""
        url = urljoin(self.base_url, "/vehicles/add")
        response = self.session.post(url, json=vehicle_data)
        if response.status_code == 201:
            return response.json()
        else:
            raise Exception(f"Failed to add vehicle: {response.status_code} - {response.text}")
    
    def book_ride(self, booking_data: Dict) -> Dict:
        """Book a ride"""
        url = urljoin(self.base_url, "/bookings/set")
        response = self.session.post(url, json=booking_data)
        if response.status_code == 201:
            return response.json()
        else:
            raise Exception(f"Failed to book ride: {response.status_code} - {response.text}")
    
    def get_bookings(self) -> List[Dict]:
        """Get user's bookings"""
        url = urljoin(self.base_url, "/bookings/")
        response = self.session.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to get bookings: {response.status_code} - {response.text}")
    
    def get_tenant_drivers(self) -> List[Dict]:
        """Get drivers for tenant"""
        url = urljoin(self.base_url, "/tenant/drivers")
        response = self.session.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to get drivers: {response.status_code} - {response.text}")

def display_menu():
    print("\n" + "="*60)
    print("🚗 RIDE BOOKING SYSTEM CLI")
    print("="*60)
    print("1. Login")
    print("2. Create Tenant")
    print("3. Create User/Rider")
    print("4. Create Driver")
    print("5. Add Vehicle")
    print("6. View Vehicles")
    print("7. Book Ride")
    print("8. View Bookings")
    print("9. View Tenant Drivers")
    print("10. Logout")
    print("11. Exit")
    print("-" * 60)

def login_flow(api: RideBookingAPI):
    print("\n🔐 Login")
    print("-" * 30)
    
    email = input("Email: ").strip()
    password = getpass.getpass("Password: ")
    
    print("Select role:")
    print("1. Rider")
    print("2. Driver") 
    print("3. Tenant")
    
    role_choice = input("Enter choice (1-3): ").strip()
    role_map = {"1": "rider", "2": "driver", "3": "tenant"}
    
    if role_choice not in role_map:
        print("❌ Invalid role selection!")
        return
    
    role = role_map[role_choice]
    
    try:
        result = api.login(email, password, role)
        print(f"✅ Login successful as {role}!")
        print(f"Access Token: {result['access_token'][:50]}...")
        api.current_user = {"email": email, "role": role}
    except Exception as e:
        print(f"❌ Login failed: {e}")

def create_tenant_flow(api: RideBookingAPI):
    print("\n🏢 Create Tenant")
    print("-" * 30)
    
    tenant_data = {
        "email": input("Email: ").strip(),
        "first_name": input("First Name: ").strip(),
        "last_name": input("Last Name: ").strip(),
        "password": getpass.getpass("Password: "),
        "phone_no": input("Phone Number: ").strip(),
        "company_name": input("Company Name: ").strip(),
        "slug": input("Company Slug: ").strip(),
        "city": input("City: ").strip(),
        "address": input("Address (optional): ").strip() or None,
        "logo_url": input("Logo URL (optional): ").strip() or None,
        "drivers_count": input("How many drivers do you have: ").strip() or 0
    }
    
    try:
        result = api.create_tenant(tenant_data)
        print(f"✅ Tenant created successfully!")
        print(f"Tenant ID: {result['id']}")
        print(f"Company: {result['company_name']}")
    except Exception as e:
        print(f"❌ Failed to create tenant: {e}")

def create_user_flow(api: RideBookingAPI):
    print("\n👤 Create User/Rider")
    print("-" * 30)
    
    try:
        tenant_id = int(input("Tenant ID: ").strip())
    except ValueError:
        print("❌ Invalid tenant ID!")
        return
    
    user_data = {
        "email": input("Email: ").strip(),
        "first_name": input("First Name: ").strip(),
        "last_name": input("Last Name: ").strip(),
        "password": getpass.getpass("Password: "),
        "phone_no": input("Phone Number: ").strip(),
        "tenant_id": tenant_id,
        "address": input("Address (optional): ").strip() or None,
        "city": input("City (optional): ").strip() or None,
        "state": input("State (optional): ").strip() or None,
        "country": input("Country (optional): ").strip() or None,
        "postal_code": input("Postal Code (optional): ").strip() or None
    }
    
    try:
        result = api.create_user(user_data)
        print(f"✅ User created successfully!")
        print(f"User ID: {result['id']}")
        print(f"Name: {result['first_name']} {result['last_name']}")
    except Exception as e:
        print(f"❌ Failed to create user: {e}")

def create_driver_flow(api: RideBookingAPI):
    print("\n🚙 Create Driver")
    print("-" * 30)
    
    try:
        tenant_id = int(input("Tenant ID: ").strip())
    except ValueError:
        print("❌ Invalid tenant ID!")
        return
    
    driver_data = {
        "tenant_id": tenant_id,
        "email": input("Email: ").strip(),
        "first_name": input("First Name: ").strip(),
        "last_name": input("Last Name: ").strip(),
        "password": getpass.getpass("Password: "),
        "phone_no": input("Phone Number: ").strip(),
        "completed_rides": 0,
        "license_number": input("License Number (optional): ").strip() or None,
        "state": input("State (optional): ").strip() or None,
        "postal_code": input("Postal Code (optional): ").strip() or None,
        "is_active": True,
        "status": "available"
    }
    
    try:
        result = api.create_driver(driver_data)
        print(f"✅ Driver created successfully!")
        print(f"Driver ID: {result['id']}")
        print(f"Name: {result['first_name']} {result['last_name']}")
    except Exception as e:
        print(f"❌ Failed to create driver: {e}")

def add_vehicle_flow(api: RideBookingAPI):
    print("\n🚗 Add Vehicle")
    print("-" * 30)
    
    if not api.access_token:
        print("❌ Please login first!")
        return
    
    try:
        tenant_id = int(input("Tenant ID: ").strip())
    except ValueError:
        print("❌ Invalid tenant ID!")
        return
    
    vehicle_data = {
        "name": input("Vehicle Name: ").strip(),
        "model": input("Model: ").strip(),
        "year": None,
        "license_plate": input("License Plate (optional): ").strip() or None,
        "color": input("Color (optional): ").strip() or None,
        "seating_capacity": None,
        "status": "available"
    }
    
    # Optional fields
    year_input = input("Year (optional): ").strip()
    if year_input:
        try:
            vehicle_data["year"] = int(year_input)
        except ValueError:
            print("⚠️  Invalid year, skipping...")
    
    capacity_input = input("Seating Capacity (optional): ").strip()
    if capacity_input:
        try:
            vehicle_data["seating_capacity"] = int(capacity_input)
        except ValueError:
            print("⚠️  Invalid capacity, skipping...")
    
    try:
        result = api.add_vehicle(vehicle_data)
        print(f"✅ Vehicle added successfully!")
        print(f"Vehicle ID: {result['id']}")
        print(f"Name: {result['name']} - {result['model']}")
    except Exception as e:
        print(f"❌ Failed to add vehicle: {e}")

def view_vehicles_flow(api: RideBookingAPI):
    print("\n🚗 Available Vehicles")
    print("-" * 30)
    
    if not api.access_token:
        print("❌ Please login first!")
        return
    
    try:
        vehicles = api.get_vehicles()
        if not vehicles:
            print("📭 No vehicles found.")
            return
        
        for vehicle in vehicles:
            print(f"ID: {vehicle['id']} | Name: {vehicle['name']} | Model: {vehicle['model']}")
            print(f"  Status: {vehicle['status']} | Capacity: {vehicle.get('seating_capacity', 'N/A')}")
            print(f"  License: {vehicle.get('license_plate', 'N/A')} | Color: {vehicle.get('color', 'N/A')}")
            print("-" * 50)
    except Exception as e:
        print(f"❌ Failed to get vehicles: {e}")

def book_ride_flow(api: RideBookingAPI):
    print("\n📅 Book a Ride")
    print("-" * 30)
    
    if not api.access_token:
        print("❌ Please login first!")
        return
    
    if api.current_user and api.current_user.get("role") != "rider":
        print("❌ Only riders can book rides!")
        return
    
    try:
        driver_id = int(input("Driver ID: ").strip())
        vehicle_id = int(input("Vehicle ID: ").strip())
    except ValueError:
        print("❌ Invalid ID format!")
        return
    
    print("\nService Types:")
    print("1. airport")
    print("2. hourly") 
    print("3. dropoff")
    
    service_choice = input("Select service type (1-3): ").strip()
    service_map = {"1": "airport", "2": "hourly", "3": "dropoff"}
    
    if service_choice not in service_map:
        print("❌ Invalid service type!")
        return
    
    service_type = service_map[service_choice]
    
    print("\nPayment Methods:")
    print("1. cash")
    print("2. card")
    
    payment_choice = input("Select payment method (1-2): ").strip()
    payment_map = {"1": "cash", "2": "card"}
    
    if payment_choice not in payment_map:
        print("❌ Invalid payment method!")
        return
    
    payment_method = payment_map[payment_choice]
    
    # Get booking details
    pickup_location = input("Pickup Location: ").strip()
    dropoff_location = input("Dropoff Location (optional for airport): ").strip() or None
    city = input("City: ").strip()
    notes = input("Notes: ").strip()
    
    # Time input
    print("\nPickup Time (format: YYYY-MM-DD HH:MM):")
    pickup_time_str = input("Pickup Time: ").strip()
    
    dropoff_time_str = None
    if service_type != "airport":
        dropoff_time_str = input("Dropoff Time (optional): ").strip() or None
    
    try:
        pickup_time = datetime.strptime(pickup_time_str, "%Y-%m-%d %H:%M")
        dropoff_time = None
        if dropoff_time_str:
            dropoff_time = datetime.strptime(dropoff_time_str, "%Y-%m-%d %H:%M")
        else:
            # Default to 1 hour later
            dropoff_time = pickup_time + timedelta(hours=1)
    except ValueError:
        print("❌ Invalid time format! Use YYYY-MM-DD HH:MM")
        return
    
    booking_data = {
        "driver_id": driver_id,
        "vehicle_id": vehicle_id,
        "service_type": service_type,
        "pickup_location": pickup_location,
        "pickup_time": pickup_time.isoformat(),
        "dropoff_location": dropoff_location,
        "dropoff_time": dropoff_time.isoformat(),
        "payment_method": payment_method,
        "city": city,
        "notes": notes
    }
    
    try:
        result = api.book_ride(booking_data)
        print(f"✅ Ride booked successfully!")
        print(f"Booking ID: {result['id']}")
        print(f"Service: {result['service_type']}")
        print(f"Pickup: {result['pickup_location']} at {result['pickup_time']}")
        print(f"Status: {result['booking_status']}")
    except Exception as e:
        print(f"❌ Failed to book ride: {e}")

def view_bookings_flow(api: RideBookingAPI):
    print("\n📋 Your Bookings")
    print("-" * 30)
    
    if not api.access_token:
        print("❌ Please login first!")
        return
    
    try:
        bookings = api.get_bookings()
        if not bookings:
            print("📭 No bookings found.")
            return
        
        for booking in bookings:
            print(f"ID: {booking['id']} | Service: {booking['service_type']}")
            print(f"  Pickup: {booking['pickup_location']} at {booking['pickup_time']}")
            print(f"  Dropoff: {booking.get('dropoff_location', 'N/A')} at {booking.get('dropoff_time', 'N/A')}")
            print(f"  Status: {booking['booking_status']} | Payment: {booking['payment_method']}")
            print(f"  Price: ${booking.get('estimated_price', 'N/A')}")
            print("-" * 50)
    except Exception as e:
        print(f"❌ Failed to get bookings: {e}")

def view_tenant_drivers_flow(api: RideBookingAPI):
    print("\n👥 Tenant Drivers")
    print("-" * 30)
    
    if not api.access_token:
        print("❌ Please login first!")
        return
    
    if api.current_user and api.current_user.get("role") != "tenant":
        print("❌ Only tenants can view their drivers!")
        return
    
    try:
        drivers = api.get_tenant_drivers()
        if not drivers:
            print("📭 No drivers found.")
            return
        
        for driver in drivers:
            print(f"ID: {driver['id']} | Name: {driver['first_name']} {driver['last_name']}")
            print(f"  Email: {driver['email']} | Phone: {driver['phone_no']}")
            print(f"  Status: {driver['status']} | Completed Rides: {driver['completed_rides']}")
            print(f"  Active: {driver['is_active']}")
            print("-" * 50)
    except Exception as e:
        print(f"❌ Failed to get drivers: {e}")

def main():
    print("🚀 Welcome to the Ride Booking System CLI!")
    print("This tool helps you test your FastAPI backend.")
    
    base_url = input("Enter API base URL (default: http://localhost:8000): ").strip()
    if not base_url:
        base_url = "http://localhost:8000"
    
    api = RideBookingAPI(base_url)
    
    while True:
        display_menu()
        
        if api.current_user:
            print(f"👤 Logged in as: {api.current_user['email']} ({api.current_user['role']})")
        
        try:
            choice = input("Enter your choice (1-11): ").strip()
            
            if choice == '1':
                login_flow(api)
            elif choice == '2':
                create_tenant_flow(api)
            elif choice == '3':
                create_user_flow(api)
            elif choice == '4':
                create_driver_flow(api)
            elif choice == '5':
                add_vehicle_flow(api)
            elif choice == '6':
                view_vehicles_flow(api)
            elif choice == '7':
                book_ride_flow(api)
            elif choice == '8':
                view_bookings_flow(api)
            elif choice == '9':
                view_tenant_drivers_flow(api)
            elif choice == '10':
                api.access_token = None
                api.current_user = None
                api.session.headers.pop("Authorization", None)
                print("✅ Logged out successfully!")
            elif choice == '11':
                print("\n👋 Thank you for using the Ride Booking System CLI!")
                break
            else:
                print("❌ Invalid choice! Please enter 1-11.")
                
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ An error occurred: {e}")
        
        # Pause before showing menu again
        input("\nPress Enter to continue...")

if __name__ == "__main__":
    main()