import React, { useState, useEffect, useCallback } from 'react';
import {
  View, Text, TextInput, FlatList, TouchableOpacity,
  StyleSheet, ActivityIndicator, ScrollView, RefreshControl,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { cargarDatos, buscar, getAccesoOk, iessStatus, cellStatus } from '../utils/dataLoader';

const C = {
  bg:     '#0d1117',
  surf:   '#161b22',
  surf2:  '#1f2937',
  border: '#2d3748',
  fg:     '#e2e8f0',
  muted:  '#8b97a9',
  accent: '#f6c90e',
  ok:     '#38c46a',
  bad:    '#e05a3a',
};

export default function HomeScreen({ navigation }) {
  const [loading, setLoading]     = useState(true);
  const [error, setError]         = useState('');
  const [data, setData]           = useState(null);   // { workers, headers, col, companies }
  const [query, setQuery]         = useState('');
  const [company, setCompany]     = useState('');
  const [fAcceso, setFAcceso]     = useState(false);
  const [fIESS, setFIESS]         = useState(false);
  const [fInd, setFInd]           = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(async (silent = false) => {
    if (!silent) setLoading(true);
    setError('');
    try {
      const d = await cargarDatos();
      setData(d);
    } catch (e) {
      setError(e.message || 'Error al cargar datos');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => { load(); }, []);

  const onRefresh = () => { setRefreshing(true); load(true); };

  const filtered = () => {
    if (!data) return [];
    let list = buscar(query, data.workers, data.col);
    if (company) list = list.filter(r => (r[data.col.empresa] || '').trim() === company);
    if (fAcceso) list = list.filter(r => getAccesoOk(r, data.col));
    if (fIESS)   list = list.filter(r => iessStatus(r[data.col.iess] || '').ok === true);
    if (fInd)    list = list.filter(r => cellStatus(r[data.col.ind_vigente] || '').ok === true);
    return list;
  };

  const rows = filtered();

  if (loading) return (
    <View style={[s.center, { backgroundColor: C.bg }]}>
      <ActivityIndicator color={C.accent} size="large" />
      <Text style={[s.muted, { marginTop: 12 }]}>Cargando consolidado…</Text>
    </View>
  );

  if (error) return (
    <View style={[s.center, { backgroundColor: C.bg, padding: 24 }]}>
      <Text style={{ fontSize: 36, marginBottom: 12 }}>⚠️</Text>
      <Text style={[s.fg, { textAlign: 'center', marginBottom: 8 }]}>{error}</Text>
      <TouchableOpacity style={s.btnAccent} onPress={() => load()}>
        <Text style={s.btnAccentTxt}>Reintentar</Text>
      </TouchableOpacity>
    </View>
  );

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: C.bg }} edges={['top']}>
      {/* Header */}
      <View style={s.header}>
        <View style={s.headerRow}>
          <View style={s.logo}><Text style={{ fontSize: 18 }}>👷</Text></View>
          <Text style={s.title}>Contratistas</Text>
          <TouchableOpacity
            style={s.iaBtn}
            onPress={() => navigation.navigate('Chat', { data })}
          >
            <Text style={s.iaBtnTxt}>✨ Asistente IA</Text>
          </TouchableOpacity>
        </View>
        {/* Search */}
        <View style={s.searchWrap}>
          <Text style={s.searchIcon}>🔍</Text>
          <TextInput
            style={s.search}
            placeholder="Nombre, apellido o cédula…"
            placeholderTextColor={C.muted}
            value={query}
            onChangeText={setQuery}
            autoCorrect={false}
          />
          {query ? (
            <TouchableOpacity onPress={() => setQuery('')} style={s.clearBtn}>
              <Text style={{ color: C.muted, fontSize: 16 }}>✕</Text>
            </TouchableOpacity>
          ) : null}
        </View>
      </View>

      {/* Filter chips */}
      <ScrollView horizontal showsHorizontalScrollIndicator={false} style={s.chipRow} contentContainerStyle={{ paddingHorizontal: 16, gap: 8 }}>
        {/* Company picker */}
        <ScrollView horizontal={false}>
          <TouchableOpacity
            style={[s.chip, company && s.chipOn]}
            onPress={() => navigation.navigate('Empresas', {
              companies: data.companies,
              selected: company,
              onSelect: c => setCompany(c),
            })}
          >
            <Text style={[s.chipTxt, company && s.chipTxtOn]}>
              {company ? `🏭 ${company}` : '🏭 Empresa'}
            </Text>
          </TouchableOpacity>
        </ScrollView>
        {[
          { key: 'fAcceso', label: '✅ Con acceso',      state: fAcceso, set: setFAcceso },
          { key: 'fIESS',   label: '🏥 IESS vigente',    state: fIESS,  set: setFIESS  },
          { key: 'fInd',    label: '📋 Inducción',        state: fInd,   set: setFInd   },
        ].map(c => (
          <TouchableOpacity key={c.key} style={[s.chip, c.state && s.chipOn]} onPress={() => c.set(!c.state)}>
            <Text style={[s.chipTxt, c.state && s.chipTxtOn]}>{c.label}</Text>
          </TouchableOpacity>
        ))}
      </ScrollView>

      {/* Count */}
      <Text style={s.count}>
        {rows.length === 0 ? 'Sin resultados' :
         rows.length === 1 ? '1 trabajador' :
         `${rows.length} trabajadores`}
        {data ? ` de ${data.workers.length}` : ''}
      </Text>

      {/* List */}
      <FlatList
        data={rows}
        keyExtractor={(_, i) => String(i)}
        contentContainerStyle={{ paddingHorizontal: 16, paddingBottom: 24 }}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={C.accent} />}
        renderItem={({ item: row }) => {
          const nombre  = `${(row[data.col.apellido] || '').trim()} ${(row[data.col.nombres] || '').trim()}`;
          const empresa = (row[data.col.empresa] || '').trim();
          const ok      = getAccesoOk(row, data.col);
          const ind     = cellStatus(row[data.col.ind_vigente] || '');
          const iess    = iessStatus(row[data.col.iess] || '');

          return (
            <TouchableOpacity
              style={s.card}
              onPress={() => navigation.navigate('Detalle', { row, data })}
              activeOpacity={0.7}
            >
              <View style={[s.dot, { backgroundColor: ok ? C.ok : C.bad }]} />
              <View style={{ flex: 1 }}>
                <Text style={s.cardName} numberOfLines={1}>{nombre}</Text>
                <Text style={s.cardMeta} numberOfLines={1}>{empresa}</Text>
                <View style={s.pillRow}>
                  <Pill label={`Ind: ${ind.text}`} ok={ind.ok} />
                  <Pill label={`IESS: ${iess.text}`} ok={iess.ok} />
                </View>
              </View>
              <Text style={{ color: C.muted, fontSize: 20 }}>›</Text>
            </TouchableOpacity>
          );
        }}
        ListEmptyComponent={
          <View style={s.empty}>
            <Text style={{ fontSize: 36, marginBottom: 8 }}>🔍</Text>
            <Text style={s.muted}>Sin resultados.</Text>
            <Text style={s.muted}>Prueba con otro nombre o limpia los filtros.</Text>
          </View>
        }
      />
    </SafeAreaView>
  );
}

