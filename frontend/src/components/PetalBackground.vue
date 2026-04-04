<script setup lang="ts">
/** 背景桃花瓣：密集、略提高不透明度，偏桃粉色 */
const PETAL_COUNT = 64

type SizeKey = 'sm' | 'md' | 'lg'

const petals = Array.from({ length: PETAL_COUNT }, (_, index) => {
  const sizeRoll = Math.random()
  const size: SizeKey = sizeRoll < 0.38 ? 'sm' : sizeRoll < 0.78 ? 'md' : 'lg'
  return {
    id: index,
    size,
    left: `${Math.random() * 104 - 2}%`,
    delay: `${Math.random() * 18}s`,
    duration: `${11 + Math.random() * 14}s`,
    scale: 0.55 + Math.random() * 0.65,
    drift: `${(Math.random() * 200 - 100).toFixed(0)}px`,
    opacity: 0.34 + Math.random() * 0.38,
    rotate: `${Math.random() * 360}deg`,
    top: `${-18 + Math.random() * 28}%`,
  }
})
</script>

<template>
  <div class="petal-stage" aria-hidden="true">
    <span
      v-for="petal in petals"
      :key="petal.id"
      class="petal"
      :class="`petal--${petal.size}`"
      :style="{
        left: petal.left,
        top: petal.top,
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
  border-radius: 52% 48% 61% 39% / 56% 42% 58% 44%;
  /* 桃花：白尖 + 浅粉到桃红 */
  background:
    radial-gradient(ellipse 90% 70% at 35% 22%, rgba(255, 255, 255, 0.95), rgba(255, 255, 255, 0) 45%),
    radial-gradient(ellipse 80% 90% at 70% 80%, rgba(255, 182, 193, 0.5), rgba(255, 182, 193, 0) 55%),
    linear-gradient(
      148deg,
      rgba(255, 248, 250, 0.98) 0%,
      rgba(255, 205, 218, 0.92) 38%,
      rgba(251, 163, 183, 0.88) 72%,
      rgba(244, 114, 182, 0.78) 100%
    );
  filter: blur(0.15px) saturate(1.15);
  box-shadow:
    0 0 12px rgba(251, 113, 133, 0.35),
    0 2px 8px rgba(244, 63, 94, 0.12);
  animation: petal-fall linear infinite;
}

.petal--sm {
  width: 11px;
  height: 15px;
}

.petal--md {
  width: 17px;
  height: 23px;
}

.petal--lg {
  width: 22px;
  height: 30px;
}

@keyframes petal-fall {
  0% {
    transform: translate3d(0, -8vh, 0) scale(var(--petal-scale, 1)) rotate(var(--petal-rotate, 0deg));
  }
  28% {
    transform: translate3d(var(--petal-drift), 30vh, 0) scale(var(--petal-scale, 1)) rotate(calc(var(--petal-rotate, 0deg) + 95deg));
  }
  62% {
    transform: translate3d(calc(var(--petal-drift) * -0.55), 68vh, 0) scale(var(--petal-scale, 1)) rotate(calc(var(--petal-rotate, 0deg) + 230deg));
  }
  100% {
    transform: translate3d(calc(var(--petal-drift) * 0.42), 118vh, 0) scale(var(--petal-scale, 1)) rotate(calc(var(--petal-rotate, 0deg) + 380deg));
  }
}
</style>
