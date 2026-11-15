#!/usr/bin/env python3
"""Canonical builder: IEEE118 video, scenario1 (outage of line26–30).

python tools/build_presentation.py [--check-only] [--root PATH]
python tools/render_presentation.py
python tools/build_oral_script.py

The previous multi-network/capture-based deck is deliberately no longer generated.
Read-only Excel consumer; does not execute MATLAB. Story: presentation_story.py.
"""
from build_video_materials import main

if __name__ == '__main__':
    main()
