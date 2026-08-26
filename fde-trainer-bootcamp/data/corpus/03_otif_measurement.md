# On-Time In-Full (OTIF) Measurement Standard

## The metric
OTIF = shipments delivered on time AND complete / total shipments, measured
at the purchase-order line level, not at the shipment level. A single short
line fails the entire PO.

## On-time definition
Delivery is on time if the truck is checked in at the receiving facility
within the appointment window. Standard windows:
- Grocery/retail DC: **-30 / +0 minutes** relative to appointment
- Manufacturing plant inbound: **-2 hours / +0 minutes**
- E-commerce fulfilment centre: **-1 hour / +15 minutes**

Early arrival outside the window is a failure. This surprises new analysts
constantly: arriving four hours early at a grocery DC is an OTIF miss, not
a service win, because the receiving dock has no labour scheduled.

## In-full definition
Quantity delivered must be within **-0% / +0%** of the PO line quantity for
ambient goods. Catch-weight categories (meat, produce) tolerate **+/- 2%**.

## Attribution
Failures are attributed in order: carrier fault, shipper fault (late load
ready), receiver fault (dock congestion), or force majeure. Attribution
drives chargebacks, so it is the most disputed field in the entire dataset.

## Known data quality traps
- Appointment times are stored in facility local time, delivery scans in UTC.
- Rescheduled appointments overwrite the original in the TMS, which hides
  shipper-caused delays unless you read the appointment audit log.
