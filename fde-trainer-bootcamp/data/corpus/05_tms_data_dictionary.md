# TMS Data Dictionary (extract)

## SHIPMENT
| Field | Type | Notes |
|---|---|---|
| shipment_id | string | Primary key. Format `SHP-<yyyymm>-<7 digits>` |
| tender_ts_utc | timestamp | When the 204 was transmitted |
| accept_ts_utc | timestamp | Null if declined or expired |
| tender_seq | int | 1 = primary, 2 = first backup, etc. |
| origin_facility_id | string | FK to FACILITY |
| dest_facility_id | string | FK to FACILITY |
| equipment | enum | DRY_VAN, REEFER, FLATBED, INTERMODAL |
| linehaul_usd | decimal | Excludes fuel and accessorials |
| fuel_surcharge_usd | decimal | Derived from DOE weekly index |
| status | enum | TENDERED, ACCEPTED, DISPATCHED, IN_TRANSIT, DELIVERED, CANCELLED |

## STOP
| Field | Type | Notes |
|---|---|---|
| stop_id | string | |
| shipment_id | string | FK |
| seq | int | 1-based |
| appt_start_local | timestamp | **Facility local time, no tz stored** |
| arrive_ts_utc | timestamp | Geofence entry |
| depart_ts_utc | timestamp | Geofence exit |
| detention_minutes | int | Computed nightly, not real time |

## Gotchas that have caused production incidents
- `appt_start_local` has no timezone column. You must join FACILITY.tz.
  Two DST-boundary incidents in the last three years trace to this.
- `detention_minutes` is a batch field. Any real-time detention alerting
  must recompute from arrive/depart, not read this column.
- `tender_seq` resets when a load is re-tendered after cancellation, so
  routing-guide depth computed naively double-counts.
