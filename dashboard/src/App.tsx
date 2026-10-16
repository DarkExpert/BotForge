import { useRef, useState, type FormEvent, type ReactNode } from 'react'
import { ApiError, loadDashboard, type DashboardData } from './api'

type IconName = 'grid' | 'bot' | 'users' | 'activity' | 'refresh' | 'lock' | 'arrow' | 'exit'

function Icon({ name, size = 20 }: { name: IconName; size?: number }) {
  const paths: Record<IconName, ReactNode> = {
    grid: <><rect x="3" y="3" width="7" height="7" rx="1.5" /><rect x="14" y="3" width="7" height="7" rx="1.5" /><rect x="3" y="14" width="7" height="7" rx="1.5" /><rect x="14" y="14" width="7" height="7" rx="1.5" /></>,
    bot: <><rect x="4" y="7" width="16" height="13" rx="3" /><path d="M12 7V4m-2 0h4M4 13H2m20 0h-2" /><circle cx="9" cy="13" r="1" /><circle cx="15" cy="13" r="1" /><path d="M9 17h6" /></>,
    users: <><circle cx="9" cy="8" r="3" /><path d="M3 20v-2a6 6 0 0 1 12 0v2H3Zm14-13a3 3 0 0 1 0 6m1 3a5 5 0 0 1 3 4" /></>,
    activity: <path d="M3 12h4l3-7 4 14 3-7h4" />,
    refresh: <><path d="M20 11a8 8 0 0 0-14-5L4 8m0-5v5h5M4 13a8 8 0 0 0 14 5l2-2m0 5v-5h-5" /></>,
    lock: <><rect x="5" y="10" width="14" height="11" rx="2" /><path d="M8 10V7a4 4 0 0 1 8 0v3m-4 5v2" /></>,
    arrow: <path d="M5 12h14m-6-6 6 6-6 6" />,
    exit: <><path d="M9 4H5a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h4m6-4 4-4-4-4m-8 4h12" /></>,
  }
  return <svg aria-hidden="true" width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">{paths[name]}</svg>
}

function Brand() {
  return <div className="brand"><span className="brand-mark"><Icon name="bot" size={22} /></span><span>Bot<span className="brand-accent">Forge</span><small>OPERATIONS CONSOLE</small></span></div>
}

function formatDate(value: string) {
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? '—' : new Intl.DateTimeFormat(undefined, { dateStyle: 'medium', timeStyle: 'short' }).format(date)
}

function Empty({ title, detail }: { title: string; detail: string }) {
  return <div className="empty"><span className="empty-symbol">◇</span><strong>{title}</strong><span>{detail}</span></div>
}

function SectionHeading({ eyebrow, title, note }: { eyebrow: string; title: string; note?: string }) {
  return <div className="section-heading"><div><span className="eyebrow">{eyebrow}</span><h2>{title}</h2></div>{note && <span className="section-note">{note}</span>}</div>
}

