import ctypes
import csv
import json
import os
import re
import shutil
import subprocess
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
import winreg as reg


def parse_launch_args(argv):
    """--close-after-run / --keep-open 과 폴더 경로(위치 인자)를 분리한다."""
    mode = None  # None | "close" | "keep"
    positional = []
    for a in argv[1:]:
        if a == "--close-after-run":
            mode = "close"
        elif a == "--keep-open":
            mode = "keep"
        elif a.startswith("-"):
            continue
        else:
            positional.append(a)
    return mode, positional


def settings_path():
    d = os.path.join(os.environ.get("LOCALAPPDATA", ""), "FileAssignmentManager")
    return os.path.join(d, "settings.json")


def load_close_after_pref():
    try:
        with open(settings_path(), encoding="utf-8") as f:
            return bool(json.load(f).get("close_after_run", False))
    except (OSError, json.JSONDecodeError, TypeError):
        return False


def save_close_after_pref(value):
    d = os.path.dirname(settings_path())
    try:
        os.makedirs(d, exist_ok=True)
        data = {}
        if os.path.isfile(settings_path()):
            try:
                with open(settings_path(), encoding="utf-8") as f:
                    data = json.load(f)
            except (json.JSONDecodeError, TypeError):
                pass
        data["close_after_run"] = bool(value)
        with open(settings_path(), "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=0)
    except OSError:
        pass


def is_frozen():
    return bool(getattr(sys, "frozen", False))


def app_install_dir():
    if is_frozen():
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.abspath(sys.argv[0]))


def explorer_menu_command(path_placeholder):
    if is_frozen():
        return f'"{os.path.abspath(sys.executable)}" "{path_placeholder}"'
    script = os.path.abspath(sys.argv[0])
    return f'"{sys.executable}" "{script}" "{path_placeholder}"'


def notify_shell_context_menus_changed():
    try:
        SHCNE_ASSOCCHANGED = 0x08000000
        SHCNF_IDLIST = 0x0000
        SHCNF_FLUSH = 0x1000
        ctypes.windll.shell32.SHChangeNotify(
            SHCNE_ASSOCCHANGED, SHCNF_IDLIST | SHCNF_FLUSH, None, None
        )
    except OSError:
        pass


_pf = os.environ.get("ProgramFiles")
if not _pf:
    _sd = os.environ.get("SystemDrive", "C:")
    _sd_root = _sd if _sd.endswith(("/", "\\")) else _sd + os.sep
    _pf = os.path.join(_sd_root, "Program Files")
PROGRAM_ASSIGN_INSTALL_DIR = os.path.join(_pf, "FileAssignmentManager")
PROGRAM_ASSIGN_EXE_NAME = "FileAssignmentManager.exe"


def context_menu_success_hint():
    try:
        v = sys.getwindowsversion()
        if v.major >= 10 and v.build >= 22000:
            return (
                "\n\nWindows 11에서는 기본 우클릭 메뉴 대신\n"
                "「추가 옵션 표시」또는 Shift+우클릭(전체 메뉴)에서 항목을 확인하세요."
            )
    except (TypeError, ValueError, AttributeError):
        pass
    return ""


def wsh_create_shortcut(link_path, target_path, arguments, working_dir, description):
    link_dir = os.path.dirname(link_path)
    if link_dir:
        os.makedirs(link_dir, exist_ok=True)
    ps = (
        "$sc = (New-Object -ComObject WScript.Shell).CreateShortcut($env:LINK); "
        "$sc.TargetPath = $env:PY; "
        "$sc.Arguments = $env:ARGS; "
        "$sc.WorkingDirectory = $env:CWD; "
        "$sc.Description = $env:DESC; "
        "$sc.Save()"
    )
    env = os.environ.copy()
    env["LINK"] = link_path
    env["PY"] = target_path
    env["ARGS"] = arguments
    env["CWD"] = working_dir
    env["DESC"] = description
    subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            ps,
        ],
        check=True,
        env=env,
        creationflags=(
            getattr(subprocess, "CREATE_NO_WINDOW", 0) if sys.platform == "win32" else 0
        ),
    )


