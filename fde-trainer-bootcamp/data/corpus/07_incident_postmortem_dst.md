# Post-Incident Review: Appointment Times Shifted One Hour (INC-4471)

## Summary
On the first Sunday of November, 1,840 delivery appointments across 62
facilities displayed one hour earlier than scheduled in the carrier portal.
214 carriers arrived an hour early; 38 loads were refused at the dock and
rescheduled, producing $71K in detention and layover exposure.

## Root cause
The appointment service stored `appt_start_local` as a naive timestamp and
the portal rendered it by applying a **fixed** UTC offset per facility, cached
at facility creation time. When DST ended, the cached offset was stale for
facilities in observing timezones. Facilities in Arizona and most of
Saskatchewan were unaffected, which is why the bug survived two prior DST
boundaries in a partial rollout.

## Contributing factors
- No integration test crossed a DST boundary.
- The offset cache had no TTL and no invalidation event.
- Monitoring alerted on appointment *volume*, not appointment *time deltas*,
  so the shift was invisible until carriers called.

## Corrective actions
1. Store IANA timezone identifier per facility; render via tz database. Done.
2. Add DST-boundary cases to the integration suite. Done.
3. Alert when >5% of appointments in a facility shift by exactly 60 minutes
   between consecutive snapshots. Done.
4. Backfill audit of historical OTIF attribution across prior DST windows.
   In progress — expected to restate 3 quarters of carrier scores.
