import os
import sys
import re
import shutil
import csv
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext

class AssignmentManagerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("과제 통합 및 학생 명단 추출 프로그램")
        self.root.geometry("650x680") # 탐색기 통합 프레임 추가에 따른 창 높이 조정
        self.root.resizable(True, True)

        # 상태 변수 설정
        self.source_dir_var = tk.StringVar()
        self.target_dir_var = tk.StringVar()
        self.rename_files_var = tk.BooleanVar(value=True)
        self.create_csv_var = tk.BooleanVar(value=True)

        # 시스템의 현재 디렉터리 경로 자동 분석 및 초기 경로 설정
        # (실행파일이나 스크립트가 실행되는 기준 위치를 찾음)
        current_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
        self.source_dir_var.set(current_dir)
        self.target_dir_var.set(os.path.join(current_dir, "통합_과제"))

        # 윈도우 우클릭 메뉴 또는 인수로 경로가 외부로부터 전달되었는지 확인
        if len(sys.argv) > 1:
            passed_path = sys.argv[1]
            if os.path.isdir(passed_path):
                self.source_dir_var.set(os.path.abspath(passed_path))
                # 기본 대상 폴더를 소스 폴더 하위의 "통합_과제"로 지정
                self.target_dir_var.set(os.path.join(os.path.abspath(passed_path), "통합_과제"))

        self.create_widgets()

    def create_widgets(self):
        # 상단 설명 레이블
        instruction_label = tk.Label(
            self.root, 
            text="학생별 폴더의 파일을 하나의 폴더로 통합하고 명단을 CSV로 추출합니다.", 
            font=("Malgun Gothic", 11, "bold"),
            fg="#2c3e50"
        )
        instruction_label.pack(pady=10)

        # 경로 설정 프레임
        path_frame = tk.LabelFrame(self.root, text="경로 설정", font=("Malgun Gothic", 9, "bold"), padx=10, pady=10)
        path_frame.pack(fill="x", padx=15, pady=5)

        # 1. 소스 폴더 (학생별 폴더들이 모여있는 곳)
        tk.Label(path_frame, text="대상 폴더 (주차별 과제):", font=("Malgun Gothic", 9)).grid(row=0, column=0, sticky="w", pady=5)
        self.source_entry = tk.Entry(path_frame, textvariable=self.source_dir_var, width=50)
        self.source_entry.grid(row=0, column=1, padx=5, pady=5)
        tk.Button(path_frame, text="찾아보기", command=self.browse_source, width=10).grid(row=0, column=2, padx=5, pady=5)

        # 2. 대상 폴더 (통합하여 저장할 곳)
        tk.Label(path_frame, text="저장할 폴더 (통합본):", font=("Malgun Gothic", 9)).grid(row=1, column=0, sticky="w", pady=5)
        self.target_entry = tk.Entry(path_frame, textvariable=self.target_dir_var, width=50)
        self.target_entry.grid(row=1, column=1, padx=5, pady=5)
        tk.Button(path_frame, text="찾아보기", command=self.browse_target, width=10).grid(row=1, column=2, padx=5, pady=5)

        # 옵션 설정 프레임
        option_frame = tk.LabelFrame(self.root, text="실행 옵션", font=("Malgun Gothic", 9, "bold"), padx=10, pady=8)
        option_frame.pack(fill="x", padx=15, pady=5)

        self.rename_cb = tk.Checkbutton(
            option_frame, 
            text="파일 이름 앞부분에 학생 이름 및 학번 추가 (예: [홍길동_2026] 파일명.pdf)", 
            variable=self.rename_files_var,
            font=("Malgun Gothic", 9)
        )
        self.rename_cb.pack(anchor="w", pady=2)

        self.csv_cb = tk.Checkbutton(
            option_frame, 
            text="학생 명단 CSV 파일 생성 (저장 폴더 내에 생성)", 
            variable=self.create_csv_var,
            font=("Malgun Gothic", 9)
        )
        self.csv_cb.pack(anchor="w", pady=2)

        # 윈도우 탐색기 통합 프레임 (우클릭 제어 시스템)
        explorer_frame = tk.LabelFrame(self.root, text="윈도우 탐색기 통합 (우클릭 메뉴 제어)", font=("Malgun Gothic", 9, "bold"), padx=10, pady=8)
        explorer_frame.pack(fill="x", padx=15, pady=5)

        btn_subframe = tk.Frame(explorer_frame)
        btn_subframe.pack(fill="x", pady=2)

        reg_btn = tk.Button(
            btn_subframe, 
            text="우클릭 메뉴에 등록", 
            command=self.register_menu, 
            bg="#2ecc71", 
            fg="white", 
            font=("Malgun Gothic", 9, "bold"),
            width=20
        )
        reg_btn.pack(side="left", padx=20, expand=True)

        unreg_btn = tk.Button(
            btn_subframe, 
            text="우클릭 메뉴에서 제거", 
            command=self.unregister_menu, 
            bg="#e74c3c", 
            fg="white", 
            font=("Malgun Gothic", 9, "bold"),
            width=20
        )
        unreg_btn.pack(side="right", padx=20, expand=True)

        info_lbl = tk.Label(
            explorer_frame, 
            text="※ 등록 후 임의의 폴더를 우클릭하면 '과제 통합 및 명단 추출 실행' 메뉴가 활성화되어 자동 구동됩니다.", 
            font=("Malgun Gothic", 8), 
            fg="#7f8c8d"
        )
        info_lbl.pack(anchor="w", pady=2)

        # 실행 버튼
        self.run_btn = tk.Button(
            self.root, 
            text="통합 작업 시작", 
            command=self.start_process, 
            font=("Malgun Gothic", 10, "bold"), 
            bg="#2980b9", 
            fg="white", 
            height=2
        )
        self.run_btn.pack(fill="x", padx=15, pady=10)

        # 로그 출력 영역
        log_frame = tk.LabelFrame(self.root, text="진행 현황", font=("Malgun Gothic", 9, "bold"), padx=5, pady=5)
        log_frame.pack(fill="both", expand=True, padx=15, pady=5)

        self.log_area = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, height=10, font=("Consolas", 9))
        self.log_area.pack(fill="both", expand=True)

    def browse_source(self):
        selected = filedialog.askdirectory(title="학생 폴더들이 포함된 대상 폴더 선택")
        if selected:
            self.source_dir_var.set(os.path.abspath(selected))
            if not self.target_dir_var.get():
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
        """
        폴더 이름 구조분석 (예: 강상우-2026651101_10310027_assignment)
        이름과 학번을 분리하여 반환한다.
        """
        # 정규표현식을 통해 하이픈(-) 앞의 이름과 뒤의 학번(숫자)을 추출한다.
        match = re.match(r"^([^-]+)-([0-9]+)", folder_name)
        if match:
            name = match.group(1).strip()
            student_id = match.group(2).strip()
            return name, student_id
        return None, None

    # --- 우클릭 메뉴 등록 및 제어 로직 ---
    def register_menu(self):
        success, message = self.register_context_menu()
        if success:
            messagebox.showinfo("성공", message)
            self.log(f"[시스템] {message}")
        else:
            messagebox.showerror("오류", message)
            self.log(f"[시스템 오류] {message}")

    def unregister_menu(self):
        success, message = self.unregister_context_menu()
        if success:
            messagebox.showinfo("성공", message)
            self.log(f"[시스템] {message}")
        else:
            messagebox.showerror("오류", message)
            self.log(f"[시스템 오류] {message}")

    def register_context_menu(self):
        if sys.platform != 'win32':
            return False, "윈도우 운영체제(Windows)에서만 지원되는 기능입니다."
        try:
            import winreg
            
            # 실행 주체가 PyInstaller로 패킹된 .exe 인지 혹은 일반 .py 스크립트인지 구분하여 분석
            is_frozen = getattr(sys, 'frozen', False)
            if is_frozen:
                exe_path = os.path.abspath(sys.executable)
                cmd = f'"{exe_path}" "%1"'
            else:
                script_path = os.path.abspath(sys.argv[0])
                python_exe = sys.executable
                # 윈도우 창만 띄우기 위해 콘솔창이 생략되는 pythonw.exe 경로 매칭 시도
                python_w = python_exe.lower().replace("python.exe", "pythonw.exe")
                exe_to_use = python_w if os.path.exists(python_w) else python_exe
                cmd = f'"{exe_to_use}" "{script_path}" "%1"'

            # 관리자 권한 없이도 안전하게 등록 가능한 HKEY_CURRENT_USER 내의 경로 탐색 및 생성
            key_path = r"Software\Classes\Directory\shell\AssignmentManager"
            
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path) as key:
                winreg.SetValue(key, "", winreg.REG_SZ, "과제 통합 및 명단 추출 실행")
                # 우클릭 메뉴에 파이썬 기본 아이콘 또는 컴파일된 실행파일 아이콘 반영
                icon_source = sys.executable if is_frozen else python_exe
                winreg.SetValueEx(key, "Icon", 0, winreg.REG_SZ, icon_source)
                
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path + r"\command") as cmd_key:
                winreg.SetValue(cmd_key, "", winreg.REG_SZ, cmd)
                
            return True, "성공적으로 윈도우 탐색기 우클릭 메뉴에 등록되었습니다."
        except Exception as e:
            return False, f"등록 중 오류가 발생했습니다: {str(e)}"

    def unregister_context_menu(self):
        if sys.platform != 'win32':
            return False, "윈도우 운영체제(Windows)에서만 지원되는 기능입니다."
        try:
            import winreg
            key_path = r"Software\Classes\Directory\shell\AssignmentManager"
            
            # 생성된 하위 커맨드 및 메인 키 탐색 후 순차 제거
            try:
                winreg.DeleteKey(winreg.HKEY_CURRENT_USER, key_path + r"\command")
            except FileNotFoundError:
                pass
            
            try:
                winreg.DeleteKey(winreg.HKEY_CURRENT_USER, key_path)
            except FileNotFoundError:
                pass
                
            return True, "우클릭 메뉴에서 성공적으로 제거되었습니다."
        except Exception as e:
            return False, f"제거 중 오류가 발생했습니다: {str(e)}"

    def start_process(self):
        source_dir = self.source_dir_var.get().strip()
        target_dir = self.target_dir_var.get().strip()

        if not source_dir or not os.path.exists(source_dir):
            messagebox.showerror("오류", "유효한 대상 폴더 경로를 선택하십시오.")
            return

        if not target_dir:
            messagebox.showerror("오류", "저장할 폴더 경로를 입력하십시오.")
            return

        # 저장 폴더가 존재하지 않는 경우 자동 생성
        if not os.path.exists(target_dir):
            try:
                os.makedirs(target_dir)
                self.log(f"[알림] 저장 폴더가 존재하지 않아 새로 생성하였습니다: {target_dir}")
            except Exception as e:
                messagebox.showerror("오류", f"저장 폴더를 생성할 수 없습니다: {str(e)}")
                return

        self.log_area.delete("1.0", tk.END)
        self.log("================= 과제 통합 작업을 시작합니다 =================")
        self.log(f"대상 폴더: {source_dir}")
        self.log(f"저장 폴더: {target_dir}\n")

        student_list = []
        copy_count = 0
        folder_count = 0

        try:
            # 대상 폴더 하위 항목 검색
            subitems = os.listdir(source_dir)
            
            for item in subitems:
                item_path = os.path.join(source_dir, item)
                
                # 디렉터리이고 통합 타겟 디렉터리와 겹치지 않는 경우만 처리
                if os.path.isdir(item_path) and os.path.abspath(item_path) != os.path.abspath(target_dir):
                    name, student_id = self.parse_student_info(item)
                    
                    if name and student_id:
                        folder_count += 1
                        self.log(f"[분석 완료] 이름: {name} / 학번: {student_id} (폴더: {item})")
                        student_list.append({
                            "이름": name,
                            "학번": student_id,
                            "기존폴더명": item
                        })

                        # 폴더 내부의 모든 파일 검사 및 복사
                        for root_dir, _, files in os.walk(item_path):
                            for file in files:
                                file_path = os.path.join(root_dir, file)
                                
                                # 임시 파일이나 시스템 파일(.DS_Store, Desktop.ini 등) 제외
                                if file.startswith("~$") or file.lower() in [".ds_store", "desktop.ini"]:
                                    continue

                                if self.rename_files_var.get():
                                    new_file_name = f"[{name}_{student_id}] {file}"
                                else:
                                    new_file_name = file

                                dest_file_path = os.path.join(target_dir, new_file_name)

                                # 동일 파일명 존재 시 번호 부여 처리 (덮어쓰기 방지)
                                base, ext = os.path.splitext(new_file_name)
                                counter = 1
                                while os.path.exists(dest_file_path):
                                    dest_file_path = os.path.join(target_dir, f"{base}_{counter}{ext}")
                                    counter += 1

                                shutil.copy2(file_path, dest_file_path)
                                self.log(f"  └ 파일 복사 완료: {file} -> {os.path.basename(dest_file_path)}")
                                copy_count += 1
                    else:
                        self.log(f"[건너뜀] 학번 패턴 불일치 폴더: {item}")

            # CSV 파일 생성 작업
            if self.create_csv_var.get() and student_list:
                csv_path = os.path.join(target_dir, "학생명단_리스트.csv")
                
                # 한글 깨짐 방지를 위해 UTF-8-SIG 인코딩 사용
                with open(csv_path, mode="w", encoding="utf-8-sig", newline="") as f:
                    writer = csv.DictWriter(f, fieldnames=["이름", "학번", "기존폴더명"])
                    writer.writeheader()
                    for student in sorted(student_list, key=lambda x: x["이름"]):
                        writer.writerow(student)
                
                self.log(f"\n[성공] 학생 명단 CSV가 생성되었습니다: {os.path.basename(csv_path)}")

            self.log("\n================= 작업이 완료되었습니다 =================")
            self.log(f"총 처리된 학생 폴더 수: {folder_count}개")
            self.log(f"총 통합된 파일 수: {copy_count}개")
            
            messagebox.showinfo("성공", f"작업이 완료되었습니다.\n통합 파일: {copy_count}개\n학생 폴더: {folder_count}개")

        except Exception as e:
            self.log(f"\n[오류 발생] 작업 수행 중 문제가 발생하였습니다: {str(e)}")
            messagebox.showerror("오류", f"작업 수행 중 오류가 발생하였습니다:\n{str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = AssignmentManagerApp(root)
    root.mainloop()