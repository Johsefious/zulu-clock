#!/usr/bin/env python3
"""repo release's step for Zulu Clock: release_step.py DEST VERSION.

Fills DEST (the zip's top folder) with the installer, a read-me and Files/, which holds only what the clock runs:
the server, the page and its script, the two fonts, the Dock icon (svg and ready-made .icns) and dock.json. No tests, docs, launch scripts,
notes or logs. The shared services (docks, ports) are added by repo release, not here."""
import os
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUNS = ['server.py', 'zulu-clock.html', 'zulu-clock.js', 'dock.json', 'icons/zulu-clock.svg', 'icons/Zulu Clock.icns',
        'fonts/share-tech-mono-latin.woff2', 'fonts/vt323-latin.woff2']
READ_ME = """Zulu Clock %s

1. Double-click "Install Zulu Clock" in this folder.
2. When it says it is installed, open Zulu Clock from the Dock (or Applications > Zulu Clock in your home folder).

The installer needs Python 3. If your Mac has none, the installer says how to get it. Run it again to update.
The clock shows weather, news and alerts from public sources. It needs no key or sign-in.
You can delete the zip and this folder after installing.
"""


def main(dest, version):
    files = os.path.join(dest, 'Files')
    for rel in RUNS:
        os.makedirs(os.path.dirname(os.path.join(files, rel)), exist_ok=True)
        shutil.copy2(os.path.join(ROOT, rel), os.path.join(files, rel))
    with open(os.path.join(files, 'VERSION'), 'w') as f:
        f.write(version + '\n')
    installer = os.path.join(dest, 'Install Zulu Clock.command')
    shutil.copy2(os.path.join(ROOT, 'tools', 'Install Zulu Clock.command'), installer)
    os.chmod(installer, 0o755)
    with open(os.path.join(dest, 'Read me.txt'), 'w') as f:
        f.write(READ_ME % version)
    print('zulu-clock %s: %d files in Files/, installer, read me' % (version, len(RUNS) + 1))


if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit('usage: release_step.py DEST VERSION')
    main(sys.argv[1], sys.argv[2])
