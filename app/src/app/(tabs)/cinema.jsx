import { View, Text, FlatList, StyleSheet, TouchableOpacity, Linking } from 'react-native';

const CINEMAS = [
  {
    name: 'PostModernissimo',
    address: 'Via del Sole, 4 — 06123 Perugia',
    url: 'https://www.postmodernissimo.com',
  },
  {
    name: 'The Space Cinema Corciano',
    address: 'Via San Giovanni Bosco — 06073 Corciano (PG)',
    url: 'https://www.thespacecinema.it',
  },
  {
    name: 'UCI Cinemas Perugia',
    address: 'Via della Pallotta, 35 — 06126 Perugia',
    url: 'https://www.ucicinemas.it',
  },
];

function CinemaCard({ cinema }) {
  return (
    <View style={styles.card}>
      <Text style={styles.name}>{cinema.name}</Text>
      <Text style={styles.address}>{cinema.address}</Text>
      <TouchableOpacity onPress={() => Linking.openURL(cinema.url)}>
        <Text style={styles.link}>Vai al sito →</Text>
      </TouchableOpacity>
    </View>
  );
}

export default function CinemaScreen() {
  return (
    <View style={styles.container}>
      <Text style={styles.header}>Cinema in Umbria</Text>
      <FlatList
        data={CINEMAS}
        keyExtractor={(item) => item.name}
        renderItem={({ item }) => <CinemaCard cinema={item} />}
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
  name: { fontSize: 16, fontWeight: '700', color: '#fff', marginBottom: 4 },
  address: { fontSize: 13, color: '#aaa', marginBottom: 8 },
  link: { fontSize: 13, color: '#E50914' },
});
