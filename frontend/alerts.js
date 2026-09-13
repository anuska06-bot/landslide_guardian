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
    regMsg.innerHTML = `<span style="color:var(--green)">${esc(r.message)}</span>`;
    document.getElementById("otpEmail").value = regEmail.value.trim().toLowerCase();
    e.target.reset();
    populateLocationSelect();
  } catch (err) {
    regMsg.innerHTML = `<span style="color:var(--red)">Registration failed: ${esc(err.message)}</span>`;
  }
}

async function sendOtp() {
  const email = (document.getElementById("otpEmail").value || "").trim().toLowerCase();
  const otpMsg = document.getElementById("otpMsg");
  if (!email) { otpMsg.innerHTML = `<span style="color:var(--red)">Enter your email first.</span>`; return; }
  try {
    const r = await API.post("/auth/send-otp", { email });
    otpMsg.innerHTML = r.demo_otp
      ? `<span style="color:var(--green)">${esc(r.message)}</span>`
      : `<span style="color:var(--green)">${esc(r.message)}</span>`;
  } catch (err) {
    otpMsg.innerHTML = `<span style="color:var(--red)">${esc(err.message)}</span>`;
  }
}

async function verifyOtp() {
  const email = (document.getElementById("otpEmail").value || "").trim().toLowerCase();
  const code = (document.getElementById("otpCode").value || "").trim();
  const otpMsg = document.getElementById("otpMsg");
  if (!email || !code) { otpMsg.innerHTML = `<span style="color:var(--red)">Enter email and code.</span>`; return; }
  try {
    const r = await API.post("/auth/verify-otp", { email, code });
    otpMsg.innerHTML = `<span style="color:var(--green)">✅ ${esc(r.message)}</span>`;
  } catch (err) {
    otpMsg.innerHTML = `<span style="color:var(--red)">${esc(err.message)}</span>`;
  }
}

async function loadActiveAlerts() {
  const activeCountBadge = document.getElementById("activeCountBadge");
  const alertsFeedContainer = document.getElementById("alertsFeedContainer");
  try {
    const alerts = await API.get("/alerts");
    activeCountBadge.textContent = `${alerts.length} Active Warnings`;
    alertsFeedContainer.innerHTML = alerts.length
      ? alerts.map((a) => `
          <div class="factor-pill">
            <span><strong>${esc(a.location)}</strong><br><small>${esc(new Date(a.timestamp).toLocaleString())}</small></span>
            <span class="badge badge-${esc(String(a.risk_level).toLowerCase())}">${esc(a.risk_level)} · ${esc(a.risk_score)}%</span>
          </div>`).join("")
      : '<div class="empty">No high-risk assessments stored yet.</div>';
  } catch (e) {
    activeCountBadge.textContent = "Unavailable";
    alertsFeedContainer.innerHTML = `<div class="empty">${esc(e.message)}</div>`;
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
    } else {
      resultDiv.innerHTML = `
        <div style="background:rgba(239,68,68,.15);border:1px solid rgba(239,68,68,.3);padding:.75rem;border-radius:6px;color:#f87171">
          <strong>❌ Delivery Failed (${esc(r.status)})</strong><br>
          ${esc(r.error || r.message || "Unknown error")}
        </div>
      `;
    }
  } catch (err) {
    resultDiv.innerHTML = `<span style="color:var(--red)">Request error: ${esc(err.message)}</span>`;
  } finally {
    btn.disabled = false;
    btn.textContent = "Send Test Email";
  }
}