# Changelog

## 0.5.0

- **Managed Kubernetes**: new `cloud k8s` command group with all 17 commands:
  `plans`, `list`, `create`, `info`, `kubeconfig`, `scale`, `add-pool`,
  `delete-pool`, `api-access`, `ip-allocate`, `ip-release`, `ptr`, `backups`,
  `backup`, `restore`, `upgrade`, `delete`.
  - `add-pool` accepts repeatable `--label key=value`, `--taint key=value:Effect`
    and `--ssh-key-id`.
  - `kubeconfig -o <file>` always writes the file with mode `0600`.
- **Impact**: new `cloud impact` command group (forests, trees, commitments).
- **Other services**: synced the rest of the CLI with the in-repo source of
  truth (`wayscloudas/wayscloud-provision-api`, `wayscloud-cli/`), adding the
  commands that were missing from the published package (for example
  `cloud db tiers`, `cloud dns zones-info`, `cloud redis regions`,
  `cloud storage keys`, and the extended `iot`/`app` groups).
- **Dependency**: requires `wayscloud>=0.4.0`, the first published SDK release
  with Kubernetes support. The 0.3.0/0.4.0 releases of this package were not
  built from this repository and never contained the Kubernetes commands; 0.5.0
  is the first release published from `wayscloudas/wayscloud-cli` that does.
- Packaging metadata, version and tests now match the released code.
