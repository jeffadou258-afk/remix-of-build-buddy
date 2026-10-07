// @lovable.dev/vite-tanstack-config already includes the following — do NOT add them manually
// or the app will break with duplicate plugins:
//   - TanStack devtools (dev-only, first), tanstackStart, viteReact, tailwindcss, tsConfigPaths,
//     nitro (build-only using cloudflare as a default target), VITE_* env injection, @ path alias,
//     React/TanStack dedupe, error logger plugins, and sandbox detection (port/host/strictPort).
// You can pass additional config via defineConfig({ vite: { ... }, etc... }) if needed.
import { defineConfig } from "@lovable.dev/vite-tanstack-config";

export default defineConfig({
  tanstackStart: {
    // Redirect TanStack Start's bundled server entry to src/server.ts (our SSR error wrapper).
    // nitro/vite builds from this
    server: { entry: "server" },
  },

  // Cible de déploiement Vercel. Avant : implicite (Cloudflare par défaut).
  // Dans un build Lovable, LOVABLE_NITRO_PRESET épingle le preset et cet override
  // ne s'applique qu'en dehors — le build Lovable n'est donc pas affecté.
  // Sortie produite : .vercel/output/ (Build Output API v3).
  nitro: { preset: "vercel" },
});
