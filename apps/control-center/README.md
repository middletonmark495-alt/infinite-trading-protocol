# Infinite Trading Intelligence Control Center

The Control Center is the owner-facing read-only operations console for the MVP.

## Local Android/Termux use

Start the API from the repository root:

```bash
./start-termux.sh
```

Then open:

```text
http://127.0.0.1:8000/docs
```

The static dashboard can be served by any static web server and configured to use the API origin. It is intentionally unable to sign transactions or move funds.

## Security boundary

- No seed phrases or private keys are accepted by the UI.
- Live financial execution remains locked.
- The emergency lock is fail-closed.
- Public wallet addresses can be added later through authenticated API routes.
