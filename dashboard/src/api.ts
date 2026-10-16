export interface Overview {
  total_bots: number
  active_bots: number
  total_users: number
  total_activities: number
}

export interface BotSummary {
  id: number
  name: string
  username: string
  is_active: boolean
  registered_user_count: number
}

export interface UserSummary {
  id: number
  bot_name: string
  bot_username: string
  display_name: string
  language_code: string
  created_at: string
}

export interface ActivitySummary {
  event_type: string
  bot_name: string
  bot_username: string
  created_at: string
  description: string
}

export interface DashboardData {
  overview: Overview
  bots: BotSummary[]
  users: UserSummary[]
  activities: ActivitySummary[]
}

export class ApiError extends Error {
  constructor(public readonly status: number) {
    super(status === 401 ? 'The admin key was rejected.' : 'Could not load dashboard data.')
  }
}

async function get<T>(path: string, adminKey: string, signal?: AbortSignal): Promise<T> {
  const response = await fetch(`/api/admin/${path}`, {
    headers: { 'X-Admin-Key': adminKey },
    cache: 'no-store',
    signal,
  })
  if (!response.ok) throw new ApiError(response.status)
  return response.json() as Promise<T>
}

export async function loadDashboard(adminKey: string, signal?: AbortSignal): Promise<DashboardData> {
  const [overview, bots, users, activities] = await Promise.all([
    get<Overview>('overview', adminKey, signal),
    get<BotSummary[]>('bots', adminKey, signal),
    get<UserSummary[]>('users', adminKey, signal),
    get<ActivitySummary[]>('activities', adminKey, signal),
  ])
  return { overview, bots, users, activities }
}
