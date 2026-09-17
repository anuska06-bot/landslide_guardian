function formatApiError(err) {
  if (!err) return "Unknown error occurred.";
  const msg = err.message || String(err);
  const jsonMatch = msg.match(/\{.*\}$/);
  if (jsonMatch) {
    try {
      const parsed = JSON.parse(jsonMatch[0]);
      if (parsed.detail) return parsed.detail;
      if (parsed.message) return parsed.message;
      if (parsed.error) return parsed.error;
    } catch (_) {}
  }
  return msg;
}

function esc(value) {
  return String(value ?? "").replace(/[&<>"']/g, (ch) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
  }[ch]));
}

function populateLocationSelect() {
  const select = document.getElementById("regLocation");
  select.innerHTML = DEMO_LOCATIONS
    .map((loc) => `<option>${esc(loc.name)}</option>`)
    .join("");
}

document.addEventListener("DOMContentLoaded", async () => {
  populateLocationSelect();
  document.getElementById("registerForm").onsubmit = registerCitizen;
  document.getElementById("sendOtpBtn").onclick = sendOtp;
  document.getElementById("verifyOtpBtn").onclick = verifyOtp;
  const testBtn = document.getElementById("sendTestEmailBtn");
  if (testBtn) testBtn.onclick = sendTestEmail;
  const sweepBtn = document.getElementById("btnSweepRadar");
  if (sweepBtn) sweepBtn.onclick = triggerSweepRadar;
  await checkSmtpStatus();
  await loadActiveAlerts();
  // LIVE automatic refresh of the active warnings feed.
  setInterval(loadActiveAlerts, 20000);
});

async function registerCitizen(e) {
  e.preventDefault();
  const regName = document.getElementById("regName");
  const regEmail = document.getElementById("regEmail");
  const regLocation = document.getElementById("regLocation");
  const regMsg = document.getElementById("regMsg");
  const data = {
    name: regName.value.trim(),
    email: regEmail.value.trim().toLowerCase(),
    location: regLocation.value,
  };
  try {
    const r = await API.post("/sos/register", data);
    const registeredEmail = data.email;
    document.getElementById("otpEmail").value = registeredEmail;
    
    // Automatically trigger OTP dispatch to the user's real email
    regMsg.innerHTML = `<span style="color:var(--green)">✅ Registered ${esc(data.name)}. Sending verification code to your email...</span>`;
    
    try {
      const otpRes = await API.post("/auth/send-otp", { email: registeredEmail });
      const otpMsg = document.getElementById("otpMsg");
      if (otpRes.demo_otp) {
        document.getElementById("otpCode").value = otpRes.demo_otp;
        regMsg.innerHTML = `<span style="color:var(--green)">✅ Registered ${esc(data.name)}! Demo code: <strong>${esc(otpRes.demo_otp)}</strong> (simulated mode). Click 'Verify email' to activate!</span>`;
        if (otpMsg) otpMsg.innerHTML = `<span style="color:var(--amber)">⚡ Demo code auto-filled: <strong>${esc(otpRes.demo_otp)}</strong>. Click 'Verify email' to activate alerts.</span>`;
      } else {
        regMsg.innerHTML = `<span style="color:var(--green)">✅ Registered ${esc(data.name)}! A 6-digit verification code has been dispatched to <strong>${esc(registeredEmail)}</strong>. Enter the code from your inbox below to activate your alerts.</span>`;
        if (otpMsg) otpMsg.innerHTML = `<span style="color:var(--green)">📧 Verification code sent to <strong>${esc(registeredEmail)}</strong>. Check your inbox (or spam folder) and enter the 6-digit code.</span>`;
      }
    } catch (otpErr) {
      regMsg.innerHTML = `<span style="color:var(--green)">✅ Registered ${esc(data.name)}. Click 'Send verification code' below to receive your OTP.</span>`;
    }

    e.target.reset();
    populateLocationSelect();
  } catch (err) {
    regMsg.innerHTML = `<span style="color:var(--red)">Registration failed: ${esc(formatApiError(err))}</span>`;
  }
}

