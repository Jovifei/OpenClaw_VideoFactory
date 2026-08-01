# P0 Fixture Preparation

Status: **passed**

Generated locally under `tests/fixtures/feishu_delivery/` without network assets, real business documents, faces, real audio, or sensitive data.

| File | MIME | Size | SHA-256 | Verification |
|---|---|---:|---|---|
| `p0-file-test.txt` | `text/plain` | 55 | `c8a155b4d5eccafd2b36758b9fa67af186174dfe6e99e184b56231bd8382663d` | Exact approved two-line content |
| `p0-image-test.png` | `image/png` | 17,247 | `624223e0f8d14374d40301574b721c9debd46d4168ad4c44d06767e5f74a4214` | 720x1280, solid background, `P0 IMAGE TEST` |
| `p0-video-test.mp4` | `video/mp4` | 8,858 | `ea8ce1539fc1c7520b1bb1d275529749a5f4190e82516f12b3e9b98eba7632cc` | 4.0 s, 720x1280, H.264, no audio stream, under 5 MB |
| `p0-video-cover.png` | `image/png` | 19,582 | `f1220bcdfac6737239951c49986efd639bdf349553cb85f455ee2ad31207d1b1` | 720x1280, solid background, `P0 VIDEO COVER` |

The TXT, PNG and MP4 delivery fixtures match explicit `.gitignore` rules and are not eligible for commit. Only `fixture_manifest.json` remains eligible for review and commit.
