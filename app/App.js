// Root dell'app: splash iniziale + navigazione. Bottom-tab (Films, Cerca,
// Località) con stack annidati per Films e Cerca, così il dettaglio film si
// apre mantenendo la barra di navigazione visibile.
import React, { useState } from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import SplashScreen from './src/components/SplashScreen';
import FilmsTab from './src/screens/FilmsTab';
import SearchTab from './src/screens/SearchTab';
import LocationTab from './src/screens/LocationTab';
import MovieDetailScreen from './src/screens/MovieDetailScreen';
import Colors from './src/constants/colors';

const Stack = createNativeStackNavigator();
const Tab = createBottomTabNavigator();

const stackScreenOptions = {
  headerShown: false,
  contentStyle: { backgroundColor: Colors.background },
  animation: 'slide_from_right',
};

// Films e Cerca sono piccoli stack (lista → dettaglio) DENTRO le tab:
// così il dettaglio film si apre con la barra di navigazione sempre visibile.
function FilmsStack() {
  return (
    <Stack.Navigator screenOptions={stackScreenOptions}>
      <Stack.Screen name="FilmsHome" component={FilmsTab} />
      <Stack.Screen name="MovieDetail" component={MovieDetailScreen} />
    </Stack.Navigator>
  );
}

function SearchStack() {
  return (
    <Stack.Navigator screenOptions={stackScreenOptions}>
      <Stack.Screen name="SearchHome" component={SearchTab} />
      <Stack.Screen name="MovieDetail" component={MovieDetailScreen} />
    </Stack.Navigator>
  );
}

function HomeTabs() {
  return (
    <Tab.Navigator
      screenOptions={({ route }) => ({
        headerShown: false,
        tabBarStyle: {
          backgroundColor: Colors.surface,
          borderTopColor: Colors.card,
          paddingBottom: 8,
          paddingTop: 6,
          height: 70,
        },
        tabBarLabelStyle: {
          fontSize: 11,
          fontWeight: '600',
        },
        tabBarActiveTintColor: Colors.primary,
        tabBarInactiveTintColor: Colors.gray,
        tabBarIcon: ({ focused, color, size }) => {
          let iconName;
          if (route.name === 'Films') {
            iconName = focused ? 'film' : 'film-outline';
          } else if (route.name === 'Cerca') {
            iconName = focused ? 'search' : 'search-outline';
          } else if (route.name === 'Località') {
            iconName = focused ? 'map' : 'map-outline';
          }
          return <Ionicons name={iconName} size={size} color={color} />;
        },
      })}
    >
      <Tab.Screen
        name="Films"
        component={FilmsStack}
        options={{ tabBarLabel: 'Films' }}
      />
      <Tab.Screen
        name="Cerca"
        component={SearchStack}
        options={{ tabBarLabel: 'Cerca' }}
      />
      <Tab.Screen
        name="Località"
        component={LocationTab}
        options={{ tabBarLabel: 'Località' }}
      />
    </Tab.Navigator>
  );
}

export default function App() {
  const [showSplash, setShowSplash] = useState(true);

  if (showSplash) {
    return <SplashScreen onAnimationEnd={() => setShowSplash(false)} />;
  }

  return (
    <SafeAreaProvider>
      <NavigationContainer>
        <HomeTabs />
      </NavigationContainer>
    </SafeAreaProvider>
  );
}
