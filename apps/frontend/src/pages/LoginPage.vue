<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const loading = ref(false)
const error = ref<string | null>(null)
const isCallback = computed(() => Boolean(route.query.code && route.query.state))

onMounted(async () => {
  const { code, state } = route.query

  // ── OAuth callback flow ─────────────────────────────────
  if (code && state) {
    loading.value = true
    try {
      await auth.handleCallback(code as string, state as string)
      router.replace('/dashboard')
    } catch (err) {
      error.value = 'SSO login failed. Please try again.'
      console.error('Callback error:', err)
    } finally {
      loading.value = false
    }
    return
  }

  // ── Already authenticated → redirect ────────────────────
  if (auth.isAuthenticated) {
    router.replace('/dashboard')
  }
})

async function startLogin() {
  loading.value = true
  error.value = null
  try {
    await auth.login()
  } catch (err) {
    error.value = 'Failed to initiate login. Please try again.'
    console.error('Login error:', err)
    loading.value = false
  }
}
</script>

<template>
  <div class="login-shell">
    <div class="login-container">
      <section class="brand-stage" aria-label="BITNP IDEAS">
        <div class="brand-copy">
          <p class="eyebrow">BITNP IDEAS</p>
          <h1>
            <span class="brand-title-main">
              <span class="brand-accent">I</span>dea-<span class="brand-accent">D</span>riven
              <span class="brand-accent">E</span>xecution
            </span>
            <small class="brand-title-sub">
              <span class="brand-accent">A</span>dministration <span class="brand-accent">S</span>ystem
            </small>
          </h1>
          <p class="lead">
            A focused workspace for collecting signals, shaping projects, and moving work through delivery.
          </p>
        </div>
      </section>

      <section class="login-panel" aria-label="Sign in">
        <div class="panel-inner">
          <div class="panel-heading">
            <img src="/assets/bitnp-logo.svg" alt="">
            <div>
              <p>Welcome back</p>
              <h2>Sign in to BITNP IDEAS</h2>
            </div>
          </div>

          <v-alert v-if="error" type="error" variant="tonal" closable class="mb-5">
            {{ error }}
          </v-alert>

          <v-btn
            block
            color="primary"
            size="x-large"
            prepend-icon="$account"
            class="login-button"
            :loading="loading"
            :disabled="loading"
            @click="startLogin"
          >
            {{ isCallback ? 'Connecting to BITNP SSO' : 'Sign in with BITNP SSO' }}
          </v-btn>

          <div class="trust-line">
            <span />
            <p>BITNP unified identity</p>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<style scoped>
.login-shell {
  position: relative;
  min-height: 100vh;
  min-height: 100dvh;
  overflow: hidden;
  background:
    linear-gradient(rgba(var(--ideas-color-ink-rgb), 0.06) 1px, transparent 1px),
    linear-gradient(90deg, rgba(var(--ideas-color-ink-rgb), 0.06) 1px, transparent 1px),
    linear-gradient(
      135deg,
      rgba(var(--v-theme-primary), 0.14),
      rgba(var(--v-theme-secondary), 0.08) 42%,
      rgba(var(--ideas-color-login-bg-rgb), 0)
    ),
    var(--ideas-color-login-bg);
  background-size: 44px 44px, 44px 44px, auto, auto;
  color: var(--ideas-color-text);
}

.login-container {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(440px, 560px);
  max-width: 1380px;
  margin: 0 auto;
  min-height: 100vh;
  min-height: 100dvh;
}

.brand-stage {
  position: relative;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 36px;
  padding: clamp(28px, 5vw, 72px);
  z-index: 1;
}

.brand-copy {
  position: relative;
  z-index: 1;
}

.panel-heading img {
  display: block;
  width: 64px;
  height: 64px;
  object-fit: contain;
}

.brand-copy {
  max-width: 690px;
}

