import { useMemo, useState } from "react";
import { api } from "../api/client.js";

export function Voting({ room, me, token, isHost }) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  const myVotes = useMemo(() => {
    const map = {};
    for (const v of room.votes) {
      if (v.user_id === me.id) map[v.option_id] = v;
    }
    return map;
  }, [room.votes, me.id]);

  async function vote(optionId, kind, dealbreaker) {
    setBusy(true); setError(null);
    try { await api.castVote(room.code, token, optionId, kind, dealbreaker); }
    catch (err) { setError(err.message); }
    finally { setBusy(false); }
  }

  async function resolve() {
    try { await api.resolve(room.code, token); }
    catch (err) { setError(err.message); }
  }

  const talliesByOption = useMemo(() => {
    const out = {};
    for (const o of room.options) out[o.id] = { keep: 0, eliminate: 0, db: 0 };
    for (const v of room.votes) {
      const t = out[v.option_id];
      if (!t) continue;
      if (v.is_dealbreaker) t.db += 1;
      else if (v.kind === "keep") t.keep += 1;
      else if (v.kind === "eliminate") t.eliminate += 1;
    }
    return out;
  }, [room.options, room.votes]);

  const votedCount = Object.keys(myVotes).length;

  return (
    <div className="phase phase--voting">
      <h2>Vote</h2>
      <p className="phase__lead">
        For each option, keep it, cut it, or flag a dealbreaker (you really can't
        live with it). You've voted on {votedCount} / {room.options.length}.
      </p>

      <div className="vote-grid">
        {room.options.map((o) => {
          const my = myVotes[o.id];
          const t = talliesByOption[o.id];
          return (
            <div key={o.id} className={`vote-card ${my ? "vote-card--voted" : ""}`}>
              <div className="vote-card__header">
                <span className="vote-card__text">{o.text}</span>
              </div>
              <div className="vote-card__tallies">
                <span className="tally tally--keep">✓ {t.keep}</span>
                <span className="tally tally--eliminate">✕ {t.eliminate}</span>
                <span className="tally tally--db">⛔ {t.db}</span>
              </div>
              <div className="vote-card__actions">
                <button
                  className={`btn btn--small ${my?.kind === "keep" && !my?.is_dealbreaker ? "btn--keep" : ""}`}
                  disabled={busy}
                  onClick={() => vote(o.id, "keep", false)}
                >
                  Keep
                </button>
                <button
                  className={`btn btn--small ${my?.kind === "eliminate" && !my?.is_dealbreaker ? "btn--cut" : ""}`}
                  disabled={busy}
                  onClick={() => vote(o.id, "eliminate", false)}
                >
                  Cut
                </button>
                <button
                  className={`btn btn--small ${my?.is_dealbreaker ? "btn--db" : ""}`}
                  disabled={busy}
                  onClick={() => vote(o.id, "eliminate", true)}
                >
                  Dealbreaker
                </button>
              </div>
            </div>
          );
        })}
      </div>

      {error && <div className="error">{error}</div>}

      {isHost && (
        <div className="host-controls">
          <button className="btn btn--primary" onClick={resolve}>
            Settle it →
          </button>
        </div>
      )}
    </div>
  );
}
