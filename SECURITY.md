# Security Policy

Motion Studio is a **local desktop tool**: it runs a no-authentication HTTP
server that drives a state-mutating editor and can read motion files you point
it at. The defaults are chosen so that, used as intended (on your own machine),
it is safe. Read this before exposing it to a network.

## Threat model & defaults

- **Localhost by default.** The server binds the loopback interface
  (`127.0.0.1`) only. It is not reachable from other machines unless you
  explicitly opt in.
- **Host/Origin guard.** Every request is checked: a non-loopback `Host` header
  or a cross-origin `Origin` is rejected with `403`. This defeats DNS-rebinding
  attacks where a malicious web page tries to drive your local server. CORS is
  same-origin only (no wildcard).
- **Upload limits.** A `MAX_CONTENT_LENGTH` cap rejects oversized bodies before
  they are read, and pose payloads are clamped on shape (`N`, `T`, `J`,
  `iters`) and checked for NaN/Inf before any heavy work runs.
- **Restricted unpickler.** Importing a legacy raw `.pkl` uses a restricted
  unpickler that whitelists only numpy array reconstruction and safe scalar
  types, and rejects everything else. The native `.motion` and `.npz` formats
  do not unpickle arbitrary objects at all.

## The `--allow-remote` risk

Binding a non-loopback address (`--host 0.0.0.0`, a LAN IP, …) requires the
explicit `--allow-remote` flag, and prints a warning. **Understand what you are
doing:**

- The API has **no authentication**. Anyone who can reach the port can drive the
  editor, read/write bundles in the workspace, and import files.
- File import can run code paths that process untrusted input. Treat the server
  as you would any unauthenticated service.
- Only enable `--allow-remote` on a trusted, firewalled network — never on the
  public internet. Prefer an SSH tunnel (`ssh -L 8815:127.0.0.1:8815 host`) to
  reach a remote instance instead of binding a public address.

## Reporting a vulnerability

Please report security issues **privately**, not in a public issue:

- Use GitHub's *Report a vulnerability* (Security → Advisories) on the
  repository, **or**
- email the maintainer (see the contact in `pyproject.toml`).

Include a description, the affected version, and a minimal reproduction if you
can. We will acknowledge the report and work with you on a fix and a coordinated
disclosure.
