from engine import *
C0 = (48, 200, 70, 212, 0.72, 1.0); C1 = (24, 224, 60, 214, 0.60, 0.84)
def ease(t): return t * t * (3 - 2 * t)
seq = [0.0] * 30 + [ease(i / 44) for i in range(45)] + [1.0] * 75 + [ease(1 - i / 44) for i in range(45)] + [0.0] * 15
frames = []
bx, by, dx, dy = 140.0, 110.0, -1.7, 1.1; p1y, p2y = 100.0, 90.0
for f, t in enumerate(seq):
    cam = lerp_cam(C0, C1, t); w = 24 * t
    img = floor(cam, w)
    fx = max(0.0, 1 - bx / 256) * w
    top, bot = 48 - fx, 200 + fx
    bx += dx; by += dy
    if by < top + 2 or by > bot - 8: dy = -dy; by += 2 * dy
    if bx < 26 or bx > 226: dx = -dx
    lo = 48 - w; hi = 200 + w - 32
    p1y += (by - 16 - p1y) * 0.09; p1y = min(max(p1y, lo), hi)
    p2y += (by - 16 - p2y) * 0.06; p2y = min(max(p2y, 48), 168)
    paddle(img, cam, 16, p1y, 32, P1); paddle(img, cam, 232, p2y, 32, P2); ball(img, cam, bx, by)
    frames.append(img)
save_gif(frames, '/mnt/user-data/outputs/lucifero_kamera.gif')
Image.fromarray(frames[0]).save('/tmp/prev/cam0.png'); Image.fromarray(frames[110]).save('/tmp/prev/cam1.png')
print('frames', len(frames))
