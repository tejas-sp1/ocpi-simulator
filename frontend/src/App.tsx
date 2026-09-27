import { useEffect, useMemo, useState } from 'react'
import {
  Activity,
  ArrowLeftRight,
  BadgeCheck,
  BarChart3,
  Cable,
  ChevronLeft,
  ChevronRight,
  CircleDot,
  CreditCard,
  Gauge,
  GitBranch,
  History,
  LayoutDashboard,
  Link2,
  ListChecks,
  LockKeyhole,
  MapPin,
  Menu,
  Play,
  Plus,
  RefreshCw,
  Server,
  Settings2,
  ShieldCheck,
  Terminal,
  Ticket,
  UsersRound,
  X,
  Zap,
} from 'lucide-react'
import { apiFetch, API_BASE } from './api'

type Page =
  | 'dashboard'
  | 'simulation'
  | 'versions'
  | 'credentials'
  | 'locations'
  | 'logs'

type Role = 'CPO' | 'eMSP' | 'CPO + eMSP'

type OcpiResponse<T> = {
  data: T
  status_code?: number
  status_message?: string
  timestamp?: string
  request_id?: string
  correlation_id?: string
}

type Version = {
  version: string
  url: string
}

type VersionDetails = {
  version: string
  endpoints: Array<{
    identifier: string
    role?: string
    url: string
  }>
}

type Credentials = {
  token: string
  url: string
  roles: Array<{
    role: string
    party_id: string
    country_code: string
    business_details?: {
      name?: string
      website?: string
    }
  }>
}

type Connector = {
  id: string
  standard: string
  format: string
  power_type: string
  max_voltage: number
  max_amperage: number
  max_electric_power?: number
  tariff_ids?: string[]
  terms_and_conditions?: string
  last_updated: string
}

type Evse = {
  uid: string
  evse_id?: string
  status: string
  connectors: Connector[]
  last_updated: string
}

type Location = {
  country_code: string
  party_id: string
  id: string
  publish: boolean
  name?: string
  address: string
  city: string
  country: string
  coordinates?: {
    latitude: string
    longitude: string
  }
  evses?: Evse[]
  time_zone: string
  last_updated: string
}

type ActivityRow = {
  time: string
  from: string
  to: string
  method: string
  endpoint: string
  status: number
}

