import { auth } from '../../../config/firebase';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

async function getAuthToken(): Promise<string> {
  const user = auth.currentUser;
  if (!user) {
    throw new Error('No authenticated user');
  }
  return await user.getIdToken();
}

// ============================================================================
// Types
// ============================================================================

export interface UserSummary {
  uid: string;
  email: string;
  display_name: string | null;
  task_count: number;
  project_count: number;
  total_tokens_used: number;
  current_tier: string;
  is_suspended: boolean;
  created_at: string;
  last_login: string | null;
}

export interface UserListResponse {
  users: UserSummary[];
  total: number;
  page: number;
  page_size: number;
  has_next: boolean;
}

export interface SystemOverview {
  total_users: number;
  active_users_today: number;
  active_users_week: number;
  total_tasks: number;
  total_projects: number;
  total_tokens_used: number;
  avg_tokens_per_user: number;
  tier_distribution: Record<string, number>;
  suspended_users: number;
}

export interface UserDetail extends UserSummary {
  phone_number: string | null;
  photo_url: string | null;
  email_verified: boolean;
  disabled: boolean;
  metadata: {
    creation_time: string;
    last_sign_in_time: string | null;
    last_refresh_time: string | null;
  };
  provider_data: Array<{
    provider_id: string;
    uid: string;
    email: string | null;
  }>;
  custom_claims: Record<string, any>;
}

export interface TokenUsageResponse {
  user_id: string;
  email: string;
  usage: Array<{
    date: string;
    total_tokens: number;
    prompt_tokens: number;
    completion_tokens: number;
    request_count: number;
  }>;
  summary: {
    total_tokens: number;
    total_requests: number;
    avg_tokens_per_request: number;
    date_range: {
      start: string;
      end: string;
    };
  };
}

export interface AuditLog {
  id: string;
  admin_id: string;
  admin_email: string;
  action: string;
  resource_type: string;
  resource_id: string | null;
  details: Record<string, any> | null;
  success: boolean;
  error_message: string | null;
  timestamp: string;
  ip_address: string | null;
}

export interface AuditLogListResponse {
  logs: AuditLog[];
  total: number;
  page: number;
  page_size: number;
  has_next: boolean;
}

export interface SystemConfig {
  default_tier: string;
  tier_limits: Record<string, {
    max_tasks: number;
    max_projects: number;
    max_tokens_per_day: number;
  }>;
  features: Record<string, boolean>;
  maintenance_mode: boolean;
  maintenance_message: string | null;
}

// ============================================================================
// User Management
// ============================================================================

export async function getAllUsers(params?: {
  page?: number;
  page_size?: number;
  search?: string;
  tier?: string;
  suspended?: boolean;
}): Promise<UserListResponse> {
  const token = await getAuthToken();
  const queryParams = new URLSearchParams();
  
  if (params?.page) queryParams.append('page', params.page.toString());
  if (params?.page_size) queryParams.append('page_size', params.page_size.toString());
  if (params?.search) queryParams.append('search', params.search);
  if (params?.tier) queryParams.append('tier', params.tier);
  if (params?.suspended !== undefined) queryParams.append('suspended', params.suspended.toString());

  const response = await fetch(`${API_BASE_URL}/api/v1/admin/users?${queryParams}`, {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch users: ${response.statusText}`);
  }

  return response.json();
}

export async function getUserDetail(userId: string): Promise<UserDetail> {
  const token = await getAuthToken();
  const response = await fetch(`${API_BASE_URL}/api/v1/admin/users/${userId}`, {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch user details: ${response.statusText}`);
  }

  return response.json();
}

export async function suspendUser(userId: string, reason: string): Promise<void> {
  const token = await getAuthToken();
  const response = await fetch(`${API_BASE_URL}/api/v1/admin/users/${userId}/suspend`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ reason }),
  });

  if (!response.ok) {
    throw new Error(`Failed to suspend user: ${response.statusText}`);
  }
}

export async function unsuspendUser(userId: string): Promise<void> {
  const token = await getAuthToken();
  const response = await fetch(`${API_BASE_URL}/api/v1/admin/users/${userId}/unsuspend`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    throw new Error(`Failed to unsuspend user: ${response.statusText}`);
  }
}

export async function updateUserTier(userId: string, tier: string): Promise<void> {
  const token = await getAuthToken();
  const response = await fetch(`${API_BASE_URL}/api/v1/admin/users/${userId}`, {
    method: 'PATCH',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ tier }),
  });

  if (!response.ok) {
    throw new Error(`Failed to update user tier: ${response.statusText}`);
  }
}

export async function deleteUser(userId: string): Promise<void> {
  const token = await getAuthToken();
  const response = await fetch(`${API_BASE_URL}/api/v1/admin/users/${userId}`, {
    method: 'DELETE',
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    throw new Error(`Failed to delete user: ${response.statusText}`);
  }
}

// ============================================================================
// Analytics
// ============================================================================

export async function getSystemOverview(): Promise<SystemOverview> {
  const token = await getAuthToken();
  const response = await fetch(`${API_BASE_URL}/api/v1/admin/analytics/overview`, {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch system overview: ${response.statusText}`);
  }

  return response.json();
}

export async function getUserTokenUsage(
  userId: string,
  days: number = 30
): Promise<TokenUsageResponse> {
  const token = await getAuthToken();
  const response = await fetch(
    `${API_BASE_URL}/api/v1/admin/analytics/token-usage/${userId}?days=${days}`,
    {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    }
  );

  if (!response.ok) {
    throw new Error(`Failed to fetch token usage: ${response.statusText}`);
  }

  return response.json();
}

// ============================================================================
// Configuration
// ============================================================================

export async function getSystemConfig(): Promise<SystemConfig> {
  const token = await getAuthToken();
  const response = await fetch(`${API_BASE_URL}/api/v1/admin/config`, {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch system config: ${response.statusText}`);
  }

  return response.json();
}

export async function updateSystemConfig(config: Partial<SystemConfig>): Promise<void> {
  const token = await getAuthToken();
  const response = await fetch(`${API_BASE_URL}/api/v1/admin/config`, {
    method: 'PATCH',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(config),
  });

  if (!response.ok) {
    throw new Error(`Failed to update system config: ${response.statusText}`);
  }
}

// ============================================================================
// Audit Logs
// ============================================================================

export async function getAuditLogs(params?: {
  page?: number;
  page_size?: number;
  admin_id?: string;
  action?: string;
  resource_type?: string;
  start_date?: string;
  end_date?: string;
}): Promise<AuditLogListResponse> {
  const token = await getAuthToken();
  const queryParams = new URLSearchParams();
  
  if (params?.page) queryParams.append('page', params.page.toString());
  if (params?.page_size) queryParams.append('page_size', params.page_size.toString());
  if (params?.admin_id) queryParams.append('admin_id', params.admin_id);
  if (params?.action) queryParams.append('action', params.action);
  if (params?.resource_type) queryParams.append('resource_type', params.resource_type);
  if (params?.start_date) queryParams.append('start_date', params.start_date);
  if (params?.end_date) queryParams.append('end_date', params.end_date);

  const response = await fetch(`${API_BASE_URL}/api/v1/admin/audit-logs?${queryParams}`, {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch audit logs: ${response.statusText}`);
  }

  return response.json();
}
