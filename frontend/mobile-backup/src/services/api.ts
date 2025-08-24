import axios, { AxiosInstance, AxiosResponse } from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';

const API_BASE_URL = 'http://localhost:8000'; // Change this to your backend URL

class ApiService {
  private api: AxiosInstance;

  constructor() {
    this.api = axios.create({
      baseURL: API_BASE_URL,
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor to add auth token
    this.api.interceptors.request.use(
      async (config) => {
        const token = await AsyncStorage.getItem('accessToken');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // Response interceptor to handle auth errors
    this.api.interceptors.response.use(
      (response: AxiosResponse) => response,
      async (error) => {
        if (error.response?.status === 401) {
          // Token expired or invalid, clear storage and redirect to login
          await AsyncStorage.multiRemove(['accessToken', 'user']);
          // You might want to trigger a navigation to login here
        }
        return Promise.reject(error);
      }
    );
  }

  // Auth endpoints
  async login(email: string, password: string) {
    const response = await this.api.post('/v1/auth/login', { email, password });
    return response.data;
  }

  async signup(userData: {
    email: string;
    password: string;
    first_name: string;
    last_name: string;
    role: string;
  }) {
    const response = await this.api.post('/v1/auth/signup', userData);
    return response.data;
  }

  // Rider endpoints
  async getRiderProfile() {
    const response = await this.api.get('/v1/rider/profile');
    return response.data;
  }

  async updateRiderProfile(profileData: any) {
    const response = await this.api.patch('/v1/rider/profile', profileData);
    return response.data;
  }

  async createBooking(bookingData: {
    pickup_location: string;
    dropoff_location: string;
    vehicle_category?: string;
    notes?: string;
  }) {
    const response = await this.api.post('/v1/rider/bookings', bookingData);
    return response.data;
  }

  async getRiderBookings() {
    const response = await this.api.get('/v1/rider/bookings');
    return response.data;
  }

  async cancelBooking(bookingId: string) {
    const response = await this.api.patch(`/v1/rider/bookings/${bookingId}/cancel`);
    return response.data;
  }

  // Driver endpoints
  async getDriverProfile() {
    const response = await this.api.get('/v1/driver/profile');
    return response.data;
  }

  async updateDriverProfile(profileData: any) {
    const response = await this.api.patch('/v1/driver/profile', profileData);
    return response.data;
  }

  async getAvailableRides() {
    const response = await this.api.get('/v1/driver/rides/available');
    return response.data;
  }

  async acceptRide(rideId: string) {
    const response = await this.api.patch(`/v1/driver/rides/${rideId}/accept`);
    return response.data;
  }

  async rejectRide(rideId: string) {
    const response = await this.api.patch(`/v1/driver/rides/${rideId}/reject`);
    return response.data;
  }

  async startRide(rideId: string) {
    const response = await this.api.patch(`/v1/driver/rides/${rideId}/start`);
    return response.data;
  }

  async completeRide(rideId: string) {
    const response = await this.api.patch(`/v1/driver/rides/${rideId}/complete`);
    return response.data;
  }

  async updateDriverLocation(location: { latitude: number; longitude: number }) {
    const response = await this.api.patch('/v1/driver/location', location);
    return response.data;
  }

  // Common endpoints
  async getVehicleCategories() {
    const response = await this.api.get('/v1/vehicles/categories');
    return response.data;
  }

  async getVehicleRates() {
    const response = await this.api.get('/v1/vehicles/rates');
    return response.data;
  }
}

export const apiService = new ApiService();
export default apiService; 