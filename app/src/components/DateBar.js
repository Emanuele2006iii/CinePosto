// Barra orizzontale di selezione data: oggi + i 6 giorni successivi.
import React from 'react';
import { View, Text, FlatList, TouchableOpacity, StyleSheet } from 'react-native';
import Colors from '../constants/colors';
import { getNext7Days, formatShortDate, isToday } from '../utils/dates';

export default function DateBar({ selectedDate, onDateSelect }) {
  const dates = getNext7Days();

  return (
    <View style={styles.container}>
      <FlatList
        data={dates}
        keyExtractor={(item) => item}
        horizontal
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={styles.list}
        renderItem={({ item }) => {
          const isActive = item === selectedDate;
          return (
            <TouchableOpacity
              style={[styles.pill, isActive && styles.pillActive]}
              onPress={() => onDateSelect(item)}
              activeOpacity={0.7}
            >
              <Text style={[styles.pillText, isActive && styles.pillTextActive]}>
                {isToday(item) ? 'Oggi' : formatShortDate(item)}
              </Text>
            </TouchableOpacity>
          );
        }}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    marginTop: 12,
    marginBottom: 4,
  },
  list: {
    paddingHorizontal: 16,
    gap: 8,
  },
  pill: {
    alignItems: 'center',
    backgroundColor: Colors.card,
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 20,
    minWidth: 60,
  },
  pillActive: {
    backgroundColor: Colors.primary,
  },
  pillText: {
    color: Colors.lightGray,
    fontSize: 11,
    fontWeight: '600',
    marginBottom: 2,
  },
  pillTextActive: {
    color: Colors.white,
  },
});
