# Lab 03 — Email Delivery & Verification

## Question

What does an application actually know when it says an email was sent?

This lab separates application generation, provider acceptance, deferral, bounce, and delivery into explicit evidence states. The first slice is intentionally provider-free and uses only fabricated events.

## Baseline

A common application-level shortcut is to treat successful message generation or provider acceptance as proof of delivery. Those events establish useful facts, but neither proves that the destination accepted the message.

The state model starts with five deliberately small states:

`generated -> accepted -> deferred | bounced | delivered`

A deferred message may remain deferred or later become bounced or delivered. Bounce and delivery are terminal in this initial model.

## Evidence in this slice

The automated tests establish that:

- generation alone is not delivery evidence;
- provider acceptance alone is not delivery evidence;
- a deferred synthetic message can later reach delivered state;
- a bounced message cannot later be recorded as delivered; and
- delivery cannot be recorded before provider acceptance.

Run the focused tests from the repository root:

```bash
PYTHONPATH=labs/03-email-delivery-verification python -m unittest discover -s labs/03-email-delivery-verification/tests -v
```

## Limitations

This is a state-machine baseline, not a deliverability simulator and not an integration with an email provider. It does not yet model authentication records, suppression lists, complaint events, retry timing, provider webhooks, mailbox placement, spam filtering, or cryptographic verification of event provenance.

All identifiers, event details, and mailbox behavior in this lab are synthetic. No real addresses, messages, provider payloads, or delivery logs are used.

## Next experiment

A useful next slice is to feed an ordered synthetic provider-event stream into the state model and make duplicate, stale, and contradictory events explicit rather than assuming webhook delivery is perfectly ordered.
