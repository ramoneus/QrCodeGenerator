import openpyxl
import pytest

from gui import _file_name
from main import MAX_SEQUENCE, _cell_text, make_sequence, read_excel


class TestMakeSequence:
    def test_counts_up(self):
        assert make_sequence(1, 4) == ["1", "2", "3", "4"]

    def test_adds_prefix_suffix_and_leading_zeros(self):
        assert make_sequence(1, 3, prefix="INV-", suffix="-A", digits=4) == ["INV-0001-A", "INV-0002-A", "INV-0003-A"]

    def test_never_cuts_numbers_longer_than_the_minimum(self):
        assert make_sequence(99, 101, digits=2) == ["99", "100", "101"]

    def test_counts_down_when_start_is_bigger(self):
        assert make_sequence(5, 1, step=2) == ["5", "3", "1"]

    def test_step_can_skip_the_end(self):
        assert make_sequence(0, 10, step=4) == ["0", "4", "8"]

    def test_single_value(self):
        assert make_sequence(7, 7) == ["7"]

    @pytest.mark.parametrize("step", [0, -1])
    def test_rejects_a_step_below_one(self, step):
        with pytest.raises(ValueError, match="Step"):
            make_sequence(1, 10, step=step)

    def test_allows_the_maximum_number_of_values(self):
        assert len(make_sequence(1, MAX_SEQUENCE)) == MAX_SEQUENCE

    def test_rejects_more_than_the_maximum(self):
        with pytest.raises(ValueError, match=str(MAX_SEQUENCE)):
            make_sequence(1, MAX_SEQUENCE + 1)


class TestCellText:
    @pytest.mark.parametrize(
        ("value", "text"),
        [
            (None, ""),
            (12345, "12345"),
            # Excel stores every number as a float; whole numbers must not get a ".0".
            (5901234123457.0, "5901234123457"),
            (12.5, "12.5"),
            ("  ABC-1  ", "ABC-1"),
            ("00123", "00123"),
        ],
    )
    def test_converts_cells_to_text(self, value, text):
        assert _cell_text(value) == text


class TestReadExcel:
    def write(self, tmp_path, rows):
        workbook = openpyxl.Workbook()
        for row in rows:
            workbook.active.append(row)
        path = tmp_path / "codes.xlsx"
        workbook.save(path)
        return path

    def test_reads_each_column_top_row_first(self, tmp_path):
        path = self.write(tmp_path, [["SKU", "EAN"], ["A-1", 5901234123457], ["A-2", 4006381333931]])
        assert read_excel(path) == {
            "A": ["SKU", "A-1", "A-2"],
            "B": ["EAN", "5901234123457", "4006381333931"],
        }

    def test_fills_short_rows_and_empty_cells_with_blanks(self, tmp_path):
        path = self.write(tmp_path, [["one"], ["two", None, "x"]])
        assert read_excel(path) == {"A": ["one", "two"], "B": ["", ""], "C": ["", "x"]}

    def test_keeps_leading_zeros_stored_as_text(self, tmp_path):
        path = self.write(tmp_path, [["0012345"]])
        assert read_excel(path) == {"A": ["0012345"]}

    def test_only_reads_the_first_sheet(self, tmp_path):
        workbook = openpyxl.Workbook()
        workbook.active.append(["first"])
        workbook.create_sheet("Other").append(["second"])
        path = tmp_path / "two-sheets.xlsx"
        workbook.save(path)
        assert read_excel(path) == {"A": ["first"]}

    def test_an_empty_sheet_has_no_columns(self, tmp_path):
        assert read_excel(self.write(tmp_path, [])) == {}


class TestFileName:
    @pytest.mark.parametrize(
        ("value", "name"),
        [
            ("INV-0001", "INV-0001"),
            ("https://example.com/a?b", "https_example.com_a_b"),
            ('a<b>c"d|e*f', "a_b_c_d_e_f"),
            ("two  words", "two_words"),
            ("..hidden..", "hidden"),
            ("///", "code"),
        ],
    )
    def test_makes_values_safe_for_windows_file_names(self, value, name):
        assert _file_name(value) == name

    def test_limits_the_length(self):
        assert len(_file_name("x" * 200)) == 80