const nav = [
  { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { id: 'simulation', label: 'Simulation', icon: Play },
  { id: 'versions', label: 'Versions', icon: GitBranch },
  { id: 'credentials', label: 'Credentials', icon: ShieldCheck },
  { id: 'locations', label: 'Locations', icon: MapPin },
  { id: 'logs', label: 'Logs', icon: History },
] satisfies Array<{
  id: Page
  label: string
  icon: React.ComponentType<{ size?: number }>
}>

function App() {
  const [role, setRole] = useState<Role>('CPO + eMSP')
  const [page, setPage] = useState<Page>('dashboard')
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [locations, setLocations] = useState<Location[]>([])
  const [activity, setActivity] = useState<ActivityRow[]>([])
  const [busy, setBusy] = useState(false)
  const [toast, setToast] = useState<string | null>(null)

  const loadLocations = async () => {
    try {
      const body = await apiFetch<OcpiResponse<Location[]>>(
        '/ocpi/cpo/2.2.1/locations?limit=50&offset=0'
      )

      setLocations(body.data || [])
    } catch (e) {
      setToast(e instanceof Error ? e.message : 'Could not load locations')
    }
  }

  useEffect(() => {
    void loadLocations()
  }, [])

  const metrics = useMemo(() => {
    const evses = locations.reduce(
      (sum, l) => sum + (l.evses?.length || 0),
      0
    )

    const sessions = locations.reduce(
      (sum, l) =>
        sum +
        (l.evses || []).filter((e) => e.status === 'CHARGING').length,
      0
    )

    return {
      locations: locations.length,
      evses,
      sessions,
    }
  }, [locations])

  const runQuick = async (endpoint: string, method = 'GET') => {
    setBusy(true)

    try {
      await apiFetch(endpoint, { method })

      const row: ActivityRow = {
        time: new Date().toLocaleTimeString(),
        from: role.includes('CPO') ? 'CPO' : 'eMSP',
        to: role.includes('eMSP') ? 'eMSP' : 'CPO',
        method,
        endpoint,
        status: 200,
      }

      setActivity((prev) => [row, ...prev].slice(0, 8))
      setToast(`${method} ${endpoint} completed`)
    } catch (e) {
      setToast(e instanceof Error ? e.message : 'Request failed')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="app-shell">
      <aside className={`sidebar ${sidebarOpen ? 'open' : 'closed'}`}>
        <div className="brand">
          <div className="brand-mark">OC</div>

          {sidebarOpen && (
            <div>
              <div className="brand-name">OCPI</div>
              <div className="brand-sub">SIMULATOR</div>
            </div>
          )}
        </div>

        <nav>
          {nav.map((item) => {
            const Icon = item.icon

            return (
              <button
                key={item.id}
                className={`nav-item ${page === item.id ? 'active' : ''}`}
                onClick={() => setPage(item.id)}
                title={item.label}
              >
                <Icon size={18} />
                {sidebarOpen && <span>{item.label}</span>}
              </button>
            )
          })}
        </nav>

        {sidebarOpen && (
          <div className="sidebar-footer">
            <div className="env-dot" />
            Backend
            <span>{API_BASE.replace(/^https?:\/\//, '')}</span>
          </div>
        )}
      </aside>

      <main className="main-area">
        <header className="topbar">
          <div className="top-left">
            <button
              className="icon-btn"
              onClick={() => setSidebarOpen((v) => !v)}
            >
              <Menu size={20} />
            </button>

            <div>
              <div className="eyebrow">OCPI 2.2.1-d2</div>
              <div className="page-title">
                {nav.find((n) => n.id === page)?.label}
              </div>
            </div>
          </div>

          <div className="top-right">
            <select
              value={role}
              onChange={(e) => setRole(e.target.value as Role)}
            >
              <option>CPO</option>
              <option>eMSP</option>
              <option>CPO + eMSP</option>
            </select>

            <div className="online-dot" />

            <span className="role-pill">Role: {role}</span>

            <div className="avatar">TS</div>
          </div>
        </header>

        <div className="content">
          {page === 'dashboard' && (
            <Dashboard
              locations={locations}
              metrics={metrics}
              activity={activity}
              onGo={setPage}
              onQuick={runQuick}
              busy={busy}
            />
          )}

          {page === 'simulation' && (
  <Simulation
    onRun={(endpoint, method = 'GET') => {
      const row: ActivityRow = {
        time: new Date().toLocaleTimeString(),
        from: 'eMSP simulator',
        to: 'CPO',
        method,
        endpoint,
        status: 200,
      }

      setActivity((prev) =>
        [row, ...prev].slice(0, 8)
      )

      setToast(
        `${method} ${endpoint} completed`
      )
    }}
    busy={busy}
  />
)}

          {page === 'versions' && (
            <Versions
              onActivity={(r) =>
                setActivity((p) => [r, ...p])
              }
            />
          )}

          {page === 'credentials' && (
            <Credentials
              onActivity={(r) =>
                setActivity((p) => [r, ...p])
              }
            />
          )}

          {page === 'locations' && (
            <Locations
              data={locations}
              reload={loadLocations}
              toast={setToast}
            />
          )}

          {page === 'logs' && <Logs activity={activity} />}
        </div>
      </main>

      {toast && (
        <div className="toast">
          <BadgeCheck size={17} />
          <span>{toast}</span>
          <button onClick={() => setToast(null)}>
            <X size={15} />
          </button>
        </div>
      )}
    </div>
  )
}

function SectionHeader({
  title,
  subtitle,
  action,
}: {
  title: string
  subtitle?: string
  action?: React.ReactNode
}) {
  return (
    <div className="section-header">
      <div>
        <h2>{title}</h2>
        {subtitle && <p>{subtitle}</p>}
      </div>

      {action}
    </div>
  )
}

function Dashboard({
  locations,
  metrics,
  activity,
  onGo,
  onQuick,
  busy,
}: {
  locations: Location[]
  metrics: {
    locations: number
    evses: number
    sessions: number
  }
  activity: ActivityRow[]
  onGo: (p: Page) => void
  onQuick: (endpoint: string, method?: string) => void
  busy: boolean
}) {
  return (
    <>
      <div className="hero">
        <div>
          <div className="mini-label">SIMULATOR CONTROL CENTER</div>

          <h1>Build, test and inspect OCPI flows.</h1>

          <p>
            Use the same simulator as a CPO, an eMSP, or both. Your backend
            remains the source of truth; this UI is the operator console.
          </p>
        </div>

        <div className="hero-actions">
          <button
            className="primary"
            onClick={() => onGo('simulation')}
          >
            <Play size={16} />
            Run simulation
          </button>

          <button
            className="secondary"
            onClick={() => onGo('locations')}
          >
            <MapPin size={16} />
            Open locations
          </button>
        </div>
      </div>

      <div className="metric-grid">
        <Metric
          icon={Link2}
          label="Connections"
          value="2"
          note="Active partners"
        />

        <Metric
          icon={MapPin}
          label="Locations"
          value={String(metrics.locations)}
          note="From CPO GET"
        />

        <Metric
          icon={Cable}
          label="EVSEs"
          value={String(metrics.evses)}
          note="Calculated from locations"
        />

        <Metric
          icon={Activity}
          label="Active sessions"
          value={String(metrics.sessions)}
          note="Charging EVSEs"
        />
      </div>

      <div className="two-col">
        <div className="panel">
          <div className="panel-title">
            <span>Recent activity</span>

            <button
              className="text-btn"
              onClick={() => onGo('logs')}
            >
              View logs →
            </button>
          </div>

          <div className="activity-list">
            {activity.length ? (
              activity.slice(0, 6).map((a, i) => (
                <div className="activity-row" key={i}>
                  <div>
                    <strong>{a.method}</strong>{' '}
                    <span>{a.endpoint}</span>
                  </div>

                  <div className="activity-meta">
                    <b>{a.status}</b>
                    <span>{a.time}</span>
                  </div>
                </div>
              ))
            ) : (
              <div className="empty">
                Run a request from Versions, Credentials or Locations
                to see it here.
              </div>
            )}
          </div>
        </div>

        <div className="panel">
          <div className="panel-title">
            <span>Platform summary</span>
            <span className="success-badge">ONLINE</span>
          </div>

          <div className="summary-grid">
            <Summary label="Party ID" value="TSP" />
            <Summary label="Country code" value="IN" />
            <Summary label="OCPI version" value="2.2.1" />
            <Summary label="Role" value="CPO + eMSP" />
            <Summary label="Backend" value="FastAPI" />
            <Summary label="Storage" value="In-memory" />
          </div>

          <div className="quick-row">
            <button
              onClick={() => onQuick('/ocpi/cpo/versions')}
            >
              <GitBranch size={17} />
              Versions
            </button>

            <button onClick={() => onGo('credentials')}>
              <ShieldCheck size={17} />
              Credentials
            </button>

            <button onClick={() => onGo('locations')}>
              <MapPin size={17} />
              Locations
            </button>
          </div>
        </div>
      </div>
    </>
  )
}

function Metric({
  icon: Icon,
  label,
  value,
  note,
}: {
  icon: React.ComponentType<{ size?: number }>
  label: string
  value: string
  note: string
}) {
  return (
    <div className="metric">
      <div className="metric-icon">
        <Icon size={19} />
      </div>

      <div>
        <div className="metric-label">{label}</div>
        <div className="metric-value">{value}</div>
        <div className="metric-note">{note}</div>
      </div>
    </div>
  )
}

function Summary({
  label,
  value,
}: {
  label: string
  value: string
}) {
  return (
    <div>
      <div className="summary-label">{label}</div>
      <div className="summary-value">{value}</div>
    </div>
  )
}

function Versions({
  onActivity,
}: {
  onActivity: (r: ActivityRow) => void
}) {
  const [kind, setKind] = useState<'cpo' | 'emsp'>('cpo')
  const [versions, setVersions] = useState<Version[]>([])
  const [details, setDetails] = useState<VersionDetails | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const load = async () => {
    setLoading(true)
    setError('')

    try {
      const prefix =
        kind === 'cpo'
          ? '/ocpi/cpo'
          : '/ocpi/emsp'

      const v = await apiFetch<OcpiResponse<Version[]>>(
        `${prefix}/versions`
      )

      const d = await apiFetch<OcpiResponse<VersionDetails>>(
        `${prefix}/2.2.1`
      )

      setVersions(v.data || [])
      setDetails(d.data || null)

      onActivity({
        time: new Date().toLocaleTimeString(),
        from: kind === 'cpo' ? 'UI → CPO' : 'UI → eMSP',
        to: 'Simulator',
        method: 'GET',
        endpoint: `${prefix}/versions`,
        status: 200,
      })

      onActivity({
        time: new Date().toLocaleTimeString(),
        from: kind === 'cpo' ? 'UI → CPO' : 'UI → eMSP',
        to: 'Simulator',
        method: 'GET',
        endpoint: `${prefix}/2.2.1`,
        status: 200,
      })
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Request failed')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void load()
  }, [kind])

  return (
    <>
      <SectionHeader
        title="Versions"
        subtitle="Discover supported OCPI versions and version-specific endpoints."
        action={
          <button
            className="secondary"
            onClick={load}
            disabled={loading}
          >
            <RefreshCw size={16} />
            Refresh
          </button>
        }
      />

      <div className="switch-row">
        <button
          className={kind === 'cpo' ? 'switch active' : 'switch'}
          onClick={() => setKind('cpo')}
        >
          CPO endpoint
        </button>

        <button
          className={kind === 'emsp' ? 'switch active' : 'switch'}
          onClick={() => setKind('emsp')}
        >
          eMSP endpoint
        </button>
      </div>

      {error && <div className="error-box">{error}</div>}

      <div className="three-col">
        <div className="panel span-2">
          <div className="panel-title">
            <span>Supported versions</span>
            <span className="count-badge">{versions.length}</span>
          </div>

          {versions.length === 0 ? (
            <div className="empty">
              No version data returned.
            </div>
          ) : (
            versions.map((v) => (
              <div className="version-card" key={v.version}>
                <div className="version-main">
                  <div className="version-badge">
                    {v.version}
                  </div>

                  <div>
                    <strong>OCPI {v.version}</strong>
                    <div className="muted">
                      Version discovery endpoint
                    </div>
                  </div>
                </div>

                <code>{v.url}</code>
              </div>
            ))
          )}
        </div>

        <div className="panel">
          <div className="panel-title">
            <span>What this proves</span>
          </div>

          <div className="callout">
            <GitBranch size={18} />

            <div>
              <strong>Discovery first</strong>
              <p>
                The Versions module tells a peer which OCPI version
                is available and where version details can be fetched.
              </p>
            </div>
          </div>

          <div className="flow">
            <span>GET /versions</span>
            <ArrowLeftRight size={15} />
            <span>GET /2.2.1</span>
          </div>
        </div>
      </div>

      <div className="panel">
        <div className="panel-title">
          <span>2.2.1 endpoint map</span>
          <span className="success-badge">
            {details?.version || '—'}
          </span>
        </div>

        <div className="endpoint-grid">
          {details?.endpoints?.map((e, i) => (
            <div
              className="endpoint-row"
              key={`${e.identifier}-${i}`}
            >
              <div>
                <strong>{e.identifier}</strong>
                <div className="muted">
                  {e.role || 'interface'}
                </div>
              </div>

              <code>{e.url}</code>
            </div>
          ))}
        </div>

        {!details && (
          <div className="empty">
            No version details loaded.
          </div>
        )}
      </div>
    </>
  )
}

function Credentials({
  onActivity,
}: {
  onActivity: (r: ActivityRow) => void
}) {
  const [kind, setKind] = useState<'cpo' | 'emsp'>('cpo')
  const [auth, setAuth] = useState('')
  const [data, setData] = useState<Credentials | null>(null)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')

  const path = `/ocpi/${kind}/2.2.1/credentials`

  const fetchCredentials = async () => {
    setError('')
    setMessage('')

    try {
      const body = await apiFetch<OcpiResponse<Credentials>>(
        path,
        {},
        auth
      )

      setData(body.data)

      setMessage(
        'Credentials loaded successfully. Token is masked in this UI.'
      )

      onActivity({
        time: new Date().toLocaleTimeString(),
        from: 'UI',
        to: kind.toUpperCase(),
        method: 'GET',
        endpoint: path,
        status: 200,
      })
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Request failed')
    }
  }

  const handshake = async () => {
    setError('')
    setMessage('')

    try {
      const body =
        await apiFetch<OcpiResponse<Credentials>>(
          '/ocpi/emsp/handshake',
          { method: 'POST' }
        )

      setData(body.data)

      setMessage(
        'eMSP handshake completed / reused the stored connection.'
      )

      onActivity({
        time: new Date().toLocaleTimeString(),
        from: 'eMSP simulator',
        to: 'CPO',
        method: 'POST',
        endpoint: '/ocpi/emsp/handshake',
        status: 200,
      })
    } catch (e) {
      setError(
        e instanceof Error ? e.message : 'Handshake failed'
      )
    }
  }

  return (
    <>
      <SectionHeader
        title="Credentials"
        subtitle="Inspect the credential state and exercise the authentication bootstrap."
      />

      <div className="two-col">
        <div className="panel">
          <div className="panel-title">
            <span>Credential endpoint</span>
            <span className="count-badge">
              {kind.toUpperCase()}
            </span>
          </div>

          <div className="switch-row">
            <button
              className={
                kind === 'cpo' ? 'switch active' : 'switch'
              }
              onClick={() => setKind('cpo')}
            >
              CPO
            </button>

            <button
              className={
                kind === 'emsp' ? 'switch active' : 'switch'
              }
              onClick={() => setKind('emsp')}
            >
              eMSP
            </button>
          </div>

          <label>
            Authorization header{' '}
            <span className="muted">
              (only needed for secured GET/POST/PUT/DELETE tests)
            </span>
          </label>

          <input
            value={auth}
            onChange={(e) => setAuth(e.target.value)}
            placeholder="Token &lt;base64-token&gt;"
          />

          <div className="button-row">
            <button
              className="primary"
              onClick={fetchCredentials}
            >
              <LockKeyhole size={16} />
              Fetch credentials
            </button>

            <button
              className="secondary"
              onClick={() => void handshake()}
            >
              <Zap size={16} />
              Run eMSP handshake
            </button>
          </div>

          <div className="endpoint-chip">
            GET {path}
          </div>

          {(error || message) && (
            <div
              className={
                error ? 'error-box' : 'success-box'
              }
            >
              {error || message}
            </div>
          )}
        </div>

        <div className="panel">
          <div className="panel-title">
            <span>Connection state</span>
            <span className="success-badge">READY</span>
          </div>

          <div className="credential-summary">
            <Summary
              label="Role"
              value={data?.roles?.[0]?.role || '—'}
            />

            <Summary
              label="Party ID"
              value={
                data?.roles?.[0]?.party_id || '—'
              }
            />

            <Summary
              label="Country"
              value={
                data?.roles?.[0]?.country_code || '—'
              }
            />

            <Summary
              label="URL"
              value={data?.url || '—'}
            />
          </div>

          {data?.roles?.[0]?.business_details && (
            <div className="callout">
              <UsersRound size={18} />

              <div>
                <strong>
                  {
                    data.roles[0].business_details
                      .name || 'Business details'
                  }
                </strong>

                <p>
                  {
                    data.roles[0].business_details
                      .website || 'No website provided'
                  }
                </p>
              </div>
            </div>
          )}

          <div className="security-note">
            <ShieldCheck size={17} />

            <span>
              Authentication tokens are intentionally
              masked/not exposed in the overview.
            </span>
          </div>
        </div>
      </div>

      <div className="panel">
        <div className="panel-title">
          <span>Credentials flow</span>
        </div>

        <div className="flow-large">
          <div>
            <span className="step-dot">1</span>
            <strong>Versions</strong>
            <small>
              GET /versions + GET /2.2.1
            </small>
          </div>

          <div className="flow-arrow">→</div>

          <div>
            <span className="step-dot">2</span>
            <strong>Credentials</strong>
            <small>POST /credentials</small>
          </div>

          <div className="flow-arrow">→</div>

          <div>
            <span className="step-dot">3</span>
            <strong>Authenticated</strong>
            <small>Use the returned token</small>
          </div>
        </div>
      </div>
    </>
  )
}

/*
 * LOCATIONS
 *
 * Important change:
 * - viewData stores the actual result from the latest CPO GET request.
 * - Apply no longer calls reload() immediately afterward.
 * - Therefore limit/offset/date_from/date_to results remain visible.
 */
function Locations({
  data,
  reload,
  toast,
}: {
  data: Location[]
  reload: () => Promise<void>
  toast: (m: string) => void
}) {
  const [search, setSearch] = useState('')
  const [status, setStatus] = useState('ALL')
  const [limit, setLimit] = useState('10')
  const [offset, setOffset] = useState('0')
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')
  const [selected, setSelected] = useState<Location | null>(null)

  // ---------------------------------------------------------
  // CREATE LOCATION
  // ---------------------------------------------------------
  const [createOpen, setCreateOpen] = useState(false)
  const [createBusy, setCreateBusy] = useState(false)
  const [createError, setCreateError] = useState('')

  type CreateEvseForm = {
    uid: string
    evse_id: string
    status: string
    connector_id: string
    standard: string
    format: string
    power_type: string
    max_voltage: string
    max_amperage: string
    max_electric_power: string
  }

  const defaultCreateEvse = (): CreateEvseForm => ({
    uid: '',
    evse_id: '',
    status: 'AVAILABLE',
    connector_id: '1',
    standard: 'IEC_62196_T2',
    format: 'SOCKET',
    power_type: 'AC_3_PHASE',
    max_voltage: '400',
    max_amperage: '32',
    max_electric_power: '22000',
  })

  const [createLocationForm, setCreateLocationForm] = useState({
    id: '',
    name: '',
    address: '',
    city: '',
    postal_code: '',
    state: '',
    country: 'IND',
    latitude: '',
    longitude: '',
    time_zone: 'Asia/Kolkata',
    evses: [defaultCreateEvse()],
  })

  const resetCreateLocationForm = () => {
    setCreateLocationForm({
      id: '',
      name: '',
      address: '',
      city: '',
      postal_code: '',
      state: '',
      country: 'IND',
      latitude: '',
      longitude: '',
      time_zone: 'Asia/Kolkata',
      evses: [defaultCreateEvse()],
    })
  }

  const startCreateLocation = () => {
    resetCreateLocationForm()
    setCreateError('')
    setCreateOpen(true)
  }

  const closeCreateLocation = () => {
    if (createBusy) return
    setCreateOpen(false)
    setCreateError('')
  }

  const addCreateEvse = () => {
    setCreateLocationForm((f) => ({
      ...f,
      evses: [
        ...f.evses,
        {
          ...defaultCreateEvse(),
          uid: `EVSE${String(f.evses.length + 1).padStart(3, '0')}`,
          evse_id: `IN*TSP*E${String(f.evses.length + 1).padStart(3, '3')}`,
        },
      ],
    }))
  }

  const removeCreateEvse = (index: number) => {
    setCreateLocationForm((f) => {
      if (f.evses.length <= 1) return f

      return {
        ...f,
        evses: f.evses.filter((_, i) => i !== index),
      }
    })
  }

  const updateCreateEvse = (
    index: number,
    field: keyof CreateEvseForm,
    value: string
  ) => {
    setCreateLocationForm((f) => ({
      ...f,
      evses: f.evses.map((evse, i) =>
        i === index
          ? { ...evse, [field]: value }
          : evse
      ),
    }))
  }

  const createNewLocation = async () => {
    const f = createLocationForm

    const requiredLocationFields: Array<[string, string]> = [
      ['Location ID', f.id],
      ['Location name', f.name],
      ['Address', f.address],
      ['City', f.city],
      ['Postal code', f.postal_code],
      ['State', f.state],
      ['Latitude', f.latitude],
      ['Longitude', f.longitude],
    ]

    const missingLocation = requiredLocationFields.find(
      ([, value]) => !value.trim()
    )

    if (missingLocation) {
      setCreateError(`${missingLocation[0]} is required.`)
      return
    }

    for (let index = 0; index < f.evses.length; index += 1) {
      const evse = f.evses[index]
      const evseNumber = index + 1

      const requiredEvseFields: Array<[string, string]> = [
        [`EVSE ${evseNumber} UID`, evse.uid],
        [`EVSE ${evseNumber} ID`, evse.evse_id],
        [`EVSE ${evseNumber} Connector ID`, evse.connector_id],
      ]

      const missingEvse = requiredEvseFields.find(
        ([, value]) => !value.trim()
      )

      if (missingEvse) {
        setCreateError(`${missingEvse[0]} is required.`)
        return
      }

      const maxVoltage = Number(evse.max_voltage)
      const maxAmperage = Number(evse.max_amperage)
      const maxPower = Number(evse.max_electric_power)

      if (
        !Number.isInteger(maxVoltage) ||
        maxVoltage <= 0 ||
        !Number.isInteger(maxAmperage) ||
        maxAmperage <= 0 ||
        !Number.isInteger(maxPower) ||
        maxPower <= 0
      ) {
        setCreateError(
          `EVSE ${evseNumber}: voltage, amperage and electric power must be positive integers.`
        )
        return
      }
    }

    setCreateBusy(true)
    setCreateError('')

    const lastUpdated = new Date().toISOString()

    const payload = {
      country_code: 'IN',
      party_id: 'TSP',
      id: f.id.trim(),
      publish: true,
      publish_allowed_to: null,
      name: f.name.trim(),
      address: f.address.trim(),
      city: f.city.trim(),
      postal_code: f.postal_code.trim(),
      state: f.state.trim(),
      country: f.country.trim().toUpperCase(),
      coordinates: {
        latitude: f.latitude.trim(),
        longitude: f.longitude.trim(),
      },
      related_locations: null,
      parking_type: null,
      evses: f.evses.map((evse) => ({
        uid: evse.uid.trim(),
        evse_id: evse.evse_id.trim(),
        status: evse.status,
        status_schedule: null,
        capabilities: null,
        connectors: [
          {
            id: evse.connector_id.trim(),
            standard: evse.standard,
            format: evse.format,
            power_type: evse.power_type,
            max_voltage: Number(evse.max_voltage),
            max_amperage: Number(evse.max_amperage),
            max_electric_power: Number(evse.max_electric_power),
            tariff_ids: null,
            terms_and_conditions: null,
            last_updated: lastUpdated,
          },
        ],
        floor_level: null,
        coordinates: {
          latitude: f.latitude.trim(),
          longitude: f.longitude.trim(),
        },
        physical_reference: null,
        directions: null,
        parking_restrictions: null,
        images: null,
        last_updated: lastUpdated,
      })),
      directions: null,
      operator: {
        name: 'OCPI Simulator',
        website: null,
      },
      suboperator: null,
      owner: null,
      facilities: null,
      time_zone: f.time_zone.trim(),
      opening_times: null,
      charging_when_closed: true,
      images: null,
      energy_mix: null,
      last_updated: lastUpdated,
    }

    try {
      const body = await apiFetch<OcpiResponse<Location>>(
        '/ocpi/simulator/cpo/2.2.1/locations',
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(payload),
        }
      )

      if (
        body.status_code !== undefined &&
        body.status_code !== 1000
      ) {
        throw new Error(
          body.status_message ||
            `Create Location failed with status ${body.status_code}`
        )
      }

      setCreateOpen(false)
      await reload()
      toast(
        `Location ${f.id.trim()} created with ${f.evses.length} EVSE(s)`
      )
    } catch (e) {
      setCreateError(
        e instanceof Error
          ? e.message
          : 'Could not create Location'
      )
    } finally {
      setCreateBusy(false)
    }
  }

  const [viewData, setViewData] = useState<Location[]>(data)

  // Location PATCH
  const [editingLocation, setEditingLocation] = useState(false)
  const [editLocationName, setEditLocationName] = useState('')

  // Location PUT
  const [putName, setPutName] = useState('')
  const [putBusy, setPutBusy] = useState(false)
  const [putError, setPutError] = useState('')

  // EVSE PATCH
  const [editingEvse, setEditingEvse] = useState<string | null>(null)
  const [editEvseStatus, setEditEvseStatus] = useState('AVAILABLE')

  // EVSE PUT
const [putEvseUid, setPutEvseUid] = useState<string | null>(null)
const [putEvseStatus, setPutEvseStatus] = useState('AVAILABLE')
const [putEvseBusy, setPutEvseBusy] = useState(false)
const [putEvseError, setPutEvseError] = useState('')

  // Connector PATCH
  const [editingConnector, setEditingConnector] = useState<string | null>(null)
  const [editingConnectorEvse, setEditingConnectorEvse] =
    useState<string | null>(null)
  const [editConnectorPower, setEditConnectorPower] = useState('')
// Connector PUT
const [putConnector, setPutConnector] = useState<string | null>(null)
const [putConnectorEvse, setPutConnectorEvse] =
  useState<string | null>(null)
const [putConnectorPower, setPutConnectorPower] = useState('')
const [putConnectorBusy, setPutConnectorBusy] = useState(false)
const [putConnectorError, setPutConnectorError] = useState('')

  const [patchBusy, setPatchBusy] = useState(false)
  const [patchError, setPatchError] = useState('')

// ---------------------------------------------------------
// CPO GET one Location
// ---------------------------------------------------------
const openLocation = async (locationId: string) => {
  try {
    const body =
      await apiFetch<OcpiResponse<Location>>(
        `/ocpi/cpo/2.2.1/locations/${encodeURIComponent(locationId)}`
      )

    // Use the fresh object returned by the backend.
    setSelected(body.data)

    toast(
      `Location ${locationId} loaded successfully`
    )
  } catch (e) {
    toast(
      e instanceof Error
        ? e.message
        : 'Could not load Location'
    )
  }
}

// ---------------------------------------------------------
// CPO GET one EVSE
// ---------------------------------------------------------
const openEvse = async (
  locationId: string,
  evseUid: string
) => {
  try {
    const body =
      await apiFetch<OcpiResponse<Evse>>(
        `/ocpi/cpo/2.2.1/locations/` +
        `${encodeURIComponent(locationId)}/` +
        `${encodeURIComponent(evseUid)}`
      )

    /*
     * Replace the EVSE inside the currently selected
     * Location with the fresh object returned by the backend.
     */
    setSelected((current) => {
      if (!current) return current

      return {
        ...current,
        evses: (current.evses || []).map(
          (evse) =>
            evse.uid === evseUid
              ? body.data
              : evse
        ),
      }
    })

    toast(
      `EVSE ${evseUid} loaded successfully`
    )
  } catch (e) {
    toast(
      e instanceof Error
        ? e.message
        : 'Could not load EVSE'
    )
  }
}
// ---------------------------------------------------------
// CPO GET one Connector
// ---------------------------------------------------------
const openConnector = async (
  locationId: string,
  evseUid: string,
  connectorId: string
) => {
  try {
    const body =
      await apiFetch<OcpiResponse<Connector>>(
        `/ocpi/cpo/2.2.1/locations/` +
        `${encodeURIComponent(locationId)}/` +
        `${encodeURIComponent(evseUid)}/` +
        `${encodeURIComponent(connectorId)}`
      )

    /*
     * Replace the connector inside the selected
     * Location with the fresh backend response.
     */
    setSelected((current) => {
      if (!current) return current

      return {
        ...current,
        evses: (current.evses || []).map(
          (evse) => {
            if (evse.uid !== evseUid) {
              return evse
            }

            return {
              ...evse,
              connectors: evse.connectors.map(
                (connector) =>
                  connector.id === connectorId
                    ? body.data
                    : connector
              ),
            }
          }
        ),
      }
    })

    toast(
      `Connector ${connectorId} loaded successfully`
    )
  } catch (e) {
    toast(
      e instanceof Error
        ? e.message
        : 'Could not load Connector'
    )
  }
}
  useEffect(() => {
    setViewData(data)

    if (selected) {
      const latest = data.find(
        (location) => location.id === selected.id
      )

      if (latest) {
        setSelected(latest)
      }
    }
  }, [data])

  // ---------------------------------------------------------
  // Frontend search/status filter
  // ---------------------------------------------------------
  const filtered = viewData.filter(
    (l) =>
      (l.name || l.id)
        .toLowerCase()
        .includes(search.toLowerCase()) &&
      (status === 'ALL' ||
        (l.evses?.[0]?.status || 'UNKNOWN') === status)
  )

  // ---------------------------------------------------------
  // CPO GET Locations
  // ---------------------------------------------------------
  const runFilteredGet = async () => {
    const qs = new URLSearchParams({
      limit,
      offset,
    })

    if (dateFrom) {
      qs.set(
        'date_from',
        new Date(dateFrom).toISOString()
      )
    }

    if (dateTo) {
      qs.set(
        'date_to',
        new Date(dateTo).toISOString()
      )
    }

    try {
      const body =
        await apiFetch<OcpiResponse<Location[]>>(
          `/ocpi/cpo/2.2.1/locations?${qs.toString()}`
        )

      setViewData(body.data || [])

      toast(
        `Loaded ${body.data?.length || 0} location(s)`
      )
    } catch (e) {
      toast(
        e instanceof Error
          ? e.message
          : 'Request failed'
      )
    }
  }

  // ---------------------------------------------------------
  // Start Location PATCH editing
  // ---------------------------------------------------------
  const startLocationEditing = () => {
    if (!selected) return

    setEditLocationName(selected.name || '')
    setPatchError('')
    setEditingLocation(true)
  }

  // ---------------------------------------------------------
  // Location PATCH
  // ---------------------------------------------------------
  const applyLocationPatch = async () => {
    if (!selected) return

    const trimmedName = editLocationName.trim()

    if (!trimmedName) {
      setPatchError('Location name cannot be empty.')
      return
    }

    setPatchBusy(true)
    setPatchError('')

    const lastUpdated = new Date().toISOString()

    const endpoint =
      `/ocpi/emsp/2.2.1/locations/` +
      `${encodeURIComponent(selected.country_code)}/` +
      `${encodeURIComponent(selected.party_id)}/` +
      `${encodeURIComponent(selected.id)}`

    try {
      await apiFetch<OcpiResponse<null>>(
        endpoint,
        {
          method: 'PATCH',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            name: trimmedName,
            last_updated: lastUpdated,
          }),
        }
      )

      setEditingLocation(false)

      await reload()

      toast(
        `Location ${selected.id} updated successfully`
      )
    } catch (e) {
      setPatchError(
        e instanceof Error
          ? e.message
          : 'PATCH request failed'
      )
    } finally {
      setPatchBusy(false)
    }
  }

  // ---------------------------------------------------------
  // Location PUT
  // ---------------------------------------------------------
  const startLocationPut = () => {
    if (!selected) return

    setPutName(selected.name || '')
    setPutError('')
  }

  const applyLocationPut = async () => {
    if (!selected) return

    const trimmedName = putName.trim()

    if (!trimmedName) {
      setPutError('Location name cannot be empty.')
      return
    }

    setPutBusy(true)
    setPutError('')

    const endpoint =
      `/ocpi/emsp/2.2.1/locations/` +
      `${encodeURIComponent(selected.country_code)}/` +
      `${encodeURIComponent(selected.party_id)}/` +
      `${encodeURIComponent(selected.id)}`

    /*
     * PUT sends the complete Location object.
     *
     * We copy the currently stored Location so the PUT
     * does not accidentally remove required fields.
     *
     * The name is taken from the PUT form and last_updated
     * is refreshed for this update.
     */
    const putLocation: Location = {
      ...selected,
      name: trimmedName,
      last_updated: new Date().toISOString(),
    }

    try {
      const body =
        await apiFetch<OcpiResponse<Location>>(
          endpoint,
          {
            method: 'PUT',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify(putLocation),
          }
        )

      /*
       * Display the complete object returned by the backend.
       */
      setSelected(body.data)

      /*
       * Refresh the CPO GET list.
       */
      await reload()

      toast(
        `Location ${selected.id} PUT successful`
      )
    } catch (e) {
      setPutError(
        e instanceof Error
          ? e.message
          : 'PUT request failed'
      )
    } finally {
      setPutBusy(false)
    }
  }

  // ---------------------------------------------------------
  // EVSE PATCH
  // ---------------------------------------------------------
  const startEvseEditing = (evse: Evse) => {
    setEditingEvse(evse.uid)
    setEditEvseStatus(evse.status)
    setPatchError('')
  }

  const applyEvsePatch = async (evseUid: string) => {
    if (!selected) return

    setPatchBusy(true)
    setPatchError('')

    const lastUpdated = new Date().toISOString()

    const endpoint =
      `/ocpi/emsp/2.2.1/locations/` +
      `${encodeURIComponent(selected.country_code)}/` +
      `${encodeURIComponent(selected.party_id)}/` +
      `${encodeURIComponent(selected.id)}/` +
      `${encodeURIComponent(evseUid)}`

    try {
      await apiFetch<OcpiResponse<null>>(
        endpoint,
        {
          method: 'PATCH',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            status: editEvseStatus,
            last_updated: lastUpdated,
          }),
        }
      )

      setEditingEvse(null)

      await reload()

      toast(
        `EVSE ${evseUid} updated successfully`
      )
    } catch (e) {
      setPatchError(
        e instanceof Error
          ? e.message
          : 'EVSE PATCH request failed'
      )
    } finally {
      setPatchBusy(false)
    }
  }

