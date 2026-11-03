import React from 'react';
import { NavigationContainer, DefaultTheme } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { SafeAreaProvider } from 'react-native-safe-area-context';

import HomeScreen    from './src/screens/HomeScreen';
import DetalleScreen from './src/screens/DetalleScreen';
import ChatScreen    from './src/screens/ChatScreen';
import EmpresasScreen from './src/screens/EmpresasScreen';

const Stack = createNativeStackNavigator();

const Theme = {
  ...DefaultTheme,
  colors: { ...DefaultTheme.colors, background: '#0d1117', card: '#0d1117', border: '#2d3748', text: '#e2e8f0' },
};

export default function App() {
  return (
    <SafeAreaProvider>
      <NavigationContainer theme={Theme}>
        <Stack.Navigator screenOptions={{ headerShown: false }}>
          <Stack.Screen name="Home"     component={HomeScreen} />
          <Stack.Screen name="Detalle"  component={DetalleScreen} />
          <Stack.Screen name="Chat"     component={ChatScreen} />
          <Stack.Screen name="Empresas" component={EmpresasScreen} options={{ presentation: 'modal' }} />
        </Stack.Navigator>
      </NavigationContainer>
    </SafeAreaProvider>
  );
}
