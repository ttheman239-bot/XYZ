package com.example.graphics2d

import android.content.Context
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.graphics.RadialGradient
import android.graphics.Shader
import android.util.AttributeSet
import android.view.MotionEvent
import android.view.View
import kotlin.math.cos
import kotlin.math.sin
import kotlin.random.Random

class GraphicsView @JvmOverloads constructor(
    context: Context,
    attrs: AttributeSet? = null,
    defStyle: Int = 0
) : View(context, attrs, defStyle) {

    enum class Scene { PARTICLES, BOUNCING, FRACTAL, WAVES }

    private val paint = Paint(Paint.ANTI_ALIAS_FLAG)
    private val fadePaint = Paint().apply { color = Color.argb(64, 5, 8, 22) }
    private val bgPaint = Paint().apply { color = Color.rgb(5, 8, 22) }

    private var scene: Scene = Scene.PARTICLES
    private var particles: List<Particle> = emptyList()
    private var balls: List<Ball> = emptyList()
    private var pointerX = 0f
    private var pointerY = 0f
    private val startNanos = System.nanoTime()
    private var running = true

    fun setScene(s: Scene) {
        scene = s
        when (s) {
            Scene.PARTICLES -> initParticles()
            Scene.BOUNCING -> initBalls()
            else -> {}
        }
        invalidate()
    }

    fun pauseAnimation() {
        running = false
    }

    fun resumeAnimation() {
        if (!running) {
            running = true
            invalidate()
        }
    }

    override fun onSizeChanged(w: Int, h: Int, oldw: Int, oldh: Int) {
        super.onSizeChanged(w, h, oldw, oldh)
        pointerX = w / 2f
        pointerY = h / 2f
        if (scene == Scene.PARTICLES && particles.isEmpty()) initParticles()
        if (scene == Scene.BOUNCING && balls.isEmpty()) initBalls()
    }

    override fun onTouchEvent(event: MotionEvent): Boolean {
        pointerX = event.x
        pointerY = event.y
        return true
    }

    override fun onDraw(canvas: Canvas) {
        val t = (System.nanoTime() - startNanos) / 1e9f
        when (scene) {
            Scene.PARTICLES -> drawParticles(canvas)
            Scene.BOUNCING -> drawBalls(canvas)
            Scene.FRACTAL -> drawFractal(canvas, t)
            Scene.WAVES -> drawWaves(canvas, t)
        }
        if (running) postInvalidateOnAnimation()
    }

    private fun initParticles() {
        val w = width.coerceAtLeast(1)
        val h = height.coerceAtLeast(1)
        particles = List(220) {
            Particle(
                x = Random.nextFloat() * w,
                y = Random.nextFloat() * h,
                vx = (Random.nextFloat() - 0.5f) * 0.6f,
                vy = (Random.nextFloat() - 0.5f) * 0.6f,
                hue = Random.nextFloat() * 360f
            )
        }
    }

    private fun drawParticles(canvas: Canvas) {
        val w = width.toFloat()
        val h = height.toFloat()
        canvas.drawRect(0f, 0f, w, h, fadePaint)

        val hsv = floatArrayOf(0f, 0.9f, 1f)
        for (p in particles) {
            val dx = pointerX - p.x
            val dy = pointerY - p.y
            val d2 = dx * dx + dy * dy + 50f
            p.vx += dx / d2 * 8f
            p.vy += dy / d2 * 8f
            p.vx *= 0.98f
            p.vy *= 0.98f
            p.x += p.vx
            p.y += p.vy
            if (p.x < 0) p.x += w
            if (p.x > w) p.x -= w
            if (p.y < 0) p.y += h
            if (p.y > h) p.y -= h

            hsv[0] = p.hue
            paint.color = Color.HSVToColor(hsv)
            canvas.drawCircle(p.x, p.y, 2.5f, paint)
        }
    }

    private fun initBalls() {
        val w = width.coerceAtLeast(1)
        val h = height.coerceAtLeast(1)
        val palette = intArrayOf(
            Color.parseColor("#7DF9FF"),
            Color.parseColor("#FF7DF9"),
            Color.parseColor("#FFD97D"),
            Color.parseColor("#7DFF9F"),
            Color.parseColor("#FF8A7D")
        )
        balls = List(24) {
            val r = 18f + Random.nextFloat() * 36f
            Ball(
                x = r + Random.nextFloat() * (w - 2 * r),
                y = r + Random.nextFloat() * (h - 2 * r),
                vx = (Random.nextFloat() - 0.5f) * 14f,
                vy = (Random.nextFloat() - 0.5f) * 14f,
                r = r,
                color = palette[Random.nextInt(palette.size)]
            )
        }
    }

    private fun drawBalls(canvas: Canvas) {
        val w = width.toFloat()
        val h = height.toFloat()
        canvas.drawRect(0f, 0f, w, h, fadePaint)

        for (b in balls) {
            b.vy += 0.45f
            b.x += b.vx
            b.y += b.vy
            if (b.x - b.r < 0) { b.x = b.r; b.vx *= -0.85f }
            else if (b.x + b.r > w) { b.x = w - b.r; b.vx *= -0.85f }
            if (b.y + b.r > h) { b.y = h - b.r; b.vy *= -0.85f; b.vx *= 0.99f }
            else if (b.y - b.r < 0) { b.y = b.r; b.vy *= -0.85f }

            val shader = RadialGradient(
                b.x - b.r * 0.3f, b.y - b.r * 0.3f, b.r,
                intArrayOf(Color.WHITE, b.color, Color.argb(180, 0, 0, 0)),
                floatArrayOf(0f, 0.35f, 1f),
                Shader.TileMode.CLAMP
            )
            paint.shader = shader
            canvas.drawCircle(b.x, b.y, b.r, paint)
            paint.shader = null
        }
    }

    private fun drawFractal(canvas: Canvas, t: Float) {
        canvas.drawRect(0f, 0f, width.toFloat(), height.toFloat(), bgPaint)
        val sway = sin(t * 1.2f) * 0.08f
        val len = (height * 0.18f).coerceAtLeast(60f)
        branch(canvas, width / 2f, height - 20f, len, (-Math.PI / 2).toFloat(), 11, sway)
    }

    private fun branch(canvas: Canvas, x: Float, y: Float, len: Float, angle: Float, depth: Int, sway: Float) {
        if (depth == 0 || len < 2f) return
        val x2 = x + cos(angle) * len
        val y2 = y + sin(angle) * len

        val hsv = floatArrayOf(120f + depth * 12f, 0.7f, 0.3f + depth * 0.05f)
        paint.color = Color.HSVToColor(hsv)
        paint.strokeWidth = depth * 0.9f
        canvas.drawLine(x, y, x2, y2, paint)

        branch(canvas, x2, y2, len * 0.72f, angle - 0.45f + sway, depth - 1, sway)
        branch(canvas, x2, y2, len * 0.72f, angle + 0.45f + sway, depth - 1, sway)
    }

    private fun drawWaves(canvas: Canvas, t: Float) {
        val w = width.toFloat()
        val h = height.toFloat()
        paint.color = Color.argb(38, 5, 8, 22)
        canvas.drawRect(0f, 0f, w, h, paint)

        val hsv = floatArrayOf(0f, 0.8f, 0.6f)
        val layers = 6
        val path = android.graphics.Path()
        for (i in 0 until layers) {
            path.reset()
            path.moveTo(0f, h)
            var x = 0f
            while (x <= w) {
                val y = h / 2f +
                        sin(x * 0.012f + t * 1.2f + i * 0.6f) * 40f +
                        sin(x * 0.005f - t * 0.8f + i) * 30f +
                        i * 22f
                path.lineTo(x, y)
                x += 8f
            }
            path.lineTo(w, h)
            path.close()
            hsv[0] = ((200 + i * 25 + t * 20) % 360f + 360f) % 360f
            paint.color = Color.HSVToColor(46, hsv)
            canvas.drawPath(path, paint)
        }
    }

    private class Particle(
        var x: Float, var y: Float,
        var vx: Float, var vy: Float,
        var hue: Float
    )

    private class Ball(
        var x: Float, var y: Float,
        var vx: Float, var vy: Float,
        val r: Float, val color: Int
    )
}
