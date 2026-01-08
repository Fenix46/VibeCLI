import { describe, it, expect } from "vitest";
import { configSchema } from "../src/config/schema.js";
describe("config schema", () => {
    it("applies defaults", () => {
        const cfg = configSchema.parse({});
        expect(cfg.serverPort).toBe(60315);
        expect(cfg.ctxSize).toBe(8192);
    });
    it("rejects invalid port", () => {
        expect(() => configSchema.parse({ serverPort: 10 })).toThrow();
    });
});
//# sourceMappingURL=config.test.js.map