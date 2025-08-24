import React, { useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Image,
  Dimensions,
  StatusBar,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { useAuth } from '../contexts/AuthContext';
import { useTheme } from '../contexts/ThemeContext';

const { width, height } = Dimensions.get('window');

export default function SplashScreen() {
  const navigation = useNavigation();
  const { isAuthenticated, isLoading, user } = useAuth();
  const { colors } = useTheme();

  useEffect(() => {
    const timer = setTimeout(() => {
      if (!isLoading) {
        if (isAuthenticated && user) {
          // Navigate based on user role
          if (user.role === 'rider') {
            navigation.replace('RiderDashboard' as never);
          } else if (user.role === 'driver') {
            navigation.replace('DriverDashboard' as never);
          } else {
            navigation.replace('Login' as never);
          }
        } else {
          navigation.replace('Login' as never);
        }
      }
    }, 2000);

    return () => clearTimeout(timer);
  }, [isLoading, isAuthenticated, user, navigation]);

  return (
    <View style={[styles.container, { backgroundColor: colors.background }]}>
      <StatusBar
        barStyle={colors.background === '#000000' ? 'light-content' : 'dark-content'}
        backgroundColor={colors.background}
      />
      
      <View style={styles.logoContainer}>
        <View style={[styles.logo, { backgroundColor: colors.primary }]}>
          <Text style={[styles.logoText, { color: colors.background }]}>M</Text>
        </View>
        <Text style={[styles.appName, { color: colors.text }]}>Maison</Text>
        <Text style={[styles.tagline, { color: colors.textSecondary }]}>
          Your Premium Transportation Partner
        </Text>
      </View>

      <View style={styles.loadingContainer}>
        <View style={[styles.loadingDot, { backgroundColor: colors.primary }]} />
        <View style={[styles.loadingDot, { backgroundColor: colors.primary }]} />
        <View style={[styles.loadingDot, { backgroundColor: colors.primary }]} />
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  logoContainer: {
    alignItems: 'center',
    marginBottom: 80,
  },
  logo: {
    width: 80,
    height: 80,
    borderRadius: 40,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 20,
  },
  logoText: {
    fontSize: 40,
    fontWeight: 'bold',
  },
  appName: {
    fontSize: 32,
    fontWeight: 'bold',
    marginBottom: 10,
  },
  tagline: {
    fontSize: 16,
    textAlign: 'center',
    paddingHorizontal: 40,
  },
  loadingContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  loadingDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginHorizontal: 4,
    opacity: 0.6,
  },
}); 