// Schermata dettaglio film: poster, metadati, trama, link al trailer e orari
// raggruppati per cinema nella data scelta.
import React, { useEffect, useState, useMemo } from 'react';
import {
  View,
  Text,
  Image,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
  StatusBar,
  Linking,
  Platform,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import PosterImage from '../components/PosterImage';
import Colors from '../constants/colors';
import CINEMAS, { CINEMA_COLORS, CINEMA_LOGOS, CINEMA_NAMES } from '../constants/cinemas';
import { getToday, getNext7Days, formatShortDate, isToday } from '../utils/dates';
import { getFilmById, getCinemas, getCinemaShowings } from '../api/api';

const HEADER_HEIGHT = 300;

// blurRadius non funziona su react-native-web: sul web la sfocatura si fa con
// la CSS filter.
const WEB_BLUR = Platform.OS === 'web' ? { filter: 'blur(22px)' } : null;

export default function MovieDetailScreen({ route, navigation }) {
  const { id, date } = route.params;
  const [film, setFilm] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedDate, setSelectedDate] = useState(date || getToday);
  const [synopsisExpanded, setSynopsisExpanded] = useState(false);
  // Orari di questo film, ognuno con il proprio `cinema` (per raggrupparli).
  const [showings, setShowings] = useState([]);

  useEffect(() => {
    const load = async () => {
      try {
        // Dettagli del film (titolo, trama, poster, ecc.).
        const data = await getFilmById(id);
        setFilm(data);

        // Gli orari per cinema NON sono nel dettaglio film: le showings del
        // backend (ShowingOut) non includono il cinema. Li ricostruiamo
        // interrogando la programmazione settimanale di ogni cinema e tenendo
        // solo quelli di questo film. Ogni showing così ottenuto (ShowingDetail)
        // porta con sé l'oggetto `cinema`, necessario per il raggruppamento.
        const cinemas = await getCinemas();
        const week = getNext7Days();
        const from = week[0];
        const to = week[week.length - 1];
        const perCinema = await Promise.all(
          cinemas.map(async (cinema) => {
            try {
              const list = await getCinemaShowings(cinema.slug, from, to);
              return list.filter((s) => s.film?.id === Number(id));
            } catch {
              return [];
            }
          })
        );
        const flat = perCinema.flat();
        setShowings(flat);
        // Molti film sono programmati in un solo giorno: se la data d'ingresso
        // non ha spettacoli per questo film, salta alla prima data utile.
        const avail = [...new Set(flat.map((s) => s.date))].sort();
        setSelectedDate((cur) => (avail.length && !avail.includes(cur) ? avail[0] : cur));
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [id]);

  // Raggruppa gli spettacoli del giorno selezionato per cinema,
  // nell'ordine fisso definito in constants/cinemas.js.
  const groupedShowtimes = useMemo(() => {
    const groups = {};
    showings
      .filter((s) => s.date === selectedDate)
      .forEach((show) => {
        const slug = show.cinema?.slug || 'sconosciuto';
        if (!groups[slug]) {
          groups[slug] = { slug, buy_url: show.buy_url, entries: [] };
        }
        const times = Array.isArray(show.times) ? show.times : [];
        times.forEach((time) => {
          groups[slug].entries.push({
            time,
            screen: show.screen,
            language: show.language,
            buy_url: show.buy_url,
          });
        });
      });

    const order = CINEMAS.map((c) => c.slug);
    return Object.values(groups).sort(
      (a, b) => order.indexOf(a.slug) - order.indexOf(b.slug)
    );
  }, [showings, selectedDate]);

  const dates = useMemo(() => getNext7Days(), []);

  if (loading) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator size="large" color={Colors.primary} />
      </View>
    );
  }

  // Senza questo bottone l'utente resterebbe bloccato: l'header
  // di navigazione è nascosto, quindi non c'è altro modo di tornare indietro.
  if (!film) {
    return (
      <View style={styles.centered}>
        <Text style={styles.errorText}>Film non trovato</Text>
        <TouchableOpacity
          style={styles.errorBackButton}
          onPress={() => navigation.goBack()}
          activeOpacity={0.7}
        >
          <Ionicons name="arrow-back" size={18} color={Colors.white} />
          <Text style={styles.errorBackText}>Torna indietro</Text>
        </TouchableOpacity>
      </View>
    );
  }

  const posterUrl = film.poster_url || null;
  const genres = film.genres?.split(',').map((g) => g.trim()).join(' · ') || '';

  return (
    <View style={styles.container}>
      <StatusBar barStyle="light-content" />
      <ScrollView showsVerticalScrollIndicator={false}>
        {/* Poster as header */}
        <View style={{ height: HEADER_HEIGHT, overflow: 'hidden' }}>
          {posterUrl ? (
            <Image
              source={{ uri: posterUrl }}
              style={[styles.backdrop, WEB_BLUR]}
              resizeMode="cover"
              blurRadius={20}
            />
          ) : (
            <View style={[styles.backdrop, styles.backdropPlaceholder]} />
          )}
          <LinearGradient
            colors={['rgba(0,0,0,0.3)', Colors.background]}
            style={StyleSheet.absoluteFill}
          />
          <TouchableOpacity
            style={styles.backButton}
            onPress={() => navigation.goBack()}
          >
            <Ionicons name="arrow-back" size={24} color={Colors.white} />
          </TouchableOpacity>
        </View>

        {/* Content */}
        <View style={styles.content}>
          <View style={styles.header}>
            {posterUrl && (
              <PosterImage uri={posterUrl} style={styles.poster} />
            )}
            <View style={styles.headerInfo}>
              <Text style={styles.title}>{film.title}</Text>
              <View style={styles.metaRow}>
                {film.runtime_minutes && (
                  <Text style={styles.metaText}>{film.runtime_minutes} min</Text>
                )}
                {film.runtime_minutes && film.director && (
                  <Text style={styles.metaDot}>•</Text>
                )}
                {film.director && (
                  <Text style={styles.metaText}>{film.director}</Text>
                )}
              </View>
              {genres ? <Text style={styles.genres}>{genres}</Text> : null}
              {film.year && (
                <Text style={styles.year}>{film.year}</Text>
              )}
            </View>
          </View>

          {/* Trama */}
          {film.synopsis ? (
            <View style={styles.section}>
              <Text style={styles.sectionTitle}>Trama</Text>
              <Text style={styles.overview} numberOfLines={synopsisExpanded ? undefined : 3}>
                {film.synopsis}
              </Text>
              {film.synopsis.length > 120 && (
                <TouchableOpacity onPress={() => setSynopsisExpanded(!synopsisExpanded)}>
                  <Text style={styles.readMore}>{synopsisExpanded ? 'Mostra meno' : 'Leggi di più...'}</Text>
                </TouchableOpacity>
              )}
            </View>
          ) : null}

          {/* Trailer */}
          <View style={styles.section}>
            <TouchableOpacity
              style={styles.trailerButton}
              onPress={() => {
                const q = encodeURIComponent(`${film.title} trailer`);
                Linking.openURL(`https://www.youtube.com/results?search_query=${q}`);
              }}
              activeOpacity={0.7}
            >
              <Ionicons name="logo-youtube" size={20} color="#FF0000" />
              <Text style={styles.trailerButtonText}>Guarda trailer</Text>
            </TouchableOpacity>
          </View>

          {/* Date selector */}
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Orari per data</Text>
            <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.dateScroll}>
              {dates.map((date) => (
                <TouchableOpacity
                  key={date}
                  style={[
                    styles.dateTab,
                    selectedDate === date && styles.dateTabActive,
                    isToday(date) && styles.dateTabToday,
                  ]}
                  onPress={() => setSelectedDate(date)}
                >
                  <Text
                    style={[
                      styles.dateTabText,
                      selectedDate === date && styles.dateTabTextActive,
                    ]}
                  >
                    {isToday(date) ? 'Oggi' : formatShortDate(date)}
                  </Text>
                </TouchableOpacity>
              ))}
            </ScrollView>
          </View>

          {/* Showtimes grouped by cinema */}
          {groupedShowtimes.length > 0 ? (
            <View style={styles.section}>
              <Text style={styles.sectionTitle}>Orari — {isToday(selectedDate) ? 'Oggi' : formatShortDate(selectedDate)}</Text>
              {groupedShowtimes.map((group) => (
                <View
                  key={group.slug}
                  style={[
                    styles.showCard,
                    { borderLeftColor: CINEMA_COLORS[group.slug] || Colors.primary },
                  ]}
                >
                  <View style={styles.showHeader}>
                    {CINEMA_LOGOS[group.slug] && (
                      <Image source={CINEMA_LOGOS[group.slug]} style={styles.cinemaLogo} resizeMode="cover" />
                    )}
                    <Text style={styles.cinemaName}>{CINEMA_NAMES[group.slug] || group.slug}</Text>
                  </View>
                  <View style={styles.timesRow}>
                    {group.entries.map((entry, eIdx) => (
                      <TouchableOpacity
                        key={eIdx}
                        style={styles.timeChip}
                        onPress={() => entry.buy_url && Linking.openURL(entry.buy_url)}
                        activeOpacity={0.7}
                      >
                        <Text style={styles.timeText}>{entry.time}</Text>
                        <View style={styles.timeDetails}>
                          {entry.language && (
                            <Text style={styles.timeDetailText}>{entry.language}</Text>
                          )}
                          {entry.screen && (
                            <Text style={styles.timeDetailText}>Sala {entry.screen}</Text>
                          )}
                        </View>
                      </TouchableOpacity>
                    ))}
                  </View>
                  {group.buy_url && (
                    <TouchableOpacity onPress={() => Linking.openURL(group.buy_url)}>
                      <Text style={styles.linkText}>Vai al sito →</Text>
                    </TouchableOpacity>
                  )}
                </View>
              ))}
            </View>
          ) : (
            <View style={styles.section}>
              <Text style={styles.emptyText}>
                Nessun orario disponibile per {isToday(selectedDate) ? 'oggi' : formatShortDate(selectedDate)}
              </Text>
            </View>
          )}
        </View>
      </ScrollView>
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
  },
  errorText: {
    color: Colors.lightGray,
    fontSize: 16,
  },
  errorBackButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.surface,
    paddingHorizontal: 20,
    paddingVertical: 10,
    borderRadius: 8,
    marginTop: 16,
    gap: 8,
  },
  errorBackText: {
    color: Colors.white,
    fontSize: 15,
    fontWeight: '600',
  },
  backdrop: {
    width: '100%',
    height: HEADER_HEIGHT,
    position: 'absolute',
  },
  backdropPlaceholder: {
    backgroundColor: Colors.card,
  },
  backButton: {
    position: 'absolute',
    top: Platform.OS === 'web' ? 16 : 50,
    left: 16,
    backgroundColor: 'rgba(0,0,0,0.5)',
    borderRadius: 20,
    padding: 8,
  },
  content: {
    padding: 16,
    marginTop: -20,
  },
  header: {
    flexDirection: 'row',
    gap: 14,
    marginBottom: 16,
  },
  poster: {
    width: 100,
    height: 150,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: Colors.card,
  },
  headerInfo: {
    flex: 1,
    justifyContent: 'flex-end',
    paddingBottom: 4,
  },
  title: {
    color: Colors.white,
    fontSize: 20,
    fontWeight: 'bold',
    lineHeight: 24,
    marginBottom: 4,
  },
  metaRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginBottom: 4,
    flexWrap: 'wrap',
  },
  metaText: {
    color: Colors.lightGray,
    fontSize: 13,
  },
  metaDot: {
    color: Colors.gray,
    fontSize: 13,
  },
  genres: {
    color: Colors.lightGray,
    fontSize: 12,
    marginBottom: 4,
  },
  year: {
    color: Colors.gray,
    fontSize: 12,
  },
  section: {
    marginBottom: 24,
  },
  sectionTitle: {
    color: Colors.white,
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 10,
  },
  overview: {
    color: Colors.lightGray,
    fontSize: 14,
    lineHeight: 22,
  },
  readMore: {
    color: Colors.primary,
    fontSize: 13,
    fontWeight: '600',
    marginTop: 6,
  },
  dateScroll: {
    marginBottom: 8,
  },
  dateTab: {
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 20,
    backgroundColor: Colors.surface,
    marginRight: 8,
  },
  dateTabActive: {
    backgroundColor: Colors.primary,
  },
  dateTabToday: {
    borderWidth: 1,
    borderColor: Colors.primary,
  },
  dateTabText: {
    color: Colors.lightGray,
    fontSize: 13,
  },
  dateTabTextActive: {
    color: Colors.white,
    fontWeight: 'bold',
  },
  showCard: {
    backgroundColor: Colors.surface,
    borderRadius: 10,
    borderLeftWidth: 3,
    padding: 14,
    marginBottom: 10,
  },
  showHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    marginBottom: 12,
  },
  cinemaLogo: {
    width: 28,
    height: 28,
    borderRadius: 14,
  },
  cinemaName: {
    color: Colors.white,
    fontSize: 15,
    fontWeight: 'bold',
  },
  timesRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
    marginBottom: 8,
  },
  timeChip: {
    backgroundColor: Colors.card,
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 6,
    minWidth: 80,
  },
  timeText: {
    color: Colors.white,
    fontSize: 15,
    fontWeight: '600',
    marginBottom: 2,
  },
  timeDetails: {
    flexDirection: 'row',
    gap: 6,
  },
  timeDetailText: {
    color: Colors.gray,
    fontSize: 11,
  },
  linkText: {
    color: Colors.primary,
    fontSize: 13,
    fontWeight: '600',
    marginTop: 6,
  },
  emptyText: {
    color: Colors.gray,
    fontSize: 14,
    textAlign: 'center',
    marginTop: 8,
  },
  trailerButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: Colors.surface,
    borderWidth: 1,
    borderColor: '#FF0000',
    borderRadius: 10,
    paddingVertical: 14,
    gap: 8,
  },
  trailerButtonText: {
    color: Colors.white,
    fontSize: 16,
    fontWeight: 'bold',
  },
});