function Pill({ label, ok }) {
  const bg = ok === true ? 'rgba(56,196,106,.15)' : ok === false ? 'rgba(224,90,58,.15)' : 'rgba(139,151,169,.12)';
  const fg = ok === true ? C.ok : ok === false ? C.bad : C.muted;
  return <View style={[s.pill, { backgroundColor: bg }]}><Text style={[s.pillTxt, { color: fg }]}>{label}</Text></View>;
}

const s = StyleSheet.create({
  center: { flex: 1, alignItems: 'center', justifyContent: 'center' },
  fg:     { color: C.fg },
  muted:  { color: C.muted, fontSize: 14, textAlign: 'center' },
  header: { paddingHorizontal: 16, paddingBottom: 10, borderBottomWidth: 1, borderColor: C.border },
  headerRow: { flexDirection: 'row', alignItems: 'center', marginBottom: 10, gap: 8 },
  logo:   { width: 32, height: 32, backgroundColor: C.accent, borderRadius: 8, alignItems: 'center', justifyContent: 'center' },
  title:  { flex: 1, color: C.fg, fontSize: 18, fontWeight: '700', letterSpacing: -0.3 },
  iaBtn:  { backgroundColor: C.surf2, borderWidth: 1, borderColor: C.border, borderRadius: 8, paddingHorizontal: 10, paddingVertical: 6 },
  iaBtnTxt: { color: C.accent, fontSize: 13, fontWeight: '600' },
  searchWrap: { flexDirection: 'row', alignItems: 'center', backgroundColor: C.surf, borderWidth: 1.5, borderColor: C.border, borderRadius: 10, paddingHorizontal: 10 },
  searchIcon: { marginRight: 6, fontSize: 15 },
  search: { flex: 1, color: C.fg, fontSize: 15, paddingVertical: 10 },
  clearBtn: { padding: 4 },
  chipRow: { borderBottomWidth: 1, borderColor: C.border, maxHeight: 50 },
  chip:    { paddingHorizontal: 14, paddingVertical: 8, borderRadius: 20, borderWidth: 1.5, borderColor: C.border, backgroundColor: C.surf },
  chipOn:  { backgroundColor: C.accent, borderColor: C.accent },
  chipTxt: { color: C.fg, fontSize: 13 },
  chipTxtOn: { color: C.bg, fontWeight: '700' },
  count:   { color: C.muted, fontSize: 12, paddingHorizontal: 16, paddingVertical: 6 },
  card:    { backgroundColor: C.surf, borderWidth: 1, borderColor: C.border, borderRadius: 12, padding: 13, marginBottom: 8, flexDirection: 'row', alignItems: 'center', gap: 10 },
  dot:     { width: 10, height: 10, borderRadius: 5, marginTop: 2 },
  cardName: { color: C.fg, fontSize: 15, fontWeight: '600', letterSpacing: -0.2 },
  cardMeta: { color: C.muted, fontSize: 12, marginTop: 2 },
  pillRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 4, marginTop: 6 },
  pill:    { borderRadius: 9, paddingHorizontal: 8, paddingVertical: 2 },
  pillTxt: { fontSize: 11, fontWeight: '500' },
  empty:   { alignItems: 'center', paddingVertical: 48 },
  btnAccent: { backgroundColor: C.accent, borderRadius: 10, paddingHorizontal: 24, paddingVertical: 12, marginTop: 12 },
  btnAccentTxt: { color: C.bg, fontWeight: '700', fontSize: 15 },
});
