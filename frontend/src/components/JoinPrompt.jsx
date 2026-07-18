import { useState } from "react";

export function JoinPrompt({ code, room, onJoin }) {
  const [name, setName] = useState("");
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  async function submit(e) {
    e.preventDefault();
    if (!name.trim()) { setError("Please enter a name"); return; }
    setLoading(true);
    try { await onJoin(name.trim()); }
    catch (err) { setError(err.message); }
    finally { setLoading(false); }
  }

  const started = room && room.phase !== "lobby";

  return (
    <div className="join-prompt">
      <div className="card">
        <h2>Join {room?.title || code}</h2>
        <p>Room code: <strong>{code}</strong></p>
        {started ? (
          <p className="error">This room has already started. You cannot join mid-session.</p>
        ) : (
          <form onSubmit={submit} className="form">
            <label className="field">
              <span>Your name</span>
              <input autoFocus value={name} onChange={(e) => setName(e.target.value)} maxLength={40} />
            </label>
            {error && <div className="error">{error}</div>}
            <button className="btn btn--primary" disabled={loading}>
              {loading ? "Joining…" : "Join room"}
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
