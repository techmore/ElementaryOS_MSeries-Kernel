# Air CPU-frequency thermal-owner integration draft

This is a source-integration draft for Aurora PR 366 commit `cee01fae63c0`, adapted to the newer WIP5 CPU-frequency structures. It applies after the preceding Air patches in the private Air-forward scratch tree; it is not a standalone patch against the WIP5 baseline, and has not been built, installed, booted, or qualified on J773g. The following Air J713-only thermal driver is not included here.

The T8132 path limits each policy to P-state 4 until a thermal owner releases the limit. The Air thermal driver is gated to `apple,j713`; it must not be used as a J773g thermal qualification. P-state 4 is an upstream bootstrap restriction, not a verified safety ceiling. CPU hotplug lifecycle, interactions with WIP5 fast-die handling, actual J773g operating points and thermal protection still need review and device qualification.

The original owner patch falls back to the lowest frequency when no eligible P-state exists. With an empty table, its `UINT_MAX` fallback is passed as signed -1, which is `PM_QOS_DEFAULT_VALUE` and can remove the maximum constraint. If all states exceed 4, the lowest frequency also violates the intended ceiling. This adaptation instead returns `-EINVAL` for either case and for frequencies outside the signed QoS range, causing QoS request addition or update to fail.

WIP5's cpufreq core takes the policy write lock around driver initialization and teardown; the owner API takes the policy read lock before its owner mutex. This explains serialization of the owner update with request removal, but is not a complete hotplug or lifetime validation. The Air-forward scratch handoff contains the patch replay state and remaining conflicts.
