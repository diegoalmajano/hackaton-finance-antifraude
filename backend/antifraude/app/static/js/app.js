/*
 * Asistente antifraude — comportamiento de la interfaz.
 * - Sin eval ni manejadores en línea (CSP estricta).
 * - El token CSRF se pide a GET /session y se guarda SOLO en memoria
 *   (nunca en el HTML, en URLs ni en localStorage/sessionStorage).
 * - Los mensajes se escriben con textContent (sin inyectar HTML); los iconos van
 *   ocultos a los lectores de pantalla y el tipo se dice con palabras («Error:»).
 * - Accesibilidad (revisión a11y): el foco se lleva al resultado, se anuncia una sola
 *   línea breve, se anuncia «Analizando…», se limpian errores antiguos y hay tiempo máximo.
 */
(function () {
  "use strict";

  var csrfToken = null;
  var ICONOS = { ok: "✅", info: "ℹ️", aviso: "⚠️", error: "⛔" };
  var PREFIJOS = { ok: "", info: "", aviso: "Aviso: ", error: "Error: " };

  function anunciar(id, texto) {
    var el = document.getElementById(id);
    if (!el) { return; }
    el.textContent = "";
    window.setTimeout(function () { el.textContent = texto; }, 50);  // fuerza el anuncio
  }

  function mostrar(selector, texto, tipo) {
    var el = document.querySelector(selector);
    if (!el) { return; }
    tipo = tipo || "info";
    el.textContent = "";
    var icono = document.createElement("span");
    icono.setAttribute("aria-hidden", "true");
    icono.textContent = ICONOS[tipo] || "";
    el.appendChild(icono);
    el.appendChild(document.createTextNode(" " + (PREFIJOS[tipo] || "") + texto));
    el.setAttribute("data-tipo", tipo);
  }

  function limpiar(selector) {
    var el = selector && document.querySelector(selector);
    if (el) { el.textContent = ""; el.removeAttribute("data-tipo"); }
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
      "Su sesión ha caducado por seguridad. Vuelva a conectar este navegador con un código nuevo del asistente. ",
      "aviso");
    var enlace = document.createElement("a");
    enlace.href = "/emparejar";
    enlace.className = "boton boton-secundario";
    enlace.textContent = "Volver a conectar";
    aviso.appendChild(enlace);
    aviso.setAttribute("tabindex", "-1");
    aviso.focus();  // se lee el mensaje completo; después, Tab lleva al enlace
  }

  var MSG_SIN_CONEXION = "No se puede conectar con el asistente. Compruebe que sigue abierta la ventana del asistente " +
    "(la ventana donde apareció el código).";

  function cargarCsrf() {
    if (!document.body.hasAttribute("data-autenticado")) { return; }
    fetch("/session", { credentials: "same-origin", cache: "no-store", headers: { "Accept": "application/json" } })
      .then(function (r) {
        if (r.status === 401) { sesionCaducada(); return null; }
        return r.ok ? r.json() : null;
      })
      .then(function (datos) { if (datos && datos.csrf_token) { csrfToken = datos.csrf_token; } })
      .catch(function () { mostrar("#aviso-global", MSG_SIN_CONEXION, "error"); });
  }

  function destinoMensajes(elt) {
    if (!elt) { return null; }
    if (elt.getAttribute && elt.getAttribute("data-mensajes")) { return elt.getAttribute("data-mensajes"); }
    var form = elt.closest ? elt.closest("[data-mensajes]") : null;
    return form ? form.getAttribute("data-mensajes") : null;
  }

  function esAnalisis(elt) {
    return elt && elt.closest && (elt.closest("#form-analizar") || elt.closest(".ejemplos"));
  }

  // Añade el token CSRF (si existe) a cada petición htmx.
  document.addEventListener("htmx:configRequest", function (evt) {
    if (csrfToken) { evt.detail.headers["X-CSRF-Token"] = csrfToken; }
  });

  // Antes de cada petición: validar, limpiar errores antiguos y anunciar la espera.
  document.addEventListener("htmx:beforeRequest", function (evt) {
    var elt = evt.detail.elt;
    if (elt && elt.id === "form-analizar") {
      var texto = document.getElementById("texto-mensaje");
      var archivo = document.getElementById("archivo-eml");
      if (texto && archivo && !texto.value.trim() && !archivo.files.length) {
        evt.preventDefault();
        mostrar("#mensaje-analisis", "Pegue el texto de un mensaje o elija un archivo para analizar.", "error");
        texto.setAttribute("aria-invalid", "true");
        texto.focus();
        return;
      }
      if (texto) { texto.removeAttribute("aria-invalid"); }
    }
    limpiar(destinoMensajes(elt));
    if (esAnalisis(elt)) { anunciar("estado-sr", "Analizando el mensaje, espere por favor."); }
  });

  // Mensajes de éxito y error en lenguaje sencillo.
  document.addEventListener("htmx:afterRequest", function (evt) {
    var xhr = evt.detail.xhr;
    var selector = destinoMensajes(evt.detail.elt);
    if (!xhr) { return; }
    if (xhr.status === 0) {
      if (selector) { mostrar(selector, MSG_SIN_CONEXION, "error"); }
      return;
    }
    if (evt.detail.successful) {
      if (selector && xhr.status === 202) { mostrar(selector, detalle(xhr, "Hecho."), "ok"); }
      return;
    }
    if (xhr.status === 401 && document.body.hasAttribute("data-autenticado")) { sesionCaducada(); return; }
    if (selector) {
      mostrar(selector, detalle(xhr, "No se ha podido completar la operación. Inténtelo de nuevo."), "error");
      if (selector === "#mensaje-emparejar") {
        var campo = document.getElementById("codigo");
        if (campo) { campo.setAttribute("aria-invalid", "true"); campo.focus(); campo.select(); }
      }
      if (esAnalisis(evt.detail.elt)) { anunciar("estado-sr", ""); }
    }
  });

  // Tras mostrar el resultado: una sola línea anunciada y el foco en el título del resultado.
  document.addEventListener("htmx:afterSettle", function (evt) {
    var destino = evt.detail.target;
    if (!destino || destino.id !== "resultado") { return; }
    var titulo = document.getElementById("t-resultado");
    var nivel = document.querySelector("#resultado-final .nivel-nombre");
    anunciar("estado-sr", "Resultado listo: riesgo " + (nivel ? nivel.textContent : "") + ".");
    if (titulo) { titulo.setAttribute("tabindex", "-1"); titulo.focus(); }
  });

  document.addEventListener("htmx:timeout", function (evt) {
    var selector = destinoMensajes(evt.detail.elt) || "#aviso-global";
    mostrar(selector, "La operación está tardando demasiado. Inténtelo de nuevo en un momento.", "error");
  });

  document.addEventListener("htmx:sendError", function (evt) {
    mostrar(destinoMensajes(evt.detail.elt) || "#aviso-global", MSG_SIN_CONEXION, "error");
  });

  document.addEventListener("DOMContentLoaded", cargarCsrf);
})();
