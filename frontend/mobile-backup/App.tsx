import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createStackNavigator } from '@react-navigation/stack';
import { Provider as PaperProvider } from 'react-native-paper';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { GestureHandlerRootView } from 'react-native-gesture-handler';

// Contexts
import { AuthProvider } from './src/contexts/AuthContext';
import { ThemeProvider } from './src/contexts/ThemeContext';

// Screens
import SplashScreen from './src/screens/SplashScreen';
import LoginScreen from './src/screens/auth/LoginScreen';
import SignupScreen from './src/screens/auth/SignupScreen';
import RiderDashboard from './src/screens/rider/RiderDashboard';
import DriverDashboard from './src/screens/driver/DriverDashboard';
import BookingScreen from './src/screens/rider/BookingScreen';
import RideHistoryScreen from './src/screens/rider/RideHistoryScreen';
import ProfileScreen from './src/screens/common/ProfileScreen';
import SettingsScreen from './src/screens/common/SettingsScreen';

// Navigation Types
export type RootStackParamList = {
  Splash: undefined;
  Login: undefined;
  Signup: undefined;
  RiderDashboard: undefined;
  DriverDashboard: undefined;
  Booking: undefined;
  RideHistory: undefined;
  Profile: undefined;
  Settings: undefined;
};

const Stack = createStackNavigator<RootStackParamList>();

export default function App() {
  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <SafeAreaProvider>
        <PaperProvider>
          <ThemeProvider>
            <AuthProvider>
              <NavigationContainer>
                <Stack.Navigator
                  initialRouteName="Splash"
                  screenOptions={{
                    headerShown: false,
                    gestureEnabled: true,
                  }}
                >
                  <Stack.Screen name="Splash" component={SplashScreen} />
                  <Stack.Screen name="Login" component={LoginScreen} />
                  <Stack.Screen name="Signup" component={SignupScreen} />
                  <Stack.Screen name="RiderDashboard" component={RiderDashboard} />
                  <Stack.Screen name="DriverDashboard" component={DriverDashboard} />
                  <Stack.Screen name="Booking" component={BookingScreen} />
                  <Stack.Screen name="RideHistory" component={RideHistoryScreen} />
                  <Stack.Screen name="Profile" component={ProfileScreen} />
                  <Stack.Screen name="Settings" component={SettingsScreen} />
                </Stack.Navigator>
              </NavigationContainer>
            </AuthProvider>
          </ThemeProvider>
        </PaperProvider>
      </SafeAreaProvider>
    </GestureHandlerRootView>
  );
} 