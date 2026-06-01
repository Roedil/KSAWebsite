"""One-off: crop marketing overlays (captions, contact bars, corner logos) off
the source photos and export clean versions for the website."""
import os
from PIL import Image

SRC = r"C:\Users\Roedil\Pictures\Website Photos"
OUT = r"D:\Claude_Projects\Website_KSA\static\img\photos"
os.makedirs(OUT, exist_ok=True)

# (source file, output name, crop fractions: left, top, right, bottom)
JOBS = [
    ("1752478844266.jpg", "coldchain.jpg", 0.00, 0.15, 1.00, 0.86),
    ("1756695156830.jpg", "temperature.jpg", 0.00, 0.17, 1.00, 0.84),
    ("1759732849221.jpg", "healthcare.jpg", 0.00, 0.16, 1.00, 0.79),
    ("1760341256098.jpg", "humidity.jpg", 0.00, 0.16, 1.00, 0.74),
    ("488940412_1002727048590618_6105626430888510248_n.jpg", "mapping.jpg", 0.00, 0.00, 1.00, 0.66),
    ("500102641_1037360081793981_5745146255461806558_n.jpg", "fieldwork.jpg", 0.00, 0.18, 1.00, 0.905),
    ("481228998_973762104820446_8877612540649373768_n.jpg", "weights.jpg", 0.00, 0.00, 1.00, 1.00),
]

for src, out, l, t, r, b in JOBS:
    im = Image.open(os.path.join(SRC, src)).convert("RGB")
    w, h = im.size
    box = (int(w * l), int(h * t), int(w * r), int(h * b))
    im.crop(box).save(os.path.join(OUT, out), quality=88)
    print(out, "->", (box[2] - box[0], box[3] - box[1]))
