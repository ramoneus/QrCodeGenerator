import re

import pytest

from main import generate_barcode, list_printers, print_images

PDF_PRINTER = "Microsoft Print to PDF"


def test_lists_installed_printers():
    printers, default = list_printers()
    assert isinstance(printers, list)
    assert all(isinstance(name, str) and name for name in printers)
    assert default in printers or not printers


@pytest.fixture
def pdf_printer():
    if PDF_PRINTER not in list_printers()[0]:
        pytest.skip(f"{PDF_PRINTER} is not installed")
    return PDF_PRINTER


def page_count(pdf):
    return len(re.findall(rb"/Type\s*/Page\b", pdf))


@pytest.mark.parametrize(("count", "columns", "rows", "pages"), [(1, 1, 1, 1), (5, 2, 2, 2), (24, 3, 8, 1), (25, 3, 8, 2)])
def test_prints_the_right_number_of_pages(pdf_printer, tmp_path, count, columns, rows, pages):
    images = [generate_barcode(f"INV-{i:04d}", "Code 128", scale=2) for i in range(count)]
    output = tmp_path / "labels.pdf"
    print_images(images, pdf_printer, columns=columns, rows=rows, output_file=str(output))

    pdf = output.read_bytes()
    assert pdf.startswith(b"%PDF")
    assert page_count(pdf) == pages
