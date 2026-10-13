---
name: bell-common-failures
description: The failures that account for most rejected Bell uploads and confused results — duplicate (date, location) pairs, weekly data declared daily, too little history, too few or dominated markets, an empty dataset list — with the engine's real error text and the fix for each. Use when an upload, allocation, design or results call fails, or when a result looks wrong.
license: Apache-2.0
metadata:
  source: Korem-consulting/bell-skills
---

Read `references/common-failures.md`. It is the same document the
connector serves as `bell://methodology/common-failures`.

Match the error text you received against it before doing anything else.
Most failures are fixed in the data, with a script, not by retrying the
call. For anything that needs a transform, go to `bell-data-prep`; its
validator reproduces these checks locally so the fix is confirmed before
the re-upload.

If the failure is not listed and you cannot resolve it in two attempts,
escalate as described in `bell-geo-experiments` rather than looping.
