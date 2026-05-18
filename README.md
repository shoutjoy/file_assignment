# 과제 통합 및 학생 명단 추출 (File Assignment Manager)

Windows용 도구입니다. **주차별·학생별로 나뉜 과제 폴더** 안의 파일을 **한 폴더로 모으고**, 필요하면 **파일 이름에 학생 이름·학번을 붙이며**, **학생 명단 CSV**를 함께 만듭니다.

---

## 활용 목적

### 연세대학교 learnUS — 과제 점검용 다운로드

**연세대학교 learnUS**에서 과제를 **학생별·폴더별로 받아 둔 자료**를, 채점·점검하기 쉽게 **한 폴더로 모을 때** 쓰기 좋습니다.

- learnUS에서 내려받은 구조가 **학생마다 하위 폴더**로 나뉘어 있을 때, 「대상 폴더」에 그 다운로드 폴더를 지정합니다.
- **이름·학번 접두어**와 **학생 명단 CSV**로 누가 제출했는지 파일만 보고도 구분할 수 있습니다.
- 통합본을 엑셀·PDF 뷰어·일괄 검색 등 **과제 점검 워크플로**에 바로 넘기기 편합니다.

> 폴더 이름이 **`이름-학번`** 형식이어야 자동 인식됩니다. learnUS에서 받은 폴더명이 다르면, 미리 이름을 맞추거나 패턴에 맞게 정리한 뒤 실행하세요.

### 그 밖의 자료 — 폴더별 저장분을 한곳으로 정리

수업 과제뿐 아니라, **여러 하위 폴더에 흩어져 저장된 자료**를 **하나의 폴더로 모아야 할 때**에도 유용합니다.

- 프로젝트·실험·행정 자료처럼 **폴더마다 나뉜 파일**을 한 디렉터리에 모을 때  
- 백업·공유·검색 전에 **중복 이름은 자동으로 `_1`, `_2` …** 로 피하면서 복사할 때  
- 하위 폴더를 유지하지 않고 **파일만 평탄하게(flat)** 모을 때  

학생 명단 CSV·이름 접두어 옵션은 learnUS 과제 점검에 맞춘 기능이지만, **「파일 이름 접두어」와 CSV 생성을 끄면** 단순히 **폴더 통합 도구**로도 쓸 수 있습니다. (이때는 하위 폴더 이름이 `이름-학번` 패턴일 때만 해당 폴더가 처리됩니다.)

---

## 제작

| | |
| --- | --- |
| **제작자** | 박중희 교수 |
| **소속** | 연세대학교 심리학과 겸임교수 |
| **문의** | [shoutjoy1@yonsei.ac.kr](mailto:shoutjoy1@yonsei.ac.kr) |

