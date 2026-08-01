# Remaining Actions V30

1. Obtain a new explicit authorization for `P0-PROJECT-GATEWAY-DEVICE-PAIRING-REQUEST-047` retry.
2. That authorization must permit at most one Gateway connection and one fresh pairing request for the existing Project identity with scope `operator.read` only.
3. Stop after `PAIRING_REQUIRED` (or an explicitly classified protocol result). Do not approve a request, use a device token, start the Project Gateway, or begin zhongshu migration without later separate authorization.
