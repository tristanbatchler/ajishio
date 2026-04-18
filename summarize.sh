#!/bin/sh

output_file="ProjectSummary.md"

printf '%s\n' "# Project Summary" >"$output_file"

git ls-files -co --exclude-standard -- ajishio/ | sort -u | while IFS= read -r file; do
    case "$file" in
        *.cpp|*.h|*.hpp|*.c|*.cs|*.py|*.js|*.ts|*.java|*.go|*.rs|*.nim|*.sh|*.ps1|*.gd) ;;
        *) continue ;;
    esac

    case "$file" in
        *.cpp|*.h|*.hpp) lang="cpp" ;;
        *.c) lang="c" ;;
        *.cs) lang="csharp" ;;
        *.py) lang="python" ;;
        *.js) lang="javascript" ;;
        *.ts) lang="typescript" ;;
        *.java) lang="java" ;;
        *.go) lang="go" ;;
        *.rs) lang="rust" ;;
        *.nim) lang="nim" ;;
        *.sh) lang="bash" ;;
        *.ps1) lang="powershell" ;;
        *.gd) lang="gdscript" ;;
        *) lang="" ;;
    esac

    printf '\n## %s\n' "$file" >>"$output_file"
    printf '```%s\n' "$lang" >>"$output_file"
    while IFS= read -r line; do
        printf '%s\n' "$line"
    done <"$file" >>"$output_file"
    printf '```\n' >>"$output_file"
done
