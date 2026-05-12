CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  email TEXT NOT NULL UNIQUE,
  password_hash TEXT NOT NULL,
  is_email_verified INTEGER NOT NULL DEFAULT 0,
  is_active INTEGER NOT NULL DEFAULT 1,
  role TEXT NOT NULL DEFAULT 'user' CHECK(role IN ('user','moderator','admin')),
  last_login_at TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS profiles (
  user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
  display_name TEXT NOT NULL,
  username TEXT NOT NULL DEFAULT '',
  bio TEXT NOT NULL DEFAULT '',
  city TEXT NOT NULL DEFAULT '',
  district TEXT NOT NULL DEFAULT '',
  timezone TEXT NOT NULL DEFAULT 'UTC',
  buddy_goals TEXT NOT NULL DEFAULT '',
  interests TEXT NOT NULL DEFAULT '',
  games TEXT NOT NULL DEFAULT '',
  hobbies TEXT NOT NULL DEFAULT '',
  online_offline_preference TEXT NOT NULL DEFAULT 'both' CHECK(online_offline_preference IN ('online','offline','both')),
  friendship_preference TEXT NOT NULL DEFAULT 'both' CHECK(friendship_preference IN ('temporary','permanent','both')),
  avatar_url TEXT,
  online_status TEXT NOT NULL DEFAULT 'offline',
  safety_level TEXT NOT NULL DEFAULT 'standard',
  verification_badge TEXT NOT NULL DEFAULT 'none',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS friendships (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  requester_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  addressee_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  status TEXT NOT NULL CHECK(status IN ('pending','accepted','declined','blocked')),
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(requester_id, addressee_id)
);

CREATE TABLE IF NOT EXISTS chats (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  chat_type TEXT NOT NULL DEFAULT 'direct',
  title TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS chat_members (
  chat_id INTEGER NOT NULL REFERENCES chats(id) ON DELETE CASCADE,
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY(chat_id, user_id)
);

CREATE TABLE IF NOT EXISTS messages (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  chat_id INTEGER NOT NULL REFERENCES chats(id) ON DELETE CASCADE,
  sender_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  body TEXT NOT NULL,
  attachment_url TEXT,
  voice_placeholder INTEGER NOT NULL DEFAULT 0,
  moderation_status TEXT NOT NULL DEFAULT 'pending',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS requests (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  sender_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  receiver_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
  request_type TEXT NOT NULL DEFAULT 'friend',
  title TEXT NOT NULL DEFAULT '',
  description TEXT NOT NULL DEFAULT '',
  message TEXT NOT NULL DEFAULT '',
  tags TEXT NOT NULL DEFAULT '',
  category TEXT NOT NULL DEFAULT 'online',
  mode TEXT NOT NULL DEFAULT 'online' CHECK(mode IN ('online','offline')),
  reward TEXT NOT NULL DEFAULT '',
  status TEXT NOT NULL DEFAULT 'pending',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS blocks (
  blocker_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  blocked_user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  reason TEXT NOT NULL DEFAULT '',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY(blocker_id, blocked_user_id)
);

CREATE TABLE IF NOT EXISTS reports (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  reporter_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
  reported_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
  message_id INTEGER REFERENCES messages(id) ON DELETE SET NULL,
  reason TEXT NOT NULL,
  details TEXT NOT NULL DEFAULT '',
  status TEXT NOT NULL DEFAULT 'open',
  priority TEXT NOT NULL DEFAULT 'normal',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS moderation_logs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
  content_type TEXT NOT NULL,
  content_id INTEGER,
  provider TEXT NOT NULL,
  decision TEXT NOT NULL,
  scores_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS verification_states (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  verification_type TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending',
  code TEXT,
  file_url TEXT,
  expires_at TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS trust_scores (
  user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
  score INTEGER NOT NULL DEFAULT 50,
  scam_signals INTEGER NOT NULL DEFAULT 0,
  spam_signals INTEGER NOT NULL DEFAULT 0,
  harassment_signals INTEGER NOT NULL DEFAULT 0,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS email_tokens (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  token TEXT NOT NULL UNIQUE,
  token_type TEXT NOT NULL CHECK(token_type IN ('verify_email','password_reset')),
  expires_at TEXT NOT NULL,
  used_at TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS upload_files (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  owner_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  filename TEXT NOT NULL UNIQUE,
  original_name TEXT NOT NULL,
  content_type TEXT NOT NULL,
  size_bytes INTEGER NOT NULL,
  storage_path TEXT NOT NULL,
  public_url TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS activity_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
  event_type TEXT NOT NULL,
  metadata_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_profiles_discovery ON profiles(city, district, online_status);
CREATE INDEX IF NOT EXISTS idx_messages_chat_id ON messages(chat_id, created_at);
CREATE INDEX IF NOT EXISTS idx_requests_receiver ON requests(receiver_id, status);
CREATE INDEX IF NOT EXISTS idx_requests_discovery ON requests(category, mode, status);
CREATE INDEX IF NOT EXISTS idx_reports_status ON reports(status, created_at);
CREATE INDEX IF NOT EXISTS idx_email_tokens_token ON email_tokens(token);
