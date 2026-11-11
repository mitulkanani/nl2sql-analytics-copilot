const $ = (id) => document.getElementById(id);
const form = $('query-form');
const question = $('question');
let lastSql = '';

function element(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = String(text);
  return node;
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
    ...options,
  });
  const payload = await response.json();
  if (!response.ok) throw new Error(payload.detail || `Request failed (${response.status})`);
  return payload;
}

function showError(message) {
  $('error-panel').textContent = message;
  $('error-panel').classList.remove('hidden');
}

function hideError() {
  $('error-panel').classList.add('hidden');
  $('error-panel').textContent = '';
}

function renderTable(columns, rows) {
  const head = $('table-head');
  const body = $('table-body');
  head.replaceChildren();
  body.replaceChildren();
  const header = document.createElement('tr');
  columns.forEach((column) => header.appendChild(element('th', '', column)));
  head.appendChild(header);
  rows.forEach((row) => {
    const tr = document.createElement('tr');
    columns.forEach((column) => {
      const value = row[column];
      const display = typeof value === 'number' ? value.toLocaleString(undefined, { maximumFractionDigits: 2 }) : (value ?? '—');
      tr.appendChild(element('td', '', display));
    });
    body.appendChild(tr);
  });
  if (!rows.length) body.appendChild(element('tr', '', 'No rows matched this question.'));
}

function renderChart(result) {
  const area = $('chart-area');
  area.replaceChildren();
  $('chart-type').textContent = result.chart_type.toUpperCase();
  if (!result.chart_x || !result.chart_y || !result.rows.length || result.chart_type === 'table') {
    area.appendChild(element('div', 'chart-empty', 'A table view is the best fit for this result.'));
    return;
  }
  const ns = 'http://www.w3.org/2000/svg';
  const svg = document.createElementNS(ns, 'svg');
  svg.setAttribute('viewBox', '0 0 620 220');
  const values = result.rows.map((row) => Math.max(0, Number(row[result.chart_y]) || 0));
  const max = Math.max(...values, 1);
  const addText = (x, y, text, anchor = 'middle') => {
    const node = document.createElementNS(ns, 'text');
    node.setAttribute('x', x); node.setAttribute('y', y);
    node.setAttribute('text-anchor', anchor); node.setAttribute('font-size', '9');
    node.setAttribute('fill', '#8894a5'); node.textContent = text;
    svg.appendChild(node);
  };

  if (result.chart_type === 'pie') {
    const total = values.reduce((sum, value) => sum + value, 0) || 1;
    const colors = ['#6675e8', '#27a783', '#f0ae52', '#a48be8', '#e17b85', '#66a9cb'];
    const radius = 65;
    const circumference = 2 * Math.PI * radius;
    let offset = 0;
    values.forEach((value, index) => {
      const portion = value / total;
      const circle = document.createElementNS(ns, 'circle');
      circle.setAttribute('cx', 105); circle.setAttribute('cy', 106); circle.setAttribute('r', radius);
      circle.setAttribute('fill', 'none'); circle.setAttribute('stroke', colors[index % colors.length]);
      circle.setAttribute('stroke-width', '27');
      circle.setAttribute('stroke-dasharray', `${portion * circumference} ${circumference}`);
      circle.setAttribute('stroke-dashoffset', String(-offset));
      circle.setAttribute('transform', 'rotate(-90 105 106)');
      svg.appendChild(circle);
      offset += portion * circumference;
      const legendY = 45 + index * Math.min(28, 150 / Math.max(values.length, 1));
      const swatch = document.createElementNS(ns, 'rect');
      swatch.setAttribute('x', 225); swatch.setAttribute('y', legendY - 9);
      swatch.setAttribute('width', 9); swatch.setAttribute('height', 9);
      swatch.setAttribute('rx', 2); swatch.setAttribute('fill', colors[index % colors.length]);
      svg.appendChild(swatch);
      const name = String(result.rows[index][result.chart_x] ?? '');
      const label = name.length > 22 ? `${name.slice(0, 21)}…` : name;
      addText(242, legendY, `${label} · ${value.toLocaleString()}`, 'start');
    });
    addText(105, 111, `${values.length}`, 'middle');
    area.appendChild(svg);
    return;
  }

  const plotTop = 10, plotHeight = 165, left = 54, plotWidth = 540;
  [0, 0.5, 1].forEach((ratio) => {
    const y = plotTop + plotHeight * (1 - ratio);
    const line = document.createElementNS(ns, 'line');
    line.setAttribute('x1', left); line.setAttribute('x2', left + plotWidth);
    line.setAttribute('y1', y); line.setAttribute('y2', y);
    line.setAttribute('stroke', '#e9edf3'); line.setAttribute('stroke-dasharray', '3 4');
    svg.appendChild(line);
  });
  if (result.chart_type === 'line') {
    const points = values.map((value, index) => ({
      x: left + (values.length === 1 ? plotWidth / 2 : index * plotWidth / (values.length - 1)),
      y: plotTop + plotHeight - (value / max) * plotHeight,
    }));
    const path = document.createElementNS(ns, 'polyline');
    path.setAttribute('points', points.map((point) => `${point.x},${point.y}`).join(' '));
    path.setAttribute('fill', 'none'); path.setAttribute('stroke', '#6675e8');
    path.setAttribute('stroke-width', '3'); path.setAttribute('stroke-linecap', 'round');
    path.setAttribute('stroke-linejoin', 'round'); svg.appendChild(path);
    points.forEach((point, index) => {
      const circle = document.createElementNS(ns, 'circle');
      circle.setAttribute('cx', point.x); circle.setAttribute('cy', point.y);
      circle.setAttribute('r', '4'); circle.setAttribute('fill', '#fff');
      circle.setAttribute('stroke', '#6675e8'); circle.setAttribute('stroke-width', '2');
      svg.appendChild(circle);
      const text = String(result.rows[index][result.chart_x] ?? '');
      addText(point.x, 195, text.length > 10 ? `${text.slice(0, 9)}…` : text);
    });
  } else {
    const gap = 9;
    const barWidth = Math.max(12, (plotWidth - gap * (values.length - 1)) / values.length);
    values.forEach((value, index) => {
      const height = (value / max) * plotHeight;
      const rect = document.createElementNS(ns, 'rect');
      rect.setAttribute('x', left + index * (barWidth + gap));
      rect.setAttribute('y', plotTop + plotHeight - height);
      rect.setAttribute('width', barWidth); rect.setAttribute('height', Math.max(2, height));
      rect.setAttribute('rx', 4); rect.setAttribute('fill', '#6675e8');
      svg.appendChild(rect);
      const text = String(result.rows[index][result.chart_x] ?? '');
      addText(left + index * (barWidth + gap) + barWidth / 2, 195, text.length > 11 ? `${text.slice(0, 10)}…` : text);
    });
  }
  area.appendChild(svg);
}

