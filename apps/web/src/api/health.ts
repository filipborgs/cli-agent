export interface HealthResponse {
  status: "ok";
}

export async function getHealth(signal?: AbortSignal): Promise<HealthResponse> {
  try {
    const response = await fetch("/api/health", { signal });
    const body: unknown = await response.json();

    if (!response.ok || !isHealthResponse(body)) {
      throw new Error("Invalid health response");
    }

    return body;
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") {
      throw error;
    }

    throw new Error("Invalid health response", { cause: error });
  }
}

function isHealthResponse(value: unknown): value is HealthResponse {
  return (
    typeof value === "object" &&
    value !== null &&
    "status" in value &&
    value.status === "ok"
  );
}