export default function App() {
  const [inputKey, setInputKey] = useState('')
  const [adminKey, setAdminKey] = useState('')
  const [data, setData] = useState<DashboardData | null>(null)
  const [working, setWorking] = useState(false)
  const [entryError, setEntryError] = useState('')
  const [refreshError, setRefreshError] = useState('')
  const [updatedAt, setUpdatedAt] = useState<Date | null>(null)
  const requestId = useRef(0)

  async function load(key: string, isRefresh = false) {
    const currentRequest = ++requestId.current
    setWorking(true)
    setEntryError('')
    setRefreshError('')
    try {
      const result = await loadDashboard(key)
      if (currentRequest !== requestId.current) return
      setData(result)
      setAdminKey(key)
      setInputKey('')
      setUpdatedAt(new Date())
    } catch (error) {
      if (currentRequest !== requestId.current) return
      if (error instanceof ApiError && error.status === 401) {
        setAdminKey('')
        setData(null)
        setInputKey('')
        setEntryError('Access denied. Check your admin key and try again.')
      } else {
        const message = 'Unable to reach the backend. Check that the service is running, then try again.'
        if (isRefresh) setRefreshError(message)
        else setEntryError(message)
      }
    } finally {
      if (currentRequest === requestId.current) setWorking(false)
    }
  }

  function disconnect() {
    requestId.current += 1
    setAdminKey('')
    setInputKey('')
    setData(null)
    setEntryError('')
    setRefreshError('')
    setUpdatedAt(null)
    setWorking(false)
  }

  function connect(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (inputKey.trim()) void load(inputKey.trim())
  }

  if (!adminKey || !data) {
    return <div className="access-shell"><div className="access-glow" /><div className="access-top"><Brand /><span className="local-pill"><span className="live-dot" /> LOCAL DEMO</span></div><main className="access-card"><div className="access-icon"><Icon name="lock" size={26} /></div><span className="eyebrow">SECURE ACCESS</span><h1>Welcome to BotForge</h1><p>Enter your local admin key to view your bot operations dashboard.</p><form onSubmit={connect}><label htmlFor="admin-key">Admin API key</label><input id="admin-key" type="password" value={inputKey} onChange={event => setInputKey(event.target.value)} placeholder="Enter your key" autoComplete="off" spellCheck={false} required /><button className="primary-button" type="submit" disabled={working || !inputKey.trim()}>{working ? 'Connecting…' : 'Connect to dashboard'} {!working && <Icon name="arrow" size={18} />}</button></form>{entryError && <p className="form-error" role="alert">{entryError}</p>}<div className="access-note"><Icon name="lock" size={15} /> Key stays in memory and clears when you reload or disconnect.</div></main><div className="access-footer">BOTFORGE / v0.1.0 <span>LOCAL OPERATIONS</span></div></div>
  }

  const metrics: { label: string; value: number; icon: IconName; detail: string }[] = [
    { label: 'Total bots', value: data.overview.total_bots, icon: 'bot', detail: 'Connected identities' },
    { label: 'Active bots', value: data.overview.active_bots, icon: 'activity', detail: 'Currently enabled' },
    { label: 'Registered users', value: data.overview.total_users, icon: 'users', detail: 'Across all bots' },
    { label: 'Activity events', value: data.overview.total_activities, icon: 'grid', detail: 'Recorded interactions' },
  ]

  return <div className="app-shell"><aside className="sidebar"><Brand /><div className="workspace-label">WORKSPACE</div><nav aria-label="Dashboard sections"><a href="#overview"><Icon name="grid" size={19} /> Overview</a><a href="#bots"><Icon name="bot" size={19} /> Connected bots</a><a href="#users"><Icon name="users" size={19} /> Registered users</a><a href="#activity"><Icon name="activity" size={19} /> Recent activity</a></nav><div className="sidebar-bottom"><div className="system-status"><span className="live-dot" /><span><strong>System connected</strong><small>Local environment</small></span></div><button className="disconnect" onClick={disconnect}><Icon name="exit" size={17} /> Disconnect</button></div></aside><div className="main-wrap"><header className="topbar"><span>Workspace <span className="crumb">/</span> Dashboard</span><div className="topbar-right"><span className="environment-tag"><span className="live-dot" /> LOCAL INSTANCE</span><button className="top-disconnect" onClick={disconnect} title="Disconnect"><Icon name="exit" size={19} /><span>Disconnect</span></button></div></header><main className="dashboard"><div className="page-head"><div><div className="eyebrow">BOTFORGE / COMMAND CENTER</div><h1>Dashboard overview</h1><p>A clear view of your Telegram bot network.</p></div><div className="page-actions"><span className="updated">{updatedAt ? `Updated ${new Intl.DateTimeFormat(undefined, { timeStyle: 'short' }).format(updatedAt)}` : ''}</span><button className="refresh-button" onClick={() => void load(adminKey, true)} disabled={working}><Icon name="refresh" size={17} />{working ? 'Refreshing…' : 'Refresh data'}</button></div></div>{refreshError && <div className="inline-error" role="alert">{refreshError}</div>}<section id="overview" aria-label="Overview"><div className="metrics">{metrics.map(metric => <article className="metric-card" key={metric.label}><div className="metric-top"><span>{metric.label}</span><span className="metric-icon"><Icon name={metric.icon} size={19} /></span></div><strong>{metric.value.toLocaleString()}</strong><small>{metric.detail}</small></article>)}</div></section><section id="bots" className="content-section"><SectionHeading eyebrow="01 / FLEET" title="Connected bots" note={`${data.bots.length} identities`} /><div className="bot-grid">{data.bots.length ? data.bots.map(bot => <article className="bot-card" key={bot.id}><div className="bot-card-top"><div className="bot-avatar"><Icon name="bot" size={25} /></div><span className={`status-badge ${bot.is_active ? 'active' : 'inactive'}`}><span />{bot.is_active ? 'Active' : 'Inactive'}</span></div><h3>{bot.name}</h3><span className="bot-username">@{bot.username}</span><div className="bot-card-footer"><span>Registered users</span><strong>{bot.registered_user_count.toLocaleString()}</strong></div></article>) : <div className="panel"><Empty title="No bots connected" detail="Bot identities will appear after the worker connects." /></div>}</div></section><section id="users" className="content-section"><SectionHeading eyebrow="02 / PEOPLE" title="Registered users" note="Most recent 50" /><div className="panel table-panel">{data.users.length ? <div className="table-scroll"><table><thead><tr><th>User</th><th>Bot</th><th>Language</th><th>Registered</th></tr></thead><tbody>{data.users.map(user => <tr key={user.id}><td><span className="user-cell"><span className="user-avatar">{user.display_name.slice(0, 1).toUpperCase() || '?'}</span><strong>{user.display_name}</strong></span></td><td><span className="bot-name-cell">{user.bot_name}<small>@{user.bot_username}</small></span></td><td><span className="language-badge">{user.language_code === 'ar' ? 'العربية' : user.language_code === 'en' ? 'English' : user.language_code}</span></td><td className="muted-cell">{formatDate(user.created_at)}</td></tr>)}</tbody></table></div> : <Empty title="No users yet" detail="People who interact with your bots will appear here." />}</div></section><section id="activity" className="content-section"><SectionHeading eyebrow="03 / EVENTS" title="Recent activity" note="Most recent 50" /><div className="panel table-panel">{data.activities.length ? <div className="table-scroll"><table><thead><tr><th>Event</th><th>Bot</th><th>Description</th><th>Time</th></tr></thead><tbody>{data.activities.map((item, index) => <tr key={`${item.bot_username}-${item.created_at}-${index}`}><td><span className="event-cell"><span className="event-dot" />{item.event_type.replaceAll('_', ' ')}</span></td><td><span className="bot-name-cell">{item.bot_name}<small>@{item.bot_username}</small></span></td><td className="muted-cell">{item.description}</td><td className="muted-cell">{formatDate(item.created_at)}</td></tr>)}</tbody></table></div> : <Empty title="No activity recorded" detail="Bot interactions will appear here as events occur." />}</div></section><footer className="page-footer"><span>BotForge v0.1.0</span><span>Local development dashboard</span></footer></main></div></div>
}
