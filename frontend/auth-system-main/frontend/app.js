/**
 * Arial Sense — Frontend Auth Client
 *
 * Token strategy:
 *   - Access token:  in-memory only (lost on page refresh — secure by design)
 *   - Refresh token: localStorage (persists; rotation — new token stored on every refresh)
 */

const API    = 'https://auth-system-production-f61f.up.railway.app';
const RT_KEY = 'as_refresh_token';

let _accessToken  = null;
let _pendingToken = null; // holds the 2FA pending JWT between login and OTP entry

// ─── Token Helpers ────────────────────────────────────────────────────────────

const getRT   = ()  => localStorage.getItem(RT_KEY);
const setRT   = (t) => localStorage.setItem(RT_KEY, t);
const clearRT = ()  => localStorage.removeItem(RT_KEY);

function clearTokens() {
  _accessToken  = null;
  _pendingToken = null;
  clearRT();
}

// ─── API Client ───────────────────────────────────────────────────────────────
// Always returns { ok, status, data }.
// JSON parse errors are caught internally — the outer catch only fires on true
// network failures (server unreachable, CORS hard block, etc.).

async function api(method, path, body = null, auth = false) {
  const headers = { 'Content-Type': 'application/json' };
  if (auth && _accessToken) headers['Authorization'] = `Bearer ${_accessToken}`;

  const res = await fetch(API + path, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });

  let data;
  try {
    data = await res.json();
  } catch {
    // Server returned a non-JSON body (plain-text 500, empty body, etc.)
    data = { detail: `Server error (HTTP ${res.status}). Check the backend logs.` };
  }

  return { ok: res.ok, status: res.status, data };
}

// ─── Refresh Flow (with token rotation) ──────────────────────────────────────

async function silentRefresh() {
  const rt = getRT();
  if (!rt) return false;
  try {
    const { ok, data } = await api('POST', '/auth/refresh', { refresh_token: rt });
    if (!ok) { clearTokens(); return false; }
    _accessToken = data.access_token;
    if (data.refresh_token) setRT(data.refresh_token);
    return true;
  } catch {
    return false;
  }
}

// ─── Toast ────────────────────────────────────────────────────────────────────

function toast(message, type = 'error') {
  const el = document.getElementById('toast');
  if (!el) return;
  el.textContent = message;
  el.className = `toast ${type}`;
}

function clearToast() {
  const el = document.getElementById('toast');
  if (!el) return;
  el.className = 'toast hidden';
}

// ─── Button helpers ───────────────────────────────────────────────────────────

function setLoading(btn, state) {
  btn.disabled = state;
  btn.classList.toggle('loading', state);
}

// ─── Password Strength ────────────────────────────────────────────────────────

function measureStrength(pw) {
  let score = 0;
  if (pw.length >= 8)           score++;
  if (/[A-Z]/.test(pw))         score++;
  if (/[a-z]/.test(pw))         score++;
  if (/\d/.test(pw))            score++;
  if (/[^A-Za-z0-9]/.test(pw)) score++;
  return score;
}

const STRENGTH_COLORS = ['#ef4444', '#f97316', '#eab308', '#22c55e', '#10b981'];

function updateStrengthBar(input) {
  const fill = document.getElementById('strength-fill');
  if (!fill) return;
  const score = measureStrength(input.value);
  fill.style.width = `${(score / 5) * 100}%`;
  fill.style.backgroundColor = score > 0 ? STRENGTH_COLORS[score - 1] : 'transparent';
}

// ─── Error extractor (Pydantic + plain strings) ───────────────────────────────

function extractError(data) {
  if (!data) return 'Something went wrong.';
  if (typeof data.detail === 'string') return data.detail;
  if (Array.isArray(data.detail) && data.detail.length > 0) {
    const msg = data.detail[0].msg || '';
    return msg.replace(/^Value error,\s*/i, '');
  }
  return 'Something went wrong.';
}

// ─────────────────────────────────────────────────────────────────────────────
// PAGE: index.html
// ─────────────────────────────────────────────────────────────────────────────

