/**
 * Crowdsourced Incident & Road Disruption Reporting
 * Handles phone camera uploads, GPS auto-detection, and live radar updates.
 */

let selectedMediaFile = null;

document.addEventListener("DOMContentLoaded", () => {
  initLocationsDatalist();
  setupGps();
  setupMediaCapture();
  setupFormSubmit();
  loadRecentReports();

  // Periodic refresh of live reports radar (every 30 seconds)
  setInterval(loadRecentReports, 30000);
});

function initLocationsDatalist() {
  const datalist = document.getElementById("locationsDatalist");
  const locInput = document.getElementById("locationName");
  const latInput = document.getElementById("reportLat");
  const lonInput = document.getElementById("reportLon");

  if (!datalist || !DEMO_LOCATIONS) return;

  DEMO_LOCATIONS.forEach(loc => {
    const opt = document.createElement("option");
    opt.value = loc.name;
    datalist.appendChild(opt);
  });

  locInput.addEventListener("change", () => {
    const found = DEMO_LOCATIONS.find(l => l.name.toLowerCase() === locInput.value.trim().toLowerCase());
    if (found) {
      latInput.value = found.lat.toFixed(4);
      lonInput.value = found.lon.toFixed(4);
    }
  });
}

function setupGps() {
  const btn = document.getElementById("btnGpsAuto");
  const badge = document.getElementById("gpsBadge");
  const latInput = document.getElementById("reportLat");
  const lonInput = document.getElementById("reportLon");
  const locInput = document.getElementById("locationName");

  if (!btn) return;

  btn.addEventListener("click", () => {
    if (!navigator.geolocation) {
      alert("Geolocation is not supported by your browser or device.");
      return;
    }

    btn.disabled = true;
    btn.textContent = "⌛ Acquiring GPS satellites...";
    badge.textContent = "Acquiring GPS...";
    badge.className = "badge badge-moderate";

    navigator.geolocation.getCurrentPosition(
      (pos) => {
        btn.disabled = false;
        btn.textContent = "📍 GPS Locked — Update Again";
        const lat = +pos.coords.latitude.toFixed(4);
        const lon = +pos.coords.longitude.toFixed(4);
        const acc = Math.round(pos.coords.accuracy || 10);

        latInput.value = lat;
        lonInput.value = lon;

        badge.textContent = `GPS Locked (±${acc}m)`;
        badge.className = "badge badge-low";

        // Find nearest known sublocation / corridor
        if (!locInput.value && typeof DEMO_LOCATIONS !== "undefined") {
          let nearest = null;
          let minDist = Infinity;
          for (const loc of DEMO_LOCATIONS) {
            const d = Math.hypot(lat - loc.lat, lon - loc.lon);
            if (d < minDist) {
              minDist = d;
              nearest = loc;
            }
          }
          if (nearest && minDist < 0.3) {
            locInput.value = `${nearest.name} (Near)`;
          }
        }
      },
      (err) => {
        btn.disabled = false;
        btn.textContent = "📍 Auto-Detect Current GPS Coordinates";
        badge.textContent = "GPS Denied / Offline";
        badge.className = "badge badge-high";
        console.warn("GPS error:", err);
        alert(`Could not acquire GPS: ${err.message}. Please enter latitude and longitude manually or select a corridor.`);
      },
      { enableHighAccuracy: true, timeout: 12000, maximumAge: 30000 }
    );
  });
}

