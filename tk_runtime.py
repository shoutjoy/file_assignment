"""Windows Python 설치의 Tcl/Tk를 GUI 실행 및 PyInstaller 빌드에 준비한다."""

import os
from pathlib import Path
import shutil
import sys
import tkinter as tk


def stage_tcl_tk(destination):
    source = Path(sys.base_prefix) / "tcl"
    destination = Path(destination)
    for directory in ("tcl8.6", "tk8.6"):
        if not (source / directory).is_dir():
            raise FileNotFoundError(f"Python Tcl/Tk 설치 폴더가 없습니다: {source / directory}")
        shutil.copytree(source / directory, destination / directory, dirs_exist_ok=True)
    return destination


def create_root():
    """Tcl 경로 문제일 때 작업 폴더의 캐시로 옮겨 한 번 더 초기화한다."""
    try:
        return tk.Tk()
    except tk.TclError as error:
        if "init.tcl" not in str(error) or getattr(sys, "frozen", False):
            raise

    staged = Path(__file__).resolve().parent / "build" / "tcl_runtime"
    if not (staged / "tcl8.6" / "init.tcl").is_file():
        stage_tcl_tk(staged)
    os.environ["TCL_LIBRARY"] = str(staged / "tcl8.6")
    os.environ["TK_LIBRARY"] = str(staged / "tk8.6")
    return tk.Tk()
