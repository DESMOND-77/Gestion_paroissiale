# Logging Configuration & Usage Guide

## Overview

Comprehensive logging has been implemented across all Django modules for debugging and monitoring. Logs are written to both console and rotating file handlers.

## Log Files

All logs are stored in the `logs/` directory at the project root:

- **`gestionparoisse.log`** — Main application log for all modules except specialized ones
- **`auth.log`** — Authentication, JWT tokens, user sessions, security-related events
- **`finance.log`** — Financial transactions, reports, money movements

### Log File Management

Each log file is configured with:
- **Max Size:** 5MB (rotating automatically when exceeded)
- **Backup Count:** 5 (keeps up to 5 rotated files)
- **Format:** `[YYYY-MM-DD HH:MM:SS] LEVEL - logger_name - function:line - message`

## Logging Configuration

Configuration is in `gestion_p/settings.py` under the `LOGGING` dictionary.

### Handlers

| Handler | Type | Output | Level |
|---------|------|--------|-------|
| `console` | StreamHandler | Terminal/stdout | DEBUG |
| `file` | RotatingFileHandler | `gestionparoisse.log` | DEBUG |
| `auth_file` | RotatingFileHandler | `auth.log` | DEBUG |
| `finance_file` | RotatingFileHandler | `finance.log` | DEBUG |

### Loggers

| Logger | Handlers | Purpose |
|--------|----------|---------|
| `accounts` | console, file, auth_file | User authentication & profiles |
| `accounts.auth` | console, auth_file | Auth service & views |
| `accounts.core` | console, auth_file | JWT tokens & core utilities |
| `finances` | console, file, finance_file | Financial transactions & reports |
| `groupes` | console, file | Group management |
| `membres` | console, file | Member management |
| `evenements` | console, file | Event management |
| `librairie` | console, file | Library & article management |

## Usage in Code

### Getting a Logger

```python
import logging

logger = logging.getLogger(__name__)
```

### Log Levels (in order of severity)

```python
logger.debug("Detailed diagnostic info")          # Development/debugging
logger.info("General informational message")       # Normal operations
logger.warning("Warning: something unexpected")    # Potential issue
logger.error("Error: something failed")            # Serious issue
logger.critical("Critical: system may fail")       # System-level failure
```

### Examples by Module

#### Authentication (accounts/auth/services.py)
```python
logger.info(f"User registered successfully: {user.email}")
logger.warning(f"Login attempt for locked account: {email}")
logger.error(f"Error during login for {email}: {str(e)}")
```

#### Financial Operations (finances/views.py)
```python
logger.info(f"Creating transaction for user {request.user}: {request.data}")
logger.info(f"Financial report: recettes={total_recettes}, depenses={total_depenses}")
logger.warning(f"Deleting transaction {instance.id} by user {request.user}")
```

#### Data Management (groupes/views.py, membres/views.py, etc.)
```python
logger.debug(f"Retrieving {resource} for user {request.user}")
logger.info(f"Created {resource} successfully: {instance.id}")
logger.warning(f"Deleting {resource} {instance.id} by user {request.user}")
```

## What Gets Logged

### Security & Authentication
- Registration attempts (successful and failed)
- Login attempts, failed attempts, and account lockouts
- Token generation, validation, and blacklisting
- Password changes and resets
- Permission checks and access denials

### Business Operations
- CRUD operations on all major resources (Users, Members, Groups, Events, Transactions, Articles)
- Financial transactions and reports generation
- Event participant registrations
- Sacrament recordings
- Library article sales and inventory alerts

### Error Handling
- Validation errors with details
- Database operation failures
- Permission denied events
- Unexpected exceptions with full traceback (in auth module)

### Performance Monitoring
- Resource counts (e.g., "Retrieved 5 members")
- Operation timings can be added for slow queries
- File operations and uploads

## Accessing Logs in Development

### View logs in real-time (console)
When running the development server:
```bash
python manage.py runserver
```
All logs will appear in the console with color coding.

### View log files
```bash
# Main log
tail -f logs/gestionparoisse.log

# Auth-specific
tail -f logs/auth.log

# Finance-specific
tail -f logs/finance.log

# Search for errors
grep ERROR logs/*.log

# Follow all logs
tail -f logs/*.log
```

### Test logging setup
```bash
python test_logging.py
```

## Best Practices

1. **Use appropriate log levels:**
   - `DEBUG`: Variable values, function entry/exit
   - `INFO`: Successfully completed operations
   - `WARNING`: Recoverable issues, unusual but handled
   - `ERROR`: Failures that affect functionality
   - `CRITICAL`: System-level failures

2. **Include context:**
   ```python
   # Good
   logger.info(f"User {user.email} registered successfully with role {user.role}")
   
   # Poor
   logger.info("User registered")
   ```

3. **Log at operation boundaries:**
   - Beginning and end of important operations
   - When calling external services
   - On error conditions

4. **Include IDs and keys for traceability:**
   ```python
   logger.info(f"Transaction {transaction.id} created by user {user.id}")
   ```

5. **Don't log sensitive information:**
   ```python
   # Bad - passwords, tokens visible in logs
   logger.info(f"Password: {password}, Token: {token}")
   
   # Good - only log what's needed for debugging
   logger.info(f"Authentication attempt for user {email}")
   ```

## Debugging Tips

### Find all errors in a session
```bash
grep ERROR logs/*.log | head -20
```

### Track a specific user's activity
```bash
grep "user@email.com" logs/*.log
```

### Find slow operations
```bash
grep -E "Retrieving|Retrieved" logs/gestionparoisse.log | tail -20
```

### Monitor in real-time during testing
In one terminal:
```bash
tail -f logs/gestionparoisse.log | grep -i "error\|warning"
```

In another:
```bash
python manage.py runserver
```

## Rotating Logs

Log files rotate automatically when they exceed 5MB. Old logs are kept as:
- `gestionparoisse.log.1`
- `gestionparoisse.log.2`
- etc. (up to 5 files)

To manually clear logs:
```bash
# Clear all logs (careful!)
rm logs/*.log*

# Or just the main log
rm logs/gestionparoisse.log
```

## Integration with Monitoring Tools

The log format is structured enough to integrate with:
- **ELK Stack** (Elasticsearch, Logstash, Kibana)
- **Splunk** — for enterprise log analysis
- **CloudWatch** — for AWS deployments
- **Sentry** — for error tracking (can be added via integration)

## Adding More Loggers

To add logging to a new app:

1. In the module, import and get logger:
```python
import logging
logger = logging.getLogger(__name__)
```

2. Add logger to `settings.py` LOGGING config:
```python
"new_app": {
    "handlers": ["console", "file"],
    "level": "DEBUG",
    "propagate": False,
},
```

3. Use logger throughout the app:
```python
logger.info("Operation completed successfully")
```

## Troubleshooting

### Logs not appearing?
- Verify `logs/` directory exists: `ls -la logs/`
- Check file permissions: `chmod 755 logs/`
- Ensure logger name matches config: `logging.getLogger(__name__)`

### Too much noise in logs?
- Adjust log level in settings from DEBUG to INFO
- Filter specific loggers to higher levels

### Logs not rotating?
- Check file size: `ls -lh logs/gestionparoisse.log`
- Verify maxBytes setting in RotatingFileHandler (should be > 0)

---

**Last Updated:** 2026-05-08
**Logging Version:** 1.0
