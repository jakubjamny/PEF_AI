import os, argparse, itertools, json

def shard(src, dst, bytes_per=8_000_000):
    os.makedirs(dst, exist_ok=True)
    paths=[]
    with open(src, 'rb') as f:
        i=0
        while True:
            chunk=f.read(bytes_per)
            if not chunk: break
            p=os.path.join(dst, f"ex_{i:03}.csv")
            with open(p,'wb') as o: o.write(chunk)
            paths.append(p.replace("\\","/"))
            i+=1
    # index.json se seznamem relativních cest
    with open(os.path.join(dst, "index.json"), "w", encoding="utf-8") as o:
        json.dump([p for p in paths if p.endswith(".csv")], o, ensure_ascii=False, indent=2)
    print(f"Sharded {src} -> {len(paths)} parts in {dst}")

if __name__ == "__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    ap.add_argument("--dst", required=True)
    ap.add_argument("--bytes", type=int, default=8_000_000)
    a=ap.parse_args()
    shard(a.src, a.dst, a.bytes)
