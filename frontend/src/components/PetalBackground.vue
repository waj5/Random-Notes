<script setup lang="ts">
const petals = Array.from({ length: 18 }, (_, index) => ({
  id: index,
  left: `${Math.random() * 100}%`,
  delay: `${Math.random() * 12}s`,
  duration: `${14 + Math.random() * 10}s`,
  scale: 0.65 + Math.random() * 0.9,
  drift: `${(Math.random() * 160 - 80).toFixed(0)}px`,
  opacity: 0.28 + Math.random() * 0.32,
  rotate: `${Math.random() * 360}deg`,
}))
</script>

<template>
  <div class="petal-stage" aria-hidden="true">
    <span
      v-for="petal in petals"
      :key="petal.id"
      class="petal"
      :style="{
        left: petal.left,
        animationDelay: petal.delay,
        animationDuration: petal.duration,
        opacity: petal.opacity,
        '--petal-drift': petal.drift,
        '--petal-scale': String(petal.scale),
        '--petal-rotate': petal.rotate,
      }"
    />
  </div>
</template>

<style scoped>
.petal-stage {
  pointer-events: none;
  position: fixed;
  inset: 0;
  overflow: hidden;
  z-index: 0;
}

.petal {
  --petal-drift: 40px;
  position: absolute;
  top: -8%;
  width: 20px;
  height: 28px;
  border-radius: 65% 35% 70% 30% / 60% 45% 55% 40%;
  background: radial-gradient(circle at 30% 30%, rgba(255,255,255,0.92), rgba(255,255,255,0) 28%),
    linear-gradient(160deg, rgba(255,229,238,0.95), rgba(255,183,197,0.88) 58%, rgba(255,146,176,0.84));
  box-shadow: 0 0 16px rgba(255, 171, 196, 0.18);
  filter: blur(0.2px);
  animation: petal-fall linear infinite;
}

@keyframes petal-fall {
  0% {
    transform: translate3d(0, -10vh, 0) scale(var(--petal-scale, 1)) rotate(var(--petal-rotate, 0deg));
  }
  30% {
    transform: translate3d(var(--petal-drift), 28vh, 0) scale(var(--petal-scale, 1)) rotate(calc(var(--petal-rotate, 0deg) + 90deg));
  }
  65% {
    transform: translate3d(calc(var(--petal-drift) * -0.65), 65vh, 0) scale(var(--petal-scale, 1)) rotate(calc(var(--petal-rotate, 0deg) + 220deg));
  }
  100% {
    transform: translate3d(calc(var(--petal-drift) * 0.45), 112vh, 0) scale(var(--petal-scale, 1)) rotate(calc(var(--petal-rotate, 0deg) + 360deg));
  }
}
</style>
