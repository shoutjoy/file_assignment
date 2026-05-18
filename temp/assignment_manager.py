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
        self.root.geometry("650x550")
        self.root.resizable(True, True)

        # 상태 변수 설정
        self.source_dir_var = tk.StringVar()
        self.target_dir_var = tk.StringVar()
        self.rename_files_var = tk.BooleanVar(value=True)
        self.create_csv_var = tk.BooleanVar(value=True)

        # 윈도우 우클릭 메뉴 또는 인수로 경로가 전달되었는지 확인
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

        self.log_area = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, height=12, font=("Consolas", 9))
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
```
eof

---

### 윈도우 마우스 우클릭 메뉴(Context Menu) 연동 가이드

작성된 파이썬 스크립트를 마우스 우클릭으로 즉시 실행하기 위해 다음과 같은 두 가지 방법 중 하나를 선택하여 적용할 수 있다.

#### 방법 1: "보내기(SendTo)" 메뉴 등록 (가장 간편하고 안전한 방법)
1. 윈도우 실행 창(`Win + R`)을 열고 `shell:sendto`를 입력한 뒤 엔터를 누른다.
2. 실행된 폴더(SendTo 폴더) 내부에 새로운 바로 가기 파일이나 배치 파일(`.bat`)을 생성한다.
3. 배치 파일 내용을 다음과 같이 작성하여 저장한다:
   ```cmd
   @echo off
   python "C:\경로\assignment_manager.py" "%1"
   ```
   *(단, `C:\경로\assignment_manager.py` 부분은 실제 스크립트가 저장된 전체 경로로 변경해야 한다.)*
4. 이후 임의의 과제 폴더(예: `9주차과제`)를 **마우스 우클릭 -> 보내기(N) -> 작성한 배치 파일명** 순으로 선택하면, 해당 폴더의 경로가 자동으로 입력된 채로 프로그램이 바로 실행된다.

#### 방법 2: 레지스트리(Registry) 직접 등록 (폴더 우클릭 시 즉시 실행)
1. 메모장을 열고 아래의 레지스트리 스크립트 내용을 복사한다.
   ```reg
   Windows Registry Editor Version 5.00

   [HKEY_CLASSES_ROOT\Directory\shell\AssignmentCompressor]
   @="과제 통합 프로그램으로 열기"

   [HKEY_CLASSES_ROOT\Directory\shell\AssignmentCompressor\command]
   @="python \"C:\\경로\\assignment_manager.py\" \"%1\""