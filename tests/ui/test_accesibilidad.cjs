// Regresiones de eventos y temporizadores del JS real, con DOM mínimo simulado.
// Ejecutar opcionalmente con Node instalado: node --test tests/ui/test_accesibilidad.cjs
const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const script = fs.readFileSync(path.join(__dirname, '../../backend/antifraude/app/static/js/app.js'), 'utf8');

function harness() {
  const listeners = new Map();
  const timers = new Map();
  let nextTimer = 0;
  let focused = null;
  function element(id = '') {
    const attrs = new Map();
    return { id, textContent: '', value: 'Mensaje sintético', files: [],
      getAttribute: key => attrs.get(key) || null,
      setAttribute: (key, value) => attrs.set(key, value),
      removeAttribute: key => attrs.delete(key),
      appendChild(child) { this.textContent += child.textContent; },
      focus() { focused = id; }, select() {},
      closest(selector) { return selector === '#form-analizar' ? this : null; }
    };
  }
  const nodes = Object.fromEntries(['estado-sr', 'mensaje-analisis', 'aviso-global',
    'texto-mensaje', 'archivo-eml', 'archivo-seleccionado', 't-resultado'].map(id => [id, element(id)]));
  const form = element('form-analizar');
  form.setAttribute('data-mensajes', '#mensaje-analisis');
  const document = {
    addEventListener: (name, fn) => listeners.set(name, fn),
    getElementById: id => nodes[id],
    querySelector: selector => selector === '#resultado-final .nivel-nombre' ? { textContent: 'ALTO' } : nodes[selector.slice(1)],
    createElement: () => element(),
    createTextNode: text => ({ textContent: text }),
    body: { hasAttribute: () => true }
  };
  const window = {
    setTimeout(fn) { const id = ++nextTimer; timers.set(id, fn); return id; },
    clearTimeout(id) { timers.delete(id); }
  };
  vm.runInNewContext(script, { document, window });
  function emit(name, extra = {}, target = null) {
    listeners.get(name)({ target, detail: { elt: form, ...extra }, preventDefault() {} });
  }
  function flush() {
    for (const [id, fn] of [...timers]) { timers.delete(id); fn(); }
  }
  return { nodes, emit, flush, timers, focus: () => focused };
}

for (const event of ['htmx:sendError', 'htmx:timeout', 'htmx:afterRequest']) {
  for (const announced of [false, true]) {
    test(`${event} cancela la espera ${announced ? 'ya anunciada' : 'pendiente'}`, () => {
      const h = harness();
      h.emit('htmx:beforeRequest');
      if (announced) {
        h.flush();
        assert.match(h.nodes['estado-sr'].textContent, /Analizando/);
      }
      h.emit(event, { xhr: { status: 0 }, successful: false });
      h.flush();
      assert.equal(h.nodes['estado-sr'].textContent, '');
      assert.match(h.nodes['mensaje-analisis'].textContent, /Error:/);
      assert.equal(h.timers.size, 0);
    });
  }
}

test('un error HTTP rápido no vuelve a anunciar la espera', () => {
  const h = harness();
  h.emit('htmx:beforeRequest');
  h.emit('htmx:afterRequest', { xhr: { status: 400, responseText: '{"detail":"Archivo no válido"}' }, successful: false });
  h.flush();
  assert.equal(h.nodes['estado-sr'].textContent, '');
  assert.match(h.nodes['mensaje-analisis'].textContent, /Archivo no válido/);
});

test('la sesión caducada cancela la espera y enfoca la reconexión', () => {
  const h = harness();
  h.emit('htmx:beforeRequest');
  h.emit('htmx:afterRequest', { xhr: { status: 401 }, successful: false });
  h.flush();
  assert.equal(h.nodes['estado-sr'].textContent, '');
  assert.equal(h.focus(), 'aviso-global');
});

test('un resultado rápido deja solo el anuncio definitivo y su foco', () => {
  const h = harness();
  h.emit('htmx:beforeRequest');
  h.emit('htmx:afterSettle', { target: { id: 'resultado' } });
  assert.equal(h.timers.size, 1);
  h.flush();
  assert.equal(h.nodes['estado-sr'].textContent, 'Resultado listo: riesgo ALTO.');
  assert.equal(h.focus(), 't-resultado');
});


test('el nombre seleccionado se muestra completo como texto, incluso si parece HTML', () => {
  const h = harness();
  const name = '<img src=x onerror=alert(1)>' + 'nombre-largo-'.repeat(20) + '.eml';
  h.nodes['archivo-eml'].files = [{ name }];
  h.emit('change', {}, h.nodes['archivo-eml']);
  assert.equal(h.nodes['archivo-seleccionado'].textContent, 'Archivo seleccionado: ' + name);
});

test('quitar el archivo borra el nombre anterior y no afecta al anuncio del análisis', () => {
  const h = harness();
  h.nodes['archivo-eml'].files = [{ name: 'prueba.eml' }];
  h.emit('change', {}, h.nodes['archivo-eml']);
  h.nodes['archivo-eml'].files = [];
  h.emit('change', {}, h.nodes['archivo-eml']);
  assert.equal(h.nodes['archivo-seleccionado'].textContent, 'No ha elegido ningún archivo.');
  assert.equal(h.nodes['estado-sr'].textContent, '');
});
