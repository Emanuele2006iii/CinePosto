// Base URL del backend FastAPI.
// Si sovrascrive a runtime con la variabile d'ambiente EXPO_PUBLIC_API_BASE,
// che Expo inserisce nel bundle all'avvio/build:
//   EXPO_PUBLIC_API_BASE="http://<IP-DEL-MAC>:8000/api/v1" npx expo start
//
// Il default 'localhost' va bene su web e simulatore iOS; su un telefono
// reale (Expo Go) serve l'IP di rete locale del computer che esegue il backend.
export const API_BASE =
  process.env.EXPO_PUBLIC_API_BASE || 'http://localhost:8000/api/v1';
