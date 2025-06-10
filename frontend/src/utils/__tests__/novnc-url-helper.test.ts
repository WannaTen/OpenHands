import { describe, it, expect, beforeEach, afterEach } from "vitest";
import { transformNovncUrl } from "../novnc-url-helper";

describe("transformNovncUrl", () => {
  const originalWindowLocation = window.location;

  beforeEach(() => {
    // Mock window.location
    Object.defineProperty(window, "location", {
      value: {
        hostname: "example.com",
      },
      writable: true,
    });
  });

  afterEach(() => {
    // Restore window.location
    Object.defineProperty(window, "location", {
      value: originalWindowLocation,
      writable: true,
    });
  });

  it("should return null if input is null", () => {
    expect(transformNovncUrl(null)).toBeNull();
  });

  it("should replace localhost with current hostname when they differ", () => {
    const input = "http://localhost:6080/vnc.html";
    const expected = "http://example.com:6080/vnc.html";

    expect(transformNovncUrl(input)).toBe(expected);
  });

  it("should not modify URL if hostname is not localhost", () => {
    const input = "http://otherhost:6080/vnc.html";

    expect(transformNovncUrl(input)).toBe(input);
  });

  it("should not modify URL if current hostname is also localhost", () => {
    // Change the mocked hostname to localhost
    Object.defineProperty(window, "location", {
      value: {
        hostname: "localhost",
      },
      writable: true,
    });

    const input = "http://localhost:6080/vnc.html";

    expect(transformNovncUrl(input)).toBe(input);
  });

  it("should handle invalid URLs gracefully", () => {
    const input = "not-a-valid-url";

    expect(transformNovncUrl(input)).toBe(input);
  });
});
