(function (window, document) {
  "use strict";

  var WIDGET_SELECTOR = ".weather-widget";
  var SCRIPT = document.currentScript;

  function trimSlash(value) {
    return String(value || "").replace(/\/+$/, "");
  }

  function getApiBaseUrl(element) {
    var explicitUrl =
      element.getAttribute("data-api") ||
      element.getAttribute("data-api-base-url") ||
      (SCRIPT && (SCRIPT.getAttribute("data-api") || SCRIPT.getAttribute("data-api-base-url")));

    if (explicitUrl) {
      return trimSlash(explicitUrl);
    }

    if (SCRIPT && SCRIPT.src) {
      var scriptUrl = new URL(SCRIPT.src, window.location.href);

      if (scriptUrl.origin && scriptUrl.origin !== "null") {
        return scriptUrl.origin;
      }
    }

    return window.location.origin;
  }

  function escapeHtml(value) {
    return String(value || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  function conditionIcon(condition) {
    var text = String(condition || "").toLowerCase();

    if (text.includes("chuva") || text.includes("rain")) return "🌧";
    if (text.includes("neve") || text.includes("snow")) return "❄";
    if (text.includes("nuv") || text.includes("cloud")) return "☁";
    if (text.includes("tempest") || text.includes("storm")) return "⛈";
    if (text.includes("limpo") || text.includes("clear")) return "☀";

    return "🌤";
  }

  function formatTime(timestamp) {
    if (!timestamp) {
      return "Atualizado agora";
    }

    try {
      return new Intl.DateTimeFormat(document.documentElement.lang || "pt-BR", {
        dateStyle: "short",
        timeStyle: "short",
      }).format(new Date(timestamp));
    } catch (error) {
      return "Atualizado agora";
    }
  }

  function createStyles() {
    return [
      ":host { all: initial; display: block; font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; }",
      ":host([hidden]) { display: none; }",
      ".card { width: min(100%, 260px); box-sizing: border-box; color: #f8fafc; background: #09090b; border: 1px solid rgba(255,255,255,.12); border-radius: 8px; padding: 14px; box-shadow: 0 12px 35px rgba(0,0,0,.25); }",
      ":host([data-theme='light']) .card { color: #111827; background: #ffffff; border-color: rgba(17,24,39,.12); box-shadow: 0 12px 35px rgba(17,24,39,.12); }",
      ".top { display: flex; align-items: center; gap: 8px; font-size: 15px; font-weight: 750; }",
      ".city { overflow-wrap: anywhere; }",
      ".icon { font-size: 22px; line-height: 1; }",
      ".temperature { margin-top: 10px; font-size: 34px; line-height: 1; font-weight: 850; letter-spacing: 0; }",
      ".condition { margin-top: 8px; color: #d4d4d8; font-size: 13px; text-transform: capitalize; }",
      ":host([data-theme='light']) .condition { color: #4b5563; }",
      ".details { display: grid; gap: 6px; margin-top: 12px; padding-top: 12px; border-top: 1px solid rgba(255,255,255,.1); color: #a1a1aa; font-size: 12px; }",
      ":host([data-theme='light']) .details { border-top-color: rgba(17,24,39,.12); color: #6b7280; }",
      ".detail { display: flex; justify-content: space-between; gap: 12px; }",
      ".detail strong { color: inherit; font-weight: 700; text-align: right; }",
      ".updated { margin-top: 8px; color: #71717a; font-size: 12px; }",
      ":host([data-theme='light']) .updated { color: #6b7280; }",
      ".error { color: #fecaca; font-size: 13px; line-height: 1.45; }",
      ":host([data-theme='light']) .error { color: #991b1b; }",
      ".loading { color: #d4d4d8; font-size: 13px; }",
      ":host([data-theme='light']) .loading { color: #4b5563; }",
      ".sr-only { position: absolute; width: 1px; height: 1px; padding: 0; margin: -1px; overflow: hidden; clip: rect(0,0,0,0); white-space: nowrap; border: 0; }",
    ].join("");
  }

  function prepareHost(element, busy) {
    if (!element.hasAttribute("role")) {
      element.setAttribute("role", "status");
    }

    if (!element.hasAttribute("aria-live")) {
      element.setAttribute("aria-live", "polite");
    }

    element.setAttribute("aria-busy", busy ? "true" : "false");
  }

  function renderWidget(element, html, busy) {
    var root = element.shadowRoot || element.attachShadow({ mode: "open" });

    prepareHost(element, busy);
    root.innerHTML = "<style>" + createStyles() + "</style>" + html;
  }

  function renderLoading(element) {
    renderWidget(
      element,
      '<article class="card" aria-label="Carregando clima"><div class="loading">Consultando clima...</div></article>',
      true
    );
  }

  function renderError(element, message) {
    renderWidget(
      element,
      '<article class="card" aria-label="Erro ao carregar clima"><div class="error">' +
        escapeHtml(message) +
        "</div></article>",
      false
    );
  }

  function renderWeather(element, weather) {
    var icon = conditionIcon(weather.condition);
    var updatedAt = formatTime(weather.timestamp);
    var detailsHidden = element.getAttribute("data-compact") === "true";
    var details = detailsHidden
      ? ""
      : [
          '<div class="details">',
          '<div class="detail"><span>Sensacao</span><strong>' + escapeHtml(weather.feels_like) + "°C</strong></div>",
          '<div class="detail"><span>Umidade</span><strong>' + escapeHtml(weather.humidity) + "%</strong></div>",
          '<div class="detail"><span>Vento</span><strong>' + escapeHtml(weather.wind_speed) + " km/h</strong></div>",
          "</div>",
        ].join("");
    var html = [
      '<article class="card" aria-label="Clima atual em ' + escapeHtml(weather.city) + '">',
      '<div class="top">',
      '<span class="icon" aria-hidden="true">' + icon + "</span>",
      '<span class="city">' + escapeHtml(weather.city) + "</span>",
      "</div>",
      '<div class="temperature" aria-label="Temperatura atual: ' +
        escapeHtml(weather.temperature) +
        ' graus Celsius">' +
        escapeHtml(weather.temperature) +
        "°C</div>",
      '<div class="condition">' + escapeHtml(weather.condition) + "</div>",
      details,
      '<div class="updated">Atualizado em ' + escapeHtml(updatedAt) + "</div>",
      "</article>",
    ].join("");

    renderWidget(element, html, false);
  }

  function buildWeatherUrl(element) {
    var city = element.getAttribute("data-city");
    var lat = element.getAttribute("data-lat");
    var lon = element.getAttribute("data-lon");
    var params = new URLSearchParams();

    if (city) params.set("city", city);

    if (lat && lon) {
      params.set("lat", lat);
      params.set("lon", lon);
    }

    if (!params.has("city") && (!params.has("lat") || !params.has("lon"))) {
      return null;
    }

    return getApiBaseUrl(element) + "/api/weather?" + params.toString();
  }

  function loadWidget(element) {
    var weatherUrl = buildWeatherUrl(element);

    if (!weatherUrl) {
      renderError(element, "Configure data-city ou data-lat/data-lon.");
      return Promise.resolve();
    }

    renderLoading(element);

    return fetch(weatherUrl, {
      headers: {
        Accept: "application/json",
      },
    })
      .then(function (response) {
        return response.json().then(function (payload) {
          if (!response.ok) {
            throw new Error(payload.message || "Nao foi possivel carregar o clima.");
          }

          return payload;
        });
      })
      .then(function (weather) {
        renderWeather(element, weather);
      })
      .catch(function (error) {
        renderError(element, error.message || "Nao foi possivel carregar o clima.");
      });
  }

  function initWidgets(root) {
    var scope = root || document;
    var widgets = scope.querySelectorAll(WIDGET_SELECTOR);

    widgets.forEach(function (element) {
      loadWidget(element);
    });
  }

  window.WeatherWidget = {
    init: initWidgets,
    refresh: loadWidget,
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () {
      initWidgets(document);
    });
  } else {
    initWidgets(document);
  }
})(window, document);
