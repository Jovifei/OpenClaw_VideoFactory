# Third-party notices

## OpenMontage production core

Selected and adapted source is derived from [calesthio/OpenMontage](https://github.com/calesthio/OpenMontage) at commit `cd9f3c1f03368be87b140af494914b8ee4e3c7a4`.

OpenMontage is licensed under GNU Affero General Public License v3.0 only (`AGPL-3.0-only`). The repository's distributable code is provided under the same license. Original source paths, upstream hashes, adaptation notes, and vendored hashes are recorded in `third_party/openmontage/PROVENANCE.json`.

The Backlot import is intentionally limited to read-only state and health endpoints. Upstream UI assets, watchers, thumbnail caches, and state-writing checkpoint authority are deferred and not included.
