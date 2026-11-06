import pytest
import zxingcpp

from main import BARCODE_TYPES, QR_CODE, generate_barcode, generate_qr

# What a scanner reads back from each type's example. Check digits are added by the app,
# and some types are reported in their full or GS1 form.
SCANNED = {
    QR_CODE: "https://example.com",
    "Data Matrix": "SN-2026-000123",
    "PDF417": "ATH-LHR 2026-11-01 Seat 14C",
    "Aztec": "TICKET-123456",
    "EAN-13": "5901234123457",
    "EAN-8": "96385074",
    "UPC-A": "0036000291452",
    "UPC-E": "0042100005264",
    "ISBN": "9783161484100",
    "GS1-128": "(01)09501101530003(10)ABC123",
    "ITF-14": "09501101530003",
    "GS1 DataBar": "(01)09501101530003",
    "GS1 DataBar Expanded": "(01)09501101530003(3103)000123",
    "Code 128": "ABC-12345",
    "Code 39": "CODE-39",
    "Code 93": "CODE-93",
    "Interleaved 2 of 5": "12345678",
    "Codabar": "A123456B",
    "PZN": "-01234562",
}


def make(barcode_type, data=None, **options):
    data = data or BARCODE_TYPES[barcode_type].example
    if barcode_type == QR_CODE:
        return generate_qr(data, **options).get_image()
    return generate_barcode(data, barcode_type, **options)


def scan(image):
    result = zxingcpp.read_barcode(image.convert("L"))
    return result.text if result else None


def test_every_type_has_an_expected_scan():
    assert set(SCANNED) == set(BARCODE_TYPES)


@pytest.mark.parametrize("barcode_type", list(BARCODE_TYPES))
def test_every_example_scans_back(barcode_type):
    assert scan(make(barcode_type)) == SCANNED[barcode_type]


@pytest.mark.parametrize("barcode_type", ["Code 128", "EAN-13", "Data Matrix", "PDF417"])
@pytest.mark.parametrize("scale", [1, 2, 5, 10])
def test_codes_scan_at_every_size(barcode_type, scale):
    assert scan(make(barcode_type, scale=scale)) == SCANNED[barcode_type]


def test_qr_code_scans_long_text():
    text = "https://example.com/" + "a" * 500
    assert scan(make(QR_CODE, text)) == text


@pytest.mark.parametrize(
    ("barcode_type", "data"),
    [("EAN-13", "abc"), ("Codabar", "12345"), ("EAN-8", "12345678901")],
)
def test_invalid_data_raises_a_readable_error(barcode_type, data):
    with pytest.raises(ValueError) as error:
        generate_barcode(data, barcode_type)
    message = str(error.value)
    assert message
    # zxing's "Error 5: ... (retval: 5)" wrapping is removed.
    assert not message.startswith("Error ")
    assert "retval" not in message


def test_linear_barcodes_never_go_below_two_pixels_per_bar():
    # At 1 pixel per bar zxing draws no text under the bars, so the app uses 2.
    assert make("Code 128", scale=1).size == make("Code 128", scale=2).size


def test_linear_barcodes_get_a_quiet_zone_above_and_below():
    image = make("Code 128", scale=2)
    for y in (0, image.height - 1):
        row = image.crop((0, y, image.width, y + 1))
        assert row.getextrema() == (255, 255)


def test_matrix_codes_scale_with_the_size_setting():
    small, large = make("Data Matrix", scale=2), make("Data Matrix", scale=6)
    assert large.width == 3 * small.width


def bar_rows(image):
    """Height of the bars: the longest run of identical rows that mix black and white."""
    data, width = image.tobytes(), image.width
    rows = [data[y * width:(y + 1) * width] for y in range(image.height)]
    longest = run = 0
    for y, row in enumerate(rows):
        mixed = 0 in row and 255 in row
        run = run + 1 if mixed and y and row == rows[y - 1] else int(mixed)
        longest = max(longest, run)
    return longest


class TestBarHeight:
    @pytest.mark.parametrize("bar_height", [20, 140, 300])
    def test_bars_are_exactly_the_height_asked_for(self, bar_height):
        assert bar_rows(make("Code 128", scale=2, bar_height=bar_height)) == bar_height

    def test_changes_only_the_bar_height(self):
        short = make("Code 128", scale=2, bar_height=40)
        tall = make("Code 128", scale=2, bar_height=140)
        assert tall.width == short.width
        assert tall.height - short.height == 100

    def test_keeps_the_text_under_the_bars(self):
        short = make("Code 128", scale=2, bar_height=40)
        tall = make("Code 128", scale=2, bar_height=140)
        text_height = 30
        bottom = lambda image: image.crop((0, image.height - text_height, image.width, image.height)).tobytes()  # noqa: E731
        assert bottom(short) == bottom(tall)

    @pytest.mark.parametrize("barcode_type", ["Code 128", "EAN-13", "ITF-14", "GS1 DataBar"])
    @pytest.mark.parametrize("bar_height", [20, 300])
    def test_still_scans_at_any_height(self, barcode_type, bar_height):
        assert scan(make(barcode_type, scale=3, bar_height=bar_height)) == SCANNED[barcode_type]

    def test_is_ignored_for_2d_codes(self):
        assert make("Data Matrix", scale=4, bar_height=500).size == make("Data Matrix", scale=4).size