function renderResult(result) {
  $('results').classList.remove('hidden');
  $('result-title').textContent = result.question;
  $('provider-badge').textContent = `${result.provider.toUpperCase()} PROVIDER`;
  $('explanation').textContent = result.explanation;
  $('row-count').textContent = result.rows_returned;
  $('execution-time').textContent = `${result.execution_ms} ms`;
  $('result-status').textContent = result.truncated ? 'Limited' : 'Complete';
  $('truncated-label').classList.toggle('hidden', !result.truncated);
  $('sql-code').textContent = result.sql;
  lastSql = result.sql;
  renderTable(result.columns, result.rows);
  renderChart(result);
  $('results').scrollIntoView({ behavior: 'smooth', block: 'start' });
}

async function loadHistory() {
  try {
    const history = await api('/api/history?limit=8');
    const list = $('history-list');
    list.replaceChildren();
    if (!history.length) list.appendChild(element('div', 'empty-state', 'Your recent questions will appear here.'));
    history.forEach((item) => {
      const row = element('div', 'history-row');
      row.appendChild(element('div', 'history-question', item.question));
      row.appendChild(element('div', 'history-meta', `${item.rows_returned} rows · ${item.execution_ms} ms · ${item.provider}`));
      list.appendChild(row);
    });
  } catch (error) { showError(error.message); }
}

async function loadSchema() {
  try {
    const data = await api('/api/schema');
    const list = $('schema-list');
    list.replaceChildren();
    data.tables.forEach((table) => {
      const node = element('div', 'schema-table');
      node.appendChild(element('strong', '', table.name));
      node.appendChild(element('p', '', table.description));
      node.appendChild(element('div', 'schema-columns', table.columns.map((column) => column.name).join(' · ')));
      list.appendChild(node);
    });
  } catch (error) { showError(error.message); }
}

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  hideError();
  const text = question.value.trim();
  if (!text) return;
  const button = $('ask-button');
  button.disabled = true;
  button.textContent = 'Analyzing…';
  try {
    const result = await api('/api/query', { method: 'POST', body: JSON.stringify({ question: text }) });
    renderResult(result);
    await loadHistory();
  } catch (error) {
    showError(error.message);
  } finally {
    button.disabled = false;
    button.innerHTML = 'Run analysis <span>↗</span>';
  }
});

document.querySelectorAll('.example-chip').forEach((button) => {
  button.addEventListener('click', () => {
    question.value = button.dataset.question;
    question.focus();
  });
});
$('copy-sql').addEventListener('click', async () => {
  if (!lastSql) return;
  try { await navigator.clipboard.writeText(lastSql); $('copy-sql').textContent = 'Copied'; }
  catch { $('copy-sql').textContent = 'Copy unavailable'; }
  setTimeout(() => { $('copy-sql').textContent = 'Copy SQL'; }, 1500);
});
$('refresh-history').addEventListener('click', loadHistory);
loadSchema();
loadHistory();