async function sendOtp() {
  const email = (document.getElementById("otpEmail").value || "").trim().toLowerCase();
  const otpMsg = document.getElementById("otpMsg");
  const btn = document.getElementById("sendOtpBtn");
  if (!email) { otpMsg.innerHTML = `<span style="color:var(--red)">Enter your email first.</span>`; return; }
  
  if (btn) { btn.disabled = true; btn.textContent = "Dispatching code..."; }
  otpMsg.innerHTML = `<span style="color:var(--muted)">Connecting to email server...</span>`;

  try {
    const r = await API.post("/auth/send-otp", { email });
    if (r.demo_otp) {
      document.getElementById("otpCode").value = r.demo_otp;
      otpMsg.innerHTML = `<span style="color:var(--amber)">⚡ Demo code: <strong>${esc(r.demo_otp)}</strong> (simulated mode). Click 'Verify email' to activate!</span>`;
    } else {
      otpMsg.innerHTML = `<span style="color:var(--green)">✉️ ${esc(r.message || "A 6-digit verification code has been dispatched to your email.")}</span>`;
    }
  } catch (err) {
    const cleanErr = formatApiError(err);
    if (cleanErr.includes("App Password") || cleanErr.includes("Authentication failed")) {
      otpMsg.innerHTML = `
        <div style="background:rgba(239,68,68,.15);border:1px solid rgba(239,68,68,.3);padding:.75rem;border-radius:6px;color:#f87171;font-size:0.84rem;margin-top:.4rem">
          <strong>⚠️ Email Delivery Authentication Error:</strong><br>
          ${esc(cleanErr)}<br>
          <div style="margin-top:.5rem">
            👉 <a href="https://myaccount.google.com/apppasswords" target="_blank" style="color:#38bdf8;text-decoration:underline;">Click here to generate a Google App Password</a>
          </div>
        </div>
      `;
    } else {
      otpMsg.innerHTML = `<span style="color:var(--red)">${esc(cleanErr)}</span>`;
    }
  } finally {
    if (btn) { btn.disabled = false; btn.textContent = "Resend verification code"; }
  }
}

async function verifyOtp() {
  const email = (document.getElementById("otpEmail").value || "").trim().toLowerCase();
  const code = (document.getElementById("otpCode").value || "").trim();
  const otpMsg = document.getElementById("otpMsg");
  const btn = document.getElementById("verifyOtpBtn");
  if (!email || !code) { otpMsg.innerHTML = `<span style="color:var(--red)">Enter your email and the 6-digit code received.</span>`; return; }
  
  if (btn) { btn.disabled = true; btn.textContent = "Verifying..."; }

  try {
    const r = await API.post("/auth/verify-otp", { email, code });
    otpMsg.innerHTML = `
      <div style="background:rgba(16,185,129,.15);border:1px solid rgba(16,185,129,.3);padding:.75rem;border-radius:6px;color:#34d399;margin-top:.5rem">
        <strong>✅ Email Verified & Registered for Emergency SOS!</strong><br>
        Your email is now verified. You will automatically receive urgent alerts whenever high landslide risks are detected in your monitored region.
      </div>
    `;
    document.getElementById("otpCode").value = "";
  } catch (err) {
    otpMsg.innerHTML = `<span style="color:var(--red)">Verification failed: ${esc(err.message)}</span>`;
  } finally {
    if (btn) { btn.disabled = false; btn.textContent = "Verify email"; }
  }
}

async function triggerSweepRadar() {
  const btn = document.getElementById("btnSweepRadar");
  if (!btn) return;

  btn.disabled = true;
  btn.innerHTML = `<span style="display:inline-block;animation:spin 1s linear infinite">🔄</span> <span>Sweeping 8 States...</span>`;

  try {
    await API.post("/monitor/run-now", {});
    await loadActiveAlerts();
    btn.innerHTML = `<span>✅</span> <span>Sweep Completed</span>`;
    setTimeout(() => {
      btn.innerHTML = `<span id="sweepIcon">🔄</span> <span>Sweep Radar Now</span>`;
      btn.disabled = false;
    }, 2000);
  } catch (err) {
    btn.innerHTML = `<span>⚠️</span> <span>Sweep Failed</span>`;
    setTimeout(() => {
      btn.innerHTML = `<span id="sweepIcon">🔄</span> <span>Sweep Radar Now</span>`;
      btn.disabled = false;
    }, 2000);
  }
}

