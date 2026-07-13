// Schermata Home ("Films"): film in cartellone nella data selezionata, con
// hero in evidenza, barra date, griglia di locandine e filtro per cinema.
import React, { useEffect, useState, useCallback } from 'react';
import {
  View,
  ScrollView,
  StyleSheet,
  ActivityIndicator,
  Text,
  RefreshControl,
  StatusBar,
  TouchableOpacity,
  Modal,
  Image,
  Platform,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import SwipeableHero from '../components/SwipeableHero';
import DateBar from '../components/DateBar';
import MovieGrid from '../components/MovieGrid';
import Colors from '../constants/colors';
import CINEMAS, { CINEMA_NAMES } from '../constants/cinemas';
import { getToday } from '../utils/dates';
import { getCinemas, getCinemaShowings } from '../api/api';

export default function FilmsTab({ navigation }) {
  const [films, setFilms] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [refreshing, setRefreshing] = useState(false);
  // true mentre si ricaricano i dati dopo un cambio data (loading resta
  // per il primo caricamento a schermo intero)
  const [updating, setUpdating] = useState(false);
  const [selectedDate, setSelectedDate] = useState(getToday);

  // Unico filtro: cinema selezionato (slug, es. 'uci-perugia'; null = tutti)
  const [selectedCinema, setSelectedCinema] = useState(null);
  const [filterModalVisible, setFilterModalVisible] = useState(false);

  const loadData = useCallback(async () => {
    try {
      setError(null);
      setUpdating(true);
      const cinemasData = await getCinemas();

      // La lista film si costruisce dagli spettacoli della data selezionata:
      // ogni showing (ShowingDetail) porta con sé il film annidato. Così ogni
      // data mostra ESATTAMENTE i film in cartellone quel giorno (prima si
      // partiva dai "film di oggi", perdendo quelli programmati in altre date).
      const byFilm = {};
      await Promise.all(
        cinemasData.map(async (cinema) => {
          try {
            const showings = await getCinemaShowings(cinema.slug, selectedDate, selectedDate);
            showings.forEach((s) => {
              if (!s.film) return;
              const id = s.film.id;
              if (!byFilm[id]) {
                byFilm[id] = { film: s.film, cinemaNames: new Set(), cinemaSlugs: new Set() };
              }
              byFilm[id].cinemaNames.add(cinema.name);
              byFilm[id].cinemaSlugs.add(cinema.slug);
            });
          } catch (e) {
            console.warn(`Orari non disponibili per ${cinema.slug}:`, e.message);
          }
        })
      );

      const enrichedFilms = Object.values(byFilm).map(({ film, cinemaNames, cinemaSlugs }) => ({
        ...film,
        cinemaNames: [...cinemaNames],
        cinemaSlugs: [...cinemaSlugs],
      }));
      setFilms(enrichedFilms);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
      setRefreshing(false);
      setUpdating(false);
    }
  }, [selectedDate]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const onRefresh = useCallback(() => {
    setRefreshing(true);
    loadData();
  }, [loadData]);

  const handleMoviePress = (movie) => {
    navigation.navigate('MovieDetail', { id: movie.id, date: selectedDate });
  };

  // Il filtro agisce sui dati già scaricati: non serve ricaricare.
  const filteredFilms = films
    .filter((f) => !selectedCinema || f.cinemaSlugs?.includes(selectedCinema))
    .sort((a, b) => a.title.localeCompare(b.title));

  const featuredMovies = filteredFilms.slice(0, 6);

  if (loading) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator size="large" color={Colors.primary} />
      </View>
    );
  }

  if (error) {
    return (
      <View style={styles.centered}>
        <Text style={styles.errorIcon}>⚠️</Text>
        <Text style={styles.errorTitle}>Errore di connessione</Text>
        <Text style={styles.errorText}>{error}</Text>
        <Text style={styles.errorHint}>Verifica la connessione e riprova</Text>
        <TouchableOpacity
          style={styles.retryButton}
          onPress={() => {
            setLoading(true);
            loadData();
          }}
          activeOpacity={0.7}
        >
          <Ionicons name="refresh" size={18} color={Colors.white} />
          <Text style={styles.retryText}>Riprova</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <StatusBar barStyle="light-content" backgroundColor="transparent" translucent />
      <ScrollView
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={onRefresh}
            tintColor={Colors.primary}
          />
        }
      >
        {/* Header con logo centrato e bottone filtro cinema */}
        <View style={styles.header}>
          {/* Versione senza tagline: a questa dimensione non sarebbe leggibile */}
          <Image source={require('../../assets/logo_header.png')} style={styles.logo} resizeMode="contain" />
          <TouchableOpacity onPress={() => setFilterModalVisible(true)} style={styles.iconButton}>
            <Ionicons name="options" size={22} color={Colors.white} />
          </TouchableOpacity>
        </View>

        {/* Chip del filtro attivo, per vederlo e toglierlo al volo */}
        {selectedCinema && (
          <View style={styles.activeFilters}>
            <TouchableOpacity style={styles.filterChip} onPress={() => setSelectedCinema(null)}>
              <Text style={styles.filterChipText}>{CINEMA_NAMES[selectedCinema]}</Text>
              <Ionicons name="close" size={14} color={Colors.white} />
            </TouchableOpacity>
          </View>
        )}

        <SwipeableHero movies={featuredMovies} onPress={handleMoviePress} />

        <DateBar selectedDate={selectedDate} onDateSelect={setSelectedDate} />

        {/* Spinner + griglia attenuata mentre si caricano gli orari
            della nuova data selezionata */}
        {updating && !refreshing && (
          <ActivityIndicator size="small" color={Colors.primary} style={styles.updatingSpinner} />
        )}

        {/* Tutti i film, ognuno una sola volta: i pallini colorati
            indicano in quali cinema è programmato */}
        <View
          style={[styles.rows, updating && styles.rowsUpdating]}
          pointerEvents={updating ? 'none' : 'auto'}
        >
          {filteredFilms.length === 0 ? (
            <Text style={styles.noResults}>Nessun film trovato</Text>
          ) : (
            <>
              <Text style={styles.gridTitle}>
                {selectedCinema ? CINEMA_NAMES[selectedCinema] : 'Tutti i film'}
              </Text>
              <MovieGrid movies={filteredFilms} onMoviePress={handleMoviePress} />
            </>
          )}
        </View>
      </ScrollView>

      {/* Modal filtro cinema */}
      <Modal
        visible={filterModalVisible}
        transparent
        animationType="slide"
        onRequestClose={() => setFilterModalVisible(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>Filtra per cinema</Text>
              <TouchableOpacity onPress={() => setFilterModalVisible(false)}>
                <Ionicons name="close" size={24} color={Colors.white} />
              </TouchableOpacity>
            </View>

            {[null, ...CINEMAS.map((c) => c.slug)].map((slug) => (
              <TouchableOpacity
                key={slug || 'all'}
                style={[
                  styles.modalOption,
                  selectedCinema === slug && styles.modalOptionActive,
                ]}
                onPress={() => {
                  setSelectedCinema(slug);
                  setFilterModalVisible(false);
                }}
              >
                <Text
                  style={[
                    styles.modalOptionText,
                    selectedCinema === slug && styles.modalOptionTextActive,
                  ]}
                >
                  {slug ? CINEMA_NAMES[slug] : 'Tutti i cinema'}
                </Text>
                {selectedCinema === slug && (
                  <Ionicons name="checkmark" size={20} color={Colors.primary} />
                )}
              </TouchableOpacity>
            ))}
          </View>
        </View>
      </Modal>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  centered: {
    flex: 1,
    backgroundColor: Colors.background,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 24,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    // Sul telefono i 50px evitano il notch; sul web non servono.
    marginTop: Platform.OS === 'web' ? 16 : 50,
    marginBottom: 12,
    paddingHorizontal: 16,
  },
  // ~44% dello schermo invece di ~60%: l'header non domina più la pagina
  logo: {
    width: 172,
    height: 52,
  },
  iconButton: {
    position: 'absolute',
    right: 16,
    padding: 8,
  },
  activeFilters: {
    flexDirection: 'row',
    alignItems: 'center',
    marginHorizontal: 16,
    marginBottom: 12,
  },
  filterChip: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.primary,
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
    gap: 6,
  },
  filterChipText: {
    color: Colors.white,
    fontSize: 13,
    fontWeight: '600',
  },
  errorIcon: {
    fontSize: 48,
    marginBottom: 12,
  },
  errorTitle: {
    color: Colors.white,
    fontSize: 20,
    fontWeight: 'bold',
    marginBottom: 8,
  },
  errorText: {
    color: Colors.lightGray,
    fontSize: 14,
    textAlign: 'center',
    marginBottom: 16,
  },
  errorHint: {
    color: Colors.primary,
    fontSize: 13,
    textAlign: 'center',
    backgroundColor: Colors.surface,
    padding: 12,
    borderRadius: 8,
  },
  rows: {
    paddingTop: 16,
  },
  rowsUpdating: {
    opacity: 0.4,
  },
  updatingSpinner: {
    marginTop: 16,
  },
  retryButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.primary,
    paddingHorizontal: 20,
    paddingVertical: 10,
    borderRadius: 8,
    marginTop: 16,
    gap: 8,
  },
  retryText: {
    color: Colors.white,
    fontSize: 15,
    fontWeight: '600',
  },
  gridTitle: {
    color: Colors.white,
    fontSize: 18,
    fontWeight: 'bold',
    marginLeft: 16,
    marginBottom: 12,
  },
  noResults: {
    color: Colors.gray,
    textAlign: 'center',
    padding: 24,
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.7)',
    justifyContent: 'flex-end',
  },
  modalContent: {
    backgroundColor: Colors.surface,
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    paddingBottom: 32,
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: Colors.card,
  },
  modalTitle: {
    color: Colors.white,
    fontSize: 18,
    fontWeight: 'bold',
  },
  modalOption: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 14,
    paddingHorizontal: 16,
    borderBottomWidth: 1,
    borderBottomColor: Colors.card,
  },
  modalOptionActive: {
    backgroundColor: Colors.card,
  },
  modalOptionText: {
    color: Colors.white,
    fontSize: 16,
  },
  modalOptionTextActive: {
    color: Colors.primary,
    fontWeight: '600',
  },
});
