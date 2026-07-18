import { api } from "../api/client.js";

export function Results({ room, isHost, token }) {
  const winner = room.options.find((o) => o.id === room.winner_option_id);

  async function reset() {
    try { await api.reset(room.code, token); }
    catch (err) { console.error(err); }
  }

  return (
    <div className="phase phase--results">
      <h2>Settled.</h2>
      {winner ? (
        <div className="winner">
          <div className="winner__label">Winner</div>
          <div className="winner__text">{winner.text}</div>
          <div className="winner__meta">
            chosen by <strong>{prettyAlgo(room.algorithm)}</strong>
          </div>
        </div>
      ) : (
        <p className="empty">No winner — all options were vetoed.</p>
      )}

      <div className="eliminated">
        <h3>Eliminated</h3>
        <ul>
          {room.options
            .filter((o) => o.id !== room.winner_option_id)
            .map((o) => (
              <li key={o.id}>{o.text}</li>
            ))}
        </ul>
      </div>

      {room.meta?.trace && (
        <details className="trace">
          <summary>Algorithm trace</summary>
          <pre>{JSON.stringify(room.meta, null, 2)}</pre>
        </details>
      )}

      {isHost && (
        <div className="host-controls">
          <button className="btn btn--secondary" onClick={reset}>
            Run another round
          </button>
        </div>
      )}
    </div>
  );
}

function prettyAlgo(a) {
  return {
    iterative_veto: "Iterative Veto",
    bracket: "Bracket",
    weighted_random: "Weighted Random",
  }[a] || a;
}
