import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  StatusBar,
  RefreshControl,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { useAuth } from '../../contexts/AuthContext';
import { useTheme } from '../../contexts/ThemeContext';
import apiService from '../../services/api';

interface Booking {
  id: string;
  pickup_location: string;
  dropoff_location: string;
  status: string;
  created_at: string;
  vehicle_category?: string;
  driver_name?: string;
  estimated_fare?: number;
}

export default function RiderDashboard() {
  const [bookings, setBookings] = useState<Booking[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  const navigation = useNavigation();
  const { user, logout } = useAuth();
  const { colors } = useTheme();

  useEffect(() => {
    loadBookings();
  }, []);

  const loadBookings = async () => {
    try {
      setIsLoading(true);
      const response = await apiService.getRiderBookings();
      setBookings(response.data || []);
    } catch (error) {
      console.error('Error loading bookings:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await loadBookings();
    setRefreshing(false);
  };

  const handleNewBooking = () => {
    navigation.navigate('Booking' as never);
  };

  const handleViewHistory = () => {
    navigation.navigate('RideHistory' as never);
  };

  const handleProfile = () => {
    navigation.navigate('Profile' as never);
  };

  const handleLogout = async () => {
    await logout();
  };

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'completed':
        return colors.success;
      case 'active':
        return colors.primary;
      case 'pending':
        return colors.warning;
      case 'cancelled':
        return colors.error;
      default:
        return colors.textSecondary;
    }
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
        {/* Quick Actions */}
        <View style={styles.section}>
          <Text style={[styles.sectionTitle, { color: colors.text }]}>
            Quick Actions
          </Text>
          <View style={styles.quickActions}>
            <TouchableOpacity
              style={[styles.actionButton, { backgroundColor: colors.primary }]}
              onPress={handleNewBooking}
            >
              <Text style={[styles.actionButtonText, { color: colors.background }]}>
                Book a Ride
              </Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[styles.actionButton, { backgroundColor: colors.surface, borderColor: colors.border }]}
              onPress={handleViewHistory}
            >
              <Text style={[styles.actionButtonText, { color: colors.text }]}>
                Ride History
              </Text>
            </TouchableOpacity>
          </View>
        </View>

        {/* Recent Bookings */}
        <View style={styles.section}>
          <View style={styles.sectionHeader}>
            <Text style={[styles.sectionTitle, { color: colors.text }]}>
              Recent Bookings
            </Text>
            <TouchableOpacity onPress={handleViewHistory}>
              <Text style={[styles.viewAllText, { color: colors.primary }]}>
                View All
              </Text>
            </TouchableOpacity>
          </View>

          {bookings.length === 0 ? (
            <View style={[styles.emptyState, { backgroundColor: colors.surface }]}>
              <Text style={[styles.emptyStateText, { color: colors.textSecondary }]}>
                No bookings yet
              </Text>
              <Text style={[styles.emptyStateSubtext, { color: colors.textSecondary }]}>
                Book your first ride to get started
              </Text>
            </View>
          ) : (
            bookings.slice(0, 3).map((booking) => (
              <View
                key={booking.id}
                style={[styles.bookingCard, { backgroundColor: colors.surface }]}
              >
                <View style={styles.bookingHeader}>
                  <View style={styles.bookingInfo}>
                    <Text style={[styles.bookingLocation, { color: colors.text }]}>
                      {booking.pickup_location} → {booking.dropoff_location}
                    </Text>
                    <Text style={[styles.bookingDate, { color: colors.textSecondary }]}>
                      {formatDate(booking.created_at)}
                    </Text>
                  </View>
                  <View
                    style={[
                      styles.statusBadge,
                      { backgroundColor: getStatusColor(booking.status) },
                    ]}
                  >
                    <Text style={[styles.statusText, { color: colors.background }]}>
                      {booking.status}
                    </Text>
                  </View>
                </View>
                {booking.estimated_fare && (
                  <Text style={[styles.estimatedFare, { color: colors.primary }]}>
                    Estimated: ${booking.estimated_fare}
                  </Text>
                )}
              </View>
            ))
          )}
        </View>

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
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: 'bold',
  },
  viewAllText: {
    fontSize: 14,
    fontWeight: '600',
  },
  quickActions: {
    flexDirection: 'row',
    gap: 12,
  },
  actionButton: {
    flex: 1,
    height: 50,
    borderRadius: 8,
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 1,
  },
  actionButtonText: {
    fontSize: 16,
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
  bookingCard: {
    padding: 16,
    borderRadius: 8,
    marginBottom: 12,
  },
  bookingHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 8,
  },
  bookingInfo: {
    flex: 1,
    marginRight: 12,
  },
  bookingLocation: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 4,
  },
  bookingDate: {
    fontSize: 14,
  },
  statusBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
  },
  statusText: {
    fontSize: 12,
    fontWeight: '600',
    textTransform: 'uppercase',
  },
  estimatedFare: {
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