def taskbar_pinned_shortcut_path():
    return os.path.join(
        os.environ.get("APPDATA", ""),
        "Microsoft",
        "Internet Explorer",
        "Quick Launch",
        "User Pinned",
        "TaskBar",
        "FileAssignmentManager.lnk",
    )


class AssignmentManagerApp:
    _REG_CLASSES = r"Software\Classes"
    _MENU_KEY_NAME = r"FileAssignmentMgr"
    _MENU_TARGETS = (
        (r"Directory\shell", "%1"),
        (r"Directory\Background\shell", "%V"),
    )

    def __init__(self, root, *, launch_mode=None, positional_paths=None):
        self.root = root
        self.root.title("과제 통합 및 학생 명단 추출")
        self.root.geometry("650x740")
        self.root.minsize(560, 600)
        self.root.resizable(True, True)

        self.source_dir_var = tk.StringVar()
        self.target_dir_var = tk.StringVar()
        self.rename_files_var = tk.BooleanVar(value=True)
        self.create_csv_var = tk.BooleanVar(value=True)

        current_dir = app_install_dir()
        self.source_dir_var.set(current_dir)
        self.target_dir_var.set(os.path.join(current_dir, "통합_과제"))

        if launch_mode == "close":
            close_initial = True
        elif launch_mode == "keep":
            close_initial = False
        else:
            close_initial = load_close_after_pref()
        self.close_after_var = tk.BooleanVar(value=close_initial)

        self._install_expanded = False

        for p in positional_paths or []:
            if os.path.isdir(p):
                ap = os.path.abspath(p)
                self.source_dir_var.set(ap)
                self.target_dir_var.set(os.path.join(ap, "통합_과제"))
                break

        self._build_ui()

    def _bind_scroll_canvas(self, canvas):
        def _wheel(event):
            canvas.yview_scroll(int(-event.delta / 120), "units")

        canvas.bind("<Enter>", lambda _e: canvas.bind_all("<MouseWheel>", _wheel))
        canvas.bind("<Leave>", lambda _e: canvas.unbind_all("<MouseWheel>"))

    def _make_scroll_body(self, parent):
        wrap = tk.Frame(parent)
        canvas = tk.Canvas(wrap, highlightthickness=0)
        sb = ttk.Scrollbar(wrap, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        body = tk.Frame(canvas)
        inner_id = canvas.create_window((0, 0), window=body, anchor="nw")

        def on_body_configure(_event=None):
            canvas.configure(scrollregion=canvas.bbox("all"))

        def on_canvas_configure(event):
            w = max(event.width, 1)
            canvas.itemconfigure(inner_id, width=w)

        body.bind("<Configure>", on_body_configure)
        canvas.bind("<Configure>", on_canvas_configure)
        self._bind_scroll_canvas(canvas)
        return wrap, canvas, body

    def _build_ui(self):
        style = ttk.Style()
        style.configure("TButton", padding=5)

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True)

        tab_main = tk.Frame(self.notebook)
        tab_main.grid_columnconfigure(0, weight=1)
        tab_main.grid_rowconfigure(5, weight=1)
        self.notebook.add(tab_main, text="통합")

        instruction = tk.Label(
            tab_main,
            text="학생별 폴더의 파일을 하나의 폴더로 통합하고 명단을 CSV로 추출합니다.",
            font=("Malgun Gothic", 11, "bold"),
            fg="#2c3e50",
        )
        instruction.grid(row=0, column=0, pady=10)

        path_frame = tk.LabelFrame(
            tab_main, text="경로 설정", font=("Malgun Gothic", 9, "bold"), padx=10, pady=10
        )
        path_frame.grid(row=1, column=0, sticky="ew", padx=15, pady=5)
        path_frame.grid_columnconfigure(1, weight=1)

        tk.Label(path_frame, text="대상 폴더 (주차별 과제):", font=("Malgun Gothic", 9)).grid(
            row=0, column=0, sticky="w", pady=5
        )
        self.source_entry = tk.Entry(path_frame, textvariable=self.source_dir_var, width=50)
        self.source_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        tk.Button(path_frame, text="찾아보기", command=self.browse_source, width=10).grid(
            row=0, column=2, padx=5, pady=5
        )

        tk.Label(path_frame, text="저장할 폴더 (통합본):", font=("Malgun Gothic", 9)).grid(
            row=1, column=0, sticky="w", pady=5
        )
        self.target_entry = tk.Entry(path_frame, textvariable=self.target_dir_var, width=50)
        self.target_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        tk.Button(path_frame, text="찾아보기", command=self.browse_target, width=10).grid(
            row=1, column=2, padx=5, pady=5
        )

        option_frame = tk.LabelFrame(
            tab_main, text="실행 옵션", font=("Malgun Gothic", 9, "bold"), padx=10, pady=8
        )
        option_frame.grid(row=2, column=0, sticky="ew", padx=15, pady=5)

        tk.Checkbutton(
            option_frame,
            text="파일 이름 앞부분에 학생 이름 및 학번 추가 "
            "(예: [홍길동_2026] 파일명.pdf)",
            variable=self.rename_files_var,
            font=("Malgun Gothic", 9),
        ).pack(anchor="w", pady=2)
        tk.Checkbutton(
            option_frame,
            text="학생 명단 CSV 파일 생성 (저장 폴더 내에 생성)",
            variable=self.create_csv_var,
            font=("Malgun Gothic", 9),
        ).pack(anchor="w", pady=2)
        tk.Checkbutton(
            option_frame,
            text="통합 완료 후 프로그램 종료",
            variable=self.close_after_var,
            command=lambda: save_close_after_pref(self.close_after_var.get()),
            font=("Malgun Gothic", 9),
        ).pack(anchor="w", pady=2)

        self.run_btn = tk.Button(
            tab_main,
            text="통합 작업 시작",
            command=self.start_process,
            font=("Malgun Gothic", 10, "bold"),
            bg="#2980b9",
            fg="white",
            height=2,
        )
        self.run_btn.grid(row=4, column=0, sticky="ew", padx=15, pady=10)

        log_frame = tk.LabelFrame(
            tab_main, text="진행 현황", font=("Malgun Gothic", 9, "bold"), padx=5, pady=5
        )
        log_frame.grid(row=5, column=0, sticky="nsew", padx=15, pady=5)
        log_frame.grid_rowconfigure(0, weight=1)
        log_frame.grid_columnconfigure(0, weight=1)
        self.log_area = scrolledtext.ScrolledText(
            log_frame, wrap=tk.WORD, height=12, font=("Consolas", 9)
        )
        self.log_area.grid(row=0, column=0, sticky="nsew")

        tab_settings = tk.Frame(self.notebook)
        tab_settings.grid_columnconfigure(0, weight=1)
        tab_settings.grid_rowconfigure(0, weight=1)
        self.notebook.add(tab_settings, text="설정")

        wrap_set, _canvas_set, body_set = self._make_scroll_body(tab_settings)
        wrap_set.grid(row=0, column=0, sticky="nsew")

        install_shell = tk.Frame(body_set)
        install_shell.pack(fill="x", padx=20, pady=5)

        self.btn_install_fold = ttk.Button(
            install_shell,
            text="앱 설치 ▼ 펼치기 (최초 1회 권장)",
            command=self._toggle_install_fold,
        )
        self.btn_install_fold.pack(anchor="w")

        self._install_detail = tk.LabelFrame(install_shell, text="앱 설치", padx=10, pady=10)
        ttk.Button(
            self._install_detail,
            text=f"설치 (Install) — {PROGRAM_ASSIGN_INSTALL_DIR} 에 복사",
            command=self.install_to_program_files,
        ).pack(fill="x", padx=5, pady=2)
        self.install_add_start_menu_var = tk.BooleanVar(value=True)
        self.install_pin_taskbar_var = tk.BooleanVar(value=False)
        cb_row = tk.Frame(self._install_detail)
        cb_row.pack(fill="x", padx=5, pady=(2, 0))
        tk.Checkbutton(
            cb_row,
            text="설치 후 시작 메뉴에 바로가기 만들기",
            variable=self.install_add_start_menu_var,
        ).pack(anchor="w")
        tk.Checkbutton(
            cb_row,
            text="작업 표시줄 고정용 바로가기 만들기 (자동 고정은 Windows에서 제한될 수 있음)",
            variable=self.install_pin_taskbar_var,
        ).pack(anchor="w")
        tk.Label(
            self._install_detail,
            text=(
                "FileAssignmentManager.exe 로 실행 중일 때 설치 버튼으로 고정 폴더에 복사합니다. "
                "※ 같은 폴더에서 이미 실행 중이면 복사 없이, 체크한 바로가기만 만들 수 있습니다.\n"
                "바로가기의 종료 여부 옵션은 「통합」탭의 「통합 완료 후 프로그램 종료」와 동일합니다.\n"
                "Python 스크립트로만 실행 중이면 설치 시 안내 메시지가 표시됩니다."
            ),
            justify="left",
            wraplength=520,
        ).pack(anchor="w", padx=5, pady=(4, 0))

        explorer_frame = tk.LabelFrame(
            body_set, text="윈도우 탐색기 통합", padx=10, pady=10
        )
        explorer_frame.pack(fill="x", padx=20, pady=5)

        btn_row = tk.Frame(explorer_frame)
        btn_row.pack(fill="x", pady=2)
        ttk.Button(
            btn_row, text="우클릭 메뉴에 등록", command=self.register_context_menu
        ).pack(side="left", expand=True, padx=5)
        ttk.Button(
            btn_row, text="우클릭 메뉴에서 제거", command=self.unregister_context_menu
        ).pack(side="left", expand=True, padx=5)

        tk.Label(
            body_set,
            text=(
                "※ 탐색기에서 메뉴가 안 보이면: Windows 11은 「추가 옵션 표시」 또는 "
                "Shift+우클릭으로 전체 메뉴를 여세요. 등록 직후 탐색기를 닫았다가 다시 열거나 "
                "PC 재시작 후 확인하세요."
            ),
            justify="left",
            wraplength=520,
            fg="#333",
        ).pack(anchor="w", padx=20, pady=(0, 6))

        start_frame = tk.LabelFrame(body_set, text="시작 메뉴 바로가기 (수동)", padx=10, pady=10)
        start_frame.pack(fill="x", padx=20, pady=(5, 16))
        ttk.Button(
            start_frame,
            text="등록 · 통합 후에도 창 유지",
            command=lambda: self.register_start_menu_shortcut(close_after=False),
        ).pack(side="left", expand=True, padx=5)
        ttk.Button(
            start_frame,
            text="등록 · 통합 완료 후 종료",
            command=lambda: self.register_start_menu_shortcut(close_after=True),
        ).pack(side="left", expand=True, padx=5)

    def _toggle_install_fold(self):
        self._install_expanded = not self._install_expanded
        if self._install_expanded:
            self._install_detail.pack(fill="x", pady=(6, 0))
            self.btn_install_fold.configure(text="앱 설치 ▲ 접기")
        else:
            self._install_detail.pack_forget()
            self.btn_install_fold.configure(text="앱 설치 ▼ 펼치기 (최초 1회 권장)")

    def browse_source(self):
        selected = filedialog.askdirectory(title="학생 폴더들이 포함된 대상 폴더 선택")
        if selected:
            self.source_dir_var.set(os.path.abspath(selected))
            if not self.target_dir_var.get().strip():
                self.target_dir_var.set(os.path.join(os.path.abspath(selected), "통합_과제"))

    def browse_target(self):
        selected = filedialog.askdirectory(title="통합 파일을 저장할 폴더 선택")
        if selected:
            self.target_dir_var.set(os.path.abspath(selected))

    def log(self, message):
        self.log_area.insert(tk.END, message + "\n")
        self.log_area.see(tk.END)
        self.root.update_idletasks()

    def parse_student_info(self, folder_name):
        match = re.match(r"^([^-]+)-([0-9]+)", folder_name)
        if match:
            name = match.group(1).strip()
            student_id = match.group(2).strip()
            return name, student_id
        return None, None

    def _start_menu_programs_dir(self):
        return os.path.join(
            os.environ.get("APPDATA", ""),
            "Microsoft",
            "Windows",
            "Start Menu",
            "Programs",
        )

    def _write_one_context_menu(self, shell_parent_path, path_placeholder):
        hkey = reg.HKEY_CURRENT_USER
        key_path = rf"{self._REG_CLASSES}\{shell_parent_path}\{self._MENU_KEY_NAME}"
        icon_src = sys.executable
        with reg.CreateKey(hkey, key_path) as key:
            reg.SetValue(key, "", reg.REG_SZ, "과제 통합 및 명단 추출")
            reg.SetValueEx(key, "Icon", 0, reg.REG_SZ, icon_src)
        command_path = key_path + r"\command"
        with reg.CreateKey(hkey, command_path) as key:
            reg.SetValue(key, "", reg.REG_SZ, explorer_menu_command(path_placeholder))

    def _delete_one_context_menu(self, shell_parent_path):
        hkey = reg.HKEY_CURRENT_USER
        key_path = rf"{self._REG_CLASSES}\{shell_parent_path}\{self._MENU_KEY_NAME}"
        reg.DeleteKey(hkey, key_path + r"\command")
        reg.DeleteKey(hkey, key_path)

    def register_context_menu(self):
        if sys.platform != "win32":
            messagebox.showerror("오류", "Windows 에서만 지원됩니다.")
            return
        try:
            for shell_parent, token in self._MENU_TARGETS:
                self._write_one_context_menu(shell_parent, token)
            notify_shell_context_menus_changed()
            self.log("우클릭 등록 완료 (폴더 아이콘 / 폴더 안 빈 곳).")
            messagebox.showinfo(
                "성공",
                "탐색기에 등록했습니다.\n"
                "· 폴더에서 우클릭\n"
                "· 폴더 안 빈 곳에서 우클릭\n\n"
                "※ 변경이 안 보이면 탐색기를 모두 닫았다 다시 여세요." + context_menu_success_hint(),
            )
        except OSError as e:
            messagebox.showerror("오류", f"메뉴 등록 중 오류: {e}")
        except Exception as e:
            messagebox.showerror("오류", f"메뉴 등록 중 오류 발생: {e}")

    def unregister_context_menu(self):
        if sys.platform != "win32":
            messagebox.showerror("오류", "Windows 에서만 지원됩니다.")
            return
        missing = True
        err = None
        for shell_parent, _ in self._MENU_TARGETS:
            try:
                self._delete_one_context_menu(shell_parent)
                missing = False
            except FileNotFoundError:
                continue
            except OSError as e:
                err = e
        if err:
            messagebox.showerror("오류", f"메뉴 제거 중 오류: {err}")
        elif missing:
            messagebox.showinfo("알림", "등록된 메뉴가 없습니다.")
        else:
            notify_shell_context_menus_changed()
            self.log("우클릭 메뉴 제거 완료.")
            messagebox.showinfo("성공", "우클릭 메뉴에서 제거되었습니다.")

    def register_start_menu_shortcut(self, *, close_after):
        appdata = os.environ.get("APPDATA", "")
        if not appdata or not os.path.isdir(appdata):
            messagebox.showerror("오류", "시작 메뉴 경로를 찾을 수 없습니다.")
            return
        programs = self._start_menu_programs_dir()
        os.makedirs(programs, exist_ok=True)
        name = (
            "FileAssignmentManager (완료 후 종료).lnk"
            if close_after
            else "FileAssignmentManager.lnk"
        )
        link_path = os.path.join(programs, name)
        py_exe = os.path.abspath(sys.executable)
        inst_dir = app_install_dir()
        if is_frozen():
            args = "--close-after-run" if close_after else "--keep-open"
        else:
            script = os.path.abspath(sys.argv[0])
            args = f'"{script}"'
            args += " --close-after-run" if close_after else " --keep-open"
        desc = "과제 통합 및 명단 추출 · " + (
            "완료 후 종료" if close_after else "창 유지"
        )
        try:
            wsh_create_shortcut(link_path, py_exe, args, inst_dir, desc)
            messagebox.showinfo("성공", f"시작 메뉴에 등록했습니다.\n{name}")
        except (OSError, subprocess.CalledProcessError) as e:
            messagebox.showerror("오류", f"바로가기 만들기 실패: {e}")

    def install_to_program_files(self):
        if not is_frozen():
            messagebox.showinfo(
                "알림",
                "이 설치(복사) 기능은 FileAssignmentManager.exe 로 실행했을 때 사용할 수 있습니다.",
            )
            return

        dest_dir = os.path.normpath(PROGRAM_ASSIGN_INSTALL_DIR)
        dest_exe = os.path.join(dest_dir, PROGRAM_ASSIGN_EXE_NAME)
        norm_src = os.path.normcase(os.path.normpath(os.path.abspath(sys.executable)))
        norm_dest = os.path.normcase(os.path.normpath(dest_exe))

        want_sm = self.install_add_start_menu_var.get()
        want_tb = self.install_pin_taskbar_var.get()

        if norm_src == norm_dest:
            if not want_sm and not want_tb:
                messagebox.showinfo(
                    "알림",
                    f"이미 설치 경로에서 실행 중입니다.\n{dest_exe}\n"
                    "시작 메뉴·작업 표시줄 바로가기를 만들려면 체크한 뒤 다시 누르세요.",
                )
                self.log(f"설치: 이미 {dest_exe} (바로가기 옵션 없음)")
                return
        else:
            try:
                os.makedirs(dest_dir, exist_ok=True)
            except OSError as e:
                messagebox.showerror(
                    "오류",
                    f"폴더를 만들 수 없습니다.\n{dest_dir}\n\n{e}\n\n"
                    "Program Files 에는 관리자 권한이 필요할 수 있습니다. "
                    "「관리자 권한으로 실행」 후 다시 시도하세요.",
                )
                return
            try:
                shutil.copy2(os.path.abspath(sys.executable), dest_exe)
            except OSError as e:
                messagebox.showerror(
                    "오류",
                    f"파일을 복사할 수 없습니다.\n→ {dest_exe}\n\n{e}",
                )
                return
            self.log(f"복사 완료: {dest_exe}")

        close_after = self.close_after_var.get()
        args = "--close-after-run" if close_after else "--keep-open"
        desc = "과제 통합 및 명단 추출 · " + (
            "완료 후 종료" if close_after else "창 유지"
        )

        done = []
        warn = []

        if want_sm:
            name = (
                "FileAssignmentManager (완료 후 종료).lnk"
                if close_after
                else "FileAssignmentManager.lnk"
            )
            link_path = os.path.join(self._start_menu_programs_dir(), name)
            try:
                wsh_create_shortcut(link_path, dest_exe, args, dest_dir, desc)
                done.append(f"시작 메뉴: {name}")
                self.log(f"바로가기: {link_path}")
            except (OSError, subprocess.CalledProcessError) as e:
                warn.append(f"시작 메뉴 바로가기: {e}")

        if want_tb:
            tb_link = taskbar_pinned_shortcut_path()
            try:
                wsh_create_shortcut(
                    tb_link,
                    dest_exe,
                    args,
                    dest_dir,
                    desc + " · 작업 표시줄",
                )
                done.append("작업 표시줄 고정 폴더에 바로가기 저장")
                self.log(f"바로가기: {tb_link}")
            except (OSError, subprocess.CalledProcessError) as e:
                warn.append(f"작업 표시줄 바로가기: {e}")

        lines = [f"설치 경로: {dest_exe}", ""]
        if done:
            lines.append("\n".join(done))
        if warn:
            lines.extend(["", "주의:\n" + "\n".join(warn)])
        lines.append("")
        lines.append(
            "탐색기 우클릭 메뉴는 위 경로 exe로 「우클릭 메뉴에 등록」 하는 것을 권장합니다."
        )
        if want_tb:
            lines.append(
                "작업 표시줄에 안 보이면: 시작 메뉴에서 앱 실행 후 작업 표시줄 아이콘 → "
                "작업 표시줄에 고정."
            )

        messagebox.showinfo("완료", "\n".join(lines))

    def start_process(self):
        source_dir = self.source_dir_var.get().strip()
        target_dir = self.target_dir_var.get().strip()

        if not source_dir or not os.path.exists(source_dir):
            messagebox.showerror("오류", "유효한 대상 폴더 경로를 선택하십시오.")
            return

        if not target_dir:
            messagebox.showerror("오류", "저장할 폴더 경로를 입력하십시오.")
            return

        if not os.path.exists(target_dir):
            try:
                os.makedirs(target_dir)
                self.log(f"[알림] 저장 폴더를 새로 만들었습니다: {target_dir}")
            except OSError as e:
                messagebox.showerror("오류", f"저장 폴더를 생성할 수 없습니다: {e}")
                return

        self.log_area.delete("1.0", tk.END)
        self.log("================= 과제 통합 작업을 시작합니다 =================")
        self.log(f"대상 폴더: {source_dir}")
        self.log(f"저장 폴더: {target_dir}\n")

        self.run_btn.config(state="disabled")
        student_list = []
        copy_count = 0
        folder_count = 0

        try:
            subitems = os.listdir(source_dir)

            for item in subitems:
                item_path = os.path.join(source_dir, item)

                if os.path.isdir(item_path) and os.path.abspath(item_path) != os.path.abspath(
                    target_dir
                ):
                    name, student_id = self.parse_student_info(item)

                    if name and student_id:
                        folder_count += 1
                        self.log(f"[분석 완료] 이름: {name} / 학번: {student_id} (폴더: {item})")
                        student_list.append(
                            {"이름": name, "학번": student_id, "기존폴더명": item}
                        )

                        for root_dir, _, files in os.walk(item_path):
                            for file in files:
                                file_path = os.path.join(root_dir, file)

                                if file.startswith("~$") or file.lower() in [
                                    ".ds_store",
                                    "desktop.ini",
                                ]:
                                    continue

                                if self.rename_files_var.get():
                                    new_file_name = f"[{name}_{student_id}] {file}"
                                else:
                                    new_file_name = file

                                dest_file_path = os.path.join(target_dir, new_file_name)

                                base, ext = os.path.splitext(new_file_name)
                                counter = 1
                                while os.path.exists(dest_file_path):
                                    dest_file_path = os.path.join(
                                        target_dir, f"{base}_{counter}{ext}"
                                    )
                                    counter += 1

                                shutil.copy2(file_path, dest_file_path)
                                self.log(
                                    f"  └ 파일 복사 완료: {file} -> {os.path.basename(dest_file_path)}"
                                )
                                copy_count += 1
                    else:
                        self.log(f"[건너뜀] 학번 패턴 불일치 폴더: {item}")

            if self.create_csv_var.get() and student_list:
                csv_path = os.path.join(target_dir, "학생명단_리스트.csv")

                with open(csv_path, mode="w", encoding="utf-8-sig", newline="") as f:
                    writer = csv.DictWriter(
                        f, fieldnames=["이름", "학번", "기존폴더명"]
                    )
                    writer.writeheader()
                    for student in sorted(student_list, key=lambda x: x["이름"]):
                        writer.writerow(student)

                self.log(f"\n[성공] 학생 명단 CSV: {os.path.basename(csv_path)}")

            self.log("\n================= 작업이 완료되었습니다 =================")
            self.log(f"총 처리된 학생 폴더 수: {folder_count}개")
            self.log(f"총 통합된 파일 수: {copy_count}개")

            messagebox.showinfo(
                "성공",
                f"작업이 완료되었습니다.\n통합 파일: {copy_count}개\n학생 폴더: {folder_count}개",
            )

            if self.close_after_var.get():
                self.root.destroy()

        except Exception as e:
            self.log(f"\n[오류 발생] {e}")
            messagebox.showerror("오류", f"작업 수행 중 오류가 발생하였습니다:\n{e}")
        finally:
            try:
                self.run_btn.config(state="normal")
            except tk.TclError:
                pass


if __name__ == "__main__":
    launch_mode, pos_paths = parse_launch_args(sys.argv)
    root = tk.Tk()
    app = AssignmentManagerApp(root, launch_mode=launch_mode, positional_paths=pos_paths)
    root.mainloop()
