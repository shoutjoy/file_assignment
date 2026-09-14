from pathlib import Path
import tempfile
import unittest

from gyeonggi_submission import (
    ONLINE_TEXT_NAME,
    merge_gyeonggi_submissions,
    parse_submission_folder,
)


class GyeonggiSubmissionTests(unittest.TestCase):
    def test_folder_pattern(self):
        self.assertEqual(
            parse_submission_folder("송민정_1699618_assignsubmission_onlinetext_"),
            ("송민정", "1699618", "onlinetext"),
        )
        self.assertEqual(
            parse_submission_folder("김지혜_1699620_assignsubmission_file_"),
            ("김지혜", "1699620", "file"),
        )
        self.assertIsNone(parse_submission_folder("송민정-1699618"))

    def test_merge_text_and_files_without_overwrite(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "source"
            target = source / "통합_과제"
            target.mkdir(parents=True)
            text_folder = source / "송민정_1699618_assignsubmission_onlinetext_"
            text_folder.mkdir()
            (text_folder / "답변.html").write_text(
                "<p>첫 번째 &amp; 답변</p><script>제외</script><p>다음 줄</p>", encoding="utf-8"
            )
            (text_folder / "추가.txt").write_text("추가 내용", encoding="utf-8")
            file_folder = source / "김지혜_1699620_assignsubmission_file_"
            file_folder.mkdir()
            nested = file_folder / "nested"
            nested.mkdir()
            (nested / "과제.pdf").write_bytes(b"new")
            (target / "[김지혜_1699620] 과제.pdf").write_bytes(b"old")

            students, folders, copied, texts = merge_gyeonggi_submissions(
                str(source), str(target), True, lambda message: None
            )

            self.assertEqual((folders, copied, texts), (2, 1, 2))
            self.assertEqual(len(students), 2)
            self.assertEqual((target / "[김지혜_1699620] 과제.pdf").read_bytes(), b"old")
            self.assertEqual((target / "[김지혜_1699620] 과제_1.pdf").read_bytes(), b"new")
            md = (target / ONLINE_TEXT_NAME).read_text(encoding="utf-8")
            self.assertEqual(md.count("## 송민정_1699618"), 1)
            self.assertIn("첫 번째 & 답변\n다음 줄", md)
            self.assertIn("추가 내용", md)
            self.assertNotIn("제외", md)

    def test_one_csv_student_for_both_submission_types_and_sorted_text(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "source"
            target = source / "통합_과제"
            target.mkdir(parents=True)
            for folder_name, filename, content in (
                ("송민정_1699618_assignsubmission_onlinetext_", "글.txt", "송민정 글"),
                ("김지혜_1699620_assignsubmission_onlinetext_", "글.txt", "김지혜 글"),
                ("송민정_1699618_assignsubmission_file_", "과제.pdf", b"PDF"),
            ):
                folder = source / folder_name
                folder.mkdir()
                if isinstance(content, bytes):
                    (folder / filename).write_bytes(content)
                else:
                    (folder / filename).write_text(content, encoding="utf-8")

            students, folders, copied, texts = merge_gyeonggi_submissions(
                str(source), str(target), False, lambda message: None
            )

            self.assertEqual((folders, copied, texts), (3, 1, 2))
            self.assertEqual(len(students), 2)
            song = next(row for row in students if row["이름"] == "송민정")
            self.assertIn("assignsubmission_file_", song["기존폴더명"])
            self.assertIn("assignsubmission_onlinetext_", song["기존폴더명"])
            md = (target / ONLINE_TEXT_NAME).read_text(encoding="utf-8")
            self.assertLess(md.index("## 김지혜_1699620"), md.index("## 송민정_1699618"))
            self.assertEqual((target / "과제.pdf").read_bytes(), b"PDF")


if __name__ == "__main__":
    unittest.main()