// ---------------------------------------------------------
// Start EVSE PUT editing
// ---------------------------------------------------------
const startEvsePut = (evse: Evse) => {
  setPutEvseUid(evse.uid)
  setPutEvseStatus(evse.status)
  setPutEvseError('')
}

// ---------------------------------------------------------
// EVSE PUT
// ---------------------------------------------------------
const applyEvsePut = async (evseUid: string) => {
  if (!selected) return

  const currentEvse = selected.evses?.find(
    (evse) => evse.uid === evseUid
  )

  if (!currentEvse) {
    setPutEvseError('EVSE not found.')
    return
  }

  setPutEvseBusy(true)
  setPutEvseError('')

  const endpoint =
    `/ocpi/emsp/2.2.1/locations/` +
    `${encodeURIComponent(selected.country_code)}/` +
    `${encodeURIComponent(selected.party_id)}/` +
    `${encodeURIComponent(selected.id)}/` +
    `${encodeURIComponent(evseUid)}`

  /*
   * PUT requires the complete EVSE object.
   *
   * We copy the existing EVSE so that its connectors
   * and all other fields are preserved.
   *
   * Only status and last_updated are changed for
   * this demo operation.
   */
  const putEvse: Evse = {
    ...currentEvse,
    status: putEvseStatus,
    connectors: [...currentEvse.connectors],
    last_updated: new Date().toISOString(),
  }

  try {
    const body =
      await apiFetch<OcpiResponse<Evse>>(
        endpoint,
        {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(putEvse),
        }
      )

    setPutEvseUid(null)

    await reload()

    toast(
      `EVSE ${evseUid} PUT successful`
    )
  } catch (e) {
    setPutEvseError(
      e instanceof Error
        ? e.message
        : 'EVSE PUT request failed'
    )
  } finally {
    setPutEvseBusy(false)
  }
}


  // ---------------------------------------------------------
  // Connector PATCH
  // ---------------------------------------------------------
  const startConnectorEditing = (
    evseUid: string,
    connector: Connector
  ) => {
    setEditingConnector(connector.id)
    setEditingConnectorEvse(evseUid)
    setEditConnectorPower(
      String(connector.max_electric_power || '')
    )
    setPatchError('')
  }

  const applyConnectorPatch = async (
    evseUid: string,
    connectorId: string
  ) => {
    if (!selected) return

    const power = Number(editConnectorPower)

    if (!Number.isInteger(power) || power <= 0) {
      setPatchError(
        'Max electric power must be a positive integer.'
      )
      return
    }

    setPatchBusy(true)
    setPatchError('')

    const lastUpdated = new Date().toISOString()

    const endpoint =
      `/ocpi/emsp/2.2.1/locations/` +
      `${encodeURIComponent(selected.country_code)}/` +
      `${encodeURIComponent(selected.party_id)}/` +
      `${encodeURIComponent(selected.id)}/` +
      `${encodeURIComponent(evseUid)}/` +
      `${encodeURIComponent(connectorId)}`

    try {
      await apiFetch<OcpiResponse<null>>(
        endpoint,
        {
          method: 'PATCH',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            max_electric_power: power,
            last_updated: lastUpdated,
          }),
        }
      )

      setEditingConnector(null)
      setEditingConnectorEvse(null)

      await reload()

      toast(
        `Connector ${connectorId} updated successfully`
      )
    } catch (e) {
      setPatchError(
        e instanceof Error
          ? e.message
          : 'Connector PATCH request failed'
      )
    } finally {
      setPatchBusy(false)
    }
  }


  // ---------------------------------------------------------
