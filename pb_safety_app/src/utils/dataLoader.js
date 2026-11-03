import Constants from 'expo-constants';

const SHEET_URL = Constants.expoConfig?.extra?.sheetCsvUrl || '';

// Columnas fijas (se sobreescriben al detectar encabezados)
let COL = { apellido:1, nombres:2, empresa:3, cedula:4, acceso:11, iess:7, ind_vigente:6 };
let HEADERS = [];

function norm(s) {
  return (s||'').normalize('NFD').replace(/[̀-ͯ]/g,'').toLowerCase().trim();
}

function parseCSV(text) {
  const rows = [];
  let row = [], f = '', q = false;
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (c === '"') {
      if (q && text[i+1] === '"') { f += '"'; i++; } else q = !q;
    } else if (c === ',' && !q) { row.push(f); f = ''; }
    else if ((c === '\n' || c === '\r') && !q) {
      if (c === '\r' && text[i+1] === '\n') i++;
      row.push(f); f = ''; rows.push(row); row = [];
    } else f += c;
  }
  if (f || row.length) { row.push(f); rows.push(row); }
  return rows;
}

function resolveColumns(headers) {
  const col = { apellido:1, nombres:2, empresa:3, cedula:4, acceso:11, iess:7, ind_vigente:6 };
  headers.forEach((h, i) => {
    const n = norm(h);
    if (n.includes('apellido')) col.apellido = i;
    else if (n.includes('nombre') && !n.includes('empresa')) col.nombres = i;
    else if (n.includes('empresa') || n.includes('contratista')) col.empresa = i;
    else if (n.includes('cedula') || n.includes('cédula') || n === 'ci') col.cedula = i;
    else if (n.includes('acceso')) col.acceso = i;
    else if (n.includes('iess')) col.iess = i;
    else if ((n.includes('induccion') || n.includes('inducción')) && !n.includes('fecha'))
      col.ind_vigente = i;
  });
  return col;
}

export async function cargarDatos() {
  const url = SHEET_URL;
  if (!url || url.startsWith('PEGAR')) throw new Error('URL del sheet no configurada');

  // En React Native no hay CORS — fetch directo
  const resp = await fetch(url);
  if (!resp.ok) throw new Error('HTTP ' + resp.status);
  const text = await resp.text();
  const rows = parseCSV(text);

  HEADERS = (rows[3] || []).map(h => h.trim());
  COL = resolveColumns(HEADERS);

  const companies = new Set();
  const workers = [];

  for (let i = 5; i < rows.length; i++) {
    const row = rows[i];
    if (!row || !(row[COL.apellido] || '').trim()) continue;
    workers.push(row);
    const emp = (row[COL.empresa] || '').trim();
    if (emp) companies.add(emp);
  }

  return {
    workers,
    headers: HEADERS,
    col: COL,
    companies: [...companies].sort(),
  };
}

export function iessStatus(val) {
  val = (val || '').trim();
  if (!val || val === '-') return { text: 'Sin dato', ok: null };
  const p = val.replace(/-/g, '/').split('/');
  if (p.length === 3) {
    try {
      let [d, m, a] = p.map(Number);
      if (a < 100) a += 2000;
      const hoy = new Date();
      const limM = hoy.getMonth() === 0 ? 11 : hoy.getMonth() - 1;
      const limY = hoy.getMonth() === 0 ? hoy.getFullYear() - 1 : hoy.getFullYear();
      return new Date(a, m - 1, 1) >= new Date(limY, limM, 1)
        ? { text: 'Vigente', ok: true }
        : { text: 'Vencido', ok: false };
    } catch (e) {}
  }
  return { text: val, ok: null };
}

export function cellStatus(val) {
  if (!val || !val.trim() || val.trim() === '-') return { text: 'Sin dato', ok: null };
  const n = norm(val);
  if (n.includes('vigente') || n.includes('apto') || n === 'si' || n === 'sí' || n === '✔')
    return { text: val.trim(), ok: true };
  if (n.includes('vencido') || n.includes('no apto') || n === 'no')
    return { text: val.trim(), ok: false };
  return { text: val.trim(), ok: null };
}

export function getAccesoOk(row, col) {
  return (row[col.acceso] || '').toUpperCase().includes('PERMITIDO');
}

export function buscar(query, workers, col) {
  const q = norm(query);
  if (!q) return workers;
  const tokens = q.split(/\s+/).filter(Boolean);
  return workers.filter(row => {
    const full = norm(row[col.apellido] || '') + ' ' + norm(row[col.nombres] || '');
    const ced = (row[col.cedula] || '').trim();
    return q === ced || tokens.every(t => full.includes(t));
  });
}
