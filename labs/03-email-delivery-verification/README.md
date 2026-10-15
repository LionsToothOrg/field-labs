# Lab 03 — Email Delivery & Verification

## Question

What does an application actually know when it says an email was sent?

This lab separates application generation, provider acceptance, deferral, bounce, and delivery into explicit evidence states. It is intentionally provider-free and uses only fabricated events.

## Baseline

A common application-level shortcut is to treat successful message generation or provider acceptance as proof of delivery. Those events establish useful facts, but neither proves that the destination accepted the message.

The state model starts with five deliberately small states:

`generated -> accepted -> deferred | bounced | delivered`

A deferred message may remain deferred or later become bounced or delivered. Bounce and delivery are terminal in this model.

## Evidence established so far

The automated tests establish that:

- generation alone is not delivery evidence;
- provider acceptance alone is not delivery evidence;
- a deferred synthetic message can later reach delivered state;
- a bounced message cannot later be recorded as delivered;
- delivery cannot be recorded before provider acceptance;
- a duplicate synthetic provider event is applied only once;
- a stale event cannot overwrite newer delivery evidence; and
- a contradictory later event cannot reverse a terminal delivery state.

The reconciliation slice uses fabricated event IDs and monotonic sequence numbers to make ordering decisions explicit. Events are processed in arrival order: duplicate IDs are ignored, events at or below the latest applied sequence are treated as stale, and transitions that contradict the delivery state machine are ignored rather than rewriting stronger evidence.

Run the focused tests from the repository root:

```bash
PYTHONPATH=labs/03-email-delivery-verification python -m unittest discover -s labs/03-email-delivery-verification/tests -v
```

## Limitations

This is a state-machine and event-ordering experiment, not a deliverability simulator and not an integration with an email provider. The synthetic sequence is an explicit lab assumption; real providers may expose timestamps, attempt counters, webhook IDs, or other ordering semantics instead. The lab does not yet model authentication records, suppression lists, complaint events, retry timing, provider webhook signatures, mailbox placement, spam filtering, durable deduplication, or cryptographic verification of event provenance.

All identifiers, event details, and mailbox behavior in this lab are synthetic. No real addresses, messages, provider payloads, or delivery logs are used.

## Next experiment

A useful next slice is to make reconciliation decisions observable as typed outcomes so duplicate, stale, applied, and contradictory events can be audited without logging provider payload contents.
