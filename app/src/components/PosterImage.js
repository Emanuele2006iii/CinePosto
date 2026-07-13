import React, { useEffect, useState } from 'react';
import { View, Image, StyleSheet } from 'react-native';

// Mostra una locandina nel riquadro verticale dato.
// Alcuni cinema (es. PostModernissimo) non forniscono veri poster ma
// immagini panoramiche 16:9: ritagliarle nel formato 2:3 le rovina.
// Qui le rileviamo con Image.getSize e le mostriamo intere, sopra una
// versione sfocata e scurita di sé stesse che riempie il riquadro.
export default function PosterImage({ uri, style }) {
  const [isLandscape, setIsLandscape] = useState(false);

  useEffect(() => {
    let mounted = true;
    Image.getSize(
      uri,
      (w, h) => { if (mounted) setIsLandscape(w > h); },
      () => {} // se le dimensioni non si leggono, rendering normale
    );
    return () => { mounted = false; };
  }, [uri]);

  if (!isLandscape) {
    return <Image source={{ uri }} style={style} resizeMode="cover" />;
  }

  return (
    <View style={[style, styles.frame]}>
      <Image source={{ uri }} style={StyleSheet.absoluteFill} resizeMode="cover" blurRadius={14} />
      <View style={[StyleSheet.absoluteFill, styles.dim]} />
      <Image source={{ uri }} style={StyleSheet.absoluteFill} resizeMode="contain" />
    </View>
  );
}

const styles = StyleSheet.create({
  frame: {
    overflow: 'hidden',
  },
  dim: {
    backgroundColor: 'rgba(0,0,0,0.35)',
  },
});