function setupMediaCapture() {
  const cameraInput = document.getElementById("cameraInput");
  const fileInput = document.getElementById("fileInput");
  const previewBox = document.getElementById("mediaPreview");
  const previewContent = document.getElementById("previewContent");
  const removeBtn = document.getElementById("removeMediaBtn");

  function handleFile(file) {
    if (!file) return;
    selectedMediaFile = file;

    const isVideo = file.type.startsWith("video/");
    const reader = new FileReader();

    reader.onload = (e) => {
      previewContent.innerHTML = "";
      if (isVideo) {
        const video = document.createElement("video");
        video.src = e.target.result;
        video.controls = true;
        previewContent.appendChild(video);
      } else {
        const img = document.createElement("img");
        img.src = e.target.result;
        previewContent.appendChild(img);
      }
      previewBox.style.display = "block";
    };

    reader.readAsDataURL(file);
  }

  if (cameraInput) {
    cameraInput.addEventListener("change", (e) => {
      if (e.target.files && e.target.files[0]) {
        handleFile(e.target.files[0]);
      }
    });
  }

  if (fileInput) {
    fileInput.addEventListener("change", (e) => {
      if (e.target.files && e.target.files[0]) {
        handleFile(e.target.files[0]);
      }
    });
  }

  if (removeBtn) {
    removeBtn.addEventListener("click", () => {
      selectedMediaFile = null;
      if (cameraInput) cameraInput.value = "";
      if (fileInput) fileInput.value = "";
      previewContent.innerHTML = "";
      previewBox.style.display = "none";
    });
  }
}

// Offline queue storage key
const OFFLINE_QUEUE_KEY = "lg_offline_reports_queue";

document.addEventListener("DOMContentLoaded", () => {
  initLocationsDatalist();
  setupGps();
  setupMediaCapture();
  setupFormSubmit();
  initOfflineSupport();
  loadRecentReports();

  // Periodic refresh of live reports radar (every 30 seconds)
  setInterval(loadRecentReports, 30000);
});

