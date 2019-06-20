# -*- mode: python -*-

import pkg_resources
import platform


block_cipher = None


def Entrypoint(dist, group, name, **kwargs):
    """https://github.com/pyinstaller/pyinstaller/wiki/Recipe-Setuptools-Entry-Point"""
    kwargs.setdefault("pathex", [])
    # get the entry point
    ep = pkg_resources.get_entry_info(dist, group, name)
    # insert path of the egg at the verify front of the search path
    kwargs["pathex"] = [ep.dist.location] + kwargs["pathex"]
    # script name must not be a valid module name to avoid name clashes on import
    script_path = os.path.join(workpath, name + "-script.py")
    print("creating script for entry point", dist, group, name)
    with open(script_path, "w") as fh:
        print("import", ep.module_name, file=fh)
        print("%s.%s()" % (ep.module_name, ".".join(ep.attrs)), file=fh)

    return Analysis([script_path] + kwargs.get("scripts", []), **kwargs)


pyglui_hidden_imports = [
    "pyglui.pyfontstash",
    "pyglui.pyfontstash.fontstash",
    "pyglui.cygl.shader",
    "pyglui.cygl.utils",
    "cysignals",
]

binaries = []
datas = [
    (ui.get_opensans_font_path(), "pyglui/"),
    (ui.get_roboto_font_path(), "pyglui/"),
    (ui.get_pupil_icons_font_path(), "pyglui/"),
]

if platform.system() == "Darwin":
    binaries.append(("/usr/local/lib/libglfw.dylib", "."))
    datas.append(("icons/*.icns", "."))
elif platform.system() == "Linux":
    binaries.append(("/usr/lib/x86_64-linux-gnu/libglfw.so", "."))

from pyglui import ui

a = Entrypoint(
    "pi-monitor",
    "console_scripts",
    "pi_monitor",
    # pathex=["/Users/papr/work/pi_monitor/pi_monitor/"],
    binaries=binaries,
    datas=datas,
    hiddenimports=["pyzmq", "pyre"] + pyglui_hidden_imports,
    # hookspath=[],
    # runtime_hooks=[],
    # excludes=[],
    # win_no_prefer_redirects=False,
    # win_private_assemblies=False,
    # cipher=block_cipher,
    # noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="pi_monitor",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
)
coll = COLLECT(
    exe, a.binaries, a.zipfiles, a.datas, strip=False, upx=True, name="pi_monitor"
)
app = BUNDLE(
    coll,
    name="PI Monitor.app",
    icon="PPL-Capture",
    version=pkg_resources.get_distribution("pi_monitor").version,
    info_plist={"NSHighResolutionCapable": "True"},
)