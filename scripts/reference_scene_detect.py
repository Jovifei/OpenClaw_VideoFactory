"""Offline PySceneDetect sidecar; stdout is a small JSON boundary list."""

from __future__ import annotations

import argparse
import json

from scenedetect import SceneManager, open_video
from scenedetect.detectors import ContentDetector


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--video", required=True)
    parser.add_argument("--duration", required=True, type=float)
    parser.add_argument("--fps", required=True, type=float)
    args = parser.parse_args()
    video = open_video(args.video)
    manager = SceneManager()
    manager.add_detector(ContentDetector(threshold=27.0, min_scene_len=max(1, int(round(args.fps * 0.8)))))
    manager.detect_scenes(video=video)
    detected = manager.get_scene_list()
    scenes = [[float(start.get_seconds()), float(end.get_seconds())] for start, end in detected if end.get_seconds() > start.get_seconds()]
    if not scenes:
        scenes = [[0.0, args.duration]]
    elif scenes[-1][1] < args.duration - 0.05:
        scenes[-1][1] = args.duration
    print(json.dumps({"scenes": scenes}, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
