// Carosello "hero" in cima alla Home: per ogni film in evidenza mostra
// locandina, titolo e azioni. Scorrimento manuale con indicatore a pallini.
import React, { useRef, useState } from 'react';
import {
  View,
  Text,
  Image,
  TouchableOpacity,
  FlatList,
  StyleSheet,
  Dimensions,
  Linking,
  Platform,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import Colors from '../constants/colors';

const { width: windowWidth, height } = Dimensions.get('window');
// Sul telefono il carosello occupa metà schermo; sul browser desktop
// l'altezza della finestra è molto maggiore, quindi la limitiamo.
const HERO_HEIGHT = Math.min(height * 0.55, 520);

// blurRadius (prop nativa) non funziona su react-native-web: sul web la
// sfocatura va fatta con la CSS filter. Il bordo sfocato ricade sul colore di
// fondo del banner (Colors.card), quindi non serve altro accorgimento.
const WEB_BLUR = Platform.OS === 'web' ? { filter: 'blur(22px)' } : null;

export default function SwipeableHero({ movies, onPress }) {
  const flatListRef = useRef(null);
  const [activeIndex, setActiveIndex] = useState(0);
  // Larghezza reale del contenitore, misurata con onLayout: sul web
  // l'app vive in una colonna centrata più stretta della finestra.
  const [slideWidth, setSlideWidth] = useState(windowWidth);

  const visibleMovies = movies.slice(0, 6);

  // Carosello a scorrimento MANUALE (swipe): niente auto-scroll, che scattava
  // e "girava da solo" mentre l'utente guardava.
  const onScroll = (e) => {
    if (!slideWidth) return;
    // Aggiornamento continuo dell'indice: i pallini seguono lo swipe in tempo
    // reale (onMomentumScrollEnd non è affidabile, specie sul web).
    const index = Math.round(e.nativeEvent.contentOffset.x / slideWidth);
    // Ignora valori fuori range: sul web un evento di scroll iniziale puo' dare
    // un offset spurio che, con una clamp, "incollava" il pallino sull'ultimo.
    if (index < 0 || index >= visibleMovies.length) return;
    setActiveIndex((cur) => (cur !== index ? index : cur));
  };

  const renderItem = ({ item }) => {
    const posterUrl = item.poster_url || null;
    const genres = item.genres?.split(',').map((g) => g.trim()).join(' · ') || '';

    return (
      <TouchableOpacity
        activeOpacity={0.9}
        onPress={() => onPress(item)}
        style={[styles.slide, { width: slideWidth }]}
      >
        <View style={[styles.hero, { width: slideWidth, backgroundColor: Colors.card }]}>
          {/* Fondale = stesso poster in versione sfocata a tutto campo.
              blurRadius per nativo, CSS filter per web (blurRadius non esiste su web). */}
          {posterUrl && (
            <Image
              source={{ uri: posterUrl }}
              style={[StyleSheet.absoluteFill, WEB_BLUR]}
              resizeMode="cover"
              blurRadius={22}
            />
          )}
          <LinearGradient
            colors={['transparent', 'rgba(20,20,20,0.75)', Colors.background]}
            locations={[0.2, 0.65, 1]}
            style={styles.gradient}
          >
            <View style={styles.content}>
              {/* Locandina piccola e NITIDA: a questa dimensione il poster a bassa
                  risoluzione non si sgrana, e la card è uguale per ogni film. */}
              {posterUrl ? (
                <Image source={{ uri: posterUrl }} style={styles.posterCard} resizeMode="cover" />
              ) : (
                <View style={[styles.posterCard, styles.posterPlaceholder]}>
                  <Text style={styles.posterPlaceholderText} numberOfLines={4}>{item.title}</Text>
                </View>
              )}

              <View style={styles.info}>
                <View style={styles.badges}>
                  <View style={styles.nowPlayingBadge}>
                    <Text style={styles.nowPlayingText}>AL CINEMA ORA</Text>
                  </View>
                </View>
                <Text style={styles.title} numberOfLines={2}>{item.title}</Text>
                {genres ? <Text style={styles.genres} numberOfLines={1}>{genres}</Text> : null}
                {item.cinemaNames?.length > 0 && (
                  <Text style={styles.cinemaInfo} numberOfLines={1}>
                    {item.cinemaNames.join(' · ')}
                  </Text>
                )}
                <View style={styles.buttons}>
                  <TouchableOpacity style={styles.playButton} onPress={() => onPress(item)}>
                    <Ionicons name="time-outline" size={16} color={Colors.dark} />
                    <Text style={styles.playText}>Orari</Text>
                  </TouchableOpacity>
                  <TouchableOpacity
                    style={styles.trailerButton}
                    onPress={() => {
                      const q = encodeURIComponent(`${item.title} trailer`);
                      Linking.openURL(`https://www.youtube.com/results?search_query=${q}`);
                    }}
                  >
                    <Ionicons name="logo-youtube" size={16} color="#FF0000" />
                    <Text style={styles.trailerText}>Trailer</Text>
                  </TouchableOpacity>
                </View>
              </View>
            </View>
          </LinearGradient>
        </View>
      </TouchableOpacity>
    );
  };

  if (!visibleMovies || visibleMovies.length === 0) return null;

  return (
    <View
      style={styles.container}
      onLayout={(e) => setSlideWidth(e.nativeEvent.layout.width)}
    >
      <FlatList
        ref={flatListRef}
        data={visibleMovies}
        keyExtractor={(item) => String(item.id)}
        renderItem={renderItem}
        horizontal
        pagingEnabled
        showsHorizontalScrollIndicator={false}
        snapToInterval={slideWidth}
        snapToAlignment="center"
        decelerationRate="fast"
        onScroll={onScroll}
        scrollEventThrottle={16}
        extraData={slideWidth}
      />
      {visibleMovies.length > 1 && (
        <View style={styles.dots}>
          {visibleMovies.map((_, idx) => (
            <View
              key={idx}
              style={[styles.dot, idx === activeIndex && styles.dotActive]}
            />
          ))}
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    position: 'relative',
  },
  slide: {
    height: HERO_HEIGHT,
  },
  hero: {
    height: HERO_HEIGHT,
    overflow: 'hidden',
  },
  gradient: {
    flex: 1,
    justifyContent: 'flex-end',
  },
  content: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    gap: 14,
    paddingHorizontal: 16,
    paddingBottom: 28,
  },
  posterCard: {
    width: 112,
    height: 168,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.15)',
    backgroundColor: Colors.card,
  },
  posterPlaceholder: {
    justifyContent: 'center',
    alignItems: 'center',
    padding: 6,
  },
  posterPlaceholderText: {
    color: Colors.lightGray,
    fontSize: 11,
    textAlign: 'center',
  },
  info: {
    flex: 1,
    justifyContent: 'flex-end',
    paddingBottom: 4,
  },
  badges: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
    gap: 8,
    flexWrap: 'wrap',
  },
  nowPlayingBadge: {
    backgroundColor: Colors.primary,
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 4,
  },
  nowPlayingText: {
    color: Colors.white,
    fontSize: 10,
    fontWeight: 'bold',
    letterSpacing: 1,
  },
  title: {
    color: Colors.white,
    fontSize: 22,
    fontWeight: 'bold',
    marginBottom: 4,
    textShadowColor: 'rgba(0,0,0,0.8)',
    textShadowOffset: { width: 0, height: 1 },
    textShadowRadius: 4,
  },
  genres: {
    color: Colors.primary,
    fontSize: 12,
    fontWeight: '600',
    marginBottom: 6,
  },
  cinemaInfo: {
    color: Colors.lightGray,
    fontSize: 11,
    marginBottom: 10,
    opacity: 0.85,
  },
  buttons: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    flexWrap: 'wrap',
  },
  playButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.white,
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 4,
    gap: 4,
  },
  playText: {
    color: Colors.dark,
    fontWeight: 'bold',
    fontSize: 12,
  },
  trailerButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(40,40,40,0.85)',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 4,
    gap: 4,
    borderWidth: 1,
    borderColor: '#FF0000',
  },
  trailerText: {
    color: Colors.white,
    fontWeight: '600',
    fontSize: 12,
  },
  dots: {
    flexDirection: 'row',
    justifyContent: 'center',
    position: 'absolute',
    bottom: 16,
    left: 0,
    right: 0,
    gap: 6,
  },
  dot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: 'rgba(255,255,255,0.3)',
  },
  dotActive: {
    backgroundColor: Colors.primary,
    width: 20,
  },
});
