import { Tabs } from 'expo-router';

export default function TabLayout() {
  return (
    <Tabs screenOptions={{ tabBarActiveTintColor: '#E50914' }}>
      <Tabs.Screen name="index" options={{ title: 'Film Oggi' }} />
      <Tabs.Screen name="cinema" options={{ title: 'Cinema' }} />
    </Tabs>
  );
}
