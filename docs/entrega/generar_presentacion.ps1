# Generates the PowerPoint deck from presentacion.json using the locally installed Microsoft PowerPoint (COM).
# ASCII-only script; the Spanish content is read as UTF-8 from the JSON file.
# Usage (from the repository root):  powershell -ExecutionPolicy Bypass -File docs\entrega\generar_presentacion.ps1
$ErrorActionPreference = "Stop"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$data = Get-Content -Raw -Encoding UTF8 (Join-Path $here "presentacion.json") | ConvertFrom-Json
$out = Join-Path $here $data.titulo_archivo

$ppLayoutTitle = 1
$ppLayoutText = 2
$ppSaveAsOpenXMLPresentation = 24
$msoFalse = 0
$navy = 0x733A07      # BGR for #073A73
$text = 0x331F0B      # BGR for #0B1F33

$app = New-Object -ComObject PowerPoint.Application
try {
    $pres = $app.Presentations.Add($msoFalse)
    $pres.PageSetup.SlideWidth = 960
    $pres.PageSetup.SlideHeight = 540
    $i = 1
    foreach ($s in $data.diapositivas) {
        if ($s.subtitulo) {
            $slide = $pres.Slides.Add($i, $ppLayoutTitle)
            $slide.Shapes.Item(1).TextFrame.TextRange.Text = $s.titulo
            $slide.Shapes.Item(2).TextFrame.TextRange.Text = $s.subtitulo
            $slide.Shapes.Item(2).TextFrame.TextRange.Font.Size = 24
        } else {
            $slide = $pres.Slides.Add($i, $ppLayoutText)
            $slide.Shapes.Item(1).TextFrame.TextRange.Text = $s.titulo
            $body = $slide.Shapes.Item(2).TextFrame.TextRange
            $body.Text = ($s.puntos -join "`r")
            $body.Font.Size = 22
            $body.Font.Color.RGB = $text
        }
        $title = $slide.Shapes.Item(1).TextFrame.TextRange
        $title.Font.Bold = 1
        $title.Font.Color.RGB = $navy
        $i++
    }
    if (Test-Path $out) { Remove-Item $out -Force }
    $pres.SaveAs($out, $ppSaveAsOpenXMLPresentation)
    $pres.Close()
    Write-Output ("OK: " + $out + " (" + ($i - 1) + " slides)")
} finally {
    $app.Quit()
    [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($app)
}
