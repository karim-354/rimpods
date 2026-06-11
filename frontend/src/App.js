import "./App.css";
import { lazy, Suspense } from "react";
import { BrowserRouter, Routes, Route, useLocation } from "react-router-dom";
import { Toaster } from "sonner";
import Landing from "./pages/Landing";

// Code splitting: halaman selain Landing dimuat on-demand
// (Checkout membawa Leaflet ~150KB — tidak perlu masuk bundle awal)
const Checkout = lazy(() => import("./pages/Checkout"));
const Success = lazy(() => import("./pages/Success"));
const AdminDashboard = lazy(() => import("./pages/admin/AdminDashboard"));
const AuthCallback = lazy(() => import("./pages/admin/AuthCallback"));

// Detect #session_id=... during render (not useEffect) to avoid race conditions
function AppRouter() {
  const location = useLocation();
  if (location.hash?.includes("session_id=")) {
    return (
      <Suspense fallback={null}>
        <AuthCallback />
      </Suspense>
    );
  }
  return (
    <Suspense fallback={null}>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/checkout" element={<Checkout />} />
        <Route path="/sukses" element={<Success />} />
        <Route path="/admin" element={<AdminDashboard />} />
      </Routes>
    </Suspense>
  );
}

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <Toaster position="top-right" theme="dark" richColors />
        <AppRouter />
      </BrowserRouter>
    </div>
  );
}

export default App;
