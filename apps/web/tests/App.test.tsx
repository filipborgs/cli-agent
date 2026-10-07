import { render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import App from "@/App";
import { getHealth } from "@/api/health";

vi.mock("@/api/health", () => ({ getHealth: vi.fn() }));

const getHealthMock = vi.mocked(getHealth);

describe("App", () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it("shows loading while the API request is pending", () => {
    getHealthMock.mockReturnValue(new Promise(() => undefined));

    render(<App />);

    expect(screen.getByText("Verificando API...")).toBeInTheDocument();
  });

  it("shows success after a valid API response", async () => {
    getHealthMock.mockResolvedValue({ status: "ok" });

    render(<App />);

    expect(await screen.findByText("API operacional")).toBeInTheDocument();
  });

  it("shows a safe error after an API failure", async () => {
    getHealthMock.mockRejectedValue(new Error("internal detail"));

    render(<App />);

    expect(
      await screen.findByText("Nao foi possivel conectar a API."),
    ).toBeInTheDocument();
    expect(screen.queryByText("internal detail")).not.toBeInTheDocument();
  });

  it("aborts a pending request when unmounted", async () => {
    let signal: AbortSignal | undefined;
    getHealthMock.mockImplementation((requestSignal) => {
      signal = requestSignal;
      return new Promise(() => undefined);
    });

    const { unmount } = render(<App />);
    unmount();

    await waitFor(() => expect(signal?.aborted).toBe(true));
  });
});
