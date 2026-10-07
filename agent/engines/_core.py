"""
Construction Agent v2.0.0 — NOYAU COMMUN.
Systeme Evidence + verification physique. Aucune affirmation sans preuve.
"""
import os, sys, json, hashlib, shutil, subprocess, datetime

AGENT_ID = "construction-agent"
AGENT_VERSION = "2.0.0"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

STATUS = ["DRAFT", "ANALYZING", "PROPOSED", "HYPOTHESIS", "USER_VALIDATION_REQUIRED",
          "VALIDATED", "IN_PROGRESS", "EXECUTED", "VERIFIED", "READY", "BLOCKED",
          "FAILED", "CANCELLED"]
DATA_STATUS = ["VERIFIED", "USER_PROVIDED", "DERIVED", "HYPOTHESIS", "UNKNOWN"]

__all__ = ["Evidence", "AGENT_ID", "AGENT_VERSION", "ROOT", "STATUS", "DATA_STATUS",
           "now", "sha256", "image_info", "file_info", "blender_path", "blender_version",
           "run_blender", "load_json", "save_json", "which", "log"]


def now():
    return datetime.datetime.now().isoformat(timespec="seconds")


def which(cmd):
    return shutil.which(cmd)


def sha256(path, chunk=1 << 20):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(chunk), b""):
            h.update(b)
    return h.hexdigest()


def image_info(path):
    """Resolution REELLE via sips (macOS). Retourne None si indisponible."""
    try:
        r = subprocess.run(["sips", "-g", "pixelWidth", "-g", "pixelHeight", path],
                           capture_output=True, text=True, timeout=30)
        w = h = None
        for line in r.stdout.splitlines():
            if "pixelWidth" in line:
                w = int(line.split(":")[1].strip())
            if "pixelHeight" in line:
                h = int(line.split(":")[1].strip())
        if w and h:
            return {"width": w, "height": h, "resolution": "%dx%d" % (w, h)}
    except Exception:
        pass
    return None


def file_info(path):
    """Preuve physique d'un fichier. None si absent."""
    if not path or not os.path.exists(path):
        return None
    st = os.stat(path)
    d = {"path": os.path.abspath(path), "exists": True,
         "size_bytes": st.st_size, "is_file": os.path.isfile(path)}
    if d["is_file"]:
        d["sha256"] = sha256(path)
        d["format"] = os.path.splitext(path)[1].lstrip(".").upper() or None
        if d["format"] == "PNG":
            ii = image_info(path)
            if ii:
                d.update(ii)
                d["format"] = "PNG"
    return d


def blender_path():
    cands = ["/Applications/Blender.app/Contents/MacOS/Blender", shutil.which("blender")]
    for p in cands:
        if p and os.path.isfile(p) and os.access(p, os.X_OK):
            return p
    return None


def blender_version(exe):
    try:
        r = subprocess.run([exe, "--version"], capture_output=True, text=True, timeout=90)
        line = (r.stdout or "").strip().splitlines()
        return line[0].strip() if line else None
    except Exception:
        return None


def run_blender(exe, script, args=(), timeout=2400):
    cmd = [exe, "--background", "--factory-startup", "--python", script]
    if args:
        cmd += ["--"] + [str(a) for a in args]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    return r.returncode, r.stdout, r.stderr


def load_json(path, default=None):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return path


def log(project_dir, engine, msg):
    p = os.path.join(project_dir, "logs", "agent.log")
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "a", encoding="utf-8") as f:
        f.write("%s [%s] %s\n" % (now(), engine, msg))


class Evidence(object):
    """Section 21 de la specification — un evidence.json par moteur."""

    def __init__(self, operation, project_dir=None):
        self.operation = operation
        self.project_dir = project_dir
        self.d = {"operation": operation, "agent": AGENT_ID, "version": AGENT_VERSION,
                  "started_at": now(), "completed_at": None, "status": "IN_PROGRESS",
                  "tools_used": [], "commands_executed": [], "files_created": [],
                  "files_verified": [], "tests": [], "errors": [], "warnings": []}

    def tool(self, name):
        if name not in self.d["tools_used"]:
            self.d["tools_used"].append(name)

    def cmd(self, c):
        self.d["commands_executed"].append(c)

    def record(self, path):
        """Verification PHYSIQUE d'un fichier. Retourne la preuve ou None."""
        info = file_info(path)
        if info is None:
            self.d["errors"].append("FICHIER ABSENT: %s" % path)
            return None
        self.d["files_verified"].append(info)
        return info

    def created(self, path):
        info = file_info(path)
        if info is None:
            self.d["errors"].append("CREATION NON CONFIRMEE: %s" % path)
            return None
        self.d["files_created"].append(info["path"])
        self.d["files_verified"].append(info)
        return info

    def test(self, name, passed, detail=""):
        self.d["tests"].append({"name": name, "passed": bool(passed),
                                "status": "PASSED" if passed else "FAILED",
                                "detail": str(detail)})
        return bool(passed)

    def warn(self, m):
        self.d["warnings"].append(m)

    def fail(self, cause):
        self.d["status"] = "FAILED"
        self.d["errors"].append(cause)
        return "FAILED"

    def block(self, cause):
        self.d["status"] = "BLOCKED"
        self.d["errors"].append(cause)
        return "BLOCKED"

    def close(self, status):
        if self.d["status"] not in ("FAILED", "BLOCKED"):
            self.d["status"] = status
        self.d["completed_at"] = now()
        self.summary = self.d
        return self.d

    def out(self, filename="evidence.json"):
        base = self.project_dir or ROOT
        path = os.path.join(base, "evidence", self.operation, filename)
        save_json(path, self.d)
        return path


def cli(operation, engine_run):
    """Point d'entree standard d'un moteur."""
    if len(sys.argv) < 2:
        print("usage: engine.py <project_dir>")
        sys.exit(2)
    project_dir = os.path.abspath(sys.argv[1])
    res = engine_run(project_dir)
    print(json.dumps(res, indent=2, ensure_ascii=False))
    return res
