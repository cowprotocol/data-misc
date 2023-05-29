import os
import unittest

from src.missing_tokens import replace_line


class TestAppendToFile(unittest.TestCase):
    def test_append_to_file(self):
        test_file = "./out/test_file.txt"
        try:
            os.mkdir("./out")
            open(test_file, "x")
        except FileExistsError:
            pass

        f = open(test_file, "a")
        file_lines = ["First Line\n", "Second Line\n"]
        f.write("".join(file_lines))
        f.close()

        with open(test_file, "r", encoding="utf-8") as file:
            self.assertEqual(file_lines, file.readlines())

        for i, old_line in enumerate(file_lines):
            new_line = f"New Line {i + 1}\n"
            replace_line(old_line, new_line, test_file)

            file_lines[i] = new_line
            with open(test_file, "r", encoding="utf-8") as file:
                self.assertEqual(file_lines, file.readlines())
        os.remove(test_file)


if __name__ == "__main__":
    unittest.main()