function getOfflineQueue() {
  try {
    const raw = localStorage.getItem(OFFLINE_QUEUE_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch (e) {
    return [];
  }
}

function saveOfflineQueue(queue) {
  try {
    localStorage.setItem(OFFLINE_QUEUE_KEY, JSON.stringify(queue));
  } catch (e) {
    console.warn("Could not save to localStorage:", e);
  }
  updateOfflineBanner();
}

function updateOfflineBanner() {
  const banner = document.getElementById("offlineQueueBanner");
  const bannerText = document.getElementById("offlineBannerText");
  if (!banner) return;

  const queue = getOfflineQueue();
  if (queue.length > 0) {
    banner.style.display = "flex";
    if (bannerText) {
      bannerText.textContent = `📦 ${queue.length} field report(s) queued offline (Will auto-sync on reconnect)`;
    }
  } else {
    banner.style.display = "none";
  }
}

function initOfflineSupport() {
  updateOfflineBanner();

  const syncBtn = document.getElementById("btnSyncNow");
  if (syncBtn) {
    syncBtn.addEventListener("click", () => {
      syncOfflineReports();
    });
  }

  window.addEventListener("online", () => {
    console.log("Network online detected. Syncing offline reports queue...");
    syncOfflineReports();
  });
}

async function syncOfflineReports() {
  const queue = getOfflineQueue();
  if (!queue.length) return;

  const msg = document.getElementById("reportStatusMsg");
  const bannerText = document.getElementById("offlineBannerText");
  if (bannerText) bannerText.textContent = `🔄 Syncing ${queue.length} queued report(s)...`;

  const remaining = [];
  let syncedCount = 0;

  for (const item of queue) {
    try {
      const formData = new FormData();
      for (const [k, v] of Object.entries(item)) {
        formData.append(k, v);
      }

      const endpoint = (window.API_BASE || "/api") + "/reports/submit";
      const res = await fetch(endpoint, {
        method: "POST",
        body: formData,
      });

      if (res.ok) {
        syncedCount++;
      } else {
        remaining.push(item);
      }
    } catch (err) {
      console.warn("Failed to sync item, retaining:", err);
      remaining.push(item);
    }
  }

  saveOfflineQueue(remaining);

  if (syncedCount > 0) {
    if (msg) {
      msg.innerHTML = `
        <div style="background:#ecfdf5;color:#065f46;border:1px solid #a7f3d0;padding:.85rem;border-radius:6px">
          <strong>✅ Synced ${syncedCount} offline report(s) successfully!</strong>
        </div>
      `;
    }
    loadRecentReports();
  }
}

function setupFormSubmit() {
  const form = document.getElementById("incidentForm");
  const msg = document.getElementById("reportStatusMsg");
  const submitBtn = document.getElementById("submitReportBtn");

  if (!form) return;

  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    const reporterName = document.getElementById("reporterName").value.trim();
    const phoneOrEmail = document.getElementById("phoneOrEmail").value.trim();
    const locationName = document.getElementById("locationName").value.trim();
    const lat = document.getElementById("reportLat").value;
    const lon = document.getElementById("reportLon").value;
    const hazardType = document.getElementById("hazardType").value;
    const severity = document.getElementById("severity").value;
    const roadStatus = document.getElementById("roadStatus").value;
    const description = document.getElementById("description").value.trim();

    if (!locationName || !lat || !lon) {
      alert("Please fill in location name, latitude, and longitude.");
      return;
    }

    const payloadObj = {
      reporter_name: reporterName || "Citizen Reporter",
      phone_or_email: phoneOrEmail,
      location_name: locationName,
      latitude: lat,
      longitude: lon,
      hazard_type: hazardType,
      severity: severity,
      road_status: roadStatus,
      description: description,
    };

    // If device is offline, immediately save to local offline queue
    if (!navigator.onLine) {
      const queue = getOfflineQueue();
      queue.push(payloadObj);
      saveOfflineQueue(queue);

      msg.innerHTML = `
        <div style="background:#fffbeb;color:#92400e;border:1px solid #fcd34d;padding:.85rem;border-radius:6px">
          <strong>📦 Offline Mode Active:</strong> You are currently offline.<br>
          Report has been saved safely to your device's local queue and will auto-sync when network connects.
        </div>
      `;
      form.reset();
      return;
    }

    const formData = new FormData();
    for (const [k, v] of Object.entries(payloadObj)) {
      formData.append(k, v);
    }

    if (selectedMediaFile) {
      formData.append("file", selectedMediaFile);
    }

    submitBtn.disabled = true;
    submitBtn.textContent = "⏳ Uploading Geo-Tagged Report...";
    msg.innerHTML = `<div style="color:var(--text-muted)">Submitting report and uploading media to radar...</div>`;

    try {
      const endpoint = (window.API_BASE || "/api") + "/reports/submit";
      const res = await fetch(endpoint, {
        method: "POST",
        body: formData,
      });

      if (!res.ok) {
        const errText = await res.text();
        throw new Error(`Server returned error ${res.status}: ${errText}`);
      }

      const data = await res.json();

      msg.innerHTML = `
        <div style="background:#ecfdf5;color:#065f46;border:1px solid #a7f3d0;padding:.85rem;border-radius:6px">
          <strong>✅ Report Logged: ${data.report_id}</strong><br>
          ${data.message}<br>
          <small>Priority: <strong>${data.response_priority || "P3_STANDARD"}</strong> | Status: <em>${data.confirmation_status || "UNCONFIRMED_CITIZEN_REPORT"}</em></small>
        </div>
      `;

      // Reset Form fields
      form.reset();
      selectedMediaFile = null;
      document.getElementById("previewContent").innerHTML = "";
      document.getElementById("mediaPreview").style.display = "none";

      // Refresh list
      loadRecentReports();
    } catch (err) {
      console.error("Report submit error:", err);
      // If network failed, offer offline persistence
      const queue = getOfflineQueue();
      queue.push(payloadObj);
      saveOfflineQueue(queue);

      msg.innerHTML = `
        <div style="background:#fffbeb;color:#92400e;border:1px solid #fcd34d;padding:.85rem;border-radius:6px">
          <strong>⚠️ Network Connection Lost:</strong> ${err.message}<br>
          Report was automatically preserved in your offline queue and will sync once connection stabilizes.
        </div>
      `;
    } finally {
      submitBtn.disabled = false;
      submitBtn.textContent = "🚀 Submit Geo-Tagged Field Report";
    }
  });
}

