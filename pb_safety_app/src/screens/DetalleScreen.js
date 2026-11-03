import React from 'react';
import { View, Text, ScrollView, StyleSheet, TouchableOpacity } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { getAccesoOk, iessStatus, cellStatus } from '../utils/dataLoader';

const C = {
  bg:'#0d1117', surf:'#161b22', border:'#2d3748',
  fg:'#e2e8f0', muted:'#8b97a9', accent:'#f6c90e',
  ok:'#38c46a', bad:'#e05a3a',
};

export default function DetalleScreen({ route, navigation }) {
  const { row, data } = route.params;
  const { col, headers } = data;

  const nombre  = `${(row[col.apellido]||'').trim()} ${(row[col.nombres]||'').trim()}`;
  const empresa = (row[col.empresa]||'').trim();
  const cedula  = (row[col.cedula]||'').trim();
  const ok      = getAccesoOk(row, col);

  // Construir todas las filas de certificados
  const certRows = [];
  headers.forEach((h, i) => {
    if (!h || i < 5) return;
    if (i === col.empresa || i === col.cedula || i === col.apellido || i === col.nombres) return;
    const val = (row[i] || '').trim();
    const s = i === col.iess ? iessStatus(val) : cellStatus(val);
    if (h.toLowerCase().includes('fecha') && !val) return; // skip empty date cols
    certRows.push({ label: h, ...s });
  });

  return (
    <SafeAreaView style={{ flex:1, backgroundColor: C.bg }} edges={['top','bottom']}>
      <View style={s.header}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={s.backBtn}>
          <Text style={{ color: C.accent, fontSize: 16 }}>‹ Volver</Text>
        </TouchableOpacity>
      </View>

      <ScrollView contentContainerStyle={s.container}>
        {/* Badge */}
        <View style={[s.badge, { backgroundColor: ok ? 'rgba(56,196,106,.18)' : 'rgba(224,90,58,.18)' }]}>
          <Text style={[s.badgeTxt, { color: ok ? C.ok : C.bad }]}>
            {ok ? 'ACCESO PERMITIDO' : 'SIN ACCESO'}
          </Text>
        </View>

        {/* Nombre */}
        <Text style={s.nombre}>{nombre}</Text>
        <Text style={s.meta}>{empresa}</Text>
        {cedula ? <Text style={s.meta}>CI: {cedula}</Text> : null}

        {/* Documentos */}
        <Text style={s.secTitle}>Estado de documentos</Text>
        <View style={s.table}>
          {certRows.map((r, i) => (
            <View key={i} style={[s.row, i < certRows.length-1 && s.rowBorder]}>
              <Text style={s.rowLabel} numberOfLines={2}>{r.label}</Text>
              <Text style={[s.rowVal, { color: r.ok === true ? C.ok : r.ok === false ? C.bad : C.muted }]}>
                {r.text || 'Sin dato'}
              </Text>
            </View>
          ))}
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  header:   { paddingHorizontal: 16, paddingVertical: 10, borderBottomWidth: 1, borderColor: '#2d3748' },
  backBtn:  { alignSelf: 'flex-start' },
  container:{ padding: 20, paddingBottom: 48 },
  badge:    { alignSelf: 'flex-start', borderRadius: 8, paddingHorizontal: 12, paddingVertical: 5, marginBottom: 12 },
  badgeTxt: { fontSize: 12, fontWeight: '700', letterSpacing: 0.5 },
  nombre:   { color: C.fg, fontSize: 22, fontWeight: '700', letterSpacing: -0.5, lineHeight: 28 },
  meta:     { color: C.muted, fontSize: 14, marginTop: 4 },
  secTitle: { color: C.muted, fontSize: 11, fontWeight: '700', letterSpacing: 1, textTransform: 'uppercase', marginTop: 24, marginBottom: 10 },
  table:    { backgroundColor: C.surf, borderRadius: 12, borderWidth: 1, borderColor: C.border, overflow: 'hidden' },
  row:      { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', padding: 13, gap: 12 },
  rowBorder:{ borderBottomWidth: 1, borderColor: C.border },
  rowLabel: { color: C.fg, fontSize: 14, flex: 1 },
  rowVal:   { fontSize: 13, fontWeight: '600', flexShrink: 0 },
});
