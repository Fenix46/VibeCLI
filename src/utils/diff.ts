export type DiffHunk = {
  oldStart: number;
  oldLines: number;
  newStart: number;
  newLines: number;
  lines: string[];
};

export function applyUnifiedDiff(original: string, diff: string): string {
  const lines = diff.split(/\r?\n/);
  const hunks = parseHunks(lines);
  const origLines = original.split(/\r?\n/);
  let offset = 0;

  for (const hunk of hunks) {
    const start = hunk.oldStart - 1 + offset;
    let index = start;
    const newChunk: string[] = [];
    for (const line of hunk.lines) {
      const prefix = line[0];
      const content = line.slice(1);
      if (prefix === " ") {
        if (origLines[index] !== content) {
          throw new Error("Hunk context mismatch");
        }
        newChunk.push(content);
        index += 1;
      } else if (prefix === "-") {
        if (origLines[index] !== content) {
          throw new Error("Hunk removal mismatch");
        }
        index += 1;
      } else if (prefix === "+") {
        newChunk.push(content);
      }
    }
    const removeCount = hunk.oldLines;
    origLines.splice(start, removeCount, ...newChunk);
    offset += hunk.newLines - hunk.oldLines;
  }

  return origLines.join("\n");
}

function parseHunks(lines: string[]): DiffHunk[] {
  const hunks: DiffHunk[] = [];
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    if (line.startsWith("@@")) {
      const match = /@@ -(\d+),(\d+) \+(\d+),(\d+) @@/.exec(line);
      if (!match) throw new Error("Invalid hunk header");
      const oldStart = Number(match[1]);
      const oldLines = Number(match[2]);
      const newStart = Number(match[3]);
      const newLines = Number(match[4]);
      const hunkLines: string[] = [];
      i += 1;
      while (i < lines.length && !lines[i].startsWith("@@")) {
        const hline = lines[i];
        if (hline.startsWith("+") || hline.startsWith("-") || hline.startsWith(" ")) {
          hunkLines.push(hline);
        }
        i += 1;
      }
      i -= 1;
      hunks.push({ oldStart, oldLines, newStart, newLines, lines: hunkLines });
    }
  }
  return hunks;
}
