import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api/client.js";
import { saveSession } from "../session.js";

const ALGORITHMS = [
  {
    id: "iterative_veto",
    name: "Iterative Veto",
    desc: "Majority rules, lowest-keep falls off. A deliberate, classroom-style elimination.",
  },
  {
    id: "bracket",
    name: "Bracket",
    desc: "March Madness for dinner plans. Options seed into head-to-head rounds.",
  },
  {
    id: "weighted_random",
    name: "Weighted Random",
    desc: "Everyone's vote tilts the odds — fate handles the rest.",
  },
];

export function Home() {
  const navigate = useNavigate();
  const [mode, setMode] = useState("create");
  const [name, setName] = useState("");
  const [title, setTitle] = useState("");
  const [algorithm, setAlgorithm] = useState("iterative_veto");
  const [code, setCode] = useState("");
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  async function submit(e) {
    e.preventDefault();
    setError(null);
    if (!name.trim()) { setError("Please enter a name"); return; }
    setLoading(true);
    try {
      let data;
      if (mode === "create") {
        data = await api.createRoom({
          title: title || "Untitled Decision",
          algorithm,
          host_name: name.trim(),
        });
      } else {
        data = await api.joinRoom(code.trim().toUpperCase(), name.trim());
      }
      saveSession(data.room.code, {
        token: data.session_token,
        userId: data.user.id,
        name: data.user.name,
      });
      navigate(`/room/${data.room.code}`);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="home">
      <header className="home__hero">
        <div className="home__logo">
          <span className="home__logo-mark">S</span>
          <span className="home__logo-word">SettleIt</span>
        </div>
        <h1 className="home__headline">
          Stop the group-chat gridlock.
          <br />
          <span className="home__headline-accent">Settle it in real time.</span>
        </h1>
        <p className="home__sub">
          Spin up a room, everyone tosses in options, and one of three algorithms
          picks a winner — synchronized across every device the moment a vote lands.
        </p>
      </header>

      <div className="card home__card">
        <div className="tabs">
          <button
            className={`tab ${mode === "create" ? "tab--active" : ""}`}
            onClick={() => setMode("create")}
          >Create a room</button>
          <button
            className={`tab ${mode === "join" ? "tab--active" : ""}`}
            onClick={() => setMode("join")}
          >Join with code</button>
        </div>

        <form onSubmit={submit} className="form">
          <label className="field">
            <span>Your name</span>
            <input
              autoFocus
              value={name}
              maxLength={40}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Alex"
            />
          </label>

          {mode === "create" ? (
            <>
              <label className="field">
                <span>What are we settling?</span>
                <input
                  value={title}
                  maxLength={120}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="Friday night dinner"
                />
              </label>
              <div className="field">
                <span>Pick your algorithm</span>
                <div className="algo-grid">
                  {ALGORITHMS.map((a) => (
                    <button
                      key={a.id}
                      type="button"
                      className={`algo ${algorithm === a.id ? "algo--active" : ""}`}
                      onClick={() => setAlgorithm(a.id)}
                    >
                      <strong>{a.name}</strong>
                      <small>{a.desc}</small>
                    </button>
                  ))}
                </div>
              </div>
            </>
          ) : (
            <label className="field">
              <span>Room code</span>
              <input
                value={code}
                maxLength={8}
                onChange={(e) => setCode(e.target.value.toUpperCase())}
                placeholder="ABCD23"
                className="field__code"
              />
            </label>
          )}

          {error && <div className="error">{error}</div>}

          <button className="btn btn--primary" disabled={loading}>
            {loading ? "Working..." : mode === "create" ? "Create room" : "Join room"}
          </button>
        </form>
      </div>

      <footer className="home__footer">
        <span>FastAPI · WebSockets · PostgreSQL · React · Docker</span>
      </footer>
    </div>
  );
}
