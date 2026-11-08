/*
 * Asistente antifraude — comportamiento de la interfaz (F0-06).
 * - Sin eval ni manejadores en línea (CSP estricta).
 * - El token CSRF se pide a GET /session y se guarda SOLO en memoria
 *   (nunca en el HTML, en URLs ni en localStorage/sessionStorage).
 * - Los mensajes del servidor se muestran con textContent (sin inyectar HTML).
 */
(function () {
  "use strict";

  var csrfToken = null;
  var ICONOS = { ok: "✅ ", info: "ℹ️ ", aviso: "⚠️ ", error: "⛔ " };

  function mostrar(selector, texto, tipo) {
    var el = document.querySelector(selector);
    if (!el) { return; }
    el.textContent = (ICONOS[tipo] || "") + texto;
    el.setAttribute("data-tipo", tipo || "info");
    el.hidden = false;
  }

  function detalle(xhr, porDefecto) {
    try {
      var datos = JSON.parse(xhr.responseText);
      if (datos && typeof datos.detail === "string") { return datos.detail; }
    } catch (e) { /* respuesta sin JSON */ }
    return porDefecto;
  }

  function sesionCaducada() {
    var aviso = document.getElementById("aviso-global");
    if (!aviso) { return; }
    mostrar("#aviso-global",
      "Su sesión ha caducado por seguridad. Vuelva a conectar este navegador con un código del asistente. ",
      "aviso");
    var enlace = document.createElement("a");
    enlace.href = "/emparejar";
    enlace.className = "boton boton-secundario";
    enlace.textContent = "Volver a conectar";
    aviso.appendChild(enlace);
    enlace.focus();
  }

  function cargarCsrf() {
    if (!document.body.hasAttribute("data-autenticado")) { return; }
    fetch("/session", { credentials: "same-origin", cache: "no-store", headers: { "Accept": "application/json" } })
      .then(function (r) {
        if (r.status === 401) { sesionCaducada(); return null; }
        return r.ok ? r.json() : null;
      })
      .then(function (datos) { if (datos && datos.csrf_token) { csrfToken = datos.csrf_token; } })
      .catch(function () {
        mostrar("#aviso-global", "No se puede conectar con el asistente. Compruebe que su ventana sigue abierta.", "error");
      });
  }

  function destinoMensajes(elt) {
    if (!elt) { return null; }
    if (elt.getAttribute && elt.getAttribute("data-mensajes")) { return elt.getAttribute("data-mensajes"); }
    var form = elt.closest ? elt.closest("[data-mensajes]") : null;
    return form ? form.getAttribute("data-mensajes") : null;
  }

  // Añade el token CSRF (si existe) a cada petición htmx.
  document.addEventListener("htmx:configRequest", function (evt) {
    if (csrfToken) { evt.detail.headers["X-CSRF-Token"] = csrfToken; }
  });

  // Mensajes de éxito y error en lenguaje sencillo.
  document.addEventListener("htmx:afterRequest", function (evt) {
    var xhr = evt.detail.xhr;
    var selector = destinoMensajes(evt.detail.elt);
    if (!xhr || xhr.status === 0) { return; }
    if (evt.detail.successful) {
      if (selector && xhr.status === 202) { mostrar(selector, detalle(xhr, "Hecho."), "ok"); }
      return;
    }
    if (xhr.status === 401 && document.body.hasAttribute("data-autenticado")) { sesionCaducada(); return; }
    if (selector) {
      mostrar(selector, detalle(xhr, "No se ha podido completar la operación. Inténtelo de nuevo."), "error");
      if (selector === "#mensaje-emparejar") {
        var campo = document.getElementById("codigo");
        if (campo) { campo.focus(); campo.select(); }
      }
    }
  });

  // Sin conexión con el servidor local.
  document.addEventListener("htmx:sendError", function () {
    mostrar("#aviso-global", "No se puede conectar con el asistente. Compruebe que su ventana sigue abierta.", "error");
  });

  document.addEventListener("DOMContentLoaded", cargarCsrf);
})();
