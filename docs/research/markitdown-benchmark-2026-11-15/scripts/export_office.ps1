# Office の COM で、DOCX と PPTX を PDF に、XLSX の式の値を計算して保存し、XLS と PDF に書き出す。
# ZIP の試料もここで作る（Excel で保存したあとの XLSX を入れるため）。
$ErrorActionPreference = 'Stop'
$corpus = Join-Path (Split-Path -Parent $PSScriptRoot) 'corpus'

$word = New-Object -ComObject Word.Application
$word.DisplayAlerts = 0
try {
    foreach ($name in 'handbook', 'handbook-2col') {
        # 読み取り専用の引数を渡すと、自動化の Word が応答しなくなった（2026-11-15）。
        $doc = $word.Documents.Open((Join-Path $corpus "$name.docx"))
        $doc.ExportAsFixedFormat((Join-Path $corpus "$name.pdf"), 17)  # wdExportFormatPDF
        $doc.Close($false)
    }
} finally { $word.Quit() }

$ppt = New-Object -ComObject PowerPoint.Application
try {
    $deck = $ppt.Presentations.Open((Join-Path $corpus 'slides.pptx'), $true, $false, $false)
    $deck.SaveAs((Join-Path $corpus 'slides.pdf'), 32)  # ppSaveAsPDF
    $deck.Close()
} finally { $ppt.Quit() }

$excel = New-Object -ComObject Excel.Application
$excel.Visible = $false
$excel.DisplayAlerts = $false
try {
    $book = $excel.Workbooks.Open((Join-Path $corpus 'expenses.xlsx'))
    $book.Application.CalculateFull()
    $book.Save()
    $book.SaveAs((Join-Path $corpus 'expenses.xls'), 56)  # xlExcel8
    $book.ExportAsFixedFormat(0, (Join-Path $corpus 'expenses.pdf'))  # xlTypePDF
    $book.Close($false)
} finally { $excel.Quit() }

$zip = Join-Path $corpus 'bundle.zip'
if (Test-Path $zip) { Remove-Item $zip }
Compress-Archive -Path (Join-Path $corpus 'handbook.docx'), (Join-Path $corpus 'staff-utf8.csv'), (Join-Path $corpus 'policy.json') -DestinationPath $zip
Get-ChildItem $corpus | Select-Object Name, Length
