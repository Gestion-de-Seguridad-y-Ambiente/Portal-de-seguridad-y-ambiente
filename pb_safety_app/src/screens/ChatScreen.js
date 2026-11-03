import React, { useState, useRef } from 'react';
import {
  View, Text, TextInput, TouchableOpacity, FlatList,
  StyleSheet, ActivityIndicator, KeyboardAvoidingView, Platform,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { preguntarIA } from '../utils/gemini';

const C = {
  bg:'#0d1117', surf:'#161b22', surf2:'#1f2937', border:'#2d3748',
  fg:'#e2e8f0', muted:'#8b97a9', accent:'#f6c90e', accentFg:'#0d1117',
  ok:'#38c46a', bad:'#e05a3a',
};

const SUGERENCIAS = [
  'Trabajadores de [empresa] con acceso',
  '¿Quiénes tienen IESS vencido?',
  'Lista de trabajadores aptos para altura',
  '¿Cuántos tienen inducción vigente?',
];

export default function ChatScreen({ route, navigation }) {
  const { data } = route.params;
  const [messages, setMessages] = useState([
    {
      id: '0', role: 'bot',
      text: `Hola 👷 Soy tu asistente de contratistas. Tengo ${data.workers.length} trabajadores cargados.\n\nPregúntame en lenguaje natural, por ejemplo:\n• "Trabajadores de Empresa X con acceso"\n• "¿Quién tiene IESS vencido?"\n• "Fernández tiene certificado médico?"`,
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const listRef = useRef(null);

  const send = async (texto) => {
    const q = (texto || input).trim();
    if (!q || loading) return;
    setInput('');

    const userMsg = { id: Date.now().toString(), role: 'user', text: q };
    setMessages(prev => [...prev, userMsg]);

    setLoading(true);
    try {
      const respuesta = await preguntarIA(q, data.workers, data.col, data.headers);
      setMessages(prev => [...prev, { id: Date.now().toString() + 'b', role: 'bot', text: respuesta }]);
    } catch (e) {
      setMessages(prev => [...prev, {
        id: Date.now().toString() + 'e', role: 'bot',
        text: 'Error al consultar el asistente. Verifica tu API key de Gemini.',
      }]);
    } finally {
      setLoading(false);
      setTimeout(() => listRef.current?.scrollToEnd({ animated: true }), 100);
    }
  };

  return (
    <SafeAreaView style={{ flex:1, backgroundColor: C.bg }} edges={['top','bottom']}>
      <View style={s.header}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={s.backBtn}>
          <Text style={{ color: C.accent, fontSize: 16 }}>‹ Volver</Text>
        </TouchableOpacity>
        <Text style={s.headerTitle}>✨ Asistente IA</Text>
        <View style={{ width: 60 }} />
      </View>

      <KeyboardAvoidingView style={{ flex:1 }} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
        <FlatList
          ref={listRef}
          data={messages}
          keyExtractor={m => m.id}
          contentContainerStyle={{ padding: 16, gap: 10 }}
          renderItem={({ item: m }) => (
            <View style={[s.bubble, m.role === 'user' ? s.bubbleUser : s.bubbleBot]}>
              <Text style={[s.bubbleTxt, m.role === 'user' ? { color: C.accentFg } : { color: C.fg }]}>
                {m.text}
              </Text>
            </View>
          )}
          ListFooterComponent={loading ? (
            <View style={s.bubbleBot}>
              <ActivityIndicator color={C.accent} size="small" />
            </View>
          ) : null}
        />

        {/* Sugerencias (solo si no hay mensajes del usuario) */}
        {messages.length === 1 && (
          <View style={s.sugerencias}>
            {SUGERENCIAS.map((s2, i) => (
              <TouchableOpacity key={i} style={s.chip} onPress={() => send(s2)}>
                <Text style={s.chipTxt}>{s2}</Text>
              </TouchableOpacity>
            ))}
          </View>
        )}

        {/* Input */}
        <View style={s.inputWrap}>
          <TextInput
            style={s.input}
            placeholder="Escribe tu pregunta…"
            placeholderTextColor={C.muted}
            value={input}
            onChangeText={setInput}
            multiline
            onSubmitEditing={() => send()}
          />
          <TouchableOpacity
            style={[s.sendBtn, (!input.trim() || loading) && { opacity: 0.4 }]}
            onPress={() => send()}
            disabled={!input.trim() || loading}
          >
            <Text style={{ fontSize: 20 }}>↑</Text>
          </TouchableOpacity>
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  header:     { flexDirection:'row', alignItems:'center', justifyContent:'space-between', paddingHorizontal:16, paddingVertical:10, borderBottomWidth:1, borderColor:C.border },
  backBtn:    {},
  headerTitle:{ color:C.fg, fontWeight:'700', fontSize:16 },
  bubble:     { maxWidth:'85%', borderRadius:16, padding:12 },
  bubbleUser: { alignSelf:'flex-end', backgroundColor:C.accent },
  bubbleBot:  { alignSelf:'flex-start', backgroundColor:C.surf, borderWidth:1, borderColor:C.border },
  bubbleTxt:  { fontSize:14, lineHeight:20 },
  sugerencias:{ paddingHorizontal:16, paddingBottom:8, flexDirection:'row', flexWrap:'wrap', gap:8 },
  chip:       { paddingHorizontal:12, paddingVertical:7, borderRadius:16, borderWidth:1, borderColor:C.border, backgroundColor:C.surf },
  chipTxt:    { color:C.muted, fontSize:12 },
  inputWrap:  { flexDirection:'row', alignItems:'flex-end', gap:8, padding:12, borderTopWidth:1, borderColor:C.border, backgroundColor:C.bg },
  input:      { flex:1, backgroundColor:C.surf, borderWidth:1.5, borderColor:C.border, borderRadius:12, paddingHorizontal:14, paddingVertical:10, color:C.fg, fontSize:15, maxHeight:100 },
  sendBtn:    { width:44, height:44, backgroundColor:C.accent, borderRadius:22, alignItems:'center', justifyContent:'center' },
});
