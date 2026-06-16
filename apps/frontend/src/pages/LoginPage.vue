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
    <section class="brand-stage" aria-label="BITNP IDEAS">
      <div class="brand-mark">
        <img src="/assets/bitnp-logo.svg" alt="BITNP" />
      </div>

      <div class="brand-copy">
        <p class="eyebrow">BITNP IDEAS</p>
        <h1>
          <span>Idea-Driven Execution</span>
          <small>Administration System</small>
        </h1>
        <p class="lead">
          A focused workspace for collecting signals, shaping projects, and moving work through delivery.
        </p>
      </div>
    </section>

    <section class="login-panel" aria-label="Sign in">
      <div class="panel-inner">
        <div class="panel-heading">
          <img src="/assets/bitnp-logo.svg" alt="" />
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
          <span></span>
          <p>BITNP unified identity</p>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
.login-shell {
  position: relative;
  min-height: 100vh;
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(360px, 500px);
  overflow: hidden;
  background:
    linear-gradient(rgba(32, 26, 22, 0.06) 1px, transparent 1px),
    linear-gradient(90deg, rgba(32, 26, 22, 0.06) 1px, transparent 1px),
    linear-gradient(135deg, rgba(218, 117, 29, 0.14), rgba(22, 124, 128, 0.08) 42%, rgba(246, 247, 249, 0)),
    #f7f4ef;
  background-size: 44px 44px, 44px 44px, auto, auto;
  color: #201a16;
}

.brand-stage {
  position: relative;
  display: flex;
  min-height: 100vh;
  flex-direction: column;
  justify-content: center;
  gap: 36px;
  padding: clamp(28px, 5vw, 72px);
  z-index: 1;
}

.brand-mark,
.brand-copy {
  position: relative;
  z-index: 1;
}

.brand-mark {
  display: inline-flex;
  width: 92px;
  height: 92px;
  align-items: center;
  justify-content: center;
  border: 1px solid rgba(32, 26, 22, 0.1);
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.76);
  box-shadow: 0 24px 70px rgba(91, 54, 21, 0.14);
}

.brand-mark img,
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
  color: #6f5542;
  font-size: 0.78rem;
  font-weight: 700;
  letter-spacing: 0;
  text-transform: uppercase;
}

.brand-copy h1 {
  max-width: 740px;
  margin: 18px 0;
  color: #231914;
  font-size: 5.2rem;
  font-weight: 800;
  line-height: 0.98;
  letter-spacing: 0;
}

.brand-copy h1 span,
.brand-copy h1 small {
  display: block;
}

.brand-copy h1 small {
  margin-top: 12px;
  font-size: 0.42em;
  font-weight: 700;
  line-height: 1.05;
}

.lead {
  max-width: 580px;
  margin: 0;
  color: #5f5148;
  font-size: 1.08rem;
  line-height: 1.75;
}

.login-panel {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 32px;
  background: transparent;
}

.login-panel::before {
  position: absolute;
  top: 50%;
  left: -190px;
  width: 440px;
  height: 440px;
  content: "";
  border: 1px solid rgba(218, 117, 29, 0.24);
  pointer-events: none;
  transform: translateY(-34%) rotate(14deg);
}

.panel-inner {
  width: 100%;
  max-width: 420px;
  padding: clamp(28px, 4vw, 44px);
  border: 1px solid rgba(32, 26, 22, 0.12);
  border-radius: 8px;
  background: rgba(255, 253, 249, 0.82);
  backdrop-filter: blur(18px);
  box-shadow: 0 30px 80px rgba(91, 54, 21, 0.16);
}

.panel-heading {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 34px;
}

.panel-heading h2 {
  margin: 4px 0 0;
  color: #251a15;
  font-size: 1.7rem;
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
  background: #167c80;
}

@media (max-width: 900px) {
  .login-shell {
    grid-template-columns: 1fr;
  }

  .brand-stage {
    min-height: auto;
    gap: 28px;
    padding-bottom: 12px;
  }

  .brand-copy h1 {
    font-size: 3.7rem;
  }

  .login-panel {
    padding: 0 18px 32px;
  }

  .login-panel::before {
    top: -100px;
    left: auto;
    right: -80px;
    width: 320px;
    height: 320px;
    transform: rotate(14deg);
  }

  .panel-inner {
    max-width: 100%;
  }
}

@media (max-width: 560px) {
  .brand-stage {
    gap: 20px;
    padding: 24px 18px 16px;
  }

  .brand-mark {
    width: 78px;
    height: 78px;
    border-radius: 18px;
  }

  .brand-mark img,
  .panel-heading img {
    width: 54px;
    height: 54px;
  }

  .brand-copy h1 {
    font-size: 2.6rem;
  }

  .brand-copy h1 small {
    margin-top: 10px;
    font-size: 0.46em;
  }

  .lead {
    font-size: 0.98rem;
    line-height: 1.6;
  }

  .login-panel {
    padding: 0 14px 22px;
  }

  .login-panel::before {
    top: -76px;
    right: -92px;
    width: 240px;
    height: 240px;
  }

  .panel-heading {
    align-items: flex-start;
  }
}
</style>
