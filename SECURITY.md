# Security and research integrity

Chronal reads local CSV/JSON and writes local experiment bundles. It contains no brokerage adapter, credential reader, external model call, network client, arbitrary strategy loader, pickle loader or executable proposal interface. Its sole runtime dependency is NumPy. Run data imports with ordinary least-privilege filesystem access.

The bounded proposal schema prevents executable content from becoming a strategy. Every imported number, timestamp, panel shape and candidate field is validated. Report strings are encoded as inert JSON and inserted as text. This does not make untrusted datasets small, resource bounded or financially accurate. Extremely large files can exhaust memory. Import only data you have rights to use, and inspect its provenance.

Manifests are local integrity records. Anyone able to rewrite all local files can also rewrite hashes. They are not digital signatures, third-party timestamps, an access-control system, a regulatory audit or proof that a human avoided the holdout. Full replay additionally checks financial outputs, model fits, selection, uncertainty and stress results against the locked source and data. It does not prove the source model is economically sound or data was genuinely available historically.

For a suspected defect, prepare a minimal synthetic reproducer and identify the source revision, execution assumptions and affected boundary. Report non-sensitive correctness issues at [GitHub Issues](https://github.com/nazeeh111/chronal/issues). If a finding needs private handling, request a private contact without posting technical exploit details or sensitive data. GitHub private vulnerability reporting is currently disabled. Never include credentials or private account information in a report.
