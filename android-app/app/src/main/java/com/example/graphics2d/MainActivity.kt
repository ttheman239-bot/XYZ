package com.example.graphics2d

import android.os.Bundle
import android.widget.Button
import androidx.appcompat.app.AppCompatActivity

class MainActivity : AppCompatActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        val view = findViewById<GraphicsView>(R.id.graphicsView)
        val buttons = mapOf(
            R.id.btnParticles to GraphicsView.Scene.PARTICLES,
            R.id.btnBouncing to GraphicsView.Scene.BOUNCING,
            R.id.btnFractal to GraphicsView.Scene.FRACTAL,
            R.id.btnWaves to GraphicsView.Scene.WAVES
        )

        fun select(id: Int) {
            buttons.keys.forEach { findViewById<Button>(it).isSelected = (it == id) }
            view.setScene(buttons.getValue(id))
        }

        buttons.keys.forEach { id ->
            findViewById<Button>(id).setOnClickListener { select(id) }
        }
        select(R.id.btnParticles)
    }

    override fun onResume() {
        super.onResume()
        findViewById<GraphicsView>(R.id.graphicsView).resumeAnimation()
    }

    override fun onPause() {
        super.onPause()
        findViewById<GraphicsView>(R.id.graphicsView).pauseAnimation()
    }
}
