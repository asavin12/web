// User types
export interface User {
  id: number;
  username: string;
  first_name: string;
  last_name: string;
  email: string;
  date_joined: string;
  last_login?: string | null;
  is_staff?: boolean;
  is_superuser?: boolean;
  profile?: UserProfile;
}

export interface UserProfile {
  id: number;
  user: User;
  bio: string;
  avatar: string | null;
  avatar_url: string | null;
  native_language?: string;
  native_language_display?: string;
  target_language: 'en' | 'de';
  language_display: string;
  level: 'beginner' | 'intermediate' | 'advanced' | 'A1' | 'A2' | 'B1' | 'B2' | 'C1' | 'C2';
  level_display: string;
  skill_focus: 'reading' | 'writing' | 'listening' | 'speaking' | 'grammar' | 'vocabulary' | 'all';
  skill_display: string;
  learning_languages?: Array<{ code: string; level: string; level_display?: string }>;
  interests?: string[];
  is_public: boolean;
  location?: string;
  website?: string;
  show_online_status?: boolean;
  allow_messages?: boolean;
  email_notifications?: boolean;
  push_notifications?: boolean;
  message_notifications?: boolean;
  friend_request_notifications?: boolean;
  updated_at: string;
}

// Resource types
export interface Category {
  id: number;
  name: string;
  slug: string;
}

export interface Tag {
  id: number;
  name: string;
  slug: string;
}

export interface Resource {
  id: number;
  title: string;
  slug: string;
  description: string;
  content?: string;
  category: Category;
  category_name: string;
  resource_type: 'book' | 'video' | 'audio' | 'document' | 'link';
  type_display: string;
  resource_type_display?: string;
  language: 'en' | 'de';
  language_display: string;
  level: 'beginner' | 'intermediate' | 'advanced';
  level_display: string;
  cover_image: string | null;
  cover_url: string | null;
  file: string | null;
  external_url: string | null;
  download_count: number;
  view_count: number;
  uploaded_by: User;
  related_resources?: Resource[];
  tags?: Tag[];
  created_at: string;
  updated_at: string;
}

// API Response types
export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
  page?: number;
  page_size?: number;
  total_pages?: number;
}

// Auth types
export interface LoginCredentials {
  username: string;
  password: string;
}

export interface RegisterData {
  username: string;
  email: string;
  password: string;
  password2: string;
  first_name?: string;
  last_name?: string;
  target_language?: string;
  level?: string;
  skill_focus?: string;
}

export interface AuthResponse {
  token: string;
  user: User;
  profile: UserProfile;
}

// Choices types (from API)
export interface Choices {
  languages: Array<{ value: string; label: string }>;
  levels: Array<{ value: string; label: string }>;
  skills: Array<{ value: string; label: string }>;
  resource_types: Array<{ value: string; label: string }>;
}

// Video type (core.Video model)
export interface Video {
  id: number;
  slug: string;
  title: string;
  description: string;
  youtube_id: string;
  youtube_url: string;
  embed_url: string;
  thumbnail: string;
  duration: string;
  language: string;
  language_display: string;
  level: string;
  level_display: string;
  view_count: number;
  is_featured: boolean;
  bookmark_count?: number;
  is_bookmarked?: boolean;
  created_at: string;
}

export interface VideoListResponse {
  results: Video[];
  count: number;
  page: number;
  page_size: number;
  total_pages: number;
  language_choices: [string, string][];
  level_choices: [string, string][];
}
