(function () {
  "use strict";

  var BUILD_MILLISECONDS = 3600;
  var BUILD_STEPS = 32;
  var canvas = document.getElementById("grid-canvas");
  var context = canvas.getContext("2d", { alpha: false });
  var boot = document.getElementById("boot");
  var data = null;
  var visible = 0;
  var generation = 0;
  var view = { zoom: 1, x: 0, y: 0 };
  var bounds = null;
  var drag = null;
  var reducedMotion = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  function createConsole() {
    var panel = document.createElement("section");
    panel.id = "tv-grid-live";
    panel.dataset.state = "waiting";
    panel.setAttribute("aria-label", "Live transmission grid build controls");
    panel.innerHTML =
      '<div class="tv-grid-live__head"><div class="tv-grid-live__eyebrow">Live grid construction</div>' +
      '<div class="tv-grid-live__state" id="tv-grid-state">loading local data</div></div>' +
      '<div class="tv-grid-live__progress" role="progressbar" aria-label="Transmission corridors drawn" aria-valuemin="0" aria-valuemax="100" aria-valuenow="0">' +
      '<span class="tv-grid-live__bar" id="tv-grid-bar"></span></div>' +
      '<div class="tv-grid-live__stats"><div class="tv-grid-live__count"><span id="tv-grid-visible">0</span>/' +
      '<span id="tv-grid-total">—</span> <small>corridors</small></div>' +
      '<div class="tv-grid-live__stamp" id="tv-grid-stamp">Receipt-backed local snapshot</div></div>' +
      '<div class="tv-grid-live__actions"><button type="button" id="tv-grid-build" disabled>Build grid</button>' +
      '<button type="button" id="tv-grid-refresh" disabled>Refresh</button>' +
      '<div class="tv-grid-live__truth">Bounded Canvas renderer<br>screening geometry</div></div>';
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

  function renderProgress(count, total) {
    var percent = total ? Math.round((count / total) * 100) : 0;
    visibleNode.textContent = String(count);
    totalNode.textContent = total ? String(total) : "—";
    barNode.style.width = percent + "%";
    progressNode.setAttribute("aria-valuenow", String(percent));
  }

  function coordinateLines(feature) {
    return feature.geometry.type === "LineString" ? [feature.geometry.coordinates] : feature.geometry.coordinates;
  }

  function measureBounds(features) {
    var box = { west: Infinity, east: -Infinity, south: Infinity, north: -Infinity };
    features.forEach(function (feature) {
      coordinateLines(feature).forEach(function (line) {
        line.forEach(function (point) {
          box.west = Math.min(box.west, point[0]);
          box.east = Math.max(box.east, point[0]);
          box.south = Math.min(box.south, point[1]);
          box.north = Math.max(box.north, point[1]);
        });
      });
    });
    return box;
  }

  function resize() {
    var ratio = Math.min(window.devicePixelRatio || 1, 2);
    var width = Math.max(1, canvas.clientWidth);
    var height = Math.max(1, canvas.clientHeight);
    canvas.width = Math.round(width * ratio);
    canvas.height = Math.round(height * ratio);
    context.setTransform(ratio, 0, 0, ratio, 0, 0);
    draw();
  }

  function projection(point) {
    var width = canvas.clientWidth;
    var height = canvas.clientHeight;
    var base = Math.min((width - 70) / (bounds.east - bounds.west), (height - 70) / (bounds.north - bounds.south));
    return [
      width / 2 + (point[0] - (bounds.east + bounds.west) / 2) * base * view.zoom + view.x,
      height / 2 - (point[1] - (bounds.north + bounds.south) / 2) * base * view.zoom + view.y
    ];
  }

  function voltageColor(voltage) {
    if (voltage >= 500) return "#ff4355";
    if (voltage >= 230) return "#ff913f";
    if (voltage >= 138) return "#ffe477";
    return "#69ccff";
  }

  function drawBackdrop(width, height) {
    var gradient = context.createRadialGradient(width * .52, height * .43, 20, width * .52, height * .43, Math.max(width, height) * .72);
    gradient.addColorStop(0, "#16334a");
    gradient.addColorStop(.52, "#0a1c2a");
    gradient.addColorStop(1, "#040b12");
    context.fillStyle = gradient;
    context.fillRect(0, 0, width, height);
    context.strokeStyle = "rgba(93, 160, 196, .075)";
    context.lineWidth = 1;
    for (var x = width % 52; x < width; x += 52) {
      context.beginPath(); context.moveTo(x, 0); context.lineTo(x, height); context.stroke();
    }
    for (var y = height % 52; y < height; y += 52) {
      context.beginPath(); context.moveTo(0, y); context.lineTo(width, y); context.stroke();
    }
  }

  function traceFeature(feature) {
    coordinateLines(feature).forEach(function (line) {
      context.beginPath();
      line.forEach(function (coordinate, index) {
        var point = projection(coordinate);
        if (index === 0) context.moveTo(point[0], point[1]);
        else context.lineTo(point[0], point[1]);
      });
      context.stroke();
    });
  }

  function draw() {
    var width = canvas.clientWidth;
    var height = canvas.clientHeight;
    drawBackdrop(width, height);
    if (!data || !bounds) return;
    var features = data.trans.features.slice(0, visible);
    context.save();
    context.globalCompositeOperation = "lighter";
    features.forEach(function (feature) {
      var voltage = Number(feature.properties.voltage_kv) || 0;
      context.strokeStyle = voltageColor(voltage);
      context.globalAlpha = .17;
      context.lineWidth = voltage >= 500 ? 8 : voltage >= 230 ? 6 : 4;
      context.shadowBlur = 11;
      context.shadowColor = voltageColor(voltage);
      traceFeature(feature);
    });
    context.restore();
    features.forEach(function (feature) {
      var voltage = Number(feature.properties.voltage_kv) || 0;
      context.strokeStyle = voltageColor(voltage);
      context.globalAlpha = .9;
      context.lineWidth = voltage >= 500 ? 2.6 : voltage >= 230 ? 2 : voltage >= 138 ? 1.45 : 1;
      context.shadowBlur = 0;
      traceFeature(feature);
    });
    context.globalAlpha = visible === data.trans.features.length ? .9 : .28;
    data.subs.features.forEach(function (feature) {
      var point = projection(feature.geometry.coordinates);
      context.beginPath(); context.arc(point[0], point[1], 2.2, 0, Math.PI * 2);
      context.fillStyle = "#f1fbff"; context.fill();
      context.strokeStyle = "#168fc5"; context.lineWidth = 1; context.stroke();
    });
    context.globalAlpha = 1;
  }

  function finish(token) {
    if (token !== generation) return;
    visible = data.trans.features.length;
    draw();
    renderProgress(visible, visible);
    setState("ready", "grid ready");
    buildButton.disabled = false;
    refreshButton.disabled = false;
    stampNode.textContent = "Rendered " + new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
  }

  function buildGrid() {
    generation += 1;
    var token = generation;
    var total = data.trans.features.length;
    var started = performance.now();
    var lastBucket = -1;
    visible = 0;
    draw();
    renderProgress(0, total);
    setState("building", "drawing network");
    buildButton.disabled = true;
    refreshButton.disabled = false;
    function frame(now) {
      if (token !== generation) return;
      var ratio = reducedMotion ? 1 : Math.min(1, (now - started) / BUILD_MILLISECONDS);
      var bucket = Math.min(BUILD_STEPS, Math.floor(ratio * BUILD_STEPS));
      if (bucket !== lastBucket || ratio === 1) {
        lastBucket = bucket;
        var eased = 1 - Math.pow(1 - ratio, 3);
        visible = ratio === 0 ? 0 : Math.min(total, Math.max(1, Math.floor(total * eased)));
        draw();
        renderProgress(visible, total);
      }
      if (visible < total) requestAnimationFrame(frame);
      else finish(token);
    }
    requestAnimationFrame(frame);
  }

  function refreshGrid() {
    generation += 1;
    visible = data.trans.features.length;
    view = { zoom: 1, x: 0, y: 0 };
    draw();
    renderProgress(visible, visible);
    setState("ready", "view refreshed");
    buildButton.disabled = false;
    refreshButton.disabled = false;
    stampNode.textContent = "Refreshed " + new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
  }

  canvas.addEventListener("pointerdown", function (event) {
    drag = { x: event.clientX, y: event.clientY, originX: view.x, originY: view.y };
    canvas.setPointerCapture(event.pointerId);
  });
  canvas.addEventListener("pointermove", function (event) {
    if (!drag) return;
    view.x = drag.originX + event.clientX - drag.x;
    view.y = drag.originY + event.clientY - drag.y;
    draw();
  });
  canvas.addEventListener("pointerup", function () { drag = null; });
  canvas.addEventListener("pointercancel", function () { drag = null; });
  canvas.addEventListener("wheel", function (event) {
    event.preventDefault();
    view.zoom = Math.max(.55, Math.min(7, view.zoom * (event.deltaY > 0 ? .9 : 1.1)));
    draw();
  }, { passive: false });
  window.addEventListener("resize", resize);

  fetch("data/grid-core.json").then(function (response) {
    if (!response.ok) throw new Error("grid core unavailable");
    return response.json();
  }).then(function (payload) {
    data = payload;
    bounds = measureBounds(data.trans.features);
    renderProgress(0, data.trans.features.length);
    setState("ready", "local data ready");
    buildButton.disabled = false;
    refreshButton.disabled = false;
    buildButton.addEventListener("click", buildGrid);
    refreshButton.addEventListener("click", refreshGrid);
    window.TV_GRID_BUILD = { build: buildGrid, refresh: refreshGrid, total: data.trans.features.length };
    resize();
    boot.classList.add("done");
    setTimeout(buildGrid, 300);
  }).catch(function (error) {
    boot.textContent = "Grid core failed to load: " + error.message;
    boot.style.color = "#ff8290";
    setState("error", "local data failed");
  });
})();
