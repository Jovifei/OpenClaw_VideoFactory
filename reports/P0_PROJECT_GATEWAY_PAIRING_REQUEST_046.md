# Project Gateway Pairing Request 046

Status: `PAIRING_NOT_QUALIFIED_FOR_APPROVAL`.

One authorized pairing-request child was launched before the external state directory ACL was corrected. Its parent result projection then failed, and the state directory did not contain a Project identity, device token, pending-pairing record, or safely reportable pairing request identifier. Therefore there is no trustworthy evidence that an approval request was created, and this run must not be treated as a valid pairing request.

The ACL root-cause is repaired: the external directory is outside the repository, inheritance is protected, and its sole access rule belongs to the current Windows SID. A health-only bridge check now returns `device_identity_missing` before connecting, which confirms the repaired empty baseline.

No replay was performed. Replaying would be a second pairing-request connection and requires fresh, explicit authorization.

