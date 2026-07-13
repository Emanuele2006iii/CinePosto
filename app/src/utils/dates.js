// Utility condivise per le date, sempre in ora locale.
// Prima erano duplicate in DateBar e MovieDetailScreen, e usavano
// toISOString() che ragiona in UTC: in Italia, tra mezzanotte e le 2
// di notte, avrebbe restituito la data di ieri.

export const DAY_NAMES = ['Dom', 'Lun', 'Mar', 'Mer', 'Gio', 'Ven', 'Sab'];

// Converte una Date in stringa 'YYYY-MM-DD' usando l'ora locale.
export function toDateString(date) {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, '0');
  const d = String(date.getDate()).padStart(2, '0');
  return `${y}-${m}-${d}`;
}

export function getToday() {
  return toDateString(new Date());
}

// Le prossime 7 date (oggi inclusa) come stringhe 'YYYY-MM-DD'.
export function getNext7Days() {
  const days = [];
  const today = new Date();
  for (let i = 0; i < 7; i++) {
    const d = new Date(today);
    d.setDate(today.getDate() + i);
    days.push(toDateString(d));
  }
  return days;
}

// 'YYYY-MM-DD' -> 'Gio 4' (il T12:00:00 evita slittamenti di fuso).
export function formatShortDate(dateStr) {
  const d = new Date(dateStr + 'T12:00:00');
  return `${DAY_NAMES[d.getDay()]} ${d.getDate()}`;
}

export function isToday(dateStr) {
  return dateStr === getToday();
}