async function initAuthPage() {
  if (getRT()) {
    const ok = await silentRefresh();
    if (ok) { window.location.replace('dashboard.html'); return; }
  }
  _setupTabs();
  _setupPasswordToggles();
  _setupSigninForm();
  _setupSignupForm();
  _setupForgotFlow();
  _setupOTPForm();
}

// ── Tab switching ─────────────────────────────────────────────────────────────

function _setupTabs() {
  document.querySelectorAll('.tab').forEach(tab => {
    tab.addEventListener('click', () => {
      document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      document.querySelectorAll('.form-panel').forEach(p => p.classList.remove('active'));
      document.getElementById(tab.dataset.tab + '-panel').classList.add('active');
      clearToast();
    });
  });
}

// ── Password Show/Hide ────────────────────────────────────────────────────────

function _setupPasswordToggles() {
  document.querySelectorAll('.pw-toggle').forEach(btn => {
    btn.addEventListener('click', () => {
      const input = btn.closest('.input-wrap').querySelector('input');
      const show  = input.type === 'password';
      input.type  = show ? 'text' : 'password';
      btn.textContent = show ? 'Hide' : 'Show';
    });
  });
}

// ── Sign In Form ──────────────────────────────────────────────────────────────

function _setupSigninForm() {
  document.getElementById('signin-form').addEventListener('submit', async e => {
    e.preventDefault();
    clearToast();
    const btn      = e.target.querySelector('.btn-primary');
    const email    = e.target.email.value.trim();
    const password = e.target.password.value;

    setLoading(btn, true);
    try {
      const { ok, data } = await api('POST', '/auth/login', { email, password });
      if (!ok) { toast(extractError(data)); return; }

      if (data.requires_otp) {
        _pendingToken = data.pending_token;
        _showOTPPanel();
        return;
      }

      _accessToken = data.access_token;
      setRT(data.refresh_token);
      window.location.replace('dashboard.html');
    } catch {
      toast('Cannot reach the server. Is the backend running?');
    } finally {
      setLoading(btn, false);
    }
  });
}

// ── Sign Up Form ──────────────────────────────────────────────────────────────

function _setupSignupForm() {
  const pwInput = document.querySelector('#signup-form input[name="password"]');
  if (pwInput) pwInput.addEventListener('input', () => updateStrengthBar(pwInput));

  document.getElementById('signup-form').addEventListener('submit', async e => {
    e.preventDefault();
    clearToast();
    const btn              = e.target.querySelector('.btn-primary');
    const email            = e.target.email.value.trim();
    const username         = e.target.username.value.trim();
    const password         = e.target.password.value;
    const confirm_password = e.target.confirm_password.value;

    setLoading(btn, true);
    try {
      const { ok, data } = await api('POST', '/auth/signup', { email, username, password, confirm_password });
      if (!ok) { toast(extractError(data)); return; }
      toast(data.message, 'success');
      e.target.reset();
      if (pwInput) updateStrengthBar(pwInput);
      setTimeout(() => document.querySelector('[data-tab="signin"]').click(), 2200);
    } catch {
      toast('Cannot reach the server. Is the backend running?');
    } finally {
      setLoading(btn, false);
    }
  });
}

// ── Forgot Password Flow ──────────────────────────────────────────────────────

function _setupForgotFlow() {
  document.getElementById('forgot-link')?.addEventListener('click', e => {
    e.preventDefault();
    clearToast();
    document.querySelectorAll('.form-panel').forEach(p => p.classList.remove('active'));
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.getElementById('forgot-panel').classList.add('active');
  });

  document.getElementById('back-to-signin')?.addEventListener('click', e => {
    e.preventDefault();
    document.querySelector('[data-tab="signin"]').click();
  });

  document.getElementById('forgot-form')?.addEventListener('submit', async e => {
    e.preventDefault();
    clearToast();
    const btn   = e.target.querySelector('.btn-primary');
    const email = e.target.email.value.trim();

    setLoading(btn, true);
    try {
      await api('POST', '/auth/forgot-password', { email });
      toast('If an account exists, a reset link has been sent.', 'success');
    } catch {
      toast('Cannot reach the server. Is the backend running?');
    } finally {
      setLoading(btn, false);
    }
  });
}

