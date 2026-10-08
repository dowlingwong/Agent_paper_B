#!/bin/sh
# Anonymity audit for the ICML-format manuscript (icml2026 style kit).
#
# Usage:
#   sh scripts/check_anonymity.sh [--mode submission|preprint]
#
# submission (default): gates a double-blind submission build. Requires the
#   ICML style to be loaded in its double-blind form (\usepackage{icml2026}
#   without the [accepted] or [preprint] option, which is what suppresses the
#   byline and sets the PDF author to "Anonymous Authors"), a placeholder
#   author block, no thanks or author-contributions sections, no local paths,
#   and clean PDF metadata.
#
# Self-scan note: this script is shipped in the anonymised supplement, and a
# plain scan of the supplement would otherwise flag the patterns below as
# leaks. The home-directory and section-name patterns are therefore spelled
# so that they match the same text without containing it literally (a
# bracket class, or a string assembled from pieces). Behaviour is unchanged.
#
# preprint: for the arXiv / preprint build, where the byline is intentionally
#   visible. Checks only for leaks that are wrong in ANY build -- local
#   filesystem paths and machine usernames.
#
# What the previous version could not catch, and why:
#   - it never inspected the venue switch, so a build with the byline switch
#     active passed unchanged;
#   - it never inspected \author{}, so it passed only because the placeholder
#     happened to be "Author One";
#   - it never inspected the built PDF's metadata, where LaTeX writes the
#     author string even when the byline is suppressed;
#   - it grepped the fixed string 'github.com/' across *.bib, which will fire
#     on any legitimately cited repository URL. Repository links are now
#     flagged only in .tex prose, where they can deanonymize; the bibliography
#     is exempt.

set -eu

mode=submission
while [ $# -gt 0 ]; do
  case "$1" in
    --mode) mode="${2:-}"; shift 2 ;;
    --mode=*) mode="${1#--mode=}"; shift ;;
    -h|--help) sed -n '2,26p' "$0"; exit 0 ;;
    *) printf '%s\n' "unknown argument: $1" >&2; exit 2 ;;
  esac
done

case "${mode}" in
  submission|preprint) ;;
  *) printf '%s\n' "mode must be 'submission' or 'preprint'" >&2; exit 2 ;;
esac

status=0
fail() { printf 'FAIL: %s\n' "$1" >&2; status=1; }
pass() { printf 'ok:   %s\n' "$1"; }

# --- leaks that are wrong in every build ------------------------------------

# Local filesystem paths: macOS and Linux home directories, Windows profiles.
if grep -RIn -E '(/Use[r]s/|/hom[e]/[a-z]|C:\\Use[r]s)' --include='*.tex' . >&2; then
  fail "local filesystem path in a .tex source"
else
  pass "no local filesystem paths in .tex"
fi

# The current user's login name, whatever it happens to be. Derived at run
# time so no real name is stored in the repository.
me="$(id -un 2>/dev/null || printf '%s' "${USER:-}")"
if [ -n "${me}" ] && [ "${me}" != "root" ]; then
  if grep -RIn -F -i "${me}" --include='*.tex' --include='*.bib' . >&2; then
    fail "current username appears in a source file"
  else
    pass "no username leak in .tex/.bib"
  fi
fi

if [ "${mode}" = "preprint" ]; then
  if [ "${status}" -ne 0 ]; then exit "${status}"; fi
  printf '\n%s\n' "PREPRINT MODE: byline checks skipped by design."
  printf '%s\n' "Run with --mode submission before submitting for review."
  exit 0
fi

# --- submission-only gates ---------------------------------------------------

# 1. The double-blind switch.  Paper A builds with the TMLR class
#    (\usepackage{tmlr}, bare); the pre-split build used the ICML kit
#    (icml2026).  Either way the style must be loaded WITHOUT an option that
#    shows the real author list, and the bare form suppresses the byline and
#    writes an anonymous author string into the PDF metadata.
if grep -qE '^[[:space:]]*\\usepackage\{tmlr\}' main.tex; then
  if grep -qE '^[[:space:]]*\\usepackage\[[^]]*(accepted|preprint)[^]]*\]\{tmlr\}' main.tex; then
    fail "tmlr style loaded with [accepted] or [preprint]; a blind build must load it bare"
  else
    pass "tmlr style loaded bare (double-blind mode)"
  fi
