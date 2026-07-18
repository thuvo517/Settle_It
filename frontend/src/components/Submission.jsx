import { useState } from "react";
import { api } from "../api/client.js";

export function Submission({ room, me, token, isHost }) {
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  const myOpts = room.options.filter((o) => o.author_id === me.id);
  const limit = 5;

  async function submit(e) {
    e.preventDefault();
    if (!text.trim()) return;
    setBusy(true); setError(null);
    try {
      await api.addOption(room.code, token, text.trim());
      setText("");
    } catch (err) {
      setError(err.message);
    } finally { setBusy(false); }
  }

  async function remove(id) {
    try { await api.deleteOption(room.code, token, id); }
    catch (err) { setError(err.message); }
  }

  async function toVoting() {
    try { await api.startVoting(room.code, token); }
    catch (err) { setError(err.message); }
  }

  return (
    <div className="phase phase--submission">
      <h2>Submit your options</h2>
      <p className="phase__lead">
        Drop anything you'd be happy with. Duplicates (even fuzzy ones) are filtered
        automatically. You have {limit - myOpts.length} submission{limit - myOpts.length === 1 ? "" : "s"} left.
      </p>

      <form onSubmit={submit} className="inline-form">
        <input
          value={text}
          maxLength={160}
          onChange={(e) => setText(e.target.value)}
          placeholder="Thai Kitchen on 3rd"
          disabled={myOpts.length >= limit}
        />
        <button className="btn btn--primary" disabled={busy || myOpts.length >= limit}>Add</button>
      </form>
      {error && <div className="error">{error}</div>}

      <div className="options-grid">
        {room.options.map((o) => (
          <div key={o.id} className="option-card">
            <div className="option-card__text">{o.text}</div>
            <div className="option-card__meta">
              <span>by {authorName(room, o.author_id)}</span>
              {o.author_id === me.id && (
                <button className="link-btn" onClick={() => remove(o.id)}>remove</button>
              )}
            </div>
          </div>
        ))}
        {room.options.length === 0 && (
          <div className="empty">No options yet — be the first!</div>
        )}
      </div>

      {isHost && (
        <div className="host-controls">
          <button
            className="btn btn--primary"
            onClick={toVoting}
            disabled={room.options.length < 2}
          >
            {room.options.length < 2 ? "Need 2+ options" : "Start voting →"}
          </button>
        </div>
      )}
    </div>
  );
}

function authorName(room, id) {
  return room.users.find((u) => u.id === id)?.name || "?";
}
