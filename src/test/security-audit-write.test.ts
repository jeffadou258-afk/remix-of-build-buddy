import { describe, it, expect, vi } from "vitest";
import { audit, requirePermission, LOGGABLE_ACTIONS, PermissionError } from "@/lib/security/guard.server";

function fakeSb(perm: boolean, suspended = false) {
  const rpc = vi.fn(async (fn: string) => (fn === "has_permission" ? { data: perm, error: null } : { data: "id", error: null }));
  const from = () => ({ select: () => ({ eq: () => ({ maybeSingle: async () => ({ data: suspended ? { status: "suspended" } : null }) }) }) });
  return { rpc, from } as never as { rpc: typeof rpc };
}

describe("écriture d'audit contrôlée", () => {
  it("n'appelle jamais log_admin_action directement", async () => {
    const sb = fakeSb(true);
    await audit(sb as never, "gates.decide", { targetType: "project", targetId: "x" });
    expect(sb.rpc.mock.calls.map((c) => c[0])).toEqual(["log_security_event"]);
  });

  it("ne transmet ni résultat, ni permission, ni motif, ni avant/après", async () => {
    const sb = fakeSb(true);
    await audit(sb as never, "audit.list");
    const args = (sb.rpc.mock.calls[0] as unknown[])[1] as Record<string, unknown>;
    for (const k of ["_result", "_permission", "_reason", "_before", "_after"]) expect(args).not.toHaveProperty(k);
  });

  it("limite les actions journalisables à la liste fermée", () => {
    expect([...LOGGABLE_ACTIONS]).toEqual(["audit.list", "gates.decide", "admin.access_denied"]);
  });

  it("refuse et journalise sans fixer le résultat côté application", async () => {
    const sb = fakeSb(false);
    await expect(requirePermission(sb as never, "u1", "audit.read", "audit.list")).rejects.toBeInstanceOf(PermissionError);
    expect(sb.rpc.mock.calls.map((c) => c[0])).toEqual(["has_permission", "log_security_event"]);
  });

  it("compte suspendu : refusé", async () => {
    const sb = fakeSb(true, true);
    await expect(requirePermission(sb as never, "u1", "audit.read", "audit.list")).rejects.toMatchObject({ status: 403 });
  });

  it("refus /admin : seule la section est transmise, la base fixe résultat et motif", async () => {
    const sb = fakeSb(false);
    await audit(sb as never, "admin.access_denied", { targetType: "admin_section", targetId: "audit" });
    const [fn, args] = sb.rpc.mock.calls[0] as unknown as [string, Record<string, unknown>];
    expect(fn).toBe("log_security_event");
    expect(args).toMatchObject({ _action: "admin.access_denied", _target_type: "admin_section", _target_id: "audit" });
    for (const k of ["_result", "_permission", "_reason", "_before", "_after"]) expect(args).not.toHaveProperty(k);
  });
});
