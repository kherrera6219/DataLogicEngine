"""Remove the second (duplicate) item 16 from TODO.md cleanly."""


path = r"C:\software\DataLogicEngine\TODO.md"
src = open(path, encoding="utf-8").read()

# Find both occurrences of item 16
# First occurrence is the correct v2 one (lines ~121-130)
# Second occurrence is the appended one (lines ~143-152)
# Both start with "16. [x] REPO-AUDIT-COMPLETE-PLAN-V2"

MARKER = "16. [x] REPO-AUDIT-COMPLETE-PLAN-V2:"

positions = []
start = 0
while True:
    pos = src.find(MARKER, start)
    if pos == -1:
        break
    positions.append(pos)
    start = pos + 1

print(f"Found {len(positions)} occurrences of item 16 at positions: {positions}")

if len(positions) == 2:
    # Keep the first, remove the second
    # Find the end of the second occurrence (next item starting with a number, or end of section)
    second_start = positions[1]
    # Find next numbered item or section header after the second occurrence
    # Look for "\n\n###" or "\n\n17." or similar
    rest = src[second_start:]
    # The second item ends when we hit the next section "### Trace Viewer"
    end_marker = "### Trace Viewer Wiring Phased Update Plan"
    end_pos = rest.find(end_marker)
    if end_pos != -1:
        second_end = second_start + end_pos
        # Remove from second_start to second_end
        cleaned = src[:second_start] + src[second_end:]
        open(path, "w", encoding="utf-8").write(cleaned)
        print("Removed duplicate item 16. TODO.md is clean.")
    else:
        print("WARNING: Could not find end marker for second item 16")
elif len(positions) == 1:
    print("Only one item 16 found — already clean.")
else:
    print(f"Unexpected: {len(positions)} occurrences")
