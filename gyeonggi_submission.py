"""경기대 과제 다운로드 폴더의 온라인 글과 첨부파일 통합."""

from html.parser import HTMLParser
import os
import re
import shutil


FOLDER_PATTERN = re.compile(
    r"^(.+)_([0-9]+)_assignsubmission_(onlinetext|file)(?:_.*)?$",
    re.IGNORECASE,
)
TEXT_EXTENSIONS = {".txt", ".text", ".md", ".markdown", ".html", ".htm"}
IGNORED_FILES = {".ds_store", "desktop.ini"}
ONLINE_TEXT_NAME = "온라인텍스트_통합.md"


def parse_submission_folder(folder_name):
    match = FOLDER_PATTERN.fullmatch(folder_name)
    if not match:
        return None
    name, student_id, kind = match.groups()
    if not name.strip():
        return None
    return name.strip(), student_id, kind.lower()


class _TextFromHTML(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.hidden = 0

    def handle_starttag(self, tag, attrs):
        if tag in {"head", "script", "style"}:
            self.hidden += 1
        elif tag in {"br", "p", "div", "li", "tr", "h1", "h2", "h3"}:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in {"head", "script", "style"}:
            self.hidden = max(0, self.hidden - 1)
        elif tag in {"p", "div", "li", "tr", "h1", "h2", "h3"}:
            self.parts.append("\n")

    def handle_data(self, data):
        if not self.hidden:
            self.parts.append(data)

    def text(self):
        lines = [line.strip() for line in "".join(self.parts).splitlines()]
        return "\n".join(line for line in lines if line)


def read_submission_text(path):
    with open(path, "rb") as source:
        data = source.read()
    encodings = ("utf-16",) if data.startswith((b"\xff\xfe", b"\xfe\xff")) else ("utf-8-sig", "cp949")
    for encoding in encodings:
        try:
            content = data.decode(encoding)
            break
        except UnicodeError:
            continue
    else:
        raise UnicodeError(f"텍스트 인코딩을 판별할 수 없습니다: {path}")
    if os.path.splitext(path)[1].lower() in {".html", ".htm"}:
        parser = _TextFromHTML()
        parser.feed(content)
        return parser.text()
    return content.strip()


def submission_files(folder, excluded_dir=None):
    for root, dirs, files in os.walk(folder):
        dirs[:] = sorted(
            d for d in dirs
            if not excluded_dir or os.path.normcase(os.path.abspath(os.path.join(root, d)))
            != excluded_dir
        )
        for filename in sorted(files):
            if filename.startswith("~$") or filename.lower() in IGNORED_FILES:
                continue
            yield os.path.join(root, filename)


def merge_gyeonggi_submissions(source_dir, target_dir, rename_files, log):
    """Return (unique students, processed folders, copied files, online texts)."""
    target_abs = os.path.normcase(os.path.abspath(target_dir))
    students = {}
    folders = 0
    copied = 0
    online_texts = {}

    for item in sorted(os.listdir(source_dir)):
        item_path = os.path.join(source_dir, item)
        if not os.path.isdir(item_path) or os.path.normcase(os.path.abspath(item_path)) == target_abs:
            continue
        parsed = parse_submission_folder(item)
        if not parsed:
            log(f"[건너뜀] 경기대 제출 폴더 패턴 불일치: {item}")
            continue
        name, student_id, kind = parsed
        folders += 1
        students.setdefault((name, student_id), []).append(item)
        log(f"[분석 완료] 이름: {name} / 학번: {student_id} / 유형: {kind}")

        for path in submission_files(item_path, target_abs):
            filename = os.path.basename(path)
            if kind == "onlinetext":
                if os.path.splitext(filename)[1].lower() not in TEXT_EXTENSIONS:
                    log(f"  └ [건너뜀] 온라인 글이 아닌 파일: {filename}")
                    continue
                content = read_submission_text(path)
                if content:
                    online_texts.setdefault((name, student_id), []).append(content)
                    log(f"  └ 온라인 글 추출: {filename}")
            else:
                output_name = f"[{name}_{student_id}] {filename}" if rename_files else filename
                base, ext = os.path.splitext(output_name)
                destination = os.path.join(target_dir, output_name)
                counter = 1
                while os.path.exists(destination) or os.path.basename(destination) == ONLINE_TEXT_NAME:
                    destination = os.path.join(target_dir, f"{base}_{counter}{ext}")
                    counter += 1
                shutil.copy2(path, destination)
                copied += 1
                log(f"  └ 파일 복사 완료: {filename} -> {os.path.basename(destination)}")

    if online_texts:
        md_path = os.path.join(target_dir, ONLINE_TEXT_NAME)
        with open(md_path, "w", encoding="utf-8") as output:
            for (name, student_id), contents in sorted(online_texts.items()):
                output.write(f"## {name}_{student_id}\n\n")
                output.write("\n\n".join(contents) + "\n\n")
        log(f"[성공] 온라인 글 {sum(map(len, online_texts.values()))}개를 {ONLINE_TEXT_NAME}에 통합했습니다.")

    student_list = [
        {"이름": name, "학번": student_id, "기존폴더명": "; ".join(folder_names)}
        for (name, student_id), folder_names in sorted(students.items())
    ]
    return student_list, folders, copied, sum(map(len, online_texts.values()))
