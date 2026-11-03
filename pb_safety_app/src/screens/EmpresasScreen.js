import React from 'react';
import { View, Text, FlatList, TouchableOpacity, StyleSheet } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

const C = { bg:'#0d1117', surf:'#161b22', border:'#2d3748', fg:'#e2e8f0', muted:'#8b97a9', accent:'#f6c90e' };

export default function EmpresasScreen({ route, navigation }) {
  const { companies, selected, onSelect } = route.params;

  const choose = (c) => {
    onSelect(c);
    navigation.goBack();
  };

  return (
    <SafeAreaView style={{ flex:1, backgroundColor: C.bg }} edges={['top','bottom']}>
      <View style={s.header}>
        <TouchableOpacity onPress={() => navigation.goBack()}>
          <Text style={{ color: C.accent, fontSize: 16 }}>‹ Cancelar</Text>
        </TouchableOpacity>
        <Text style={s.title}>Seleccionar empresa</Text>
        <View style={{ width: 70 }} />
      </View>
      <FlatList
        data={[{ name: 'Todas las empresas', key: '' }, ...companies.map(c => ({ name: c, key: c }))]}
        keyExtractor={i => i.key}
        contentContainerStyle={{ paddingVertical: 8 }}
        renderItem={({ item }) => (
          <TouchableOpacity style={s.row} onPress={() => choose(item.key)}>
            <Text style={[s.name, item.key === selected && { color: C.accent }]}>{item.name}</Text>
            {item.key === selected && <Text style={{ color: C.accent }}>✓</Text>}
          </TouchableOpacity>
        )}
      />
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  header: { flexDirection:'row', alignItems:'center', justifyContent:'space-between', paddingHorizontal:16, paddingVertical:12, borderBottomWidth:1, borderColor:'#2d3748' },
  title:  { color:'#e2e8f0', fontWeight:'700', fontSize:16 },
  row:    { flexDirection:'row', justifyContent:'space-between', alignItems:'center', paddingHorizontal:20, paddingVertical:16, borderBottomWidth:1, borderColor:'#1f2937' },
  name:   { color:'#e2e8f0', fontSize:15 },
});