async function loadRecentReports() {
  const container = document.getElementById("recentReportsList");
  const countBadge = document.getElementById("reportCountBadge");

  if (!container) return;

  try {
    const endpoint = (window.API_BASE || "/api") + "/reports/all?limit=30";
    const res = await fetch(endpoint);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    const reports = data.reports || [];

    if (countBadge) {
      countBadge.textContent = `${reports.length} Reports`;
    }

    if (!reports.length) {
      container.innerHTML = `
        <div style="text-align:center;padding:2.5rem 1rem;color:var(--text-muted);border:1px dashed var(--border);border-radius:8px">
          No live incident reports active. The network is operating nominally.
        </div>
      `;
      return;
    }

    container.innerHTML = reports.map(r => {
      const roadClass = {
        "FULLY_OPEN": "badge-fully-open",
        "SINGLE_LANE": "badge-single-lane",
        "ESCORT_ONLY": "badge-escort-only",
        "BLOCKED": "badge-blocked"
      }[r.road_status] || "badge-moderate";

      const roadText = {
        "FULLY_OPEN": "🟢 Fully Open",
        "SINGLE_LANE": "🟡 Single Lane",
        "ESCORT_ONLY": "🔵 Escort Only",
        "BLOCKED": "🔴 BLOCKED ROAD"
      }[r.road_status] || r.road_status;

      const sevBadge = r.severity === "CRITICAL" ? "badge-critical" :
                       r.severity === "HIGH" ? "badge-high" :
                       r.severity === "MODERATE" ? "badge-moderate" : "badge-low";

      const priorityBadge = {
        "P1_EMERGENCY": "badge-critical",
        "P2_URGENT": "badge-high",
        "P3_STANDARD": "badge-moderate",
        "P4_ADVISORY": "badge-low"
      }[r.response_priority] || "badge-moderate";

      const isConfirmed = r.confirmation_status === "OFFICIALLY_CONFIRMED" || r.status === "VERIFIED";
      const confirmBadge = isConfirmed
        ? `<span class="badge badge-fully-open">✅ Officially Confirmed</span>`
        : `<span class="badge" style="background:#f3f4f6;color:#4b5563;border:1px solid #d1d5db">⏳ Unconfirmed Citizen Report</span>`;

      const timeStr = r.timestamp ? new Date(r.timestamp).toLocaleString() : "Recently";

      let mediaHtml = "";
      if (r.media_url) {
        const fullMediaUrl = r.media_url.startsWith("http") ? r.media_url : `${window.BACKEND_ORIGIN || ""}${r.media_url}`;
        if (r.media_type === "video") {
          mediaHtml = `<video src="${fullMediaUrl}" controls class="report-media-thumb"></video>`;
        } else {
          mediaHtml = `<a href="${fullMediaUrl}" target="_blank"><img src="${fullMediaUrl}" alt="Incident Media" class="report-media-thumb" loading="lazy"></a>`;
        }
      }

      return `
        <div class="report-card-item">
          <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:.35rem">
            <strong>${r.location_name}</strong>
            <div style="display:flex;gap:.3rem;align-items:center;flex-wrap:wrap">
              <span class="badge ${roadClass}">${roadText}</span>
              <span class="badge ${sevBadge}">${r.severity}</span>
              <span class="badge ${priorityBadge}">${r.response_priority || "P3_STANDARD"}</span>
            </div>
          </div>

          <div style="font-size:.82rem;color:var(--text-muted);display:flex;gap:.75rem;flex-wrap:wrap">
            <span>📍 ${r.latitude}°, ${r.longitude}°</span>
            <span>⚠️ ${r.hazard_type}</span>
            <span>🕒 ${timeStr}</span>
          </div>

          ${r.description ? `<p style="font-size:.88rem;margin:0.25rem 0;color:var(--text-color)">${r.description}</p>` : ""}

          ${mediaHtml}

          <div style="font-size:.78rem;color:var(--text-muted);display:flex;justify-content:space-between;align-items:center;margin-top:.25rem;flex-wrap:wrap;gap:.35rem">
            <span>Reported by: ${r.reporter_name}</span>
            <div style="display:flex;gap:.4rem;align-items:center">
              ${confirmBadge}
              <span style="font-size:.75rem;padding:2px 6px;background:#e5e7eb;border-radius:4px">Lifecycle: ${r.status || "SUBMITTED"}</span>
            </div>
          </div>
        </div>
      `;
    }).join("");
  } catch (err) {
    console.warn("Could not load reports feed:", err);
    container.innerHTML = `
      <div style="text-align:center;padding:1.5rem;color:var(--text-muted)">
        Live reports feed currently offline. Local cache enabled.
      </div>
    `;
  }
}