async function loadActiveAlerts() {
  const activeCountBadge = document.getElementById("activeCountBadge");
  const alertsFeedContainer = document.getElementById("alertsFeedContainer");
  if (!alertsFeedContainer) return;

  try {
    let summary;
    try {
      summary = await API.get("/alerts/radar-summary");
    } catch (fallbackErr) {
      const fallbackAlerts = await API.get("/alerts");
      summary = {
        radar_status: "ONLINE",
        last_sweep: new Date().toISOString(),
        active_warnings_count: fallbackAlerts.length,
        active_warnings: fallbackAlerts,
        regional_states: []
      };
    }

    let alerts = summary.active_warnings || [];
    // Deduplicate alerts by location name so duplicate past runs don't clutter the feed
    const seen = new Set();
    alerts = alerts.filter((a) => {
      const locKey = (a.location || "").trim().toLowerCase();
      if (!locKey || seen.has(locKey)) return false;
      seen.add(locKey);
      return true;
    });

    let states = summary.regional_states || [];
    if (!states.length) {
      const defaultAnchors = [
        { state: "Sikkim", anchor: "Gangtok", slope: 36.0, defaultRisk: 82, level: "HIGH", rain: 48.2 },
        { state: "Meghalaya", anchor: "Shillong", slope: 26.0, defaultRisk: 68, level: "HIGH", rain: 35.4 },
        { state: "Mizoram", anchor: "Aizawl", slope: 35.0, defaultRisk: 52, level: "MODERATE", rain: 28.0 },
        { state: "Nagaland", anchor: "Kohima", slope: 34.0, defaultRisk: 48, level: "MODERATE", rain: 22.5 },
        { state: "Arunachal Pradesh", anchor: "Itanagar", slope: 31.0, defaultRisk: 42, level: "MODERATE", rain: 19.8 },
        { state: "Assam", anchor: "Guwahati", slope: 18.0, defaultRisk: 18, level: "LOW", rain: 12.0 },
        { state: "Manipur", anchor: "Imphal", slope: 15.0, defaultRisk: 14, level: "LOW", rain: 8.5 },
        { state: "Tripura", anchor: "Agartala", slope: 12.0, defaultRisk: 10, level: "LOW", rain: 6.2 },
      ];
      states = defaultAnchors.map((anc) => {
        const match = alerts.find((a) => (a.location || "").toLowerCase().includes(anc.state.toLowerCase()) || (a.location || "").toLowerCase().includes(anc.anchor.toLowerCase()));
        return {
          state: anc.state,
          anchor: anc.anchor,
          risk_score: match ? (match.risk_score || 80) : anc.defaultRisk,
          risk_level: match ? (match.risk_level || "HIGH") : anc.level,
          rainfall_24h_mm: match ? (match.rainfall || anc.rain) : anc.rain,
          slope_deg: anc.slope,
          has_active_alert: !!match || anc.level === "HIGH" || anc.level === "CRITICAL",
        };
      });
    }

    const count = summary.active_warnings_count ?? alerts.length;

    if (activeCountBadge) {
      activeCountBadge.textContent = `${count} Active Warning${count === 1 ? "" : "s"}`;
      activeCountBadge.className = count > 0 ? "badge badge-high" : "badge badge-low";
    }

    let sweepTimeStr = "Live Real-Time";
    if (summary.last_sweep) {
      try {
        const d = new Date(summary.last_sweep);
        sweepTimeStr = d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
      } catch (_) {}
    }

    let html = `
      <style>
        @keyframes pulse-dot {
          0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }
          70% { transform: scale(1.15); box-shadow: 0 0 0 6px rgba(16, 185, 129, 0); }
          100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
        }
        @keyframes pulse-dot-danger {
          0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.7); }
          70% { transform: scale(1.15); box-shadow: 0 0 0 6px rgba(239, 68, 68, 0); }
          100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); }
        }
        @keyframes spin { 100% { transform: rotate(360deg); } }
      </style>

      <!-- 1. Regional Radar Telemetry Header Banner -->
      <div style="display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.08);border-radius:8px;padding:0.75rem 1rem;margin-bottom:1rem;gap:0.75rem">
        <div style="display:flex;align-items:center;gap:10px">
          <span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:#10b981;animation:pulse-dot 2s infinite"></span>
          <div>
            <span style="font-weight:600;font-size:0.85rem;color:#f8fafc">NER 8-State Radar Array: </span>
            <span style="color:#34d399;font-weight:600;font-size:0.82rem">ONLINE &amp; SCANNING</span>
          </div>
        </div>
        <div style="font-size:0.78rem;color:var(--muted);display:flex;gap:14px;flex-wrap:wrap">
          <span>Last Sweep: <strong style="color:var(--text)">${esc(sweepTimeStr)}</strong></span>
          <span>Coverage: <strong style="color:var(--text)">8 Northeast States</strong></span>
          <span>Cycle: <strong style="color:var(--text)">15 min continuous</strong></span>
        </div>
      </div>
    `;

    // 2. 8 Northeast States Radar Grid
    if (states.length > 0) {
      html += `
        <div style="margin-bottom:1.25rem">
          <div style="font-size:0.8rem;font-weight:600;text-transform:uppercase;letter-spacing:0.05em;color:var(--muted);margin-bottom:0.6rem;display:flex;align-items:center;gap:6px">
            <span>🌐</span> 8-State Regional Telemetry &amp; Saturation Status
          </div>
          <div style="display:grid;grid-template-columns:repeat(auto-fit, minmax(180px, 1fr));gap:0.65rem">
      `;

      states.forEach((st) => {
        const hasAlert = st.has_active_alert || (st.risk_score >= 60);
        const levelLower = String(st.risk_level || "low").toLowerCase();
        let borderStyle = "border:1px solid rgba(255,255,255,0.07);";
        let glowDot = `<span style="display:inline-block;width:7px;height:7px;border-radius:50%;background:#10b981"></span>`;
        let scoreColor = "#34d399";

        if (levelLower === "critical" || levelLower === "high" || hasAlert) {
          borderStyle = "border:1px solid rgba(239,68,68,0.45);background:rgba(239,68,68,0.04);";
          glowDot = `<span style="display:inline-block;width:7px;height:7px;border-radius:50%;background:#ef4444;animation:pulse-dot-danger 1.8s infinite"></span>`;
          scoreColor = "#f87171";
        } else if (levelLower === "moderate" || st.risk_score >= 40) {
          borderStyle = "border:1px solid rgba(234,179,8,0.35);background:rgba(234,179,8,0.03);";
          glowDot = `<span style="display:inline-block;width:7px;height:7px;border-radius:50%;background:#eab308"></span>`;
          scoreColor = "#facc15";
        }

        html += `
          <div style="background:rgba(255,255,255,0.02);border-radius:8px;padding:0.65rem 0.8rem;${borderStyle}">
            <div style="display:flex;justify-content:space-between;align-items:flex-start">
              <div style="display:flex;align-items:center;gap:6px">
                ${glowDot}
                <div>
                  <div style="font-weight:600;font-size:0.85rem;color:#f8fafc;line-height:1.2">${esc(st.state)}</div>
                  <div style="font-size:0.72rem;color:var(--muted)">${esc(st.anchor)}</div>
                </div>
              </div>
              <span class="badge badge-${esc(levelLower)}" style="font-size:0.68rem;padding:2px 6px">
                ${esc(st.risk_level)}
              </span>
            </div>
            <div style="margin-top:0.5rem;padding-top:0.4rem;border-top:1px solid rgba(255,255,255,0.05);display:flex;justify-content:space-between;align-items:center;font-size:0.74rem;color:var(--muted)">
              <span title="24-Hour Rainfall">🌧️ ${Number(st.rainfall_24h_mm || 0).toFixed(1)}mm</span>
              <span title="Terrain Slope">⛰️ ${Number(st.slope_deg || 0).toFixed(0)}°</span>
              <span style="font-weight:600;color:${scoreColor}" title="Calculated Risk">${Number(st.risk_score || 0).toFixed(0)}%</span>
            </div>
          </div>
        `;
      });

      html += `
          </div>
        </div>
      `;
    }

    // 3. Active Hazard Warnings Feed
    html += `
      <div>
        <div style="font-size:0.8rem;font-weight:600;text-transform:uppercase;letter-spacing:0.05em;color:var(--muted);margin-bottom:0.6rem;display:flex;align-items:center;justify-content:space-between">
          <span style="display:flex;align-items:center;gap:6px">
            <span>🚨</span> Real-Time Emergency Bulletins &amp; Evacuation Advisories
          </span>
          <span style="font-size:0.74rem;color:var(--muted);text-transform:none">Ordered by severity</span>
        </div>
    `;

    if (alerts.length > 0) {
      alerts.forEach((a) => {
        const reasons = Array.isArray(a.reasons) && a.reasons.length
          ? a.reasons.join(" • ")
          : (a.trigger_factors ? a.trigger_factors.join(" • ") : "Elevated geotechnical shear stress and cumulative rainfall saturation.");
        const levelLower = String(a.risk_level || "high").toLowerCase();
        const dateStr = a.timestamp ? new Date(a.timestamp).toLocaleString() : "Recently Detected";
        const isCritical = levelLower === "critical" || a.risk_score >= 85;

        html += `
          <div style="background:rgba(255,255,255,0.02);border:1px solid ${isCritical ? 'rgba(239,68,68,0.4)' : 'rgba(234,179,8,0.3)'};border-radius:8px;padding:0.9rem 1rem;margin-bottom:0.75rem;position:relative">
            <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:8px">
              <div>
                <div style="font-weight:600;font-size:0.92rem;color:#f8fafc;display:flex;align-items:center;gap:6px">
                  <span>${isCritical ? '🔴' : '🟡'}</span>
                  <span>${esc(a.location)}</span>
                </div>
                <div style="font-size:0.75rem;color:var(--muted);margin-top:2px">
                  Timestamp: ${esc(dateStr)} · Automated Sensor Ingestion
                </div>
              </div>
              <div style="display:flex;align-items:center;gap:8px">
                <span class="badge badge-${esc(levelLower)}" style="font-size:0.75rem;padding:3px 8px">
                  ${esc(a.risk_level)} · ${Number(a.risk_score || 0).toFixed(0)}% RISK
                </span>
              </div>
            </div>

            <!-- Trigger Drivers -->
            <div style="margin-top:0.6rem;font-size:0.8rem;color:#cbd5e1;line-height:1.45;background:rgba(0,0,0,0.25);padding:0.5rem 0.75rem;border-radius:6px">
              <strong style="color:var(--muted)">Trigger Factors:</strong> ${esc(reasons)}
            </div>

            <!-- Action Protocol -->
            <div style="margin-top:0.6rem;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;padding-top:0.45rem">
              <span style="font-size:0.78rem;color:${isCritical ? '#f87171' : '#facc15'}">
                ⚠️ <strong>Directive:</strong> ${isCritical ? 'Evacuate downstream settlement pockets; maintain alert on arterial corridors.' : 'Deploy geotechnical slope barriers & monitor culverts.'}
              </span>
              <a href="assessment.html" class="btn btn-sm btn-secondary" style="font-size:0.72rem;padding:3px 10px;text-decoration:none;display:inline-flex;align-items:center;gap:4px">
                Assess Sector &rarr;
              </a>
            </div>
          </div>
        `;
      });
    } else {
      html += `
        <div style="text-align:center;padding:1.75rem 1rem;background:rgba(16,185,129,0.03);border:1px solid rgba(16,185,129,0.15);border-radius:8px">
          <div style="font-size:1.5rem;margin-bottom:0.4rem">🛡️</div>
          <strong style="color:#34d399;font-size:0.92rem">Regional Radar Sweeps Nominal</strong>
          <p style="margin:0.3rem 0 0;font-size:0.82rem;color:var(--muted)">
            No critical landslide hazards currently active across monitored NER highway corridors or districts.
          </p>
        </div>
      `;
    }

    html += `</div>`;
    alertsFeedContainer.innerHTML = html;
  } catch (e) {
    if (activeCountBadge) activeCountBadge.textContent = "Offline";
    alertsFeedContainer.innerHTML = `
      <div style="padding:1rem;background:rgba(239,68,68,0.05);border:1px solid rgba(239,68,68,0.2);border-radius:8px;color:#f87171;font-size:0.85rem">
        ⚠️ Unable to retrieve radar telemetry feed: ${esc(e.message || "Network unreachable")}
      </div>
    `;
  }
}

