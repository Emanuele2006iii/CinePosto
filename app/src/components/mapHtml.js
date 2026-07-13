// Genera l'HTML della mappa Leaflet con i marker dei cinema.
// Usato sia dalla WebView nativa che dall'iframe sul web.
export default function buildMapHtml(cinemas) {
  const markers = cinemas.map((c) => ({
    slug: c.slug,
    name: c.name,
    address: c.address,
    color: c.color,
    logo: c.logoDataUri,
    lat: c.coords.latitude,
    lon: c.coords.longitude,
  }));

  return `
  <!DOCTYPE html>
  <html>
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <style>
      body { margin: 0; padding: 0; }
      #map { width: 100%; height: 100vh; }
    </style>
  </head>
  <body>
    <div id="map"></div>
    <script>
      var map = L.map('map', { zoomControl: false }).setView([43.105, 12.33], 10);
      map.attributionControl.setPrefix(false); // niente link "Leaflet"
      // Stile "Voyager" di Carto: chiaro e leggibile, simile a Google Maps.
      L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; OpenStreetMap &copy; CARTO',
        maxZoom: 19
      }).addTo(map);

      var cinemas = ${JSON.stringify(markers)};

      cinemas.forEach(function(cinema) {
        var icon = L.divIcon({
          className: 'custom-marker',
          html: '<div style="width:44px;height:44px;border-radius:50%;overflow:hidden;border:3px solid ' + cinema.color + ';box-shadow:0 2px 8px rgba(0,0,0,0.5);background:white;"><img src="' + cinema.logo + '" style="width:100%;height:100%;object-fit:cover;" /></div>',
          iconSize: [44, 44],
          iconAnchor: [22, 22]
        });
        L.marker([cinema.lat, cinema.lon], {icon: icon})
          .addTo(map)
          .bindPopup('<b>' + cinema.name + '</b><br>' + cinema.address);
      });

      var bounds = L.latLngBounds(cinemas.map(function(c) {
        return [c.lat, c.lon];
      }));
      map.fitBounds(bounds, { padding: [40, 40] });
    </script>
  </body>
  </html>`;
}
