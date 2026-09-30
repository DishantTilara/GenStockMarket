# Risk Engine Specification

The Risk Engine serves as a mandatory gatekeeper between trading recommendations (human or AI-generated) and the broker execution API.

```text
Trade Setup Generated
        ↓
Risk Engine Pre-Flight Checks
        ├── 1. Market Status Check (Exchange Open?)
        ├── 2. Data Freshness Check (Quote age <= 5 seconds?)
        ├── 3. User Authorization & Role Check
        ├── 4. Available Fund Check (Order value + margin <= available_balance)
        ├── 5. Maximum Single-Order Limit (<= MAX_ORDER_VALUE_INR)
        ├── 6. Portfolio Concentration Limit (<= 25% portfolio in single stock)
        ├── 7. Daily Max Loss Limit (<= 5% daily drawdown cutoff)
        ├── 8. Reasonable Stop-Loss Check (Stop loss specified and < entry for BUY)
        └── 9. Idempotency & Duplicate Order Prevention
        ↓
    All Passed?
     ├── NO  ──> REJECT with descriptive error code & message
     └── YES ──> Produce Approved Setup -> Require User Explicit Confirmation Modal
```

## Critical Invariants
1. **Never Bypass Risk Checks**: Even administrative users must adhere to risk controls.
2. **Explicit User Signature**: Automated trades must not be silently submitted without user confirmation token.
3. **Deterministic Verification**: Risk limits are computed using PostgreSQL transactions and `NUMERIC(20,2)` types.
