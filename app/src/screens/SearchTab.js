// Schermata "Cerca": ricerca film per titolo con debounce e annullamento
// delle risposte obsolete (conta solo l'ultima query digitata).
import React, { useState, useRef, useEffect } from 'react';
import {
  View,
  TextInput,
  FlatList,
  Text,
  Image,
  TouchableOpacity,
  StyleSheet,
  StatusBar,
  ActivityIndicator,
  Keyboard,
  Platform,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import PosterImage from '../components/PosterImage';
import Colors from '../constants/colors';
import { searchFilms, getCinemas, getCinemaShowings } from '../api/api';

const SEARCH_DEBOUNCE_MS = 300;

export default function SearchTab({ navigation }) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);

  // Timer del debounce e contatore per scartare le risposte "vecchie":
  // se l'utente digita in fretta, solo l'ultima ricerca conta.
  const debounceTimer = useRef(null);
  const requestId = useRef(0);

  useEffect(() => {
    return () => clearTimeout(debounceTimer.current);
  }, []);

  const runSearch = async (text) => {
    const id = ++requestId.current;
    setLoading(true);
    setSearched(true);
    try {
      const [filmsData, cinemasData] = await Promise.all([
        searchFilms(text),
        getCinemas(),
      ]);

      const filmCinemaMap = {};
      filmsData.forEach((f) => { filmCinemaMap[f.id] = new Set(); });

      // Nessun risultato: inutile scaricare gli orari dei cinema.
      await Promise.all(
        (filmsData.length === 0 ? [] : cinemasData).map(async (cinema) => {
          try {
            const showings = await getCinemaShowings(cinema.slug);
            showings.forEach((s) => {
              // ShowingDetail annida il film: s.film.id (non s.film_id).
              const filmId = s.film?.id;
              if (filmCinemaMap[filmId]) {
                filmCinemaMap[filmId].add(cinema.name);
              }
            });
          } catch (e) {
            console.warn(`Orari non disponibili per ${cinema.slug}:`, e.message);
          }
        })
      );

      // Nel frattempo è partita una ricerca più recente: ignora questa.
      if (id !== requestId.current) return;

      const enriched = filmsData.map((f) => ({
        ...f,
        cinemaNames: [...(filmCinemaMap[f.id] || [])],
      }));
      setResults(enriched);
    } catch (e) {
      console.warn('Errore nella ricerca:', e.message);
    } finally {
      if (id === requestId.current) setLoading(false);
    }
  };

  const handleSearch = (text) => {
    setQuery(text);
    clearTimeout(debounceTimer.current);
    if (text.trim().length < 2) {
      setResults([]);
      setSearched(false);
      setLoading(false);
      return;
    }
    debounceTimer.current = setTimeout(() => runSearch(text), SEARCH_DEBOUNCE_MS);
  };

  const handlePress = (film) => {
    Keyboard.dismiss();
    navigation.navigate('MovieDetail', { id: film.id });
  };

  const renderItem = ({ item }) => (
    <TouchableOpacity style={styles.resultItem} onPress={() => handlePress(item)} activeOpacity={0.7}>
      {item.poster_url ? (
        <PosterImage uri={item.poster_url} style={styles.poster} />
      ) : (
        <View style={[styles.poster, styles.posterPlaceholder]}>
          <Text style={styles.posterText}>{item.title?.[0] || '?'}</Text>
        </View>
      )}
      <View style={styles.resultInfo}>
        <Text style={styles.resultTitle} numberOfLines={1}>{item.title}</Text>
        {item.runtime_minutes && (
          <Text style={styles.resultMeta}>{item.runtime_minutes} min</Text>
        )}
        {item.cinemaNames?.length > 0 && (
          <Text style={styles.resultCinemas} numberOfLines={1}>
            {item.cinemaNames.join(' · ')}
          </Text>
        )}
      </View>
      <Ionicons name="chevron-forward" size={18} color={Colors.gray} />
    </TouchableOpacity>
  );

  return (
    <View style={styles.container}>
      <StatusBar barStyle="light-content" backgroundColor="transparent" translucent />
      <View style={styles.header}>
        {/* Versione senza tagline: a questa dimensione non sarebbe leggibile */}
        <Image source={require('../../assets/logo_header.png')} style={styles.logo} resizeMode="contain" />
      </View>

      <View style={styles.searchContainer}>
        <Ionicons name="search" size={18} color={Colors.gray} style={styles.searchIcon} />
        <TextInput
          style={styles.searchInput}
          placeholder="Cerca film..."
          placeholderTextColor={Colors.gray}
          value={query}
          onChangeText={handleSearch}
          autoFocus
          returnKeyType="search"
        />
        {query.length > 0 && (
          <TouchableOpacity onPress={() => { setQuery(''); setResults([]); setSearched(false); }}>
            <Ionicons name="close-circle" size={18} color={Colors.gray} />
          </TouchableOpacity>
        )}
      </View>

      {loading ? (
        <ActivityIndicator size="large" color={Colors.primary} style={styles.loader} />
      ) : searched && results.length === 0 ? (
        <View style={styles.emptyContainer}>
          <Ionicons name="search-outline" size={48} color={Colors.gray} />
          <Text style={styles.emptyText}>Nessun film trovato</Text>
        </View>
      ) : (
        <FlatList
          data={results}
          keyExtractor={(item) => String(item.id)}
          renderItem={renderItem}
          contentContainerStyle={styles.list}
          showsVerticalScrollIndicator={false}
          keyboardDismissMode="on-drag"
        />
      )}
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
    marginBottom: 4,
  },
  // ~44% dello schermo invece di ~60%: l'header non domina più la pagina
  logo: {
    width: 172,
    height: 52,
  },
  searchContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.surface,
    marginHorizontal: 16,
    marginBottom: 12,
    borderRadius: 12,
    paddingHorizontal: 12,
  },
  searchIcon: {
    marginRight: 8,
  },
  searchInput: {
    flex: 1,
    color: Colors.white,
    fontSize: 16,
    paddingVertical: 12,
  },
  loader: {
    marginTop: 40,
  },
  list: {
    paddingHorizontal: 16,
  },
  resultItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: Colors.card,
  },
  poster: {
    width: 45,
    height: 67,
    borderRadius: 4,
    marginRight: 12,
  },
  posterPlaceholder: {
    backgroundColor: Colors.card,
    justifyContent: 'center',
    alignItems: 'center',
  },
  posterText: {
    color: Colors.lightGray,
    fontSize: 18,
    fontWeight: 'bold',
  },
  resultInfo: {
    flex: 1,
  },
  resultTitle: {
    color: Colors.white,
    fontSize: 15,
    fontWeight: '600',
    marginBottom: 2,
  },
  resultMeta: {
    color: Colors.gray,
    fontSize: 12,
    marginBottom: 2,
  },
  resultCinemas: {
    color: Colors.primary,
    fontSize: 11,
  },
  emptyContainer: {
    alignItems: 'center',
    marginTop: 60,
    gap: 12,
  },
  emptyText: {
    color: Colors.gray,
    fontSize: 16,
  },
});
