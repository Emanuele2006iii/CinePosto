import { View, Text, FlatList, StyleSheet, TouchableOpacity, Linking } from 'react-native';

const TODAY = new Date().toISOString().split('T')[0];

const MOCK_FILMS = [
  {
    title: 'Inside Out 2',
    genres: ['Animazione', 'Commedia'],
    director: 'Kelsey Mann',
    duration: '100 min',
    present_in: [
      { cinema: 'UCI Cinemas Perugia', times: ['15:30', '18:00', '20:30'], language: 'ITA', url: 'https://www.ucicinemas.it' },
    ],
  },
  {
    title: 'Deadpool & Wolverine',
    genres: ['Azione', 'Commedia'],
    director: 'Shawn Levy',
    duration: '128 min',
    present_in: [
      { cinema: 'PostModernissimo', times: ['17:00', '21:00'], language: 'ITA', url: 'https://www.postmodernissimo.com' },
      { cinema: 'The Space Cinema Corciano', times: ['16:30', '19:00', '21:30'], language: 'ITA', url: 'https://www.thespacecinema.it' },
    ],
  },
  {
    title: 'Alien: Romulus',
    genres: ['Horror', 'Fantascienza'],
    director: 'Fede Álvarez',
    duration: '119 min',
    present_in: [
      { cinema: 'The Space Cinema Corciano', times: ['20:30'], language: 'ITA', url: 'https://www.thespacecinema.it' },
    ],
  },
];

function FilmCard({ film }) {
  return (
    <View style={styles.card}>
      <Text style={styles.title}>{film.title}</Text>
      <Text style={styles.meta}>{film.genres.join(', ')} · {film.duration}</Text>
      {film.present_in.map((show, i) => (
        <TouchableOpacity key={i} style={styles.showRow} onPress={() => Linking.openURL(show.url)}>
          <Text style={styles.cinemaName}>{show.cinema}</Text>
          <Text style={styles.times}>{show.times.join('  ·  ')} — {show.language}</Text>
          <Text style={styles.link}>Acquista biglietto →</Text>
        </TouchableOpacity>
      ))}
    </View>
  );
}

export default function HomeScreen() {
  return (
    <View style={styles.container}>
      <Text style={styles.header}>Film Oggi — {TODAY}</Text>
      <FlatList
        data={MOCK_FILMS}
        keyExtractor={(item) => item.title}
        renderItem={({ item }) => <FilmCard film={item} />}
        contentContainerStyle={styles.list}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#111' },
  header: { fontSize: 18, fontWeight: 'bold', color: '#fff', padding: 16, backgroundColor: '#E50914' },
  list: { padding: 12 },
  card: { backgroundColor: '#1c1c1e', borderRadius: 10, padding: 14, marginBottom: 12 },
  title: { fontSize: 17, fontWeight: '700', color: '#fff', marginBottom: 4 },
  meta: { fontSize: 13, color: '#aaa', marginBottom: 10 },
  showRow: { borderTopWidth: 1, borderTopColor: '#333', paddingTop: 8, marginTop: 4 },
  cinemaName: { fontSize: 14, fontWeight: '600', color: '#e0e0e0' },
  times: { fontSize: 13, color: '#bbb', marginTop: 2 },
  link: { fontSize: 12, color: '#E50914', marginTop: 4 },
});
