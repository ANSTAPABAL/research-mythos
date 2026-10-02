param([Parameter(Mandatory=$true)][string]$InputDocx,[Parameter(Mandatory=$true)][string]$OutputPdf)
$ErrorActionPreference = 'Stop'
$sourcePath = (Resolve-Path -LiteralPath $InputDocx).Path
$destinationPath = [System.IO.Path]::GetFullPath($OutputPdf)
$wordConverter = $null
$conversionDocument = $null
try {
    $wordConverter = New-Object -ComObject Word.Application
    $wordConverter.Visible = $false
    $wordConverter.DisplayAlerts = 0
    $conversionDocument = $wordConverter.Documents.Open($sourcePath,$false,$true,$false)
    $conversionDocument.Repaginate()
    $pages = $conversionDocument.ComputeStatistics(2)
    $conversionDocument.ExportAsFixedFormat($destinationPath,17)
    Write-Output "Word PDF exported; pages=$pages; path=$destinationPath"
} finally {
    if ($null -ne $conversionDocument) { $conversionDocument.Close(0); [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($conversionDocument) }
    if ($null -ne $wordConverter) { $wordConverter.Quit(); [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($wordConverter) }
}
