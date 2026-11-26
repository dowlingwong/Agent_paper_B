#!/bin/bash
# Read-only backfill verification for an already-moved entry: original is in /ceph/dwong/_to_delete/<X>.moved_20261114,
# the copy is /work/dwong/<X>. Compares count, file-content bytes, dir count, symlink-list SHA, permission-list SHA,
# file SHA manifest and (nested) git state. Appends one row to MOVE_BACKFILL.tsv. NO writes outside that file.
set -u
X="${1:?entry}"; W=/work/dwong/htcondor_prep_20261114
O="/ceph/dwong/_to_delete/${X}.moved_20261114"; N="/work/dwong/$X"
OUT="$W/moves/MOVE_BACKFILL.tsv"
[ -f "$OUT" ] || printf 'entry\torig\tcopy\tcount_equal\tbytes_equal\tdirs_equal\tsymlink_sha_equal\tperm_sha_equal\tmanifest_sha256\tdirs\tfiles\tverdict\n' > "$OUT"
[ -d "$O" ] && [ -d "$N" ] || { echo "MISSING $X"; exit 1; }
fb(){ find "$1" -type f -printf '%s\n' 2>/dev/null | awk '{s+=$1} END{print s+0}'; }
dc(){ find "$1" -type d 2>/dev/null | wc -l; }
sl(){ ( cd "$1" && find . -type l -printf '%p -> %l\n' 2>/dev/null | LC_ALL=C sort ) | sha256sum | awk '{print $1}'; }
pm(){ ( cd "$1" && find . -printf '%m %p\n' 2>/dev/null | LC_ALL=C sort ) | sha256sum | awk '{print $1}'; }
mf(){ ( cd "$1" && find . -type f ! -path '*/.git/index' -print0 | sort -z | xargs -0 sha256sum 2>/dev/null ) | sha256sum | awk '{print $1}'; }
eq(){ [ "$1" = "$2" ] && echo yes || echo no; }
C1=$(find "$O" -xdev -type f|wc -l); C2=$(find "$N" -xdev -type f|wc -l)
B1=$(fb "$O"); B2=$(fb "$N"); D1=$(dc "$O"); D2=$(dc "$N")
L1=$(sl "$O"); L2=$(sl "$N"); P1=$(pm "$O"); P2=$(pm "$N"); M1=$(mf "$O"); M2=$(mf "$N")
V=ok
[ "$C1" != "$C2" ] && V=count_mismatch
[ "$B1" != "$B2" ] && V=bytes_mismatch
[ "$D1" != "$D2" ] && V=dir_mismatch
[ "$L1" != "$L2" ] && V=symlink_mismatch
[ "$P1" != "$P2" ] && V=perm_mismatch
[ "$M1" != "$M2" ] && V=manifest_mismatch
printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' "$X" "$O" "$N" "$(eq "$C1" "$C2")" "$(eq "$B1" "$B2")" "$(eq "$D1" "$D2")" "$(eq "$L1" "$L2")" "$(eq "$P1" "$P2")" "$M1" "$D1" "$C1" "$V" >> "$OUT"
echo "BACKFILL $X verdict=$V dirs=$D1 files=$C1 manifest=$M1"