// ── 2FA OTP Flow ──────────────────────────────────────────────────────────────

function _showOTPPanel() {
  document.querySelectorAll('.form-panel').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  document.getElementById('otp-panel').classList.add('active');
  clearToast();
  document.getElementById('otp-input')?.focus();
}

function _setupOTPForm() {
  document.getElementById('back-from-otp')?.addEventListener('click', e => {
    e.preventDefault();
    _pendingToken = null;
    document.querySelector('[data-tab="signin"]').click();
  });

  document.getElementById('otp-form')?.addEventListener('submit', async e => {
    e.preventDefault();
    clearToast();
    const btn = e.target.querySelector('.btn-primary');
    const otp = e.target.otp.value.trim();

    if (!_pendingToken) {
      toast('Session expired. Please sign in again.');
      document.querySelector('[data-tab="signin"]').click();
      return;
    }

    setLoading(btn, true);
    try {
      const { ok, data } = await api('POST', '/auth/verify-otp', { pending_token: _pendingToken, otp });
      if (!ok) { toast(extractError(data)); return; }

      _accessToken  = data.access_token;
      _pendingToken = null;
      setRT(data.refresh_token);
      window.location.replace('dashboard.html');
    } catch {
      toast('Cannot reach the server. Is the backend running?');
    } finally {
      setLoading(btn, false);
    }
  });
}

// ─────────────────────────────────────────────────────────────────────────────
// PAGE: dashboard.html
// ─────────────────────────────────────────────────────────────────────────────

async function initDashboardPage() {
  if (!_accessToken) {
    const ok = await silentRefresh();
    if (!ok) { window.location.replace('index.html'); return; }
  }
  document.getElementById('logout-btn').addEventListener('click', _handleLogout);
  await _loadProfile();
}

async function _loadProfile() {
  try {
    const { ok, data } = await api('GET', '/users/me', null, true);
    if (!ok) { window.location.replace('index.html'); return; }

    const initials = (data.username || data.email).charAt(0).toUpperCase();
    document.getElementById('avatar-initials').textContent   = initials;
    document.getElementById('user-display-name').textContent = data.username || data.email.split('@')[0];
    document.getElementById('user-email').textContent        = data.email;
    document.getElementById('user-id').textContent           = data.id;
    document.getElementById('user-joined').textContent       = _formatDate(data.created_at);

    document.getElementById('user-status').innerHTML = data.is_verified
      ? '<span class="badge verified">&#10003; Verified</span>'
      : '<span class="badge unverified">&#9888; Unverified</span>';

    document.getElementById('user-active').innerHTML = data.is_active
      ? '<span class="badge active-badge">Active</span>'
      : '<span class="badge unverified">Inactive</span>';

    _render2FARow(data.is_2fa_enabled);

    document.getElementById('user-card').classList.remove('hidden');
    document.getElementById('skeleton-card').classList.add('hidden');
  } catch {
    window.location.replace('index.html');
  }
}

function _render2FARow(enabled) {
  const badge = document.getElementById('user-2fa');
  const btn   = document.getElementById('toggle-2fa-btn');
  if (!badge || !btn) return;

  badge.innerHTML = enabled
    ? '<span class="badge verified">&#10003; Enabled</span>'
    : '<span class="badge unverified">Disabled</span>';

  btn.textContent  = enabled ? 'Disable' : 'Enable';
  btn.className    = enabled ? 'toggle-2fa-btn danger' : 'toggle-2fa-btn';
  btn.style.display = 'inline-flex';
  btn.dataset.enabled = enabled ? 'true' : 'false';
}

