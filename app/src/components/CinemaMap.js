import React from 'react';
import { WebView } from 'react-native-webview';
import buildMapHtml from './mapHtml';

// Versione NATIVA (iOS/Android) della mappa: usa react-native-webview.
// Sul web Metro carica automaticamente CinemaMap.web.js al suo posto.
export default function CinemaMap({ cinemas, style }) {
  return (
    <WebView
      source={{ html: buildMapHtml(cinemas) }}
      style={style}
      originWhitelist={['*']}
      scrollEnabled={false}
      javaScriptEnabled={true}
    />
  );
}
