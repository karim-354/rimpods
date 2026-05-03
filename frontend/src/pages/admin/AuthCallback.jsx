import { useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { exchangeSession } from "../../lib/auth";

// Handles /admin#session_id=xxx returning from Emergent Auth.
// Exchanges session_id for an httpOnly session cookie, then navigates clean to /admin.
export default function AuthCallback() {
  const hasProcessed = useRef(false);
  const navigate = useNavigate();

  useEffect(() => {
    // Idempotent guard — Strict Mode re-invocation safe
    if (hasProcessed.current) return;
    hasProcessed.current = true;

    const hash = window.location.hash || "";
    const match = hash.match(/session_id=([^&]+)/);
    const sessionId = match ? decodeURIComponent(match[1]) : null;

    (async () => {
      if (!sessionId) {
        navigate("/admin", { replace: true });
        return;
      }
      try {
        const user = await exchangeSession(sessionId);
        // Clean URL, pass user to ProtectedRoute via state to skip re-check
        navigate("/admin", { replace: true, state: { user } });
      } catch (err) {
        console.error("Auth exchange failed:", err);
        navigate("/admin", { replace: true, state: { authError: "Autentikasi gagal, mohon coba lagi." } });
      }
    })();
  }, [navigate]);

  return (
    <div className="min-h-screen grid place-items-center bg-[hsl(var(--reef-deep,198_75%_8%))] text-white">
      <div className="text-center">
        <div className="w-10 h-10 border-2 border-current border-t-transparent rounded-full animate-spin mx-auto opacity-60" />
        <p className="mt-4 opacity-70">Menyelesaikan autentikasi…</p>
      </div>
    </div>
  );
}
