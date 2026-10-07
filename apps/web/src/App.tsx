import { useEffect, useState } from "react";

import { getHealth } from "@/api/health";

type Status = "loading" | "success" | "error";

export default function App() {
  const [status, setStatus] = useState<Status>("loading");

  useEffect(() => {
    const controller = new AbortController();

    void getHealth(controller.signal).then(
      () => {
        if (!controller.signal.aborted) {
          setStatus("success");
        }
      },
      () => {
        if (!controller.signal.aborted) {
          setStatus("error");
        }
      },
    );

    return () => controller.abort();
  }, []);

  return (
    <main>
      <section aria-live="polite">
        <h1>Clinic</h1>
        {status === "loading" && <p>Verificando API...</p>}
        {status === "success" && <p>API operacional</p>}
        {status === "error" && <p>Nao foi possivel conectar a API.</p>}
      </section>
    </main>
  );
}
