# QR Code Generator

A simple Python script that turns a URL into a QR code image.

## Setup

```bash
pip install -r requirements.txt
```

## Usage

```bash
python main.py
```

Enter a URL when prompted. The QR code is saved as `qrcode.png` in the current folder.

### Graphical interface

```bash
python gui.py
```

Type text or numbers, pick a type, click **Generate**, then **Save image** to export a PNG. Until you generate your own code, the preview shows an example of the selected type, and a short hint under the type list says what data it accepts.

Supported types:

| Group | Types |
| --- | --- |
| 2D | QR Code, Data Matrix, PDF417, Aztec |
| Retail | EAN-13, EAN-8, UPC-A, UPC-E, ISBN |
| Logistics (GS1) | GS1-128, ITF-14, GS1 DataBar, GS1 DataBar Expanded |
| General | Code 128, Code 39, Code 93, Interleaved 2 of 5, Codabar |
| Pharma | PZN |

- **Size** sets the width of the thinnest bar (or each square of a 2D code); **Height** sets the bar height for linear barcodes. Bars are always whole pixels wide, so the codes stay scannable at every size.
- **Import Excel…** loads the first sheet of an `.xlsx` file. Pick a column, click a value to preview it, or use **Save all as PNG…** to export every value to a folder. Invalid values are skipped and listed.
- **Number sequence** creates the list for you: From, To, Step, Prefix, Suffix and Min digits (e.g. `INV-` and 4 digits gives `INV-0001`, `INV-0002`, …).
- **Print…** prints the current code and **Print all…** prints every value in the list. Choose the printer, one code per page/label (label printers) or several per page (sticker sheets), and the copies of each. The page or label size comes from the printer's settings in Windows; each code is enlarged to fill it while keeping the bars exact.

Tip: numbers with leading zeros (e.g. `0123…`) must be stored as text in Excel, otherwise Excel drops the zeros.
