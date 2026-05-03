import "./App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Toaster } from "sonner";
import Landing from "./pages/Landing";
import Checkout from "./pages/Checkout";
import Success from "./pages/Success";

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <Toaster position="top-right" theme="dark" richColors />
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/checkout" element={<Checkout />} />
          <Route path="/sukses" element={<Success />} />
        </Routes>
      </BrowserRouter>
    </div>
  );
}

export default App;
