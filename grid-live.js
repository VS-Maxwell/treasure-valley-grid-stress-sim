(function () {
  "use strict";

  var SOURCE_ID = "trans";
  var BUILD_MILLISECONDS = 3600;
  var BUILD_STEPS = 32;
  var POLL_LIMIT = 120;
  var generation = 0;
  var sourceFeatures = [];
  var originalGlowFilter = null;
  var auxiliaryVisibility = null;
  var reducedMotion = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  function createConsole() {
    var panel = document.createElement("section");
    panel.id = "tv-grid-live";
    panel.dataset.state = "waiting";
    panel.setAttribute("aria-label", "Live transmission grid build controls");
    panel.innerHTML =
      '<div class="tv-grid-live__head">' +
        '<div class="tv-grid-live__eyebrow">Live grid construction</div>' +
        '<div class="tv-grid-live__state" id="tv-grid-state">waiting for map</div>' +
      "</div>" +
      '<div class="tv-grid-live__progress" role="progressbar" aria-label="Transmission corridors drawn" aria-valuemin="0" aria-valuemax="100" aria-valuenow="0">' +
        '<span class="tv-grid-live__bar" id="tv-grid-bar"></span>' +
      "</div>" +
      '<div class="tv-grid-live__stats">' +
        '<div class="tv-grid-live__count"><span id="tv-grid-visible">0</span>/<span id="tv-grid-total">—</span> <small>corridors</small></div>' +
        '<div class="tv-grid-live__stamp" id="tv-grid-stamp">Embedded historical snapshot</div>' +
      "</div>" +
      '<div class="tv-grid-live__actions">' +
        '<button type="button" id="tv-grid-build" disabled>Build grid</button>' +
        '<button type="button" id="tv-grid-refresh" disabled>Refresh</button>' +
        '<div class="tv-grid-live__truth">Visible renderer state<br>screening data</div>' +
      "</div>";
    document.body.appendChild(panel);
    return panel;
  }

  var panel = createConsole();
  var stateNode = document.getElementById("tv-grid-state");
  var visibleNode = document.getElementById("tv-grid-visible");
  var totalNode = document.getElementById("tv-grid-total");
  var stampNode = document.getElementById("tv-grid-stamp");
  var barNode = document.getElementById("tv-grid-bar");
  var progressNode = panel.querySelector('[role="progressbar"]');
  var buildButton = document.getElementById("tv-grid-build");
  var refreshButton = document.getElementById("tv-grid-refresh");

  function setState(state, label) {
    panel.dataset.state = state;
    stateNode.textContent = label;
  }

  function renderProgress(visible, total) {
    var pct = total ? Math.round((visible / total) * 100) : 0;
    visibleNode.textContent = String(visible);
    totalNode.textContent = total ? String(total) : "—";
    barNode.style.width = pct + "%";
    progressNode.setAttribute("aria-valuenow", String(pct));
  }

  function currentSource() {
    try {
      return typeof map !== "undefined" ? map.getSource(SOURCE_ID) : null;
    } catch (error) {
      return null;
    }
  }

  function announce(type, detail) {
    window.dispatchEvent(new CustomEvent("tv:grid-progress", { detail: detail }));
    try {
      window.parent.postMessage({ type: type, detail: detail }, "*");
    } catch (error) {
      // Visual operation remains local if the parent cannot receive status.
    }
  }

  function restoreScenarioPaint() {
    try {
      var active = document.querySelector("[data-scen].active");
      var scenario = active ? active.getAttribute("data-scen") : "base";
      if (typeof setScen === "function") setScen(scenario);
    } catch (error) {
      // Source refresh is still valid if scenario styling is unavailable.
    }
  }

  function setVisibleCorridors(visible) {
    if (typeof map === "undefined" || !map.getLayer("trans-glow")) return;
    if (visible >= sourceFeatures.length) {
      map.setFilter("trans-glow", originalGlowFilter);
      return;
    }
    if (visible <= 0) {
      map.setFilter("trans-glow", ["==", ["get", "line_id"], "__tv_grid_none__"]);
      return;
    }
    var ids = sourceFeatures.slice(0, visible).map(function (feature) {
      return String(feature.properties.line_id);
    });
    map.setFilter("trans-glow", ["in", ["to-string", ["get", "line_id"]], ["literal", ids]]);
  }

  function hideAuxiliaryGridLayers() {
    auxiliaryVisibility = {};
    ["crit-line", "trans-flow"].forEach(function (layerId) {
      if (typeof map === "undefined" || !map.getLayer(layerId)) return;
      auxiliaryVisibility[layerId] = map.getLayoutProperty(layerId, "visibility") || "visible";
      map.setLayoutProperty(layerId, "visibility", "none");
    });
  }

  function restoreAuxiliaryGridLayers() {
    if (!auxiliaryVisibility || typeof map === "undefined") return;
    Object.keys(auxiliaryVisibility).forEach(function (layerId) {
      if (map.getLayer(layerId)) {
        map.setLayoutProperty(layerId, "visibility", auxiliaryVisibility[layerId]);
      }
    });
    auxiliaryVisibility = null;
  }

  function finish(token) {
    if (token !== generation) return;
    setVisibleCorridors(sourceFeatures.length);
    restoreAuxiliaryGridLayers();
    renderProgress(sourceFeatures.length, sourceFeatures.length);
    restoreScenarioPaint();
    setState("ready", "grid ready");
    buildButton.disabled = false;
    refreshButton.disabled = false;
    stampNode.textContent = "Rendered " + new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
    announce("tv-grid-ready", { visible: sourceFeatures.length, total: sourceFeatures.length, state: "ready" });
  }

  function buildGrid() {
    if (!currentSource() || !sourceFeatures.length) {
      setState("error", "source unavailable");
      return;
    }

    generation += 1;
    var token = generation;
    var total = sourceFeatures.length;
    var started = performance.now();
    var lastBucket = -1;
    restoreAuxiliaryGridLayers();
    hideAuxiliaryGridLayers();
    setVisibleCorridors(0);
    buildButton.disabled = true;
    refreshButton.disabled = false;
    setState("building", "drawing network");
    renderProgress(0, total);
    announce("tv-grid-building", { visible: 0, total: total, state: "building" });

    function frame(now) {
      if (token !== generation) return;
      var ratio = reducedMotion ? 1 : Math.min(1, (now - started) / BUILD_MILLISECONDS);
      var bucket = Math.min(BUILD_STEPS, Math.floor(ratio * BUILD_STEPS));
      if (bucket === lastBucket && ratio < 1) {
        requestAnimationFrame(frame);
        return;
      }
      lastBucket = bucket;
      var eased = 1 - Math.pow(1 - ratio, 3);
      var visible = ratio === 0 ? 0 : Math.min(total, Math.max(1, Math.floor(total * eased)));
      setVisibleCorridors(visible);
      renderProgress(visible, total);
      announce("tv-grid-building", { visible: visible, total: total, state: "building" });
      if (visible < total) requestAnimationFrame(frame);
      else finish(token);
    }

    requestAnimationFrame(frame);
  }

  function refreshGrid() {
    generation += 1;
    if (!currentSource() || !sourceFeatures.length) {
      setState("error", "source unavailable");
      return;
    }
    setVisibleCorridors(sourceFeatures.length);
    restoreAuxiliaryGridLayers();
    restoreScenarioPaint();
    if (typeof map !== "undefined" && typeof map.triggerRepaint === "function") map.triggerRepaint();
    renderProgress(sourceFeatures.length, sourceFeatures.length);
    setState("ready", "data refreshed");
    buildButton.disabled = false;
    refreshButton.disabled = false;
    stampNode.textContent = "Refreshed " + new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
    announce("tv-grid-refreshed", { visible: sourceFeatures.length, total: sourceFeatures.length, state: "ready" });
  }

  function connect(attempt) {
    var source = currentSource();
    var features = typeof DATA !== "undefined" && DATA.trans && Array.isArray(DATA.trans.features)
      ? DATA.trans.features
      : [];
    if (!source || !features.length) {
      if (attempt < POLL_LIMIT) {
        setTimeout(function () { connect(attempt + 1); }, 250);
      } else {
        setState("error", "grid did not initialize");
        stampNode.textContent = "Open /dev/ for blocker details";
      }
      return;
    }

    sourceFeatures = features.slice();
    originalGlowFilter = typeof map !== "undefined" && map.getLayer("trans-glow")
      ? map.getFilter("trans-glow")
      : null;
    renderProgress(sourceFeatures.length, sourceFeatures.length);
    setState("ready", "source connected");
    buildButton.disabled = false;
    refreshButton.disabled = false;
    buildButton.addEventListener("click", buildGrid);
    refreshButton.addEventListener("click", refreshGrid);
    window.TV_GRID_BUILD = {
      build: buildGrid,
      refresh: refreshGrid,
      total: sourceFeatures.length,
      get state() { return panel.dataset.state; }
    };
    setTimeout(buildGrid, 650);
  }

  connect(0);
})();
