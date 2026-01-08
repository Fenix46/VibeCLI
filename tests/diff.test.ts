import { describe, it, expect } from "vitest";
import { applyUnifiedDiff } from "../src/utils/diff.js";

describe("applyUnifiedDiff", () => {
  it("applies a simple hunk", () => {
    const original = "one\ntwo\nthree";
    const diff = [
      "--- a/file.txt",
      "+++ b/file.txt",
      "@@ -1,3 +1,3 @@",
      " one",
      "-two",
      "+TWO",
      " three"
    ].join("\n");
    const updated = applyUnifiedDiff(original, diff);
    expect(updated).toBe("one\nTWO\nthree");
  });
});
