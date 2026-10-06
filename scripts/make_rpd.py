"""Turns a Quartus .sof into the 270,336-byte .rpd that Alorium's xlr8reconfig loads into the
application (image 1) slot of a Sno M2 (MAX 10 10M16).

Usage:  python scripts/make_rpd.py path/to/design.sof [-o out.rpd]

The design must have been compiled with INTERNAL_FLASH_UPDATE_MODE "Dual Images" (see README).
"""
import argparse
import glob
import os
import shutil
import subprocess
import sys
import tempfile

SLOT_BYTES = 270336            # CFM1 slot of a 10M16 = 2112 pages of 128 bytes
HEADER = bytes.fromhex("50ff47ff4dff49d243ff42fbff1c6f00")   # first 16 bytes of every valid image

COF = """<?xml version="1.0" encoding="US-ASCII" standalone="yes"?>
<cof>
	<output_filename>design.pof</output_filename>
	<n_pages>2</n_pages>
	<width>1</width>
	<mode>14</mode>
	<sof_data>
		<user_name>Page_0</user_name>
		<page_flags>1</page_flags>
		<bit0>
			<sof_filename>{sof}<compress_bitstream>1</compress_bitstream></sof_filename>
		</bit0>
	</sof_data>
	<sof_data>
		<user_name>Page_1</user_name>
		<page_flags>2</page_flags>
		<bit0>
			<sof_filename>{sof}<compress_bitstream>1</compress_bitstream></sof_filename>
		</bit0>
	</sof_data>
	<version>10</version>
	<create_cvp_file>0</create_cvp_file>
	<create_hps_iocsr>0</create_hps_iocsr>
	<auto_create_rpd>1</auto_create_rpd>
	<rpd_little_endian>1</rpd_little_endian>
	<options>
		<map_file>1</map_file>
	</options>
	<MAX10_device_options>
		<por>0</por>
		<io_pullup>1</io_pullup>
		<config_from_cfm0_only>0</config_from_cfm0_only>
		<isp_source>0</isp_source>
		<verify_protect>1</verify_protect>
		<epof>0</epof>
		<ufm_source>0</ufm_source>
	</MAX10_device_options>
	<advanced_options>
		<ignore_epcs_id_check>2</ignore_epcs_id_check>
		<ignore_condone_check>2</ignore_condone_check>
		<plc_adjustment>0</plc_adjustment>
		<post_chain_bitstream_pad_bytes>-1</post_chain_bitstream_pad_bytes>
		<post_device_bitstream_pad_bytes>-1</post_device_bitstream_pad_bytes>
		<bitslice_pre_padding>1</bitslice_pre_padding>
	</advanced_options>
</cof>
"""


def find_cpf():
    exe = shutil.which("quartus_cpf") or shutil.which("quartus_cpf.exe")
    if exe:
        return exe
    root = os.environ.get("QUARTUS_ROOTDIR")
    if root:
        for sub in ("bin64", "bin"):
            p = os.path.join(root, sub, "quartus_cpf.exe")
            if os.path.isfile(p):
                return p
    for base in (r"C:\altera_lite", r"C:\intelFPGA_lite", r"C:\altera", r"C:\intelFPGA"):
        for p in sorted(glob.glob(os.path.join(base, "*", "quartus", "bin64", "quartus_cpf.exe")),
                        reverse=True):
            return p
    sys.exit("quartus_cpf not found: add Quartus' bin64 folder to PATH or set QUARTUS_ROOTDIR")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("sof")
    ap.add_argument("-o", "--out")
    a = ap.parse_args()
    sof = os.path.abspath(a.sof)
    if not os.path.isfile(sof):
        sys.exit("not found: " + sof)
    out = os.path.abspath(a.out) if a.out else os.path.splitext(sof)[0] + ".rpd"

    with tempfile.TemporaryDirectory() as tmp:
        cof = os.path.join(tmp, "design.cof")
        with open(cof, "w", encoding="ascii") as f:
            f.write(COF.format(sof=sof.replace("\\", "/")))
        r = subprocess.run([find_cpf(), "-c", cof], cwd=tmp, capture_output=True, text=True)
        if r.returncode != 0:
            print(r.stdout[-2000:], r.stderr[-2000:])
            sys.exit("quartus_cpf failed (was the design compiled with 'Dual Images'?)")
        src = os.path.join(tmp, "design_cfm1_auto.rpd")
        if not os.path.isfile(src):
            sys.exit("quartus_cpf did not produce design_cfm1_auto.rpd")
        shutil.copyfile(src, out)

    d = open(out, "rb").read()
    end = len(d)
    while end and d[end - 1] == 0xFF:
        end -= 1
    print("wrote", out)
    print("size  : %d bytes (expected %d)" % (len(d), SLOT_BYTES))
    print("design: %d bytes = %.0f%% of the image slot" % (end, 100.0 * end / SLOT_BYTES))
    ok = True
    if len(d) != SLOT_BYTES:
        print("WARNING: unexpected size; the loader writes exactly %d bytes" % SLOT_BYTES)
        ok = False
    if d[:16] != HEADER:
        print("WARNING: header differs from a valid image: " + d[:16].hex(" "))
        print("         (a 3b instead of fb in byte 12 means it was NOT compiled in Dual Images mode)")
        ok = False
    print("check : " + ("OK" if ok else "FAILED"))
    sys.exit(0 if ok else 2)


main()
