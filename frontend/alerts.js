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
      regMsg.innerHTML = `<span style="color:var(--green)">✅ Registered! A 6-digit verification code has been dispatched to <strong>${esc(registeredEmail)}</strong>. Enter it below to activate your SOS alerts.</span>`;
      const otpMsg = document.getElementById("otpMsg");
      if (otpMsg) otpMsg.innerHTML = `<span style="color:var(--green)">📧 Verification code dispatched to your inbox. Check spam/junk if not visible within 1 minute.</span>`;
    } catch (otpErr) {
      regMsg.innerHTML = `<span style="color:var(--green)">✅ Registered ${esc(data.name)}. Please click 'Send verification code' below to receive your OTP.</span>`;
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
    otpMsg.innerHTML = `<span style="color:var(--green)">✉️ ${esc(r.message || "A 6-digit verification code has been dispatched to your email.")}</span>`;
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