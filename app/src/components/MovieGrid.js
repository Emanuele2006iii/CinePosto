import React, { useState } from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import PosterImage from './PosterImage';
import Colors from '../constants/colors';

const H_PADDING = 16;
const GAP = 10;

// Griglia di locandine adattiva: misura il proprio contenitore con
// onLayout (sul web l'app vive in una colonna centrata più stretta
// della finestra). Ogni film appare una sola volta.
export default function MovieGrid({ movies, onMoviePress }) {
  const [gridWidth, setGridWidth] = useState(0);
  const columns = Math.max(3, Math.min(6, Math.floor(gridWidth / 160)));
  const cardWidth = (gridWidth - H_PADDING * 2 - GAP * (columns - 1)) / columns;
  const posterHeight = cardWidth * 1.5;

  if (!movies || movies.length === 0) return null;

  return (
    <View
      style={styles.grid}
      onLayout={(e) => setGridWidth(e.nativeEvent.layout.width)}
    >
      {gridWidth > 0 && movies.map((movie) => (
        <TouchableOpacity
          key={movie.id}
          style={{ width: cardWidth }}
          onPress={() => onMoviePress(movie)}
          activeOpacity={0.75}
        >
          {movie.poster_url ? (
            <PosterImage
              uri={movie.poster_url}
              style={[styles.poster, { width: cardWidth, height: posterHeight }]}
            />
          ) : (
            <View style={[styles.posterPlaceholder, { width: cardWidth, height: posterHeight }]}>
              <Text style={styles.placeholderText} numberOfLines={3}>{movie.title}</Text>
            </View>
          )}
          <Text style={styles.title} numberOfLines={2}>{movie.title}</Text>
        </TouchableOpacity>
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  grid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    paddingHorizontal: H_PADDING,
    gap: GAP,
  },
  poster: {
    borderRadius: 8,
  },
  posterPlaceholder: {
    backgroundColor: Colors.card,
    borderRadius: 8,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 8,
  },
  placeholderText: {
    color: Colors.lightGray,
    fontSize: 12,
    textAlign: 'center',
  },
  title: {
    color: Colors.white,
    fontSize: 12,
    fontWeight: '600',
    marginTop: 6,
    marginBottom: 12,
    lineHeight: 15,
  },
});
