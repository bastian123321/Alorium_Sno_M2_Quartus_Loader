"""Copies Intel's alt_dual_boot.v (the MAX 10 dual-boot / remote-update wrapper) from your Quartus
install into third_party/. The file is Intel IP, so it is not stored in this repository.

Usage:  python scripts/copy_dual_boot.py [path-to-Quartus-install-root]
        (the folder that contains 'quartus' and 'ip', e.g. C:\\altera_lite\\25.1std)
"""
import glob
import os
import shutil
import sys

REL = os.path.join("ip", "altera", "altera_dual_boot", "rtl", "alt_dual_boot.v")


def candidates():
    if len(sys.argv) > 1:
        yield sys.argv[1]
    root = os.environ.get("QUARTUS_ROOTDIR")          # ...\quartus
    if root:
        yield os.path.dirname(os.path.abspath(root))
    for base in (r"C:\altera_lite", r"C:\intelFPGA_lite", r"C:\altera", r"C:\intelFPGA",
                 r"C:\altera_pro", r"C:\intelFPGA_pro"):
        for d in sorted(glob.glob(os.path.join(base, "*")), reverse=True):
            yield d


def main():
    for c in candidates():
        src = os.path.join(c, REL)
        if os.path.isfile(src):
            dst = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "third_party",
                               "alt_dual_boot.v")
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copyfile(src, dst)
            print("copied", src, "->", os.path.normpath(dst))
            return 0
    print("alt_dual_boot.v not found. Pass your Quartus install root as an argument.")
    return 1


sys.exit(main())
