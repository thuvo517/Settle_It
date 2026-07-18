import { useState } from "react";
import { api } from "../api/client.js";

const ALGORITHMS = [
  { id: "iterative_veto", name: "Iterative Veto" },
  { id: "bracket", name: "Bracket" },
  { id: "weighted_random", name: "Weighted Random" },
];

export function Lobby({ room, isHost, token }) {
  const [algorithm, setAlgorithm] = useState(room.algorithm);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  async function start() {
    setBusy(true); setError(null);
    try { await api.start(room.code, token, algorithm); }
    catch (err) { setError(err.message); }
    finally { setBusy(false); }
  }

  const inviteUrl = `${window.location.origin}/room/${room.code}`;

  return (
    <div className="phase phase--lobby">
      <h2>Lobby</h2>
      <p className="phase__lead">
        Share the invite link so everyone can jump in. When you're ready, the host
        opens submissions.
      </p>

      <div className="invite">
        <div className="invite__code">{room.code}</div>
        <button className="btn btn--secondary" onClick={() => navigator.clipboard.writeText(inviteUrl)}>
          Copy invite link
        </button>
      </div>

      {isHost ? (
        <div className="host-controls">
          <div className="field">
            <span>Algorithm</span>
            <div className="algo-grid">
              {ALGORITHMS.map((a) => (
                <button
                  key={a.id}
                  type="button"
                  className={`algo ${algorithm === a.id ? "algo--active" : ""}`}
                  onClick={() => setAlgorithm(a.id)}
                >
                  <strong>{a.name}</strong>
                </button>
              ))}
            </div>
          </div>
          {error && <div className="error">{error}</div>}
          <button className="btn btn--primary" disabled={busy || room.users.length < 2} onClick={start}>
            {room.users.length < 2 ? "Need at least 2 players" : busy ? "Starting…" : "Start submissions →"}
          </button>
        </div>
      ) : (
        <p className="waiting">Waiting for host to start…</p>
      )}
    </div>
  );
}
