import { z } from "zod";

export const configSchema = z.object({
  defaultModelId: z.string().optional(),
  serverPort: z.number().int().min(1024).max(65535).default(60315),
  ctxSize: z.number().int().min(1024).max(131072).default(8192),
  gpuLayers: z.number().int().min(0).max(200).default(0),
  idleTimeoutMinutes: z.number().int().min(0).max(1440).default(15),
  llamaServerPath: z.string().optional()
});

export type AppConfig = z.infer<typeof configSchema>;

export function defaultConfig(): AppConfig {
  return configSchema.parse({});
}
