// Splash screen d'avvio: animazione del logo (zoom-in, pausa, zoom-out + fade).
import React, { useEffect, useRef } from 'react';
import { Animated, StyleSheet, Image } from 'react-native';
import Colors from '../constants/colors';

export default function SplashScreen({ onAnimationEnd }) {
  const scale = useRef(new Animated.Value(0.3)).current;
  const opacity = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    Animated.sequence([
      // Zoom in
      Animated.parallel([
        Animated.spring(scale, {
          toValue: 1,
          tension: 40,
          friction: 7,
          useNativeDriver: true,
        }),
        Animated.timing(opacity, {
          toValue: 1,
          duration: 500,
          useNativeDriver: true,
        }),
      ]),
      // Pausa
      Animated.delay(1200),
      // Zoom out + fade out
      Animated.parallel([
        Animated.timing(scale, {
          toValue: 1.5,
          duration: 500,
          useNativeDriver: true,
        }),
        Animated.timing(opacity, {
          toValue: 0,
          duration: 500,
          useNativeDriver: true,
        }),
      ]),
    ]).start(() => onAnimationEnd());
  }, []);

  return (
    <Animated.View style={[styles.container, { opacity }]}>
      <Animated.Image
        source={require('../../assets/logo.png')}
        style={[styles.logo, { transform: [{ scale }] }]}
        resizeMode="contain"
      />
    </Animated.View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
    justifyContent: 'center',
    alignItems: 'center',
  },
  logo: {
    width: 240,
    height: 80,
  },
});
