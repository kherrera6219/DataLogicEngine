# Local-First Error Handling Standard

**Applies To:**
- DataLogicEngine (UKG)
- TheFactory
- CyberGenDoc

---

# 1. Design Principle

Errors must be handled locally, safely, and predictably.

The application shall:

- Never crash silently.
- Never expose secrets in error messages.
- Never lose user data without warning.
- Never require internet connectivity to diagnose core errors.
- Always provide clear user-facing recovery guidance.

---

# 2. Error Categories

All errors shall be classified into one of these categories:

```text
ValidationError
ConfigurationError
StorageError
EncryptionError
IntegrityError
SignatureError
PermissionError
FileSystemError
DatabaseError
ModelExecutionError
GenerationError
ImportExportError
PluginExecutionError
UnexpectedError
```

---

# 3. Error Severity Levels

Use consistent severity levels:

```text
Info
Warning
RecoverableError
CriticalError
FatalError
```

## Definitions

### Info
Normal operational event.

### Warning
Something unexpected occurred, but the application can continue.

### RecoverableError
The user can fix the issue and retry.

### CriticalError
A core operation failed and user data may be at risk.

### FatalError
The application cannot safely continue.

---

# 4. User-Facing Error Rules

User-facing errors must be:

- Clear
- Non-technical where possible
- Actionable
- Free of secrets
- Free of stack traces
- Free of raw file paths unless needed

## Required Format

```text
Something went wrong.
What happened: <plain English explanation>
What you can do: <recommended next step>
Error code: <stable error code>
```

## Example

```text
Something went wrong.
What happened: The workspace could not be opened because its integrity check failed.
What you can do: Restore from a backup or open a different workspace.
Error code: UKG-INTEGRITY-001
```

---

# 5. Developer-Facing Error Rules

Developer logs may include:

- Error category
- Error code
- Timestamp
- Component name
- Operation name
- Correlation ID
- Sanitized exception message
- Sanitized stack trace

Developer logs must not include:

- Encryption keys
- Tokens
- Secrets
- Private keys
- Full document contents
- Prompt contents containing sensitive data
- Raw user data
- Decrypted payloads

---

# 6. Standard Error Object

Use a consistent internal error object:

```json
{
  "error_id": "uuid",
  "error_code": "UKG-STORAGE-001",
  "severity": "RecoverableError",
  "category": "StorageError",
  "component": "WorkspaceService",
  "operation": "OpenWorkspace",
  "user_message": "The workspace could not be opened.",
  "developer_message": "Workspace file was locked or unavailable.",
  "recovery_action": "Close other applications using the file and try again.",
  "timestamp": "2026-05-28T00:00:00Z",
  "correlation_id": "uuid"
}
```

---

# 7. Error Code Naming Standard

Use stable, searchable error codes.

## Format

```text
<APP>-<CATEGORY>-<NUMBER>
```

## App Prefixes

```text
UKG     = DataLogicEngine / UKG
FACTORY = TheFactory
CGD     = CyberGenDoc
CORE    = Shared core libraries
```

## Examples

```text
UKG-STORAGE-001
UKG-ENCRYPTION-001
FACTORY-PLUGIN-001
CGD-EXPORT-001
CORE-PERMISSION-001
```

---

# 8. Encryption Error Handling

Encryption errors must be treated as security-sensitive.

## Requirements

- Never continue after failed decryption.
- Never write partially decrypted data.
- Never expose raw cryptographic exception details to users.
- Log sanitized failure details only.
- Prompt user to restore from backup if data cannot be decrypted.

## Example User Message

```text
Something went wrong.
What happened: This workspace could not be decrypted for the current Windows user.
What you can do: Make sure you are logged into the same Windows account that created this workspace.
Error code: CORE-ENCRYPTION-001
```

---

# 9. Integrity Error Handling

Integrity failures may indicate corruption or tampering.

## Requirements

- Stop loading the affected file/workspace.
- Do not auto-repair silently.
- Preserve the original file.
- Create a safe diagnostic record.
- Ask user before attempting recovery.

## Example User Message

```text
Something went wrong.
What happened: The selected file failed an integrity check.
What you can do: Restore a trusted backup or import a verified copy.
Error code: CORE-INTEGRITY-001
```

---

# 10. Signature Error Handling

Signature failures must block trusted import/export workflows.

## Requirements

- Reject unsigned artifacts when signatures are required.
- Reject modified artifacts when signature verification fails.
- Do not bypass signature checks silently.
- Record verification failure in audit log.

