import { useEffect, useState } from "react";

export function useCountdown(deadlineISO) {
  const [remaining, setRemaining] = useState(() => calc(deadlineISO));

  useEffect(() => {
    setRemaining(calc(deadlineISO));
    if (!deadlineISO) return;
    const id = setInterval(() => setRemaining(calc(deadlineISO)), 250);
    return () => clearInterval(id);
  }, [deadlineISO]);

  return remaining;
}

function calc(iso) {
  if (!iso) return null;
  const end = new Date(iso).getTime();
  const now = Date.now();
  return Math.max(0, Math.round((end - now) / 1000));
}
