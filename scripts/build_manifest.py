
import os, csv, argparse, hashlib
from pathlib import Path

try:
    from PIL import Image
    HAVE_PIL = True
except Exception:
    HAVE_PIL = False

def sha256_file(path, chunk=1024*1024):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            b = f.read(chunk)
            if not b: break
            h.update(b)
    return h.hexdigest()

def probe_size(path):
    if not HAVE_PIL:
        return "", ""
    try:
        with Image.open(path) as im:
            w, h = im.size
        return str(w), str(h)
    except Exception:
        return "", ""

def main():
    project_root = Path(__file__).parent.parent
    default_root = project_root / "data" / "targets"
    default_out = project_root / "data" / "manifests" / "targets_manifest.csv"

    ap = argparse.ArgumentParser(description="Build manifest for target images.")
    ap.add_argument("--root", default=str(default_root), help="图片根目录")
    ap.add_argument("--out",  default=str(default_out), help="输出CSV路径")
    ap.add_argument("--exts", default=".jpg,.jpeg,.png", help="要扫描的文件后缀")
    args = ap.parse_args()

    root = Path(args.root)
    out = Path(args.out)
    exts = {e.strip().lower() for e in args.exts.split(",") if e.strip()}

    if not root.is_dir():
        print(f"[ERR] 找不到目录: {root}")
        print(f"请将目标图片放置在: {root}")
        return

    out.parent.mkdir(parents=True, exist_ok=True)

    files = []
    for dp, _, fns in os.walk(root):
        for fn in fns:
            if any(fn.lower().endswith(e) for e in exts):
                files.append(os.path.join(dp, fn))

    files.sort()

    if not files:
        print(f"[WARN] 在 {root} 下找不到图片文件")
        return

    print(f"[INFO] 找到 {len(files)} 个图片文件")

    rows = []
    for idx, fpath in enumerate(files, 1):
        fname = os.path.basename(fpath)
        rel_path = os.path.relpath(fpath, root.parent)
        abs_path = os.path.abspath(fpath)
        fbytes = os.path.getsize(fpath)
        w, h = probe_size(fpath)
        sha = sha256_file(fpath)
        mtime = int(os.path.getmtime(fpath))

        rows.append({
            "index": idx,
            "filename": fname,
            "rel_path": rel_path,
            "abs_path": abs_path,
            "bytes": fbytes,
            "width": w,
            "height": h,
            "sha256": sha,
            "mtime": mtime,
            "difficulty": "medium",
            "prompt_id": 1,
            "ground_truth": ""
        })

    fieldnames = ["index", "filename", "rel_path", "abs_path", "bytes",
                 "width", "height", "sha256", "mtime", "difficulty",
                 "prompt_id", "ground_truth"]

    with open(out, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"[OK] 已生成 manifest 文件: {out}")
    print(f"     共 {len(rows)} 条记录")

if __name__ == "__main__":
    main()
