// Schermata "Località": mappa Leaflet dei cinema + elenco con indirizzi,
// ognuno apribile in Google Maps.
import React, { useState, useEffect } from 'react';
import { View, Text, Image, StyleSheet, StatusBar, Linking, TouchableOpacity, Platform } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { Asset } from 'expo-asset';
import CinemaMap from '../components/CinemaMap';
import Colors from '../constants/colors';
import CINEMAS from '../constants/cinemas';

// Converte il logo in data URI per incorporarlo nell'HTML della mappa.
// Usa fetch + FileReader (funzionano su iOS, Android e web) invece di
// expo-file-system, le cui funzioni legacy non esistono più in SDK 54.
// Il FileReader imposta da solo il MIME type corretto.
async function assetToDataUri(assetModule) {
  const asset = Asset.fromModule(assetModule);
  await asset.downloadAsync().catch(() => {});
  const uri = asset.localUri || asset.uri;
  try {
    const blob = await (await fetch(uri)).blob();
    return await new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onloadend = () => resolve(reader.result);
      reader.onerror = reject;
      reader.readAsDataURL(blob);
    });
  } catch {
    return uri;
  }
}

export default function LocationTab() {
  const [cinemas, setCinemas] = useState([]);

  useEffect(() => {
    (async () => {
      const loaded = await Promise.all(
        CINEMAS.map(async (c) => ({
          ...c,
          logoDataUri: await assetToDataUri(c.logo),
        }))
      );
      setCinemas(loaded);
    })();
  }, []);

  const openInMaps = (cinema) => {
    const url = `https://www.google.com/maps/search/?api=1&query=${cinema.coords.latitude},${cinema.coords.longitude}`;
    Linking.openURL(url);
  };

  return (
    <View style={styles.container}>
      <StatusBar barStyle="light-content" backgroundColor="transparent" translucent />
      <View style={styles.header}>
        <Image source={require('../../assets/logo.png')} style={styles.logo} resizeMode="contain" />
      </View>
      {cinemas.length > 0 && <CinemaMap cinemas={cinemas} style={styles.map} />}

      <View style={styles.listPanel}>
        <Text style={styles.panelTitle}>Cinema in Umbria</Text>
        {cinemas.map((cinema) => (
          <TouchableOpacity
            key={cinema.slug}
            style={styles.cinemaRow}
            onPress={() => openInMaps(cinema)}
            activeOpacity={0.7}
          >
            <View style={[styles.dot, { backgroundColor: cinema.color }]} />
            <View style={styles.cinemaDetails}>
              <Text style={styles.cinemaName}>{cinema.name}</Text>
              <Text style={styles.cinemaAddress}>{cinema.address}</Text>
            </View>
            <Ionicons name="navigate-outline" size={20} color={Colors.primary} />
          </TouchableOpacity>
        ))}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  header: {
    alignItems: 'center',
    justifyContent: 'center',
    // Sul telefono i 50px evitano il notch; sul web non servono.
    marginTop: Platform.OS === 'web' ? 16 : 50,
    marginBottom: 8,
  },
  logo: {
    width: 230,
    height: 74,
  },
  map: {
    flex: 1,
  },
  listPanel: {
    backgroundColor: Colors.surface,
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    padding: 20,
    paddingBottom: 32,
  },
  panelTitle: {
    color: Colors.white,
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 16,
  },
  cinemaRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: Colors.card,
  },
  dot: {
    width: 12,
    height: 12,
    borderRadius: 6,
    marginRight: 12,
  },
  cinemaDetails: {
    flex: 1,
  },
  cinemaName: {
    color: Colors.white,
    fontSize: 15,
    fontWeight: '600',
    marginBottom: 2,
  },
  cinemaAddress: {
    color: Colors.gray,
    fontSize: 12,
  },
});
