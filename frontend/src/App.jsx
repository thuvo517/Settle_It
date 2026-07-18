import { Routes, Route, Navigate } from "react-router-dom";
import { Home } from "./components/Home.jsx";
import { Room } from "./components/Room.jsx";

export default function App() {
  return (
    <div className="app-shell">
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/room/:code" element={<Room />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </div>
  );
}
