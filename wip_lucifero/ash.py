from engine import *
rng = np.random.default_rng(5)
base = floor(CAM0)
N = 30
ax = rng.uniform(0, 256, N); ay = rng.uniform(48, 224, N); vy = rng.uniform(0.25, 0.6, N)
ph = rng.uniform(0, 6.28, N); amp = rng.uniform(0.2, 0.6, N); sz = np.where(rng.uniform(0, 1, N) < 0.75, 2, 1)
col = [np.array([215, 212, 205], float), np.array([175, 172, 166], float)]
frames = []
bx, by, dx, dy = 60.0, 120.0, 1.6, 0.7; p1y, p2y = 100.0, 90.0
for f in range(150):
    img = base.copy()
    bx += dx; by += dy
    if by < 50 or by > 194: dy = -dy
    if bx < 26 or bx > 226: dx = -dx
    p1y += (by - 16 - p1y) * 0.08; p2y += (by - 16 - p2y) * 0.06
    paddle(img, CAM0, 16, p1y, 32, P1); paddle(img, CAM0, 232, p2y, 32, P2); ball(img, CAM0, bx, by)
    gust = 0.8 * math.sin(f / 40.0) ** 3
    for i in range(N):
        ay[i] += vy[i]; ax[i] += amp[i] * math.sin(f / 18.0 + ph[i]) + gust
        if ay[i] > 223: ay[i] = 48; ax[i] = rng.uniform(0, 256)
        ax[i] %= 256
        X, Y = int(ax[i]), int(ay[i]); c = col[i % 2]
        for dyy in range(sz[i]):
            for dxx in range(sz[i]):
                yy, xx = Y + dyy, X + dxx
                if 48 <= yy < 224 and 0 <= xx < 256:
                    img[yy, xx] = (img[yy, xx].astype(float) * 0.3 + c * 0.7).astype(np.uint8)
    frames.append(img)
save_gif(frames, '/mnt/user-data/outputs/lucifero_popiol.gif')
Image.fromarray(frames[60]).save('/tmp/prev/ash_frame.png')
print('ok')
