// Dati statici dei cinema supportati, condivisi da tutte le schermate.
// Prima erano duplicati in FilmsTab, CinemaTab, LocationTab e MovieDetailScreen.

const CINEMAS = [
  {
    slug: 'the-space-corciano',
    name: 'The Space Cinema Corciano',
    shortName: 'The Space',
    color: '#1E90FF',
    address: 'Via Pierluigi Nervi, 6, 06073 Corciano',
    coords: { latitude: 43.0989921, longitude: 12.3143414 },
    logo: require('../../assets/the-space.jpg'),
  },
  {
    slug: 'uci-perugia',
    name: 'UCI Cinemas Perugia',
    shortName: 'UCI',
    color: '#FFA500',
    address: 'Vle Centova, 1d, 06132 Perugia PG',
    coords: { latitude: 43.0963682, longitude: 12.3553159 },
    logo: require('../../assets/uci.png'),
  },
  {
    slug: 'postmodernissimo',
    name: 'PostModernissimo',
    shortName: 'PostMod',
    color: '#E50914',
    address: 'Via del Carmine, 8, 06122 Perugia',
    coords: { latitude: 43.1128253, longitude: 12.3932433 },
    logo: require('../../assets/post.jpg'),
  },
];

// Mappe di comodo per accedere ai dati partendo dallo slug.
export const CINEMA_COLORS = Object.fromEntries(CINEMAS.map((c) => [c.slug, c.color]));
export const CINEMA_LOGOS = Object.fromEntries(CINEMAS.map((c) => [c.slug, c.logo]));
export const CINEMA_NAMES = Object.fromEntries(CINEMAS.map((c) => [c.slug, c.name]));

export default CINEMAS;
