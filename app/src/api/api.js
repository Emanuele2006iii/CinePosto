// Client HTTP verso il backend CinePosto (film, cinema, spettacoli) +
// gestione dei preferiti in locale tramite AsyncStorage.
import AsyncStorage from '@react-native-async-storage/async-storage';
import { API_BASE } from '../constants/config';

// Costruisce '?chiave=valore&...' saltando i parametri vuoti.
// Non usiamo new URL(): su React Native url.searchParams non è affidabile.
const buildQuery = (params) => {
  const parts = Object.entries(params)
    .filter(([, v]) => v !== undefined && v !== null && v !== '')
    .map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(v)}`);
  return parts.length > 0 ? `?${parts.join('&')}` : '';
};

// Film
export const getFilmsToday = async () => {
  const res = await fetch(`${API_BASE}/film/oggi`);
  if (!res.ok) throw new Error('Errore nel caricamento film');
  return res.json();
};

export const searchFilms = async (query) => {
  const res = await fetch(`${API_BASE}/film/search?q=${encodeURIComponent(query)}`);
  if (!res.ok) throw new Error('Errore nella ricerca');
  return res.json();
};

export const getFilmById = async (id) => {
  const res = await fetch(`${API_BASE}/film/${id}`);
  if (!res.ok) throw new Error('Film non trovato');
  return res.json();
};

// Cinema
export const getCinemas = async () => {
  const res = await fetch(`${API_BASE}/cinema`);
  if (!res.ok) throw new Error('Errore nel caricamento cinema');
  return res.json();
};

export const getCinemaBySlug = async (slug) => {
  const res = await fetch(`${API_BASE}/cinema/${slug}`);
  if (!res.ok) throw new Error('Cinema non trovato');
  return res.json();
};

export const getCinemaShowings = async (slug, dateFrom, dateTo) => {
  const query = buildQuery({ date_from: dateFrom, date_to: dateTo });
  const res = await fetch(`${API_BASE}/cinema/${slug}/showings${query}`);
  if (!res.ok) throw new Error('Errore nel caricamento programmazione');
  return res.json();
};

// Showings
export const getShowingsToday = async () => {
  const res = await fetch(`${API_BASE}/showings`);
  if (!res.ok) throw new Error('Errore nel caricamento spettacoli');
  return res.json();
};

export const getShowings = async (filters = {}) => {
  const res = await fetch(`${API_BASE}/showings${buildQuery(filters)}`);
  if (!res.ok) throw new Error('Errore nel caricamento spettacoli');
  return res.json();
};

// Preferiti (locali con AsyncStorage)
const FAVORITES_KEY = '@cineposto_favorites';

export const getFavorites = async () => {
  try {
    const json = await AsyncStorage.getItem(FAVORITES_KEY);
    return json ? JSON.parse(json) : [];
  } catch {
    return [];
  }
};

export const addFavorite = async (filmId) => {
  const favorites = await getFavorites();
  if (!favorites.includes(filmId)) {
    favorites.push(filmId);
    await AsyncStorage.setItem(FAVORITES_KEY, JSON.stringify(favorites));
  }
};

export const removeFavorite = async (filmId) => {
  const favorites = await getFavorites();
  const updated = favorites.filter((id) => id !== filmId);
  await AsyncStorage.setItem(FAVORITES_KEY, JSON.stringify(updated));
};

export const isFavorite = async (filmId) => {
  const favorites = await getFavorites();
  return favorites.includes(filmId);
};