.eyebrow,
.panel-heading p,
.trust-line p {
  margin: 0;
  color: var(--ideas-color-text-soft);
  font-size: 0.8rem;
  font-weight: 700;
  letter-spacing: 0;
  text-transform: uppercase;
}

.brand-copy h1 {
  max-width: 740px;
  margin: 18px 0;
  color: var(--ideas-color-text-strong);
  font-size: 5rem;
  font-weight: 800;
  line-height: 0.98;
  letter-spacing: 0;
}

.brand-title-main,
.brand-title-sub {
  display: block;
}

.brand-accent {
  color: rgb(var(--v-theme-primary));
}

.brand-title-sub {
  margin-top: 12px;
  color: var(--ideas-color-text-soft);
  font-size: 0.42em;
  font-weight: 700;
  line-height: 1.05;
}

.lead {
  max-width: 580px;
  margin: 0;
  color: var(--ideas-color-text-muted);
  font-size: 1.05rem;
  line-height: 1.7;
}

.login-panel {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 32px 48px;
  background: transparent;
}

.login-panel::before {
  position: absolute;
  top: 50%;
  left: clamp(-240px, -18vw, -140px);
  width: clamp(280px, 40vw, 480px);
  height: clamp(280px, 40vw, 480px);
  content: "";
  border: 1px solid rgba(var(--v-theme-primary), 0.24);
  pointer-events: none;
  transform: translateY(-34%) rotate(14deg);
}

.panel-inner {
  width: 100%;
  max-width: 520px;
  padding: 36px;
  border: 1px solid rgba(var(--ideas-color-ink-rgb), 0.12);
  border-radius: 8px;
  background: rgba(var(--ideas-color-paper-rgb), 0.82);
  backdrop-filter: blur(18px);
  box-shadow: 0 30px 80px rgba(var(--ideas-color-shadow-rgb), 0.16);
}

.panel-heading {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 34px;
}

.panel-heading h2 {
  margin: 4px 0 0;
  color: var(--ideas-color-text-card);
  font-size: 1.75rem;
  font-weight: 800;
  line-height: 1.2;
  letter-spacing: 0;
}

.login-button {
  min-height: 56px;
  font-weight: 700;
}

.trust-line {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 20px;
}

.trust-line span {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: rgb(var(--v-theme-secondary));
}

@media (max-width: 900px) {
  .login-container {
    grid-template-columns: 1fr;
    max-width: 540px;
    min-height: 100vh;
    min-height: 100dvh;
    align-content: center;
  }

  .brand-stage {
    justify-content: flex-end;
    gap: 16px;
    padding: 24px 16px 10px;
  }

  .brand-copy h1 {
    font-size: 4rem;
  }

  .login-panel {
    align-items: flex-start;
    justify-content: flex-start;
    padding: 8px 16px 24px;
  }

  .login-panel::before {
    top: -80px;
    left: auto;
    right: clamp(-120px, -10vw, -60px);
    width: clamp(240px, 38vw, 360px);
    height: clamp(240px, 38vw, 360px);
    transform: rotate(14deg);
  }

  .panel-inner {
    max-width: 100%;
  }
}

@media (max-width: 560px) {
  .brand-stage {
    gap: 14px;
    padding: 20px 16px 10px;
  }

  .panel-heading img {
    width: 52px;
    height: 52px;
  }

  .brand-copy h1 {
    font-size: 2.9rem;
  }

  .brand-title-sub {
    margin-top: 10px;
    font-size: 0.45em;
  }

  .lead {
    font-size: 0.96rem;
    line-height: 1.6;
  }

  .login-panel {
    padding: 10px 16px 20px;
  }

  .login-panel::before {
    top: -60px;
    right: clamp(-100px, -12vw, -60px);
    width: clamp(180px, 34vw, 260px);
    height: clamp(180px, 34vw, 260px);
  }

  .panel-heading {
    align-items: flex-start;
    gap: 12px;
    margin-bottom: 24px;
  }
}
</style>
