import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  StatusBar,
  RefreshControl,
  Alert,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { useAuth } from '../../contexts/AuthContext';
import { useTheme } from '../../contexts/ThemeContext';
import apiService from '../../services/api';

interface Ride {
  id: string;
  pickup_location: string;
  dropoff_location: string;
  status: string;
  rider_name: string;
  estimated_fare: number;
  created_at: string;
  vehicle_category?: string;
}

export default function DriverDashboard() {
  const [availableRides, setAvailableRides] = useState<Ride[]>([]);
  const [activeRide, setActiveRide] = useState<Ride | null>(null);
  const [isOnline, setIsOnline] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  const navigation = useNavigation();
  const { user, logout } = useAuth();
  const { colors } = useTheme();

  useEffect(() => {
    if (isOnline) {
      loadAvailableRides();
      const interval = setInterval(loadAvailableRides, 30000); // Refresh every 30 seconds
      return () => clearInterval(interval);
    }
  }, [isOnline]);

  const loadAvailableRides = async () => {
    try {
      const response = await apiService.getAvailableRides();
      setAvailableRides(response.data || []);
    } catch (error) {
      console.error('Error loading available rides:', error);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await loadAvailableRides();
    setRefreshing(false);
  };

  const toggleOnlineStatus = () => {
    setIsOnline(!isOnline);
    if (!isOnline) {
      loadAvailableRides();
    } else {
      setAvailableRides([]);
    }
  };

  const handleAcceptRide = async (ride: Ride) => {
    try {
      setIsLoading(true);
      await apiService.acceptRide(ride.id);
      setActiveRide(ride);
      setAvailableRides(prev => prev.filter(r => r.id !== ride.id));
      Alert.alert('Success', 'Ride accepted! Navigate to pickup location.');
    } catch (error: any) {
      Alert.alert('Error', error.response?.data?.detail || 'Failed to accept ride');
    } finally {
      setIsLoading(false);
    }
  };

  const handleStartRide = async () => {
    if (!activeRide) return;
    
    try {
      setIsLoading(true);
      await apiService.startRide(activeRide.id);
      Alert.alert('Ride Started', 'You can now begin the trip.');
    } catch (error: any) {
      Alert.alert('Error', error.response?.data?.detail || 'Failed to start ride');
    } finally {
      setIsLoading(false);
    }
  };

  const handleCompleteRide = async () => {
    if (!activeRide) return;
    
    try {
      setIsLoading(true);
      await apiService.completeRide(activeRide.id);
      setActiveRide(null);
      Alert.alert('Ride Completed', 'Thank you for the safe ride!');
    } catch (error: any) {
      Alert.alert('Error', error.response?.data?.detail || 'Failed to complete ride');
    } finally {
      setIsLoading(false);
    }
  };

  const handleProfile = () => {
    navigation.navigate('Profile' as never);
  };

  const handleLogout = async () => {
    await logout();
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString();
  };

  return (
    <View style={[styles.container, { backgroundColor: colors.background }]}>
      <StatusBar
        barStyle={colors.background === '#000000' ? 'light-content' : 'dark-content'}
        backgroundColor={colors.background}
      />
      
      {/* Header */}
      <View style={[styles.header, { backgroundColor: colors.surface }]}>
        <View style={styles.headerContent}>
          <View>
            <Text style={[styles.greeting, { color: colors.textSecondary }]}>
              Welcome back,
            </Text>
            <Text style={[styles.userName, { color: colors.text }]}>
              {user?.firstName} {user?.lastName}
            </Text>
          </View>
          <TouchableOpacity onPress={handleProfile} style={styles.profileButton}>
            <View style={[styles.avatar, { backgroundColor: colors.primary }]}>
              <Text style={[styles.avatarText, { color: colors.background }]}>
                {user?.firstName?.[0]}{user?.lastName?.[0]}
              </Text>
            </View>
          </TouchableOpacity>
        </View>
      </View>

      <ScrollView
        style={styles.content}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
      >
        {/* Online Status Toggle */}
        <View style={styles.section}>
          <TouchableOpacity
            style={[
              styles.onlineToggle,
              {
                backgroundColor: isOnline ? colors.success : colors.error,
              },
            ]}
            onPress={toggleOnlineStatus}
          >
            <Text style={[styles.onlineToggleText, { color: colors.background }]}>
              {isOnline ? '🟢 Online' : '🔴 Offline'}
            </Text>
          </TouchableOpacity>
        </View>

        {/* Active Ride */}
        {activeRide && (
          <View style={styles.section}>
            <Text style={[styles.sectionTitle, { color: colors.text }]}>
              Active Ride
            </Text>
            <View style={[styles.activeRideCard, { backgroundColor: colors.primary }]}>
              <Text style={[styles.activeRideTitle, { color: colors.background }]}>
                🚗 Active Trip
              </Text>
              <Text style={[styles.activeRideLocation, { color: colors.background }]}>
                {activeRide.pickup_location} → {activeRide.dropoff_location}
              </Text>
              <Text style={[styles.activeRideRider, { color: colors.background }]}>
                Rider: {activeRide.rider_name}
              </Text>
              <Text style={[styles.activeRideFare, { color: colors.background }]}>
                Fare: ${activeRide.estimated_fare}
              </Text>
              
              <View style={styles.activeRideActions}>
                <TouchableOpacity
                  style={[styles.rideActionButton, { backgroundColor: colors.background }]}
                  onPress={handleStartRide}
                  disabled={isLoading}
                >
                  <Text style={[styles.rideActionButtonText, { color: colors.primary }]}>
                    Start Ride
                  </Text>
                </TouchableOpacity>
                
                <TouchableOpacity
                  style={[styles.rideActionButton, { backgroundColor: colors.background }]}
                  onPress={handleCompleteRide}
                  disabled={isLoading}
                >
                  <Text style={[styles.rideActionButtonText, { color: colors.primary }]}>
                    Complete Ride
                  </Text>
                </TouchableOpacity>
              </View>
            </View>
          </View>
        )}

        {/* Available Rides */}
        {isOnline && (
          <View style={styles.section}>
            <Text style={[styles.sectionTitle, { color: colors.text }]}>
              Available Rides
            </Text>
            
            {availableRides.length === 0 ? (
              <View style={[styles.emptyState, { backgroundColor: colors.surface }]}>
                <Text style={[styles.emptyStateText, { color: colors.textSecondary }]}>
                  No rides available
                </Text>
                <Text style={[styles.emptyStateSubtext, { color: colors.textSecondary }]}>
                  Stay online to receive ride requests
                </Text>
              </View>
            ) : (
              availableRides.map((ride) => (
                <View
                  key={ride.id}
                  style={[styles.rideCard, { backgroundColor: colors.surface }]}
                >
                  <View style={styles.rideHeader}>
                    <Text style={[styles.rideLocation, { color: colors.text }]}>
                      {ride.pickup_location} → {ride.dropoff_location}
                    </Text>
                    <Text style={[styles.rideFare, { color: colors.primary }]}>
                      ${ride.estimated_fare}
                    </Text>
                  </View>
                  
                  <View style={styles.rideDetails}>
                    <Text style={[styles.rideRider, { color: colors.textSecondary }]}>
                      Rider: {ride.rider_name}
                    </Text>
                    <Text style={[styles.rideDate, { color: colors.textSecondary }]}>
                      {formatDate(ride.created_at)}
                    </Text>
                  </View>
                  
                  <TouchableOpacity
                    style={[styles.acceptButton, { backgroundColor: colors.success }]}
                    onPress={() => handleAcceptRide(ride)}
                    disabled={isLoading}
                  >
                    <Text style={[styles.acceptButtonText, { color: colors.background }]}>
                      Accept Ride
                    </Text>
                  </TouchableOpacity>
                </View>
              ))
            )}
          </View>
        )}

        {/* Settings & Logout */}
        <View style={styles.section}>
          <TouchableOpacity
            style={[styles.settingButton, { backgroundColor: colors.surface }]}
            onPress={() => navigation.navigate('Settings' as never)}
          >
            <Text style={[styles.settingButtonText, { color: colors.text }]}>
              Settings
            </Text>
          </TouchableOpacity>
          
          <TouchableOpacity
            style={[styles.logoutButton, { backgroundColor: colors.error }]}
            onPress={handleLogout}
          >
            <Text style={[styles.logoutButtonText, { color: colors.background }]}>
              Logout
            </Text>
          </TouchableOpacity>
        </View>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  header: {
    paddingTop: 60,
    paddingBottom: 20,
    paddingHorizontal: 20,
  },
  headerContent: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  greeting: {
    fontSize: 14,
    marginBottom: 4,
  },
  userName: {
    fontSize: 24,
    fontWeight: 'bold',
  },
  profileButton: {
    padding: 8,
  },
  avatar: {
    width: 40,
    height: 40,
    borderRadius: 20,
    justifyContent: 'center',
    alignItems: 'center',
  },
  avatarText: {
    fontSize: 16,
    fontWeight: 'bold',
  },
  content: {
    flex: 1,
    paddingHorizontal: 20,
  },
  section: {
    marginBottom: 32,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    marginBottom: 16,
  },
  onlineToggle: {
    height: 50,
    borderRadius: 8,
    justifyContent: 'center',
    alignItems: 'center',
  },
  onlineToggleText: {
    fontSize: 16,
    fontWeight: '600',
  },
  activeRideCard: {
    padding: 20,
    borderRadius: 12,
  },
  activeRideTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 12,
    textAlign: 'center',
  },
  activeRideLocation: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 8,
    textAlign: 'center',
  },
  activeRideRider: {
    fontSize: 14,
    marginBottom: 4,
    textAlign: 'center',
  },
  activeRideFare: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 16,
    textAlign: 'center',
  },
  activeRideActions: {
    flexDirection: 'row',
    gap: 12,
  },
  rideActionButton: {
    flex: 1,
    height: 40,
    borderRadius: 8,
    justifyContent: 'center',
    alignItems: 'center',
  },
  rideActionButtonText: {
    fontSize: 14,
    fontWeight: '600',
  },
  emptyState: {
    padding: 32,
    borderRadius: 8,
    alignItems: 'center',
  },
  emptyStateText: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 8,
  },
  emptyStateSubtext: {
    fontSize: 14,
    textAlign: 'center',
  },
  rideCard: {
    padding: 16,
    borderRadius: 8,
    marginBottom: 12,
  },
  rideHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  rideLocation: {
    fontSize: 16,
    fontWeight: '600',
    flex: 1,
    marginRight: 12,
  },
  rideFare: {
    fontSize: 18,
    fontWeight: 'bold',
  },
  rideDetails: {
    marginBottom: 16,
  },
  rideRider: {
    fontSize: 14,
    marginBottom: 4,
  },
  rideDate: {
    fontSize: 14,
  },
  acceptButton: {
    height: 40,
    borderRadius: 8,
    justifyContent: 'center',
    alignItems: 'center',
  },
  acceptButtonText: {
    fontSize: 14,
    fontWeight: '600',
  },
  settingButton: {
    height: 50,
    borderRadius: 8,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 12,
  },
  settingButtonText: {
    fontSize: 16,
    fontWeight: '600',
  },
  logoutButton: {
    height: 50,
    borderRadius: 8,
    justifyContent: 'center',
    alignItems: 'center',
  },
  logoutButtonText: {
    fontSize: 16,
    fontWeight: '600',
  },
}); 