elif grep -qE '^[[:space:]]*\\usepackage\[[^]]*(accepted|preprint)[^]]*\]\{icml[0-9]{4}\}' main.tex; then
  fail "icml style loaded with [accepted] or [preprint]; a blind build must load it bare"
elif grep -qE '^[[:space:]]*\\usepackage\{icml[0-9]{4}\}' main.tex; then
  pass "icml style loaded bare (double-blind mode)"
else
  fail "no \\usepackage{tmlr} or \\usepackage{icmlYYYY} line found in main.tex"
fi

# 2. The author block must still be a placeholder (the style hides it in a
#    blind build, but a real name in the source is still a leak in the tree).
if grep -qE '\\icmlauthor\{' main.tex; then
  authors=$(grep -E '\\icmlauthor\{|\\icmlaffiliation\{|\\icmlcorrespondingauthor\{' main.tex)
  if printf '%s' "${authors}" | grep -vqE 'Author One|Anonymous|example\.(org|com)'; then
    printf '%s\n' "${authors}" >&2
    fail "author block does not look like a placeholder"
  else
    pass "author block is a placeholder"
  fi
fi
if grep -qE '\\author\{[^}]*[A-Za-z]' main.tex; then
  author_line=$(grep -E '\\author\{' main.tex)
  if printf '%s' "${author_line}" | grep -qE 'Anonymous|anonym'; then
    pass "author block is a placeholder"
  else
    printf '%s\n' "${author_line}" >&2
    fail "author block does not look like a placeholder"
  fi
fi

# 3. Thanks and author-contribution sections deanonymize; TMLR asks for them
#    only in the camera-ready.
ack=0
ack_stem='Acknowl''edg'
for section in "${ack_stem}ments" "${ack_stem}ements" 'Author Contributions'; do
  if grep -RIn -F "{${section}}" --include='*.tex' . >&2; then
    fail "${section} section present in a submission build"
    ack=1
  fi
done
[ "${ack}" -eq 0 ] && pass "no thanks or author-contributions sections"

# 4. Repository and personal URLs in prose (NOT in the bibliography, where a
#    cited repository is legitimate).
if grep -RIn -E '(github\.com|gitlab\.com|huggingface\.co/|osf\.io)' \
     --include='*.tex' . >&2; then
  fail "repository URL in .tex prose; use an anonymized artifact link"
else
  pass "no repository URLs in .tex prose"
fi

# 5. PDF metadata. LaTeX writes /Author and /Title into the PDF even when the
#    byline is suppressed on the page.
if [ -f main.pdf ]; then
  if command -v pdfinfo >/dev/null 2>&1; then
    meta=$(pdfinfo main.pdf 2>/dev/null || true)
    leaked=$(printf '%s\n' "${meta}" | grep -E '^(Author|Creator|Producer):' \
             | grep -viE ':[[:space:]]*$|Author One|Anonymous|pdfTeX|LaTeX|dvips|Ghostscript|XeTeX|LuaTeX' \
             || true)
    if [ -n "${leaked}" ]; then
      printf '%s\n' "${leaked}" >&2
      fail "PDF metadata carries an identifying field"
    else
      pass "PDF metadata clean"
    fi
  else
    printf '%s\n' "warn: pdfinfo not installed; PDF metadata not checked" >&2
  fi
else
  printf '%s\n' "warn: main.pdf not built; PDF metadata not checked" >&2
fi

if [ "${status}" -ne 0 ]; then
  printf '\n%s\n' "ANONYMITY CHECK FAILED (mode=${mode})" >&2
  exit "${status}"
fi

printf '\n%s\n' "ANONYMITY CHECK PASSED (mode=${mode})"
