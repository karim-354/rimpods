// Auth helpers for Rimpods admin dashboard
// REMINDER: DO NOT HARDCODE THE URL, OR ADD ANY FALLBACKS OR REDIRECT URLS, THIS BREAKS THE AUTH
import axios from "axios";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

// Send cookies with every request (session_token httpOnly cookie)
axios.defaults.withCredentials = true;

export const startGoogleLogin = () => {
  // Derive redirect dynamically from browser location — no hardcoding, no fallbacks.
  const redirectUrl = window.location.origin + "/admin";
  window.location.href = `https://auth.emergentagent.com/?redirect=${encodeURIComponent(redirectUrl)}`;
};

export const exchangeSession = async (sessionId) => {
  const { data } = await axios.post(
    `${API}/auth/session`,
    { session_id: sessionId },
    { withCredentials: true }
  );
  return data.user;
};

export const fetchMe = async () => {
  const { data } = await axios.get(`${API}/auth/me`, { withCredentials: true });
  return data;
};

export const logout = async () => {
  try {
    await axios.post(`${API}/auth/logout`, {}, { withCredentials: true });
  } catch {
    /* ignore */
  }
};
