# Trusted Media Roots

The production ingest MCP now trusts exactly two explicit roots: the OpenClaw global inbound directory (`openclaw_global`) and the VideoFactory workspace inbound directory (`video_factory_workspace`). It no longer auto-trusts CWD, the project root, or arbitrary absolute paths.

The implementation and tests enforce canonical path comparison, separator boundaries, Windows case insensitivity, drive/UNC/device/ADS rejection, reparse checks for every ancestor and the file, and source stat/hash verification before and after copy. The matrix passed 25/25; the existing PowerShell ingest suite remained 32/32.
