import { createRouter, createWebHistory } from 'vue-router'
import LoginView from '../views/LoginView.vue'
import RegisterView from '../views/RegisterView.vue'
import MeView from '../views/MeView.vue'
import ChangePasswordView from '../views/ChangePasswordView.vue'
import AdminView from '../views/AdminView.vue'
import DashboardView from '../views/DashboardView.vue'
import { auth } from '../stores/auth'

function resolveHomePath(user) {
  const role = String(user?.role || '').toLowerCase()
  if (role === 'admin') return '/admin'
  if (role === 'professional') return '/dashboard'
  if (role === 'insurance') return '/insurance'
  return '/me'
}

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/login' },

    { path: '/login', component: LoginView, meta: { guestOnly: true } },
    { path: '/register', component: RegisterView, meta: { guestOnly: true } },

    { path: '/change-password', component: ChangePasswordView, meta: { requiresAuth: true } },
    { path: '/me', component: MeView, meta: { requiresAuth: true } },

    {
      path: '/admin',
      component: AdminView,
      meta: { requiresAuth: true, role: 'admin' }
    },

    {
      path: '/dashboard',
      component: DashboardView,
      meta: { requiresAuth: true, role: 'professional' }
    },
    {
      path: '/insurance',
      component: () => import('../views/insurance/InsuranceLayout.vue'),
      meta: { requiresAuth: true, role: ['insurance', 'admin'] },
      children: [
        { path: '', redirect: 'overview' },
        { path: 'overview', component: () => import('../views/insurance/InsuranceOverviewView.vue') },
        { path: 'coverage', component: () => import('../views/insurance/CoveragePoliciesView.vue') },
        { path: 'claims', component: () => import('../views/insurance/ClaimsListView.vue') },
        { path: 'claims/new', component: () => import('../views/insurance/ClaimCreateView.vue') },
        { path: 'claims/:id', component: () => import('../views/insurance/ClaimDetailView.vue') }
      ]
    },


    {
      path: '/perfil',
      component: () => import('../views/AdminTab.vue'),
      meta: { requiresAuth: true, role: 'admin' }
    },
    {
      path: '/perfil-pro',
      component: () => import('../views/ProfessionalTab.vue'),
      meta: { requiresAuth: true, role: 'professional' }
    },
    {
      path: '/perfil-insurance',
      component: () => import('../views/InsuranceTab.vue'),
      meta: { requiresAuth: true, role: 'insurance' }
    },


    
    // ✅ AGENDA / APPOINTMENTS (admin + professional)
    {
      path: '/agenda',
      component: () => import('../views/agenda/AgendaLayout.vue'),
      meta: { requiresAuth: true, role: ['admin', 'professional'] },
      children: [
        { path: '', component: () => import('../views/agenda/AgendaIndexView.vue') },
        {
          path: 'admin',
          component: () => import('../views/agenda/AdminAgendaView.vue'),
          meta: { requiresAuth: true, role: ['admin'] }
        },
        {
          path: 'me',
          component: () => import('../views/agenda/ProfessionalAgendaView.vue'),
          meta: { requiresAuth: true, role: ['professional'] }
        }
      ]
    },
// ✅ CASES (admin + professional)
    {
      path: '/cases',
      component: () => import('../views/cases/CasesHomeView.vue'),
      meta: { requiresAuth: true, role: ['admin', 'professional'] }
    },
    {
      path: '/cases/new',
      component: () => import('../views/cases/CreateCaseView.vue'),
      meta: { requiresAuth: true, role: ['admin', 'professional'] }
    },
    {
      path: '/cases/:id',
      component: () => import('../views/cases/CaseDetailView.vue'),
      meta: { requiresAuth: true, role: ['admin', 'professional'] }
    },

    // ✅ REPORTS (admin + professional "mine")
    {
      path: '/reports',
      component: () => import('../views/reports/ReportsLayout.vue'),
      meta: { requiresAuth: true, role: ['admin', 'professional'] },
      children: [
        { path: '', component: () => import('../views/reports/ReportsHomeRedirect.vue') },
        { path: 'summary', component: () => import('../views/reports/ReportsSummaryView.vue') },
        { path: 'activity', component: () => import('../views/reports/ReportsActivityView.vue') },
        { path: 'cases', component: () => import('../views/reports/ReportsCasesView.vue') },
        { path: 'appointments', component: () => import('../views/reports/ReportsAppointmentsView.vue') },
        { path: 'security', component: () => import('../views/reports/ReportsSecurityView.vue') },
        { path: 'exports', component: () => import('../views/reports/ReportsExportsView.vue') },
        { path: 'mine', component: () => import('../views/reports/ReportsMineView.vue') }
      ]
    }
  ]
})

router.beforeEach((to) => {
  const isAuthed = auth.isAuthenticated()
  const user = auth.user?.() || null

  // 🔒 auth required
  if (to.meta.requiresAuth && !isAuthed) {
    return '/login'
  }

  // 🔑 must change password
  if (isAuthed && auth.mustChangePassword() && to.path !== '/change-password') {
    return '/change-password'
  }

  // 🚫 guest only
  if (to.meta.guestOnly && isAuthed) {
    return resolveHomePath(user)
  }

  // 👮 role guard (string or array)
  if (to.meta.role && user?.role) {
    const need = Array.isArray(to.meta.role)
      ? to.meta.role.map((r) => String(r).toLowerCase())
      : [String(to.meta.role).toLowerCase()]

    const have = String(user.role).toLowerCase()
    if (!need.includes(have)) return resolveHomePath(user)
  }

  return true
})

export default router