async function _toggle2FA() {
  const btn     = document.getElementById('toggle-2fa-btn');
  const enabled = btn.dataset.enabled === 'true';
  const endpoint = enabled ? '/users/2fa/disable' : '/users/2fa/enable';

  btn.disabled    = true;
  btn.textContent = '...';

  const { ok, data } = await api('POST', endpoint, null, true);
  if (ok) {
    _render2FARow(!enabled);
  } else {
    // Restore button and show error briefly
    _render2FARow(enabled);
    const badge = document.getElementById('user-2fa');
    const prev  = badge.innerHTML;
    badge.innerHTML = `<span style="color:var(--error);font-size:12px;">${extractError(data)}</span>`;
    setTimeout(() => { badge.innerHTML = prev; }, 3000);
  }
}

function _formatDate(iso) {
  return new Date(iso).toLocaleDateString('en-US', {
    year: 'numeric', month: 'long', day: 'numeric',
  });
}

async function _handleLogout() {
  const rt = getRT();
  if (rt) {
    try { await api('POST', '/auth/logout', { refresh_token: rt }); } catch { /* best-effort */ }
  }
  clearTokens();
  window.location.replace('index.html');
}

// ─────────────────────────────────────────────────────────────────────────────
// PAGE: verify-email.html
// ─────────────────────────────────────────────────────────────────────────────

async function initVerifyEmailPage() {
  const token    = new URLSearchParams(window.location.search).get('token');
  const statusEl = document.getElementById('status');

  if (!token) {
    statusEl.innerHTML = '<div class="toast error">Missing verification token. Please use the link from your email.</div>';
    return;
  }

  statusEl.innerHTML = '<p style="color:var(--text-muted);font-size:14px;">Verifying your email&hellip;</p>';

  try {
    const { ok, data } = await api('POST', '/auth/verify-email', { token });
    if (ok) {
      statusEl.innerHTML = `<div class="toast success">${data.message}</div>
        <p style="color:var(--text-muted);font-size:13px;margin-top:14px;">
          Redirecting to sign in&hellip;
        </p>`;
      setTimeout(() => window.location.replace('index.html'), 2000);
    } else {
      statusEl.innerHTML = `<div class="toast error">${extractError(data)}</div>
        <p style="margin-top:14px;font-size:13px;color:var(--text-muted);">
          <a href="index.html" style="color:var(--primary);">Back to sign in</a>
        </p>`;
    }
  } catch {
    statusEl.innerHTML = '<div class="toast error">Cannot reach the server. Is the backend running?</div>';
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// PAGE: reset-password.html
// ─────────────────────────────────────────────────────────────────────────────

async function initResetPasswordPage() {
  const token    = new URLSearchParams(window.location.search).get('token');
  const formEl   = document.getElementById('reset-form');
  const statusEl = document.getElementById('status');

  if (!token) {
    statusEl.innerHTML = '<div class="toast error">Missing reset token. Please use the link from your email.</div>';
    if (formEl) formEl.style.display = 'none';
    return;
  }

  _setupPasswordToggles();

  const pwInput = document.querySelector('#reset-form input[name="password"]');
  if (pwInput) pwInput.addEventListener('input', () => updateStrengthBar(pwInput));

  formEl?.addEventListener('submit', async e => {
    e.preventDefault();
    statusEl.innerHTML = '';
    const btn              = e.target.querySelector('.btn-primary');
    const password         = e.target.password.value;
    const confirm_password = e.target.confirm_password.value;

    setLoading(btn, true);
    try {
      const { ok, data } = await api('POST', '/auth/reset-password', { token, password, confirm_password });
      if (ok) {
        statusEl.innerHTML = `<div class="toast success">${data.message}</div>`;
        if (formEl) formEl.style.display = 'none';
        setTimeout(() => window.location.replace('index.html'), 2000);
      } else {
        statusEl.innerHTML = `<div class="toast error">${extractError(data)}</div>`;
      }
    } catch {
      statusEl.innerHTML = '<div class="toast error">Cannot reach the server. Is the backend running?</div>';
    } finally {
      setLoading(btn, false);
    }
  });
}
