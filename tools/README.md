# Operational tools

These tools use only the Python standard library and require Python 3.11 or
newer. They are intended to run on the primary workstation or a Linux batch
node without network access.

## Grid topology pack

Validate the checked-in inputs without changing outputs:

```bash
python tools/build_grid_topology_v2.py --check-only
```

Build both the data copy and browser copy atomically:

```bash
python tools/build_grid_topology_v2.py
```

The builder preserves unresolved endpoint identities as blocked; it does not
invent electrical connections.

## Unreal diagnostic

The diagnostic searches `UNREAL_EDITOR`, `PATH`, and known local paths. A batch
job can consume JSON and fail closed with `--strict`:

```bash
UNREAL_EDITOR=/path/to/UnrealEditor \
  python tools/test_unreal_editor_companion.py --json --strict
```

The diagnostic does not install Unreal Engine or plugins. Installation belongs
to the machine image or administrator-managed software environment; no network
installer is required by these scripts.