// Start Connector PUT editing
// ---------------------------------------------------------
const startConnectorPut = (
  evseUid: string,
  connector: Connector
) => {
  setPutConnector(connector.id)
  setPutConnectorEvse(evseUid)

  setPutConnectorPower(
    String(connector.max_electric_power || '')
  )

  setPutConnectorError('')
}

// ---------------------------------------------------------
// Connector PUT
// ---------------------------------------------------------
const applyConnectorPut = async (
  evseUid: string,
  connectorId: string
) => {
  if (!selected) return

  const evse = selected.evses?.find(
    (item) => item.uid === evseUid
  )

  if (!evse) {
    setPutConnectorError('EVSE not found.')
    return
  }

  const connector = evse.connectors.find(
    (item) => item.id === connectorId
  )

  if (!connector) {
    setPutConnectorError('Connector not found.')
    return
  }

  const power = Number(putConnectorPower)

  if (!Number.isInteger(power) || power <= 0) {
    setPutConnectorError(
      'Max electric power must be a positive integer.'
    )
    return
  }

  setPutConnectorBusy(true)
  setPutConnectorError('')

  const endpoint =
    `/ocpi/emsp/2.2.1/locations/` +
    `${encodeURIComponent(selected.country_code)}/` +
    `${encodeURIComponent(selected.party_id)}/` +
    `${encodeURIComponent(selected.id)}/` +
    `${encodeURIComponent(evseUid)}/` +
    `${encodeURIComponent(connectorId)}`

  /*
   * Connector PUT requires the complete Connector object.
   *
   * We preserve the existing connector fields and only
   * change max_electric_power and last_updated.
   */
  const completeConnector: Connector = {
    ...connector,
    max_electric_power: power,
    last_updated: new Date().toISOString(),
  }

  try {
    await apiFetch<OcpiResponse<Connector>>(
      endpoint,
      {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(completeConnector),
      }
    )

    setPutConnector(null)
    setPutConnectorEvse(null)

    await reload()

    toast(
      `Connector ${connectorId} PUT successful`
    )
  } catch (e) {
    setPutConnectorError(
      e instanceof Error
        ? e.message
        : 'Connector PUT request failed'
    )
  } finally {
    setPutConnectorBusy(false)
  }
}

  // ---------------------------------------------------------
  // Close modal
  // ---------------------------------------------------------
  const closeModal = () => {
    setSelected(null)
    setEditingLocation(false)
    setEditingEvse(null)
    setEditingConnector(null)
    setEditingConnectorEvse(null)
    setPatchError('')
    setPutError('')
  }

  return (
    <>
      <SectionHeader
        title="Locations"
        subtitle="CPO sender view: Locations → EVSEs → Connectors."
        action={
          <div className="button-row">
            <button
              className="primary"
              onClick={startCreateLocation}
            >
              <Plus size={16} />
              Add Location
            </button>

            <button
              className="secondary"
              onClick={() => void reload()}
            >
              <RefreshCw size={16} />
              Refresh
            </button>
          </div>
        }
      />

      {/* =====================================================
          FILTERS
      ===================================================== */}
      <div className="filter-bar panel">
        <div className="search">
          <Ticket size={16} />

          <input
            value={search}
            onChange={(e) =>
              setSearch(e.target.value)
            }
            placeholder="Search location..."
          />
        </div>

        <select
          value={status}
          onChange={(e) =>
            setStatus(e.target.value)
          }
        >
          <option value="ALL">Status: All</option>
          <option>AVAILABLE</option>
          <option>BLOCKED</option>
          <option>CHARGING</option>
          <option>INOPERATIVE</option>
          <option>OUTOFORDER</option>
          <option>PLANNED</option>
          <option>REMOVED</option>
          <option>UNKNOWN</option>
        </select>

        <input
          type="datetime-local"
          value={dateFrom}
          onChange={(e) =>
            setDateFrom(e.target.value)
          }
        />

        <input
          type="datetime-local"
          value={dateTo}
          onChange={(e) =>
            setDateTo(e.target.value)
          }
        />

        <input
          className="small-input"
          type="number"
          min="1"
          value={limit}
          onChange={(e) =>
            setLimit(e.target.value)
          }
        />

        <input
          className="small-input"
          type="number"
          min="0"
          value={offset}
          onChange={(e) =>
            setOffset(e.target.value)
          }
        />

        <button
          className="primary"
          onClick={runFilteredGet}
        >
          <BarChart3 size={16} />
          Apply
        </button>
      </div>

      {/* =====================================================
          LOCATION TABLE
      ===================================================== */}
      <div className="panel table-panel">
        <div className="panel-title">
          <span>Locations</span>

          <span className="muted">
            Showing {filtered.length} loaded
          </span>
        </div>

        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Location ID</th>
                <th>Name</th>
                <th>City</th>
                <th>EVSEs</th>
                <th>Connectors</th>
                <th>Status</th>
                <th>Updated</th>
                <th>Action</th>
              </tr>
            </thead>

            <tbody>
              {filtered.map((l) => {
                const evses = l.evses || []

                const connectors = evses.reduce(
                  (sum, e) =>
                    sum +
                    (e.connectors?.length || 0),
                  0
                )

                const st =
                  evses[0]?.status || '—'

                return (
                  <tr key={l.id}>
                    <td>
                      <strong>{l.id}</strong>
                    </td>

                    <td>
                      {l.name || '—'}
                    </td>

                    <td>{l.city}</td>

                    <td>{evses.length}</td>

                    <td>{connectors}</td>

                    <td>
                      <span
                        className={`status ${st.toLowerCase()}`}
                      >
                        {st}
                      </span>
                    </td>

                    <td>
                      {new Date(
                        l.last_updated
                      ).toLocaleString()}
                    </td>

                    <td>
                      <button
  className="icon-text"
  onClick={() =>
    void openLocation(l.id)
  }
>
  <CircleDot size={15} />
  View
</button>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>

          {filtered.length === 0 && (
            <div className="empty">
              No matching locations.
            </div>
          )}
        </div>
      </div>

      {/* =====================================================
          HIERARCHY + PAGINATION
      ===================================================== */}
      <div className="panel two-panels">
        <div>
          <div className="panel-title">
            <span>OCPI hierarchy</span>
          </div>

          <div className="tree">
            <div>
              <MapPin size={16} />
              Location
            </div>

            <div>
              <Server size={16} />
              EVSE
            </div>

            <div>
              <Cable size={16} />
              Connector
            </div>
          </div>
        </div>

        <div>
          <div className="panel-title">
            <span>Pagination</span>
          </div>

          <div className="pagination-copy">
            <strong>limit</strong> = maximum number returned
            <br />

            <strong>offset</strong> = number of records skipped
            <br />

            <strong>date_from</strong> = updated on/after
            <br />

            <strong>date_to</strong> = updated before
          </div>
        </div>
      </div>

      {/* =====================================================
          CREATE LOCATION MODAL
      ===================================================== */}
      {createOpen && (
        <div
          className="modal-backdrop"
          onClick={closeCreateLocation}
        >
          <div
            className="modal"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="modal-head">
              <div>
                <div className="eyebrow">
                  CREATE LOCATION
                </div>

                <h3>Add a new CPO Location</h3>
              </div>

              <button
                className="icon-btn"
                onClick={closeCreateLocation}
                disabled={createBusy}
              >
                <X size={18} />
              </button>
            </div>

            <div className="security-note">
              <MapPin size={17} />

              <span>
                This creates a CPO-owned Location in the
                simulator. The country code is IN and the
                Party ID is TSP for this simulator.
              </span>
            </div>

            <div className="panel inset">
              <div className="panel-title">
                <span>Location details</span>
                <span className="count-badge">CPO</span>
              </div>

              <div className="detail-grid create-grid">
                <div className="patch-form">
                  <label>Location ID</label>
                  <input
                    value={createLocationForm.id}
                    onChange={(e) =>
                      setCreateLocationForm((f) => ({
                        ...f,
                        id: e.target.value,
                      }))
                    }
                    placeholder="LOC002"
                  />
                </div>

                <div className="patch-form">
                  <label>Location name</label>
                  <input
                    value={createLocationForm.name}
                    onChange={(e) =>
                      setCreateLocationForm((f) => ({
                        ...f,
                        name: e.target.value,
                      }))
                    }
                    placeholder="Bengaluru Charging Hub"
                  />
                </div>

                <div className="patch-form">
                  <label>Address</label>
                  <input
                    value={createLocationForm.address}
                    onChange={(e) =>
                      setCreateLocationForm((f) => ({
                        ...f,
                        address: e.target.value,
                      }))
                    }
                    placeholder="MG Road"
                  />
                </div>

                <div className="patch-form">
                  <label>City</label>
                  <input
                    value={createLocationForm.city}
                    onChange={(e) =>
                      setCreateLocationForm((f) => ({
                        ...f,
                        city: e.target.value,
                      }))
                    }
                    placeholder="Bengaluru"
                  />
                </div>

                <div className="patch-form">
                  <label>Postal code</label>
                  <input
                    value={createLocationForm.postal_code}
                    onChange={(e) =>
                      setCreateLocationForm((f) => ({
                        ...f,
                        postal_code: e.target.value,
                      }))
                    }
                    placeholder="560001"
                  />
                </div>

                <div className="patch-form">
                  <label>State</label>
                  <input
                    value={createLocationForm.state}
                    onChange={(e) =>
                      setCreateLocationForm((f) => ({
                        ...f,
                        state: e.target.value,
                      }))
                    }
                    placeholder="Karnataka"
                  />
                </div>

                <div className="patch-form">
                  <label>Country</label>
                  <input
                    value={createLocationForm.country}
                    onChange={(e) =>
                      setCreateLocationForm((f) => ({
                        ...f,
                        country: e.target.value,
                      }))
                    }
                    maxLength={3}
                    placeholder="IND"
                  />
                </div>

                <div className="patch-form">
                  <label>Time zone</label>
                  <input
                    value={createLocationForm.time_zone}
                    onChange={(e) =>
                      setCreateLocationForm((f) => ({
                        ...f,
                        time_zone: e.target.value,
                      }))
                    }
                    placeholder="Asia/Kolkata"
                  />
                </div>

                <div className="patch-form">
                  <label>Latitude</label>
                  <input
                    value={createLocationForm.latitude}
                    onChange={(e) =>
                      setCreateLocationForm((f) => ({
                        ...f,
                        latitude: e.target.value,
                      }))
                    }
                    placeholder="12.971599"
                  />
                </div>

                <div className="patch-form">
                  <label>Longitude</label>
                  <input
                    value={createLocationForm.longitude}
                    onChange={(e) =>
                      setCreateLocationForm((f) => ({
                        ...f,
                        longitude: e.target.value,
                      }))
                    }
                    placeholder="77.594566"
                  />
                </div>
              </div>
            </div>

            <div className="panel inset">
              <div className="panel-title">
                <span>EVSEs</span>

                <div className="button-row">
                  <span className="count-badge">
                    {createLocationForm.evses.length} EVSE(s)
                  </span>

                  <button
                    type="button"
                    className="secondary"
                    onClick={addCreateEvse}
                    disabled={createBusy}
                  >
                    <Plus size={15} />
                    Add EVSE
                  </button>
                </div>
              </div>

              <div className="security-note">
                <Server size={17} />

                <span>
                  One Location can contain multiple EVSEs. Each EVSE below
                  includes one Connector for this creation form.
                </span>
              </div>

              {createLocationForm.evses.map((evse, index) => (
                <div
                  className="panel inset"
                  key={`${index}-${evse.uid}`}
                >
                  <div className="panel-title">
                    <span>
                      EVSE {index + 1}
                    </span>

                    <div className="button-row">
                      <span className="count-badge">
                        1 Connector
                      </span>

                      {createLocationForm.evses.length > 1 && (
                        <button
                          type="button"
                          className="secondary"
                          onClick={() => removeCreateEvse(index)}
                          disabled={createBusy}
                        >
                          <X size={15} />
                          Remove
                        </button>
                      )}
                    </div>
                  </div>

                  <div className="detail-grid create-grid">
                    <div className="patch-form">
                      <label>EVSE UID</label>
                      <input
                        value={evse.uid}
                        onChange={(e) =>
                          updateCreateEvse(
                            index,
                            'uid',
                            e.target.value
                          )
                        }
                        placeholder={`EVSE${String(index + 1).padStart(3, '0')}`}
                      />
                    </div>

                    <div className="patch-form">
                      <label>EVSE ID</label>
                      <input
                        value={evse.evse_id}
                        onChange={(e) =>
                          updateCreateEvse(
                            index,
                            'evse_id',
                            e.target.value
                          )
                        }
                        placeholder={`IN*TSP*E${String(index + 1).padStart(3, '0')}`}
                      />
                    </div>

                    <div className="patch-form">
                      <label>EVSE status</label>
                      <select
                        value={evse.status}
                        onChange={(e) =>
                          updateCreateEvse(
                            index,
                            'status',
                            e.target.value
                          )
                        }
                      >
                        <option>AVAILABLE</option>
                        <option>BLOCKED</option>
                        <option>CHARGING</option>
                        <option>INOPERATIVE</option>
                        <option>OUTOFORDER</option>
                        <option>PLANNED</option>
                        <option>REMOVED</option>
                        <option>RESERVED</option>
                        <option>UNKNOWN</option>
                        <option>UNREACHABLE</option>
                      </select>
                    </div>

                    <div className="patch-form">
                      <label>Connector ID</label>
                      <input
                        value={evse.connector_id}
                        onChange={(e) =>
                          updateCreateEvse(
                            index,
                            'connector_id',
                            e.target.value
                          )
                        }
                        placeholder="1"
                      />
                    </div>

                    <div className="patch-form">
                      <label>Standard</label>
                      <select
                        value={evse.standard}
                        onChange={(e) =>
                          updateCreateEvse(
                            index,
                            'standard',
                            e.target.value
                          )
                        }
                      >
                        <option>IEC_62196_T2</option>
                        <option>IEC_62196_T2_COMBO</option>
                        <option>CHADEMO</option>
                        <option>TESLA_S</option>
                        <option>TESLA_R</option>
                      </select>
                    </div>

                    <div className="patch-form">
                      <label>Format</label>
                      <select
                        value={evse.format}
                        onChange={(e) =>
                          updateCreateEvse(
                            index,
                            'format',
                            e.target.value
                          )
                        }
                      >
                        <option>SOCKET</option>
                        <option>CABLE</option>
                      </select>
                    </div>

                    <div className="patch-form">
                      <label>Power type</label>
                      <select
                        value={evse.power_type}
                        onChange={(e) =>
                          updateCreateEvse(
                            index,
                            'power_type',
                            e.target.value
                          )
                        }
                      >
                        <option>AC_1_PHASE</option>
                        <option>AC_2_PHASE</option>
                        <option>AC_2_PHASE_SPLIT</option>
                        <option>AC_3_PHASE</option>
                        <option>DC</option>
                      </select>
                    </div>

                    <div className="patch-form">
                      <label>Max voltage (V)</label>
                      <input
                        type="number"
                        min="1"
                        value={evse.max_voltage}
                        onChange={(e) =>
                          updateCreateEvse(
                            index,
                            'max_voltage',
                            e.target.value
                          )
                        }
                      />
                    </div>

                    <div className="patch-form">
                      <label>Max amperage (A)</label>
                      <input
                        type="number"
                        min="1"
                        value={evse.max_amperage}
                        onChange={(e) =>
                          updateCreateEvse(
                            index,
                            'max_amperage',
                            e.target.value
                          )
                        }
                      />
                    </div>

                    <div className="patch-form">
                      <label>Max electric power (W)</label>
                      <input
                        type="number"
                        min="1"
                        value={evse.max_electric_power}
                        onChange={(e) =>
                          updateCreateEvse(
                            index,
                            'max_electric_power',
                            e.target.value
                          )
                        }
                      />
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {createError && (
              <div className="error-box">
                {createError}
              </div>
            )}

            <div className="button-row">
              <button
                className="primary"
                onClick={() =>
                  void createNewLocation()
                }
                disabled={createBusy}
              >
                <Plus size={16} />

                {createBusy
                  ? 'Creating...'
                  : 'Create Location'}
              </button>

              <button
                className="secondary"
                onClick={closeCreateLocation}
                disabled={createBusy}
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* =====================================================
          LOCATION DETAILS MODAL
      ===================================================== */}
      {selected && (
        <div
          className="modal-backdrop"
          onClick={closeModal}
        >
          <div
            className="modal"
            onClick={(e) =>
              e.stopPropagation()
            }
          >
            {/* Header */}
            <div className="modal-head">
              <div>
                <div className="eyebrow">
                  LOCATION DETAILS
                </div>

                <h3>
                  {selected.name || selected.id}
                </h3>
              </div>

              <button
                className="icon-btn"
                onClick={closeModal}
              >
                <X size={18} />
              </button>
            </div>

            {/* Location details */}
            <div className="detail-grid">
              <Summary
                label="Location ID"
                value={selected.id}
              />

              <Summary
                label="Party ID"
                value={selected.party_id}
              />

              <Summary
                label="Country"
                value={selected.country_code}
              />

              <Summary
                label="City"
                value={selected.city}
              />

              <Summary
                label="Address"
                value={selected.address}
              />

              <Summary
                label="Timezone"
                value={selected.time_zone}
              />
            </div>

            {/* =================================================
                LOCATION PUT
            ================================================= */}
            <div className="panel inset">
              <div className="panel-title">
                <span>
                  eMSP Location PUT
                </span>

                <span className="count-badge">
                  COMPLETE OBJECT
                </span>
              </div>

              <div className="patch-form">
                <label>
                  Location name
                </label>

                <input
                  value={putName}
                  onChange={(e) =>
                    setPutName(e.target.value)
                  }
                  onFocus={startLocationPut}
                  placeholder={
                    selected.name ||
                    'Location name'
                  }
                />

                <div className="endpoint-chip">
                  PUT
                  {' '}
                  /ocpi/emsp/2.2.1/locations/
                  {selected.country_code}/
                  {selected.party_id}/
                  {selected.id}
                </div>

                <div className="security-note">
                  <Settings2 size={17} />

                  <span>
                    PUT sends the complete Location
                    object. The other Location,
                    EVSE and Connector fields are
                    preserved.
                  </span>
                </div>

                {putError && (
                  <div className="error-box">
                    {putError}
                  </div>
                )}

                <div className="button-row">
                  <button
                    className="primary"
                    onClick={() =>
                      void applyLocationPut()
                    }
                    disabled={putBusy}
                  >
                    <BadgeCheck size={16} />

                    {putBusy
                      ? 'Sending PUT...'
                      : 'Send Location PUT'}
                  </button>
                </div>
              </div>
            </div>

            {/* =================================================
                LOCATION PATCH
            ================================================= */}
            <div className="panel inset">
              <div className="panel-title">
                <span>
                  eMSP Location PATCH
                </span>

                {!editingLocation && (
                  <button
                    className="secondary"
                    onClick={
                      startLocationEditing
                    }
                  >
                    Edit Location
                  </button>
                )}
              </div>

              {!editingLocation ? (
                <div className="empty">
                  Use PATCH to partially update this
                  Location without replacing the complete
                  object.
                </div>
              ) : (
                <div className="patch-form">
                  <label>
                    Location name
                  </label>

                  <input
                    value={editLocationName}
                    onChange={(e) =>
                      setEditLocationName(
                        e.target.value
                      )
                    }
                    placeholder="Enter location name"
                  />

                  <div className="endpoint-chip">
                    PATCH
                    {' '}
                    /ocpi/emsp/2.2.1/locations/
                    {selected.country_code}/
                    {selected.party_id}/
                    {selected.id}
                  </div>

                  {patchError && (
                    <div className="error-box">
                      {patchError}
                    </div>
                  )}

                  <div className="button-row">
                    <button
                      className="primary"
                      onClick={() =>
                        void applyLocationPatch()
                      }
                      disabled={patchBusy}
                    >
                      <BadgeCheck size={16} />

                      {patchBusy
                        ? 'Updating...'
                        : 'Apply PATCH'}
                    </button>

                    <button
                      className="secondary"
                      onClick={() => {
                        setEditingLocation(false)
                        setPatchError('')
                      }}
                      disabled={patchBusy}
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              )}
            </div>

            {/* =================================================
                EVSE SECTION
            ================================================= */}
            <div className="panel inset">
              <div className="panel-title">
                <span>EVSEs</span>

                <span className="count-badge">
                  {selected.evses?.length || 0}
                </span>
              </div>

              {(selected.evses || []).map(
                (evse) => (
                  <div
                    className="evse-item"
                    key={evse.uid}
                  >
                    <div className="evse-main">
                      <div className="evse-title-row">
                        <strong>
                          {evse.uid}
                        </strong>

                        <span
                          className={`status ${evse.status.toLowerCase()}`}
                        >
                          {evse.status}
                        </span>

                        {evse.evse_id && (
                          <span className="muted">
                            {evse.evse_id}
                          </span>
                        )}
                      </div>

                      <div className="muted">
                        {evse.connectors.length}{' '}
                        connector(s)
                      </div>
                    </div>

<div className="evse-actions">
  {editingEvse !== evse.uid && (
    <button
      className="secondary"
      onClick={() =>
        startEvseEditing(evse)
      }
    >
      Edit EVSE
    </button>
  )}
<button
  className="secondary"
  onClick={() =>
    void openEvse(
      selected.id,
      evse.uid
    )
  }
>
  Get EVSE
</button>

  {putEvseUid !== evse.uid && (
    <button
      className="secondary"
      onClick={() =>
        startEvsePut(evse)
      }
    >
      EVSE PUT
    </button>
  )}
</div>

                    {editingEvse ===
                      evse.uid && (
                      <div className="patch-form evse-edit">
                        <label>
                          EVSE status
                        </label>

                        <select
                          value={
                            editEvseStatus
                          }
                          onChange={(e) =>
                            setEditEvseStatus(
                              e.target.value
                            )
                          }
                        >
                          <option>
                            AVAILABLE
                          </option>

                          <option>
                            BLOCKED
                          </option>

                          <option>
                            CHARGING
                          </option>

                          <option>
                            INOPERATIVE
                          </option>

                          <option>
                            OUTOFORDER
                          </option>

                          <option>
                            PLANNED
                          </option>

                          <option>
                            REMOVED
                          </option>

                          <option>
                            UNKNOWN
                          </option>
                        </select>

                        <div className="endpoint-chip">
                          PATCH
                          {' '}
                          /ocpi/emsp/2.2.1/locations/
                          {selected.country_code}/
                          {selected.party_id}/
                          {selected.id}/
                          {evse.uid}
                        </div>

                        {patchError && (
                          <div className="error-box">
                            {patchError}
                          </div>
                        )}

                        <div className="button-row">
                          <button
                            className="primary"
                            onClick={() =>
                              void applyEvsePatch(
                                evse.uid
                              )
                            }
                            disabled={
                              patchBusy
                            }
                          >
                            <BadgeCheck
                              size={16}
                            />

                            {patchBusy
                              ? 'Updating...'
                              : 'Apply EVSE PATCH'}
                          </button>

                          <button
                            className="secondary"
                            onClick={() => {
                              setEditingEvse(
                                null
                              )
                              setPatchError('')
                            }}
                            disabled={
                              patchBusy
                            }
                          >
                            Cancel
                          </button>
                        </div>
                      </div>
                    )}
{putEvseUid === evse.uid && (
  <div className="patch-form evse-edit">
    <label>
      EVSE status
    </label>

    <select
      value={putEvseStatus}
      onChange={(e) =>
        setPutEvseStatus(e.target.value)
      }
    >
      <option>AVAILABLE</option>
      <option>BLOCKED</option>
      <option>CHARGING</option>
      <option>INOPERATIVE</option>
      <option>OUTOFORDER</option>
      <option>PLANNED</option>
      <option>REMOVED</option>
      <option>UNKNOWN</option>
    </select>

    <div className="endpoint-chip">
      PUT
      {' '}
      /ocpi/emsp/2.2.1/locations/
      {selected.country_code}/
      {selected.party_id}/
      {selected.id}/
      {evse.uid}
    </div>

    <div className="security-note">
      <Settings2 size={17} />

      <span>
        PUT sends the complete EVSE object.
        Existing connectors and other EVSE
        fields are preserved.
      </span>
    </div>

    {putEvseError && (
      <div className="error-box">
        {putEvseError}
      </div>
    )}

    <div className="button-row">
      <button
        className="primary"
        onClick={() =>
          void applyEvsePut(evse.uid)
        }
        disabled={putEvseBusy}
      >
        <BadgeCheck size={16} />

        {putEvseBusy
          ? 'Sending PUT...'
          : 'Send EVSE PUT'}
      </button>

      <button
        className="secondary"
        onClick={() => {
          setPutEvseUid(null)
          setPutEvseError('')
        }}
        disabled={putEvseBusy}
      >
        Cancel
      </button>
    </div>
  </div>
)}
                    {/* =================================================
                        CONNECTOR SECTION
                    ================================================= */}
                    <div className="connector-section">
                      <div className="connector-header">
                        <div className="connector-title">
                          <Cable size={17} />

                          <strong>
                            Connectors
                          </strong>

                          <span className="count-badge">
                            {evse.connectors.length}
                          </span>
                        </div>
                      </div>

                      {evse.connectors.map(
                        (connector) => {
                          const isEditing =
                            editingConnector ===
                              connector.id &&
                            editingConnectorEvse ===
                              evse.uid

                          return (
                            <div
                              className="connector-card"
                              key={connector.id}
                            >
                              <div className="connector-info">
                                <div className="connector-id">
                                  <strong>
                                    Connector #
                                    {connector.id}
                                  </strong>
                                </div>

                                <div className="connector-details">
                                  <span>
                                    Standard:{' '}
                                    {
                                      connector.standard
                                    }
                                  </span>

                                  <span>
                                    Format:{' '}
                                    {
                                      connector.format
                                    }
                                  </span>

                                  <span>
                                    Power type:{' '}
                                    {
                                      connector.power_type
                                    }
                                  </span>

                                  <span>
                                    Max power:{' '}
                                    {
                                      connector.max_electric_power ||
                                      '—'
                                    }{' '}
                                    W
                                  </span>
                                </div>
                              </div>

                              {!isEditing &&
  !(
    putConnector === connector.id &&
    putConnectorEvse === evse.uid
  ) && (
    <div className="button-row">
      <button
        className="secondary"
        onClick={() =>
          startConnectorEditing(
            evse.uid,
            connector
          )
        }
      >
        Edit Connector
      </button>
<button
  className="secondary"
  onClick={() =>
    void openConnector(
      selected.id,
      evse.uid,
      connector.id
    )
  }
>
  Get Connector
</button>
      <button
        className="secondary"
        onClick={() =>
          startConnectorPut(
            evse.uid,
            connector
          )
        }
      >
        Connector PUT
      </button>
    </div>
)}

                              {isEditing && (
                                <div className="patch-form connector-edit">
                                  <label>
                                    Max electric
                                    power (W)
                                  </label>

                                  <input
                                    type="number"
                                    min="1"
                                    value={
                                      editConnectorPower
                                    }
                                    onChange={(e) =>
                                      setEditConnectorPower(
                                        e.target.value
                                      )
                                    }
                                  />

                                  <div className="endpoint-chip">
                                    PATCH
                                    {' '}
                                    /ocpi/emsp/2.2.1/locations/
                                    {
                                      selected.country_code
                                    }
                                    /
                                    {
                                      selected.party_id
                                    }
                                    /
                                    {selected.id}/
                                    {evse.uid}/
                                    {connector.id}
                                  </div>

                                  <div className="security-note">
                                    <Settings2
                                      size={17}
                                    />

                                    <span>
                                      Only
                                      <strong>
                                        {' '}
                                        max_electric_power
                                      </strong>{' '}
                                      and
                                      <strong>
                                        {' '}
                                        last_updated
                                      </strong>{' '}
                                      will be sent.
                                    </span>
                                  </div>

                                  {patchError && (
                                    <div className="error-box">
                                      {patchError}
                                    </div>
                                  )}

                                  <div className="button-row">
                                    <button
                                      className="primary"
                                      onClick={() =>
                                        void applyConnectorPatch(
                                          evse.uid,
                                          connector.id
                                        )
                                      }
                                      disabled={
                                        patchBusy
                                      }
                                    >
                                      <BadgeCheck
                                        size={16}
                                      />

                                      {patchBusy
                                        ? 'Updating...'
                                        : 'Apply Connector PATCH'}
                                    </button>

                                    <button
                                      className="secondary"
                                      onClick={() => {
                                        setEditingConnector(
                                          null
                                        )
                                        setEditingConnectorEvse(
                                          null
                                        )
                                        setPatchError('')
                                      }}
                                      disabled={
                                        patchBusy
                                      }
                                    >
                                      Cancel
                                    </button>
                                  </div>
                                </div>
                              )}

                              {putConnector === connector.id &&
                                putConnectorEvse === evse.uid && (
                                  <div className="patch-form connector-edit">
                                    <label>
                                      Max electric power (W)
                                    </label>

                                    <input
                                      type="number"
                                      min="1"
                                      value={putConnectorPower}
                                      onChange={(e) =>
                                        setPutConnectorPower(e.target.value)
                                      }
                                    />

                                    <div className="endpoint-chip">
                                      PUT
                                      {' '}
                                      /ocpi/emsp/2.2.1/locations/
                                      {selected.country_code}/
                                      {selected.party_id}/
                                      {selected.id}/
                                      {evse.uid}/
                                      {connector.id}
                                    </div>

                                    <div className="security-note">
                                      <Settings2 size={17} />

                                      <span>
                                        PUT sends the complete Connector object.
                                        Existing connector properties are preserved.
                                      </span>
                                    </div>

                                    {putConnectorError && (
                                      <div className="error-box">
                                        {putConnectorError}
                                      </div>
                                    )}

                                    <div className="button-row">
                                      <button
                                        className="primary"
                                        onClick={() =>
                                          void applyConnectorPut(
                                            evse.uid,
                                            connector.id
                                          )
                                        }
                                        disabled={putConnectorBusy}
                                      >
                                        <BadgeCheck size={16} />

                                        {putConnectorBusy
                                          ? 'Sending PUT...'
                                          : 'Send Connector PUT'}
                                      </button>

                                      <button
                                        className="secondary"
                                        onClick={() => {
                                          setPutConnector(null)
                                          setPutConnectorEvse(null)
                                          setPutConnectorError('')
                                        }}
                                        disabled={putConnectorBusy}
                                      >
                                        Cancel
                                      </button>
                                    </div>
                                  </div>
                                )}
                            </div>
                          )
                        }
                      )}
                    </div>
                  </div>
                )
              )}
            </div>

            {/* Last updated */}
            <div className="security-note">
              <History size={17} />

              <span>
                Last updated:{' '}
                {new Date(
                  selected.last_updated
                ).toLocaleString()}
              </span>
            </div>
          </div>
        </div>
      )}
    </>
  )
}

function Simulation({
  onRun,
  busy,
}: {
  onRun: (
    endpoint: string,
    method?: string
  ) => void
  busy: boolean
}) {
  const [scenario, setScenario] = useState(
    'Credential Registration'
  )

  const [running, setRunning] = useState(false)
  const [completed, setCompleted] = useState(false)
  const [error, setError] = useState('')

  const [backendResult, setBackendResult] =
    useState<Credentials | null>(null)

  const [locationResult, setLocationResult] =
    useState<Location[]>([])

  const [steps, setSteps] = useState<
    Array<{
      label: string
      status:
        | 'Pending'
        | 'Running'
        | 'Completed'
        | 'Failed'
    }>
  >([])

  const run = async () => {
    setRunning(true)
    setCompleted(false)
    setError('')
    setBackendResult(null)
    setLocationResult([])

    // =======================================================
    // CREDENTIAL REGISTRATION
    // =======================================================
    if (
      scenario === 'Credential Registration'
    ) {
      const handshakeSteps = [
        'Discover CPO supported versions',
        'Fetch CPO OCPI 2.2.1 endpoint details',
        'Locate Credentials receiver endpoint',
        'Send eMSP credentials',
        'Store returned CPO credentials',
      ]

      setSteps(
        handshakeSteps.map((label) => ({
          label,
          status: 'Pending',
        }))
      )

      try {
        setSteps((current) =>
          current.map((step, index) =>
            index === 0
              ? {
                  ...step,
                  status: 'Running',
                }
              : step
          )
        )

        /*
         * This is the REAL backend handshake.
         */
        const body =
          await apiFetch<
            OcpiResponse<Credentials>
          >(
            '/ocpi/emsp/handshake',
            {
              method: 'POST',
            }
          )

        if (
          body.status_code !== undefined &&
          body.status_code !== 1000
        ) {
          throw new Error(
            body.status_message ||
              `OCPI handshake failed with status ${body.status_code}`
          )
        }

        setBackendResult(body.data)

        setSteps(
          handshakeSteps.map((label) => ({
            label,
            status: 'Completed',
          }))
        )

        setCompleted(true)

        onRun(
          '/ocpi/emsp/handshake',
          'POST'
        )
      } catch (e) {
        const message =
          e instanceof Error
            ? e.message
            : 'Simulation failed'

        setError(message)

        setSteps((current) =>
          current.map((step) => ({
            ...step,
            status: 'Failed',
          }))
        )
      } finally {
        setRunning(false)
      }

      return
    }

    // =======================================================
    // LOCATION SYNC
    // =======================================================
    if (scenario === 'Location Sync') {
      const locationSteps = [
        'Request CPO Locations',
        'Receive Location data',
        'Read EVSE and Connector hierarchy',
      ]

      setSteps(
        locationSteps.map((label) => ({
          label,
          status: 'Pending',
        }))
      )

      try {
        setSteps((current) =>
          current.map((step, index) =>
            index === 0
              ? {
                  ...step,
                  status: 'Running',
                }
              : step
          )
        )

        /*
         * REAL backend CPO GET Locations call.
         *
         * Using the same endpoint already used by
         * the Locations screen.
         */
        const body =
          await apiFetch<
            OcpiResponse<Location[]>
          >(
            '/ocpi/cpo/2.2.1/locations?limit=10&offset=0'
          )

        if (
          body.status_code !== undefined &&
          body.status_code !== 1000
        ) {
          throw new Error(
            body.status_message ||
              `Location request failed with status ${body.status_code}`
          )
        }

        const locations =
          body.data || []

        setLocationResult(locations)

        setSteps(
          locationSteps.map((label) => ({
            label,
            status: 'Completed',
          }))
        )

        setCompleted(true)

        onRun(
          '/ocpi/cpo/2.2.1/locations?limit=10&offset=0',
          'GET'
        )
      } catch (e) {
        const message =
          e instanceof Error
            ? e.message
            : 'Location sync failed'

        setError(message)

        setSteps((current) =>
          current.map((step) => ({
            ...step,
            status: 'Failed',
          }))
        )
      } finally {
        setRunning(false)
      }
    }
  }

  return (
    <>
      <SectionHeader
        title="Simulation"
        subtitle="Execute an OCPI workflow through the FastAPI backend and inspect the result."
      />

      {/* =====================================================
          CONTROLS
      ===================================================== */}
      <div className="panel sim-controls">
        <div>
          <label>From (Sender)</label>

          <select>
            <option>CPO (TSP / IN)</option>
            <option>eMSP (TSP / IN)</option>
          </select>
        </div>

        <ArrowLeftRight size={22} />

        <div>
          <label>To (Receiver)</label>

          <select>
            <option>eMSP (TSP / IN)</option>
            <option>CPO (TSP / IN)</option>
          </select>
        </div>

        <div>
          <label>Scenario</label>

          <select
            value={scenario}
            onChange={(e) =>
              setScenario(e.target.value)
            }
          >
            <option>
              Credential Registration
            </option>

            <option>
              Location Sync
            </option>
          </select>
        </div>

        <button
          className="primary big"
          onClick={() => void run()}
          disabled={running || busy}
        >
          <Play size={17} />

          {running
            ? 'RUNNING...'
            : 'RUN SIMULATION'}
        </button>
      </div>

      {/* =====================================================
          ERROR
      ===================================================== */}
      {error && (
        <div className="error-box">
          <strong>Simulation failed:</strong>{' '}
          {error}
        </div>
      )}

      {/* =====================================================
          CREDENTIAL RESULT
      ===================================================== */}
      {scenario ===
        'Credential Registration' &&
        completed &&
        backendResult && (
          <div className="panel">
            <div className="panel-title">
              <span>Backend result</span>

              <span className="success-badge">
                OCPI 1000 · SUCCESS
              </span>
            </div>

            <div className="summary-grid">
              <Summary
                label="Role"
                value={
                  backendResult.roles?.[0]
                    ?.role || '—'
                }
              />

              <Summary
                label="Party ID"
                value={
                  backendResult.roles?.[0]
                    ?.party_id || '—'
                }
              />

              <Summary
                label="Country"
                value={
                  backendResult.roles?.[0]
                    ?.country_code || '—'
                }
              />

              <Summary
                label="Version URL"
                value={
                  backendResult.url || '—'
                }
              />
            </div>
          </div>
        )}

      {/* =====================================================
          LOCATION RESULT
      ===================================================== */}
      {scenario === 'Location Sync' &&
        completed && (
          <div className="panel">
            <div className="panel-title">
              <span>Location sync result</span>

              <span className="success-badge">
                {locationResult.length} LOCATION(S)
              </span>
            </div>

            {locationResult.length === 0 ? (
              <div className="empty">
                No Locations were returned.
              </div>
            ) : (
              locationResult.map((location) => {
                const evseCount =
                  location.evses?.length || 0

                const connectorCount =
                  (location.evses || []).reduce(
                    (sum, evse) =>
                      sum +
                      (evse.connectors?.length ||
                        0),
                    0
                  )

                return (
                  <div
                    className="version-card"
                    key={location.id}
                  >
                    <div>
                      <strong>
                        {location.id}
                      </strong>

                      <div className="muted">
                        {location.name ||
                          'Unnamed Location'}
                      </div>
                    </div>

                    <div className="location-mini-summary">
                      <span>
                        {location.city}
                      </span>

                      <span>
                        EVSEs: {evseCount}
                      </span>

                      <span>
                        Connectors:{' '}
                        {connectorCount}
                      </span>
                    </div>
                  </div>
                )
              })
            )}
          </div>
        )}

      {/* =====================================================
          PROGRESS
      ===================================================== */}
      <div className="panel">
        <div className="panel-title">
          <span>
            Simulation progress
          </span>

          {completed && (
            <span className="success-badge">
              Backend workflow completed
            </span>
          )}
        </div>

        {steps.length === 0 ? (
          <div className="empty">
            Choose a scenario and run the
            simulation.
          </div>
        ) : (
          <>
            <div className="flow-note">
              <Terminal size={17} />

              <span>
                These stages represent the
                workflow executed through the
                FastAPI backend.
              </span>
            </div>

            <div className="step-list">
              {steps.map((step, index) => (
                <div
                  className="step"
                  key={index}
                >
                  <span className="step-dot">
                    {index + 1}
                  </span>

                  <div>
                    <strong>
                      {step.label}
                    </strong>

                    <div className="muted">
                      {step.status}
                    </div>
                  </div>

                  {step.status ===
                    'Completed' && (
                    <BadgeCheck
                      size={18}
                    />
                  )}

                  {step.status ===
                    'Running' && (
                    <RefreshCw
                      size={18}
                      className="spin"
                    />
                  )}
                </div>
              ))}
            </div>
          </>
        )}
      </div>

      {/* =====================================================
          EXPLANATION
      ===================================================== */}
      <div className="panel">
        <div className="panel-title">
          <span>
            What this simulation demonstrates
          </span>
        </div>

        <div className="simulation-explanation">
          <div>
            <strong>
              Credential Registration
            </strong>

            <p>
              The eMSP discovers the CPO and
              performs the Credentials handshake.
            </p>
          </div>

          <div>
            <strong>Location Sync</strong>

            <p>
              The simulator requests the CPO
              Location data and displays the
              returned Location, EVSE and
              Connector information.
            </p>
          </div>
        </div>
      </div>
    </>
  )
}



function Logs({
  activity,
}: {
  activity: ActivityRow[]
}) {
  return (
    <>
      <SectionHeader
        title="Communication Log"
        subtitle="Requests launched from the UI are collected here for demo visibility."
      />

      <div className="panel table-panel">
        <div className="panel-title">
          <span>Request history</span>
          <span className="count-badge">
            {activity.length}
          </span>
        </div>

        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Time</th>
                <th>From</th>
                <th>To</th>
                <th>Method</th>
                <th>Endpoint</th>
                <th>Status</th>
              </tr>
            </thead>

            <tbody>
              {activity.map((a, i) => (
                <tr key={i}>
                  <td>{a.time}</td>
                  <td>{a.from}</td>
                  <td>{a.to}</td>

                  <td>
                    <span className="method">
                      {a.method}
                    </span>
                  </td>

                  <td>
                    <code>{a.endpoint}</code>
                  </td>

                  <td>
                    <span className="status success">
                      {a.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {activity.length === 0 && (
            <div className="empty">
              No UI requests yet.
            </div>
          )}
        </div>
      </div>
    </>
  )
}

export default App