**저장소**: [github.com/shoutjoy/file_assignment](https://github.com/shoutjoy/file_assignment)

---

## 이 앱이 하는 일

### 핵심 기능

1. **과제 파일 통합**  
   「대상 폴더」 아래 **학생별 하위 폴더**에 들어 있는 파일을 모두 찾아, 「저장할 폴더」**한 곳**으로 복사합니다. 하위 폴더 구조는 펼쳐서(재귀적으로) 파일만 가져옵니다.

2. **학생 폴더 이름 인식**  
   폴더 이름이 **`이름-학번`** 형식일 때만 처리합니다.  
   - 예: `홍길동-20261234` → 이름 `홍길동`, 학번 `20261234`  
   - 정규식: 맨 앞 `이름` + `-` + **숫자로만 된 학번**  
   - 패턴에 맞지 않는 폴더는 **건너뛰고** 진행 현황에 기록합니다.

3. **파일 이름 변경 (선택)**  
   옵션을 켜면 복사할 때 파일명 앞에 **`[이름_학번]`** 을 붙입니다.  
   - 예: `과제.pdf` → `[홍길동_20261234] 과제.pdf`  
   - 같은 이름이 이미 있으면 `_1`, `_2` … 를 붙여 **덮어쓰지 않습니다**.

4. **학생 명단 CSV (선택)**  
   처리된 학생에 대해 저장 폴더에 **`학생명단_리스트.csv`** 를 만듭니다.  
   - 열: `이름`, `학번`, `기존폴더명`  
   - UTF-8 BOM(엑셀에서 한글이 깨지지 않도록)  
   - 이름 기준으로 정렬

5. **불필요 파일 제외**  
   복사하지 않는 파일: `~$`로 시작하는 임시 파일, `.ds_store`, `desktop.ini`

6. **저장 폴더 자동 생성**  
   저장 경로가 없으면 만들고 로그에 알립니다. 대상 폴더와 **같은 경로**인 하위 폴더(통합본 폴더 자신)는 복사 대상에서 제외합니다.

### 화면 구성

| 탭 | 내용 |
| --- | --- |
| **통합** | 경로 설정, 실행 옵션, **통합 작업 시작**, 진행 현황 로그 |
| **설정** | Program Files 설치, 탐색기 우클릭 메뉴, 시작 메뉴 바로가기 |

### 설정 탭 부가 기능

- **앱 설치**: `FileAssignmentManager.exe` 실행 시 `C:\Program Files\FileAssignmentManager` 로 복사, 시작 메뉴·작업 표시줄용 바로가기(선택)
- **윈도우 탐색기 통합**: 폴더·폴더 빈 곳 우클릭 → 「과제 통합 및 명단 추출」 (해당 폴더를 대상으로 앱 실행)
- **시작 메뉴 바로가기**: 통합 후 창 유지(`--keep-open`) / 통합 완료 후 종료(`--close-after-run`)

통합 탭의 **「통합 완료 후 프로그램 종료」** 는 `%LOCALAPPDATA%\FileAssignmentManager\settings.json` 에 저장됩니다.

---

## 폴더 준비 예시

```
대상 폴더 (주차별 과제)/
├── 홍길동-20261234/
│   ├── report.pdf
│   └── code.zip
├── 김연세-20269876/
│   └── 과제.hwp
└── 잘못된이름폴더/          ← 패턴 불일치 → 건너뜀
    └── file.txt
```

실행 후 **저장할 폴더** 예:

```
통합_과제/
├── [홍길동_20261234] report.pdf
├── [홍길동_20261234] code.zip
├── [김연세_20269876] 과제.hwp
└── 학생명단_리스트.csv
```

---

## 다운로드 방법

### 바로 가기 (링크)

| 받는 방법 | 링크 |
| --- | --- |
| **릴리스 최신본** (태그가 올라온 뒤 exe·dist ZIP) | [github.com/shoutjoy/file_assignment/releases/latest](https://github.com/shoutjoy/file_assignment/releases/latest) |
| **릴리스에서 EXE만** (파일명 고정, latest) | [`FileAssignmentManager.exe` 다운로드](https://github.com/shoutjoy/file_assignment/releases/latest/download/FileAssignmentManager.exe) |
| **릴리스에서 dist 폴더 ZIP** (통째로 받기, latest) | [`FileAssignmentManager-dist.zip` 다운로드](https://github.com/shoutjoy/file_assignment/releases/latest/download/FileAssignmentManager-dist.zip) |
| **Actions 빌드 목록** (매 푸시마다 생성되는 Artifact) | [Build Windows EXE 워크플로](https://github.com/shoutjoy/file_assignment/actions/workflows/build-windows-exe.yml) |

> `releases/latest/download/...` 주소는 **GitHub에 릴리스와 해당 파일이 올라가 있어야** 열립니다. 아직 릴리스가 없으면 아래 **방법 2**로 Actions **Artifacts**에서 받으세요.

### 방법 1 — GitHub에서 저장소 받기 (소스 + 직접 실행)

1. 브라우저에서 [https://github.com/shoutjoy/file_assignment](https://github.com/shoutjoy/file_assignment) 를 엽니다.  
2. 초록색 **Code** → **Download ZIP** 으로 전체를 받거나, Git이 있으면:

   ```bash
   git clone git@github.com:shoutjoy/file_assignment.git
   ```

3. 압축을 풀거나 clone한 폴더가 `File_assignment_manager`(또는 `file_assignment`) 입니다.

### 방법 2 — GitHub Actions에서 받기 (권장)

저장소에 **GitHub Actions** 워크플로(`Build Windows EXE`)가 있으면, **main/master에 푸시될 때마다** `dist` 폴더 내용이 빌드되어 **Artifacts**로 올라갑니다. Python 설치 없이 최신 빌드를 받을 때 편합니다.

1. 위 표의 **[Build Windows EXE 워크플로](https://github.com/shoutjoy/file_assignment/actions/workflows/build-windows-exe.yml)** 링크로 이동하거나, 저장소 **Actions** 탭에서 같은 워크플로를 엽니다.
2. **초록 체크가 있는 최근 실행**을 클릭합니다.
3. 페이지 하단 **Artifacts** 에서 **`FileAssignmentManager-dist`** 를 내려받습니다 (ZIP).
4. ZIP을 풀면 **빌드 결과물(`dist`와 동일한 구성)** 이 들어 있습니다. 보통 **`FileAssignmentManager.exe`** 한 개이며, PyInstaller가 다른 파일을 두면 함께 포함됩니다.

**릴리스에서 받기:** `v1.0.0` 같이 **`v`로 시작하는 태그**를 push하면, 워크플로가 **`FileAssignmentManager.exe`** 와 **`FileAssignmentManager-dist.zip`**(dist 통째)을 **Releases**에 올립니다. [Releases](https://github.com/shoutjoy/file_assignment/releases) 의 **Assets** 또는 위 표의 **바로 가기** 링크를 이용하세요.

### 방법 3 — EXE만 쓰고 싶을 때 (`dist`가 저장소에 있을 때)

EXE는 저장소에 **`dist` 폴더**로 올려 두는 경우가 있습니다(관리자가 빌드·커밋한 뒤).

1. GitHub에서 **`dist`** 폴더로 이동  
2. **`FileAssignmentManager.exe`** 클릭 → **Download raw file** (또는 **⋯ → Download**)

`dist`가 없으면 **방법 2**(Actions)·**방법 4**(로컬 빌드)를 이용하거나, `FileAssignmentManager.spec` 으로 PyInstaller 빌드로 `dist\FileAssignmentManager.exe` 를 만듭니다.

### 방법 4 — 로컬에서 EXE 빌드

저장소를 받은 뒤, **Windows**에서 Python 3.9+ 와 `build_exe.cmd` 가 있는 폴더로 이동:

```bash
build_exe.cmd
```

또는:

```bash
python -m pip install -r requirements-build.txt
python -m PyInstaller --noconfirm FileAssignmentManager.spec
```

완료 후 **`dist\FileAssignmentManager.exe`** 가 생성됩니다.

---

## 실행 방법

### A) EXE로 실행 (Python 설치 불필요)

`dist\FileAssignmentManager.exe` 를 더블클릭합니다.

### B) Python 스크립트로 실행

저장소 루트에서:

```bash
python file_assignment_manager.py
```

또는 **`실행.bat`** 을 더블클릭합니다 (PATH에 `python` 이 있어야 합니다).

### C) 특정 과제 폴더를 열어서 실행

명령줄에 **대상 폴더 경로**를 넘기면, 통합 탭의 「대상 폴더」가 그 경로로 채워지고, 저장 폴더는 기본으로 `...\통합_과제` 로 잡힙니다.

```bash
python file_assignment_manager.py "D:\과제\3주차"
```

탐색기 우클릭 메뉴로 등록해 두었다면(설정 탭), 폴더에서 우클릭만 해도 같은 효과입니다.

### D) 통합 후 자동 종료 / 창 유지

시작 메뉴 바로가기 또는 명령줄 인자:

| 인자 | 동작 |
| --- | --- |
| `--keep-open` | 통합이 끝나도 창을 유지 |
| `--close-after-run` | 통합이 끝나면 프로그램 종료 |

통합 탭의 **「통합 완료 후 프로그램 종료」** 체크와 동일한 설정이 설정 파일에 저장됩니다.

---

## 사용 순서 (통합 탭)

1. 프로그램을 실행합니다.  
2. **대상 폴더 (주차별 과제)**  
   학생별 하위 폴더가 들어 있는 폴더를 **찾아보기**로 지정합니다.  
3. **저장할 폴더 (통합본)**  
   모은 파일을 둘 폴더를 지정합니다. 비우지 않았다면 대상 폴더 아래 `통합_과제` 가 기본값입니다.  
4. **실행 옵션**  
   - 파일 이름에 학생 이름·학번 추가  
   - 학생 명단 CSV 생성  
   - 통합 완료 후 프로그램 종료  
5. **통합 작업 시작** 을 누릅니다.  
6. **진행 현황** 에서 복사·건너뜀·CSV 생성 결과를 확인합니다.  
7. 완료 메시지 후 저장 폴더에서 통합 파일과 `학생명단_리스트.csv` 를 확인합니다.

---

## 설치 (선택, 설정 탭)

- **EXE로 실행 중**일 때만 `Program Files\FileAssignmentManager` 로 복사하는 **설치** 버튼이 동작합니다.  
- **관리자 권한**이 필요할 수 있습니다.  
- **install.cmd** / **install.ps1** 로 스크립트 설치를 시도할 수도 있습니다(환경에 따라 다름).  
- 제거: **uninstall.cmd** / **uninstall.ps1**

---

## 필요 환경

| 실행 방식 | 필요 사항 |
| --- | --- |
| **EXE** | Windows 10 / 11 (64비트 권장) |
| **스크립트** | Python 3.9+ (tkinter 포함), Windows |

macOS / Linux 는 탐색기·레지스트리·바로가기 기능이 없어 **Windows 전용**으로 보시면 됩니다.

---

## 문제 해결

| 증상 | 확인 |
| --- | --- |
| 학생 폴더가 모두 「건너뜀」 | 폴더 이름이 **`이름-학번`**(학번은 숫자만) 인지 확인 |
| 탐색기 우클릭에 메뉴 없음 | 설정 탭에서 **등록** 후, Windows 11은 **추가 옵션 표시** 또는 Shift+우클릭 |
| Program Files 설치 실패 | **관리자 권한으로 실행** |
| `실행.bat` 오류 | `python --version` 으로 PATH에 Python 설치 여부 확인 |

---

## 파일 구성 (참고)

| 파일 | 설명 |
| --- | --- |
| `file_assignment_manager.py` | 메인 프로그램 |
| `FileAssignmentManager.spec` | PyInstaller 빌드 설정 |
| `build_exe.cmd` | EXE 빌드 배치 |
| `실행.bat` | Python으로 앱 실행 |
| `install.cmd` / `uninstall.cmd` | 설치·제거 보조 |

---

## 문의

기능 문의·오류 보고: **shoutjoy1@yonsei.ac.kr**