---

# 11. File and Storage Error Handling

## Requirements

- Check file existence before opening.
- Check file permissions before writing.
- Handle locked files gracefully.
- Use atomic writes where possible.
- Write to a temporary file first.
- Verify write success.
- Rename temporary file into place.
- Preserve previous valid file on failure.

## Atomic Write Pattern

```text
1. Write new content to temp file.
2. Flush content to disk.
3. Verify hash.
4. Replace original file.
5. Keep backup copy if replacement fails.
```

---

# 12. Database Error Handling

## Requirements

- Use transactions for multi-step writes.
- Roll back failed transactions.
- Never leave partial workspace updates.
- Validate database schema version before opening.
- Block opening unsupported schema versions.
- Back up before migrations.

---

# 13. Model / Generation Error Handling

Applies to local model calls, generation pipelines, document generation, and agent workflows.

## Requirements

- Detect failed generation.
- Detect empty output.
- Detect malformed JSON/YAML/Markdown.
- Validate generated files before saving.
- Never overwrite valid user files with invalid generated output.
- Save failed generation diagnostics separately.
- Allow retry.

---

# 14. Plugin / Script Execution Error Handling

Applies especially to TheFactory.

## Requirements

- Plugin errors must not crash the host application.
- Run plugins in a controlled execution boundary.
- Require explicit user approval before execution.
- Capture stdout/stderr safely.
- Time-limit long-running plugin tasks.
- Block plugins from accessing unauthorized paths.
- Record plugin failures in audit logs.

---

# 15. Import / Export Error Handling

## Import Requirements

- Validate file type.
- Validate schema.
- Validate hash.
- Validate signature if required.
- Scan for unsafe paths.
- Reject malformed imports.

## Export Requirements

- Write export to temporary location first.
- Hash export bundle.
- Sign export bundle if required.
- Verify export after write.
- Only then show success.

---

# 16. Recovery Standards

Every recoverable error must provide one recovery action.

Examples:

```text
Try again
Close the file and retry
Choose another workspace
Restore from backup
Rebuild the local index
Run integrity check
Open as read-only
```

---

# 17. Crash Handling

## Requirements

- Catch unhandled exceptions at the application boundary.
- Save sanitized crash report locally.
- Do not upload crash reports.
- Do not include secrets or document contents.
- Offer user a safe restart.
- Preserve unsaved work where possible.

---

# 18. Offline Diagnostics

Diagnostics must work without internet.

## Required Local Diagnostic Outputs

```text
diagnostics.json
application.log
security.log
audit.log
crash-report.json
integrity-report.json
```

Store diagnostics under:

```text
%LOCALAPPDATA%\<Company>\<AppName>\Diagnostics\
```

---

# 19. Logging Levels

Use consistent logging levels:

```text
Trace
Debug
Info
Warning
Error
Critical
```

## Production Default

```text
Info
Warning
Error
Critical
```

Trace and Debug should be disabled by default in production.

---

# 20. Required Codex Review Checklist

## General Error Handling

- [ ] All errors are classified.
- [ ] All errors have stable error codes.
- [ ] User-facing messages are clear and actionable.
- [ ] Stack traces are not shown to users.
- [ ] Secrets are not included in errors.
- [ ] Recovery actions are provided.

## Security Errors

- [ ] Decryption failure stops processing.
- [ ] Integrity failure blocks loading.
- [ ] Signature failure blocks trusted import.
- [ ] Security failures are logged safely.
- [ ] Raw crypto errors are not exposed.

## Storage Errors

- [ ] Atomic writes are used.
- [ ] Failed writes do not corrupt existing files.
- [ ] Database transactions are rolled back.
- [ ] Schema migration failures are handled safely.

## Generation Errors

- [ ] Generated output is validated before save.
- [ ] Invalid generated output does not overwrite valid files.
- [ ] Failed generation can be retried.

## Plugin Errors

- [ ] Plugin failure does not crash host app.
- [ ] Plugin execution is bounded.
- [ ] Plugin errors are logged safely.
- [ ] User approval is required before code execution.

## Crash Handling

- [ ] Unhandled exceptions are caught.
- [ ] Crash reports are stored locally.
- [ ] Crash reports are sanitized.
- [ ] Application can restart safely.

---

# Compliance Statement

All applications shall implement local-first error handling that protects user data, preserves workspace integrity, avoids secret exposure, and provides clear recovery paths without requiring external services.