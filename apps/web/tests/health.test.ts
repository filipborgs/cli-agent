import { afterEach, describe, expect, it, vi } from "vitest";

import { getHealth } from "@/api/health";

describe("getHealth", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("returns the valid health response", async () => {
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockResolvedValue(
          new Response(JSON.stringify({ status: "ok" }), { status: 200 }),
        ),
    );

    await expect(getHealth()).resolves.toEqual({ status: "ok" });
  });

  it.each([
    [503, { status: "unavailable" }],
    [200, { status: "unexpected" }],
    [200, "not-an-object"],
  ])("rejects an invalid API response", async (status, body) => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response(JSON.stringify(body), { status })),
    );

    await expect(getHealth()).rejects.toThrow("Invalid health response");
  });

  it("normalizes malformed JSON as an invalid response", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: vi.fn().mockRejectedValue(new SyntaxError()),
      }),
    );

    await expect(getHealth()).rejects.toThrow("Invalid health response");
  });
});
