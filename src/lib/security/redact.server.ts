/**
 * Filtre de sortie : aucune réponse de l'application ne doit contenir de secret.
 * Masque par nom de champ, par forme de valeur et par valeur exacte des secrets serveur.
 */
export const MASK = "[MASQUÉ]";

const SECRET_KEY = /(api[_-]?key|apikey|secret|password|passwd|authorization|private[_-]?key|service[_-]?role|access[_-]?token|refresh[_-]?token|^token$|bearer)/i;
const PATTERNS: RegExp[] = [
  /sb_secret_[A-Za-z0-9_\-]+/g,
  /sb_publishable_[A-Za-z0-9_\-]+/g,
  /Bearer\s+[A-Za-z0-9._\-]+/gi,
  /eyJ[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+/g,
  /sk-[A-Za-z0-9_\-]{16,}/g,
  /rpa_[A-Za-z0-9]{16,}/g,
];

export function redactText(text: string, secretValues: readonly (string | undefined)[] = []): string {
  let out = text;
  for (const v of secretValues) if (v && v.length >= 8) out = out.split(v).join(MASK);
  for (const p of PATTERNS) out = out.replace(p, MASK);
  return out;
}

export function redactSecrets<T>(value: T, secretValues: readonly (string | undefined)[] = []): T {
  const walk = (v: unknown): unknown => {
    if (typeof v === "string") return redactText(v, secretValues);
    if (Array.isArray(v)) return v.map(walk);
    if (v && typeof v === "object") {
      const o: Record<string, unknown> = {};
      for (const [k, val] of Object.entries(v)) o[k] = SECRET_KEY.test(k) ? MASK : walk(val);
      return o;
    }
    return v;
  };
  return walk(value) as T;
}

/** Valeurs des secrets serveur à ne jamais renvoyer. À appeler dans un handler. */
export function serverSecretValues(): string[] {
  return ["CA_API_KEY", "LOVABLE_API_KEY", "SUPABASE_SERVICE_ROLE_KEY", "SUPABASE_SECRET_KEYS", "LOVABLE_CRON_SECRET", "SUPABASE_DB_URL"]
    .map((k) => process.env[k])
    .filter((v): v is string => !!v);
}

/** Corps de réponse texte (JSON ou non) nettoyé. */
export function redactBody(text: string): string {
  const secrets = serverSecretValues();
  try {
    return JSON.stringify(redactSecrets(JSON.parse(text), secrets));
  } catch {
    return redactText(text, secrets);
  }
}
