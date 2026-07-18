import { useEffect, useMemo, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { api } from "../api/client.js";
import { getSession, clearSession, saveSession } from "../session.js";
import { useRoomSocket } from "../hooks/useRoomSocket.js";
import { useCountdown } from "../hooks/useCountdown.js";
import { Lobby } from "./Lobby.jsx";
import { Submission } from "./Submission.jsx";
import { Voting } from "./Voting.jsx";
import { Results } from "./Results.jsx";
import { JoinPrompt } from "./JoinPrompt.jsx";

export function Room() {
  const { code } = useParams();
  const upperCode = (code || "").toUpperCase();
  const navigate = useNavigate();
  const [session, setSession] = useState(() => getSession(upperCode));
  const [initial, setInitial] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;
    api
      .getRoom(upperCode)
      .then((state) => { if (!cancelled) setInitial(state); })
      .catch((err) => { if (!cancelled) setError(err.message); });
    return () => { cancelled = true; };
  }, [upperCode]);

  const { state, connected } = useRoomSocket(
    session ? upperCode : null,
    session?.token,
    initial,
  );
  const remaining = useCountdown(state?.phase_deadline);

  const me = useMemo(
    () => state?.users?.find((u) => u.id === session?.userId) || null,
    [state, session],
  );

  if (error) {
    return (
      <div className="room__error">
        <p>{error}</p>
        <button className="btn" onClick={() => navigate("/")}>Home</button>
      </div>
    );
  }

  if (!initial) {
    return <div className="loading">Loading room…</div>;
  }

  if (!session || !me) {
    return (
      <JoinPrompt
        code={upperCode}
        room={state || initial}
        onJoin={async (name) => {
          const data = await api.joinRoom(upperCode, name);
          const s = {
            token: data.session_token,
            userId: data.user.id,
            name: data.user.name,
          };
          saveSession(upperCode, s);
          setSession(s);
          setInitial(data.room);
        }}
      />
    );
  }

  const current = state || initial;
  const isHost = me?.is_host;

  return (
    <div className="room">
      <header className="room__header">
        <div>
          <button className="btn btn--ghost" onClick={() => navigate("/")}>← Home</button>
        </div>
        <div className="room__title">
          <h2>{current.title}</h2>
          <div className="room__meta">
            <span className="pill">Code: <strong>{current.code}</strong></span>
            <span className="pill">Algorithm: {prettyAlgo(current.algorithm)}</span>
            <span className="pill">Phase: {current.phase}</span>
            <span className={`pill pill--status ${connected ? "on" : "off"}`}>
              {connected ? "live" : "offline"}
            </span>
            {remaining !== null && (
              <span className="pill pill--timer">⏱ {remaining}s</span>
            )}
          </div>
        </div>
        <button
          className="btn btn--ghost"
          onClick={() => { clearSession(upperCode); navigate("/"); }}
        >
          Leave
        </button>
      </header>

      <div className="room__body">
        <aside className="room__sidebar">
          <h3>Players ({current.users.length})</h3>
          <ul className="player-list">
            {current.users.map((u) => (
              <li key={u.id} className={u.is_online ? "on" : "off"}>
                <span className="dot" />
                <span>{u.name}</span>
                {u.is_host && <span className="badge">host</span>}
                {u.id === me.id && <span className="badge badge--me">you</span>}
              </li>
            ))}
          </ul>
        </aside>

        <main className="room__main">
          {current.phase === "lobby" && (
            <Lobby room={current} me={me} isHost={isHost} token={session.token} />
          )}
          {current.phase === "submission" && (
            <Submission room={current} me={me} token={session.token} isHost={isHost} />
          )}
          {current.phase === "voting" && (
            <Voting room={current} me={me} token={session.token} isHost={isHost} />
          )}
          {current.phase === "results" && (
            <Results room={current} isHost={isHost} token={session.token} />
          )}
        </main>
      </div>
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
