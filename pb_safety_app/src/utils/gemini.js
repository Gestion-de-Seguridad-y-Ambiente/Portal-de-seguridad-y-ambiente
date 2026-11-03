import { GoogleGenerativeAI } from '@google/generative-ai';
import Constants from 'expo-constants';
import { iessStatus, cellStatus, getAccesoOk } from './dataLoader';

const API_KEY = Constants.expoConfig?.extra?.geminiApiKey || '';

function workerToText(row, col, headers) {
  const nombre = `${(row[col.apellido] || '').trim()} ${(row[col.nombres] || '').trim()}`;
  const empresa = (row[col.empresa] || '').trim();
  const cedula = (row[col.cedula] || '').trim();
  const acceso = getAccesoOk(row, col) ? 'ACCESO PERMITIDO' : 'SIN ACCESO';

  const certs = [];
  headers.forEach((h, i) => {
    if (!h || i < 5) return;
    if (i === col.empresa || i === col.cedula || i === col.apellido || i === col.nombres) return;
    const val = (row[i] || '').trim();
    if (!val) return;
    const s = i === col.iess ? iessStatus(val) : cellStatus(val);
    certs.push(`${h}: ${s.text}`);
  });

  return `${nombre} | ${empresa} | CI:${cedula} | ${acceso} | ${certs.join(' | ')}`;
}

export async function preguntarIA(pregunta, workers, col, headers) {
  if (!API_KEY || API_KEY.startsWith('PEGAR')) {
    return 'Configura tu API Key de Gemini en app.json para usar el asistente.';
  }

  const genAI = new GoogleGenerativeAI(API_KEY);
  const model = genAI.getGenerativeModel({ model: 'gemini-1.5-flash' });

  // Preparar resumen de datos (máx 500 trabajadores para no exceder contexto)
  const muestra = workers.slice(0, 500);
  const datosTexto = muestra.map(r => workerToText(r, col, headers)).join('\n');

  const columnas = headers.filter(Boolean).join(', ');

  const prompt = `Eres un asistente de seguridad industrial en la empresa Plantabal (Ecuador).
Tienes acceso al consolidado de contratistas con ${workers.length} trabajadores.

Columnas disponibles: ${columnas}

Datos del consolidado:
${datosTexto}

Pregunta del técnico en campo: "${pregunta}"

Responde de forma clara y directa en español. Si es una lista, enumérala.
Si preguntas por una persona específica, da su estado completo.
Si no hay datos suficientes, dilo claramente.`;

  const result = await model.generateContent(prompt);
  return result.response.text();
}
