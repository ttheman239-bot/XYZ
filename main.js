const canvas = document.getElementById("stage");
const ctx = canvas.getContext("2d");
const W = canvas.width;
const H = canvas.height;

let currentScene = null;
let rafId = null;
let startTime = 0;

const scenes = {
  particles: createParticles(),
  bouncing: createBouncing(),
  fractal: createFractal(),
  waves: createWaves(),
};

function setScene(name) {
  if (rafId) cancelAnimationFrame(rafId);
  currentScene = scenes[name];
  currentScene.reset();
  startTime = performance.now();
  document.querySelectorAll(".controls button").forEach((b) => {
    b.classList.toggle("active", b.dataset.scene === name);
  });
  loop();
}

function loop() {
  const t = (performance.now() - startTime) / 1000;
  currentScene.draw(t);
  rafId = requestAnimationFrame(loop);
}

document.querySelectorAll(".controls button").forEach((btn) => {
  btn.addEventListener("click", () => setScene(btn.dataset.scene));
});

canvas.addEventListener("mousemove", (e) => {
  const rect = canvas.getBoundingClientRect();
  const x = ((e.clientX - rect.left) / rect.width) * W;
  const y = ((e.clientY - rect.top) / rect.height) * H;
  if (currentScene && currentScene.onPointer) currentScene.onPointer(x, y);
});

setScene("particles");

function createParticles() {
  const count = 220;
  let particles = [];
  let pointer = { x: W / 2, y: H / 2 };

  function reset() {
    particles = Array.from({ length: count }, () => ({
      x: Math.random() * W,
      y: Math.random() * H,
      vx: (Math.random() - 0.5) * 0.6,
      vy: (Math.random() - 0.5) * 0.6,
      hue: Math.random() * 360,
    }));
  }

  function draw() {
    ctx.fillStyle = "rgba(5, 8, 22, 0.25)";
    ctx.fillRect(0, 0, W, H);

    for (const p of particles) {
      const dx = pointer.x - p.x;
      const dy = pointer.y - p.y;
      const d2 = dx * dx + dy * dy + 50;
      p.vx += (dx / d2) * 8;
      p.vy += (dy / d2) * 8;
      p.vx *= 0.98;
      p.vy *= 0.98;
      p.x += p.vx;
      p.y += p.vy;
      if (p.x < 0) p.x += W;
      if (p.x > W) p.x -= W;
      if (p.y < 0) p.y += H;
      if (p.y > H) p.y -= H;

      ctx.fillStyle = `hsl(${p.hue}, 90%, 65%)`;
      ctx.beginPath();
      ctx.arc(p.x, p.y, 2, 0, Math.PI * 2);
      ctx.fill();
    }
  }

  return {
    reset,
    draw,
    onPointer(x, y) {
      pointer.x = x;
      pointer.y = y;
    },
  };
}

function createBouncing() {
  let balls = [];
  const colors = ["#7df9ff", "#ff7df9", "#ffd97d", "#7dff9f", "#ff8a7d"];

  function reset() {
    balls = Array.from({ length: 24 }, () => {
      const r = 12 + Math.random() * 22;
      return {
        x: r + Math.random() * (W - 2 * r),
        y: r + Math.random() * (H - 2 * r),
        vx: (Math.random() - 0.5) * 6,
        vy: (Math.random() - 0.5) * 6,
        r,
        color: colors[Math.floor(Math.random() * colors.length)],
      };
    });
  }

  function draw() {
    ctx.fillStyle = "rgba(5, 8, 22, 0.4)";
    ctx.fillRect(0, 0, W, H);

    for (const b of balls) {
      b.vy += 0.18;
      b.x += b.vx;
      b.y += b.vy;

      if (b.x - b.r < 0) {
        b.x = b.r;
        b.vx *= -0.85;
      } else if (b.x + b.r > W) {
        b.x = W - b.r;
        b.vx *= -0.85;
      }
      if (b.y + b.r > H) {
        b.y = H - b.r;
        b.vy *= -0.85;
        b.vx *= 0.99;
      } else if (b.y - b.r < 0) {
        b.y = b.r;
        b.vy *= -0.85;
      }

      const grad = ctx.createRadialGradient(
        b.x - b.r * 0.3,
        b.y - b.r * 0.3,
        b.r * 0.1,
        b.x,
        b.y,
        b.r
      );
      grad.addColorStop(0, "#ffffff");
      grad.addColorStop(0.3, b.color);
      grad.addColorStop(1, "rgba(0,0,0,0.6)");
      ctx.fillStyle = grad;
      ctx.beginPath();
      ctx.arc(b.x, b.y, b.r, 0, Math.PI * 2);
      ctx.fill();
    }
  }

  return { reset, draw };
}

function createFractal() {
  let phase = 0;

  function reset() {
    phase = 0;
  }

  function branch(x, y, len, angle, depth, sway) {
    if (depth === 0 || len < 2) return;
    const x2 = x + Math.cos(angle) * len;
    const y2 = y + Math.sin(angle) * len;
    ctx.strokeStyle = `hsl(${120 + depth * 12}, 70%, ${30 + depth * 5}%)`;
    ctx.lineWidth = depth * 0.7;
    ctx.beginPath();
    ctx.moveTo(x, y);
    ctx.lineTo(x2, y2);
    ctx.stroke();

    branch(x2, y2, len * 0.72, angle - 0.45 + sway, depth - 1, sway);
    branch(x2, y2, len * 0.72, angle + 0.45 + sway, depth - 1, sway);
  }

  function draw(t) {
    ctx.fillStyle = "#050816";
    ctx.fillRect(0, 0, W, H);
    const sway = Math.sin(t * 1.2) * 0.08;
    branch(W / 2, H - 20, 110, -Math.PI / 2, 11, sway);
    phase = t;
  }

  return { reset, draw };
}

function createWaves() {
  function reset() {}

  function draw(t) {
    ctx.fillStyle = "rgba(5, 8, 22, 0.15)";
    ctx.fillRect(0, 0, W, H);

    const layers = 6;
    for (let i = 0; i < layers; i++) {
      ctx.beginPath();
      ctx.moveTo(0, H);
      for (let x = 0; x <= W; x += 8) {
        const y =
          H / 2 +
          Math.sin(x * 0.012 + t * 1.2 + i * 0.6) * 40 +
          Math.sin(x * 0.005 - t * 0.8 + i) * 30 +
          i * 20;
        ctx.lineTo(x, y);
      }
      ctx.lineTo(W, H);
      ctx.closePath();
      const hue = (200 + i * 25 + t * 20) % 360;
      ctx.fillStyle = `hsla(${hue}, 80%, 60%, 0.18)`;
      ctx.fill();
    }
  }

  return { reset, draw };
}
