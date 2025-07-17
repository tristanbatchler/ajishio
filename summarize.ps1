# Output file
$outputFile = "ProjectSummary.md"
"# Project Summary`n" | Set-Content $outputFile

# Get all Git-tracked source files
$files = git ls-files | Where-Object {
    $_ -match '\.(cpp|h|hpp|c|cs|py|js|ts|java|go|rs|nim|sh|ps1)$'
}

# Map file extensions to markdown code block languages
$extensionMap = @{
    ".cpp"  = "cpp"
    ".h"    = "cpp"
    ".hpp"  = "cpp"
    ".c"    = "c"
    ".cs"   = "csharp"
    ".py"   = "python"
    ".js"   = "javascript"
    ".ts"   = "typescript"
    ".java" = "java"
    ".go"   = "go"
    ".rs"   = "rust"
    ".nim"  = "nim"
    ".sh"   = "bash"
    ".ps1"  = "powershell"
    ".gd"   = "gdscript"
}

# Process each file
foreach ($file in $files) {
    # Avoid THIS powershell file and the output file
    if ($file -eq "summarize.ps1" -or $file -eq $outputFile) {
        continue
    }

    $ext = [System.IO.Path]::GetExtension($file)
    $lang = $extensionMap[$ext.ToLower()] ?? ""

    Add-Content $outputFile "`n## $file`n"
    Add-Content $outputFile "``````$lang"
    Get-Content $file | Add-Content $outputFile
    Add-Content $outputFile "``````"
}