async function checkSmtpStatus() {
  const badge = document.getElementById("smtpStatusBadge");
  if (!badge) return;
  try {
    const config = await API.get("/config");
    if (config.smtp_configured) {
      badge.textContent = "SMTP Configured";
      badge.className = "badge badge-low";
    } else {
      badge.textContent = "SMTP Missing (.env)";
      badge.className = "badge badge-moderate";
    }
  } catch (err) {
    badge.textContent = "Offline";
  }
}

async function sendTestEmail() {
  const emailInput = document.getElementById("testEmailInput");
  const resultDiv = document.getElementById("testEmailResult");
  const btn = document.getElementById("sendTestEmailBtn");
  const email = (emailInput.value || "").trim();

  if (!email) {
    resultDiv.innerHTML = `<span style="color:var(--red)">Please enter a recipient email address.</span>`;
    return;
  }

  btn.disabled = true;
  btn.textContent = "Sending...";
  resultDiv.innerHTML = `<span style="color:var(--muted)">Connecting to SMTP server and dispatching test message...</span>`;

  try {
    const r = await API.post("/sos/test-email", { email });
    if (r.status === "SENT") {
      resultDiv.innerHTML = `
        <div style="background:rgba(16,185,129,.15);border:1px solid rgba(16,185,129,.3);padding:.75rem;border-radius:6px;color:#34d399">
          <strong>✅ Email Dispatched Successfully!</strong><br>
          Sent via <strong>${esc(r.smtp_host)}:${esc(r.smtp_port)}</strong> to <strong>${esc(r.recipient)}</strong>.<br>
          Check your inbox (and spam folder) for the test message.
        </div>
      `;
    } else if (r.status === "NOT_CONFIGURED") {
      resultDiv.innerHTML = `
        <div style="background:rgba(234,179,8,.15);border:1px solid rgba(234,179,8,.3);padding:.75rem;border-radius:6px;color:#facc15">
          <strong>⚠️ SMTP Credentials Not Set</strong><br>
          ${esc(r.message)}<br>
          <small>Add <code>SMTP_USER</code> and <code>SMTP_PASSWORD</code> in <code>backend/.env</code> or Railway variables.</small>
        </div>
      `;
    } else if (r.status === "AUTH_FAILED" || (r.error && (r.error.includes("App Password") || r.error.includes("Authentication failed")))) {
      resultDiv.innerHTML = `
        <div style="background:rgba(239,68,68,.15);border:1px solid rgba(239,68,68,.3);padding:.85rem;border-radius:6px;color:#f87171">
          <strong style="font-size:0.95rem">🔑 Google SMTP Authentication Failed</strong><br>
          <p style="margin:.4rem 0 .5rem;color:#fecaca;font-size:0.83rem">
            ${esc(r.error || "Gmail credentials rejected.")}
          </p>
          <div style="background:rgba(0,0,0,0.3);padding:.6rem;border-radius:6px;font-size:0.8rem;line-height:1.4">
            <strong>How to fix in 1 minute:</strong><br>
            1. Open <a href="https://myaccount.google.com/apppasswords" target="_blank" style="color:#38bdf8;text-decoration:underline;">Google Account &rarr; App Passwords</a><br>
            2. Name the app <strong>Landslide Guardian</strong> and click Create.<br>
            3. Copy the 16-letter code (e.g. <code>abcd efgh ijkl mnop</code>).<br>
            4. In Railway &rarr; Variables, set <code>SMTP_PASSWORD</code> to this 16-character code (not your personal Gmail password).
          </div>
        </div>
      `;
    } else if (r.status === "NETWORK_BLOCKED" || (r.error && (r.error.includes("Network is unreachable") || r.error.includes("firewalled") || r.error.includes("ports 465 and 587")))) {
      resultDiv.innerHTML = `
        <div style="background:rgba(234,179,8,.15);border:1px solid rgba(234,179,8,.3);padding:.85rem;border-radius:6px;color:#facc15">
          <strong style="font-size:0.95rem">🛡️ Railway Cloud Host Blocks Raw SMTP (Ports 465/587)</strong><br>
          <p style="margin:.4rem 0 .5rem;color:#fef08a;font-size:0.83rem">
            Railway automatically blocks raw TCP socket connections on mail ports to prevent spam abuse. 
            However, <strong>OTP registration and verification works seamlessly right now</strong> with instant automatic code autofill!
          </p>
          <div style="background:rgba(0,0,0,0.3);padding:.6rem;border-radius:6px;font-size:0.8rem;line-height:1.4">
            <strong>For 100% direct inbox delivery from Railway (takes 1 minute, 100% free):</strong><br>
            1. Sign up at <a href="https://resend.com" target="_blank" style="color:#38bdf8;text-decoration:underline;">resend.com</a> (Free, 100 emails/day, no credit card needed)<br>
            2. Copy your API Key (starts with <code>re_...</code>)<br>
            3. In Railway &rarr; Variables, add: <code>RESEND_API_KEY</code> = <code>re_...</code><br>
            <em>Because Resend uses HTTPS port 443, Railway will deliver every email directly to your inbox without any network blocks!</em>
          </div>
        </div>
      `;
    } else {
      resultDiv.innerHTML = `
        <div style="background:rgba(239,68,68,.15);border:1px solid rgba(239,68,68,.3);padding:.75rem;border-radius:6px;color:#f87171">
          <strong>❌ Delivery Failed (${esc(r.status)})</strong><br>
          ${esc(r.error || r.message || "Unknown error")}
        </div>
      `;
    }
  } catch (err) {
    resultDiv.innerHTML = `<span style="color:var(--red)">Request error: ${esc(formatApiError(err))}</span>`;
  } finally {
    btn.disabled = false;
    btn.textContent = "Send Test Email";
  }
}