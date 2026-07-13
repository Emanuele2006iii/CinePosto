import React from 'react';
import { View } from 'react-native';
import buildMapHtml from './mapHtml';

// Versione WEB della mappa: react-native-webview non esiste nel browser,
// quindi usiamo un normale <iframe> con lo stesso HTML Leaflet.
export default function CinemaMap({ cinemas, style }) {
  return (
    <View style={style}>
      <iframe
        srcDoc={buildMapHtml(cinemas)}
        title="Mappa dei cinema"
        style={{ width: '100%', height: '100%', border: 'none' }}
      />
    </View>
  );
}
