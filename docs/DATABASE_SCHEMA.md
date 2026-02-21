# UnstressVN Database Schema

**Exported:** 2026-01-25 07:19:31

## Database Info

| Property | Value |
|----------|-------|
| Database | `unstressvn` |
| Host | `localhost:5433` |
| Size | 11 MB |
| Tables | 43 |

---

## Tables

### Table of Contents

- [accounts_notification](#accounts-notification)
- [accounts_userprofile](#accounts-userprofile)
- [auth_group](#auth-group)
- [auth_group_permissions](#auth-group-permissions)
- [auth_permission](#auth-permission)
- [auth_user](#auth-user)
- [auth_user_groups](#auth-user-groups)
- [auth_user_user_permissions](#auth-user-user-permissions)
- [authtoken_token](#authtoken-token)
- [chat_chatroom](#chat-chatroom)
- [chat_chatroom_participants](#chat-chatroom-participants)
- [chat_message](#chat-message)
- [core_apikey](#core-apikey)
- [core_navigationlink](#core-navigationlink)
- [core_sitesettings](#core-sitesettings)
- [core_video](#core-video)
- [core_video_bookmarks](#core-video-bookmarks)
- [django_admin_log](#django-admin-log)
- [django_content_type](#django-content-type)
- [django_migrations](#django-migrations)
- [django_session](#django-session)
- [filemanager_mediafile](#filemanager-mediafile)
- [filemanager_sitelogo](#filemanager-sitelogo)
- [forum_forumbookmark](#forum-forumbookmark)
- [forum_forumlike](#forum-forumlike)
- [forum_forumpost](#forum-forumpost)
- [forum_forumreply](#forum-forumreply)
- [knowledge_category](#knowledge-category)
- [knowledge_knowledgearticle](#knowledge-knowledgearticle)
- [news_article](#news-article)
- [news_category](#news-category)
- [partners_friendrequest](#partners-friendrequest)
- [partners_studyroom](#partners-studyroom)
- [partners_studyroom_members](#partners-studyroom-members)
- [resources_category](#resources-category)
- [resources_resource](#resources-resource)
- [resources_resource_bookmarks](#resources-resource-bookmarks)
- [resources_resource_tags](#resources-resource-tags)
- [resources_tag](#resources-tag)
- [tools_flashcard](#tools-flashcard)
- [tools_flashcarddeck](#tools-flashcarddeck)
- [tools_tool](#tools-tool)
- [tools_toolcategory](#tools-toolcategory)

---

### accounts_notification

**Rows:** 7

#### Columns

| # | Column | Type | Nullable | Default |
|---|--------|------|----------|---------|
| 1 | `id` 🔑 | `bigint` | ✗ | - |
| 2 | `notification_type` | `character varying(20)` | ✗ | - |
| 3 | `title` | `character varying(200)` | ✗ | - |
| 4 | `message` | `text` | ✗ | - |
| 5 | `link` | `character varying(500)` | ✗ | - |
| 6 | `is_read` | `boolean` | ✗ | - |
| 7 | `created_at` | `timestamp with time zone` | ✗ | - |
| 8 | `recipient_id` | `integer` | ✗ | - |
| 9 | `sender_id` | `integer` | ✓ | - |

#### Foreign Keys

| Column | References |
|--------|------------|
| `recipient_id` | `auth_user.id` |
| `sender_id` | `auth_user.id` |

#### Indexes

- `accounts_notification_pkey`
- `accounts_notification_recipient_id_cb6b57f5`
- `accounts_notification_sender_id_a2b8299c`

---

### accounts_userprofile

**Rows:** 7

#### Columns

| # | Column | Type | Nullable | Default |
|---|--------|------|----------|---------|
| 1 | `id` 🔑 | `bigint` | ✗ | - |
| 2 | `avatar` | `character varying(100)` | ✓ | - |
| 3 | `bio` | `text` | ✗ | - |
| 4 | `target_language` | `character varying(20)` | ✗ | - |
| 5 | `level` | `character varying(2)` | ✗ | - |
| 6 | `skill_focus` | `character varying(20)` | ✗ | - |
| 7 | `is_public` | `boolean` | ✗ | - |
| 8 | `created_at` | `timestamp with time zone` | ✗ | - |
| 9 | `updated_at` | `timestamp with time zone` | ✗ | - |
| 10 | `user_id` | `integer` | ✗ | - |
| 11 | `allow_messages` | `boolean` | ✗ | - |

#### Foreign Keys

| Column | References |
|--------|------------|
| `user_id` | `auth_user.id` |

#### Indexes

- `accounts_userprofile_pkey`
- `accounts_userprofile_user_id_key`

---

### auth_group

**Rows:** N/A

#### Columns

| # | Column | Type | Nullable | Default |
|---|--------|------|----------|---------|
| 1 | `id` 🔑 | `integer` | ✗ | - |
| 2 | `name` | `character varying(150)` | ✗ | - |

#### Indexes

- `auth_group_pkey`
- `auth_group_name_key`
- `auth_group_name_a6ea08ec_like`

---

### auth_group_permissions

**Rows:** N/A

#### Columns

| # | Column | Type | Nullable | Default |
|---|--------|------|----------|---------|
| 1 | `id` 🔑 | `bigint` | ✗ | - |
| 2 | `group_id` | `integer` | ✗ | - |
| 3 | `permission_id` | `integer` | ✗ | - |

#### Foreign Keys

| Column | References |
|--------|------------|
| `group_id` | `auth_group.id` |
| `permission_id` | `auth_permission.id` |

#### Indexes

- `auth_group_permissions_pkey`
- `auth_group_permissions_group_id_permission_id_0cd325b0_uniq`
- `auth_group_permissions_group_id_b120cbf9`
- `auth_group_permissions_permission_id_84c5c92e`

---

### auth_permission

**Rows:** 140

#### Columns

| # | Column | Type | Nullable | Default |
|---|--------|------|----------|---------|
| 1 | `id` 🔑 | `integer` | ✗ | - |
| 2 | `name` | `character varying(255)` | ✗ | - |
| 3 | `content_type_id` | `integer` | ✗ | - |
| 4 | `codename` | `character varying(100)` | ✗ | - |

#### Foreign Keys

| Column | References |
|--------|------------|
| `content_type_id` | `django_content_type.id` |

#### Indexes

- `auth_permission_pkey`
- `auth_permission_content_type_id_codename_01ab375a_uniq`
- `auth_permission_content_type_id_2f476e4b`

---

### auth_user

**Rows:** 7

#### Columns

| # | Column | Type | Nullable | Default |
|---|--------|------|----------|---------|
| 1 | `id` 🔑 | `integer` | ✗ | - |
| 2 | `password` | `character varying(128)` | ✗ | - |
| 3 | `last_login` | `timestamp with time zone` | ✓ | - |
| 4 | `is_superuser` | `boolean` | ✗ | - |
| 5 | `username` | `character varying(150)` | ✗ | - |
| 6 | `first_name` | `character varying(150)` | ✗ | - |
| 7 | `last_name` | `character varying(150)` | ✗ | - |
| 8 | `email` | `character varying(254)` | ✗ | - |
| 9 | `is_staff` | `boolean` | ✗ | - |
| 10 | `is_active` | `boolean` | ✗ | - |
| 11 | `date_joined` | `timestamp with time zone` | ✗ | - |

#### Indexes

- `auth_user_pkey`
- `auth_user_username_key`
- `auth_user_username_6821ab7c_like`

---

### auth_user_groups

**Rows:** N/A

#### Columns

| # | Column | Type | Nullable | Default |
|---|--------|------|----------|---------|
| 1 | `id` 🔑 | `bigint` | ✗ | - |
| 2 | `user_id` | `integer` | ✗ | - |
| 3 | `group_id` | `integer` | ✗ | - |

#### Foreign Keys

| Column | References |
|--------|------------|
| `user_id` | `auth_user.id` |
| `group_id` | `auth_group.id` |

#### Indexes

- `auth_user_groups_pkey`
- `auth_user_groups_user_id_group_id_94350c0c_uniq`
- `auth_user_groups_user_id_6a12ed8b`
- `auth_user_groups_group_id_97559544`

---

### auth_user_user_permissions

**Rows:** N/A

#### Columns

| # | Column | Type | Nullable | Default |
|---|--------|------|----------|---------|
| 1 | `id` 🔑 | `bigint` | ✗ | - |
| 2 | `user_id` | `integer` | ✗ | - |
| 3 | `permission_id` | `integer` | ✗ | - |

#### Foreign Keys

| Column | References |
|--------|------------|
| `user_id` | `auth_user.id` |
| `permission_id` | `auth_permission.id` |

#### Indexes

- `auth_user_user_permissions_pkey`
- `auth_user_user_permissions_user_id_permission_id_14a6b632_uniq`
- `auth_user_user_permissions_user_id_a95ead1b`
- `auth_user_user_permissions_permission_id_1fbb5f2c`

---

### authtoken_token

**Rows:** 1

#### Columns

| # | Column | Type | Nullable | Default |
|---|--------|------|----------|---------|
| 1 | `key` 🔑 | `character varying(40)` | ✗ | - |
| 2 | `created` | `timestamp with time zone` | ✗ | - |
| 3 | `user_id` | `integer` | ✗ | - |

#### Foreign Keys

| Column | References |
|--------|------------|
| `user_id` | `auth_user.id` |

#### Indexes

- `authtoken_token_pkey`
- `authtoken_token_user_id_key`
- `authtoken_token_key_10f0b77e_like`

---

### chat_chatroom

**Rows:** N/A

#### Columns

| # | Column | Type | Nullable | Default |
|---|--------|------|----------|---------|
| 1 | `id` 🔑 | `bigint` | ✗ | - |
| 2 | `created_at` | `timestamp with time zone` | ✗ | - |
| 3 | `updated_at` | `timestamp with time zone` | ✗ | - |

#### Indexes

- `chat_chatroom_pkey`

---

### chat_chatroom_participants

**Rows:** N/A

#### Columns

| # | Column | Type | Nullable | Default |
|---|--------|------|----------|---------|
| 1 | `id` 🔑 | `bigint` | ✗ | - |
| 2 | `chatroom_id` | `bigint` | ✗ | - |
| 3 | `user_id` | `integer` | ✗ | - |

#### Foreign Keys

| Column | References |
|--------|------------|
| `chatroom_id` | `chat_chatroom.id` |
| `user_id` | `auth_user.id` |

#### Indexes

- `chat_chatroom_participants_pkey`
- `chat_chatroom_participants_chatroom_id_user_id_a0328aed_uniq`
- `chat_chatroom_participants_chatroom_id_9c40ed95`
- `chat_chatroom_participants_user_id_9f2b6693`

---

### chat_message

**Rows:** N/A

#### Columns

| # | Column | Type | Nullable | Default |
|---|--------|------|----------|---------|
| 1 | `id` 🔑 | `bigint` | ✗ | - |
| 2 | `content` | `text` | ✗ | - |
| 3 | `is_read` | `boolean` | ✗ | - |
| 4 | `created_at` | `timestamp with time zone` | ✗ | - |
| 5 | `room_id` | `bigint` | ✗ | - |
| 6 | `sender_id` | `integer` | ✗ | - |

#### Foreign Keys

| Column | References |
|--------|------------|
| `room_id` | `chat_chatroom.id` |
| `sender_id` | `auth_user.id` |

#### Indexes

- `chat_message_pkey`
- `chat_message_room_id_5e7d8d78`
- `chat_message_sender_id_991c686c`

---

### core_apikey

**Rows:** 2

#### Columns

| # | Column | Type | Nullable | Default |
|---|--------|------|----------|---------|
| 1 | `id` 🔑 | `bigint` | ✗ | - |
| 2 | `name` | `character varying(100)` | ✗ | - |
| 3 | `key` | `character varying(255)` | ✗ | - |
| 4 | `key_type` | `character varying(20)` | ✗ | - |
| 5 | `description` | `text` | ✗ | - |
| 6 | `is_active` | `boolean` | ✗ | - |
| 7 | `last_used_at` | `timestamp with time zone` | ✓ | - |
| 8 | `usage_count` | `integer` | ✗ | - |
| 9 | `created_at` | `timestamp with time zone` | ✗ | - |
| 10 | `updated_at` | `timestamp with time zone` | ✗ | - |

#### Indexes

- `core_apikey_pkey`
- `core_apikey_name_key`
- `core_apikey_name_83d164df_like`

---

### core_navigationlink

**Rows:** 19

#### Columns

| # | Column | Type | Nullable | Default |
|---|--------|------|----------|---------|
| 1 | `id` 🔑 | `bigint` | ✗ | - |
| 2 | `name` | `character varying(100)` | ✗ | - |
| 3 | `url` | `character varying(500)` | ✗ | - |
| 4 | `icon` | `character varying(50)` | ✗ | - |
| 5 | `location` | `character varying(10)` | ✗ | - |
| 6 | `footer_section` | `character varying(20)` | ✗ | - |
| 7 | `open_in_new_tab` | `boolean` | ✗ | - |
| 8 | `is_active` | `boolean` | ✗ | - |
| 9 | `order` | `integer` | ✗ | - |
| 10 | `created_at` | `timestamp with time zone` | ✗ | - |
| 11 | `updated_at` | `timestamp with time zone` | ✗ | - |
| 12 | `parent_id` | `bigint` | ✓ | - |

#### Foreign Keys

| Column | References |
|--------|------------|
| `parent_id` | `core_navigationlink.id` |

#### Indexes

- `core_navigationlink_pkey`
- `core_navigationlink_parent_id_5e27c3fd`

---

### core_sitesettings

**Rows:** 7

#### Columns

| # | Column | Type | Nullable | Default |
|---|--------|------|----------|---------|
| 1 | `id` 🔑 | `bigint` | ✗ | - |
| 2 | `name` | `character varying(100)` | ✗ | - |
| 3 | `value` | `text` | ✗ | - |
| 4 | `setting_type` | `character varying(20)` | ✗ | - |
| 5 | `is_secret` | `boolean` | ✗ | - |
| 6 | `description` | `text` | ✗ | - |
| 7 | `created_at` | `timestamp with time zone` | ✗ | - |
| 8 | `updated_at` | `timestamp with time zone` | ✗ | - |

#### Indexes

- `core_sitesettings_pkey`
- `core_sitesettings_name_key`
- `core_sitesettings_name_e716c2f0_like`

---

### core_video

**Rows:** 5

#### Columns

| # | Column | Type | Nullable | Default |
|---|--------|------|----------|---------|
| 1 | `id` 🔑 | `bigint` | ✗ | - |
| 2 | `title` | `character varying(255)` | ✗ | - |
| 3 | `slug` | `character varying(300)` | ✗ | - |
| 4 | `description` | `text` | ✗ | - |
| 5 | `youtube_id` | `character varying(100)` | ✗ | - |
| 6 | `thumbnail` | `character varying(200)` | ✗ | - |
| 7 | `duration` | `character varying(10)` | ✗ | - |
| 8 | `language` | `character varying(5)` | ✗ | - |
| 9 | `level` | `character varying(5)` | ✗ | - |
| 10 | `view_count` | `integer` | ✗ | - |
| 11 | `is_featured` | `boolean` | ✗ | - |
| 12 | `is_active` | `boolean` | ✗ | - |
| 13 | `order` | `integer` | ✗ | - |
| 14 | `created_at` | `timestamp with time zone` | ✗ | - |
| 15 | `updated_at` | `timestamp with time zone` | ✗ | - |
| 16 | `ai_model` | `character varying(50)` | ✗ | - |
| 17 | `human_reviewed` | `boolean` | ✗ | - |
| 18 | `is_ai_generated` | `boolean` | ✗ | - |
| 19 | `n8n_created_at` | `timestamp with time zone` | ✓ | - |
| 20 | `n8n_execution_id` | `character varying(100)` | ✗ | - |
| 21 | `n8n_workflow_id` | `character varying(50)` | ✗ | - |
| 22 | `reviewed_at` | `timestamp with time zone` | ✓ | - |
| 23 | `reviewed_by_id` | `integer` | ✓ | - |
| 24 | `source` | `character varying(20)` | ✗ | - |
| 25 | `source_id` | `character varying(100)` | ✗ | - |
| 26 | `source_url` | `character varying(200)` | ✗ | - |

#### Foreign Keys

| Column | References |
|--------|------------|
| `reviewed_by_id` | `auth_user.id` |

#### Indexes

- `core_video_pkey`
- `core_video_slug_key`
- `core_video_slug_7d268743_like`
- `core_video_reviewed_by_id_1869a94e`

---

### core_video_bookmarks

**Rows:** N/A

#### Columns

| # | Column | Type | Nullable | Default |
|---|--------|------|----------|---------|
| 1 | `id` 🔑 | `bigint` | ✗ | - |
| 2 | `video_id` | `bigint` | ✗ | - |
| 3 | `user_id` | `integer` | ✗ | - |

#### Foreign Keys

| Column | References |
|--------|------------|
| `video_id` | `core_video.id` |
| `user_id` | `auth_user.id` |

#### Indexes

- `core_video_bookmarks_pkey`
- `core_video_bookmarks_video_id_user_id_b086dbcf_uniq`
- `core_video_bookmarks_video_id_a38bd651`
- `core_video_bookmarks_user_id_e92c8e18`

---

### django_admin_log

**Rows:** N/A

#### Columns

| # | Column | Type | Nullable | Default |
|---|--------|------|----------|---------|
| 1 | `id` 🔑 | `integer` | ✗ | - |
| 2 | `action_time` | `timestamp with time zone` | ✗ | - |
| 3 | `object_id` | `text` | ✓ | - |
| 4 | `object_repr` | `character varying(200)` | ✗ | - |
| 5 | `action_flag` | `smallint` | ✗ | - |
| 6 | `change_message` | `text` | ✗ | - |
| 7 | `content_type_id` | `integer` | ✓ | - |
| 8 | `user_id` | `integer` | ✗ | - |

#### Foreign Keys

| Column | References |
|--------|------------|
| `content_type_id` | `django_content_type.id` |
| `user_id` | `auth_user.id` |

#### Indexes

- `django_admin_log_pkey`
- `django_admin_log_content_type_id_c4bce8eb`
- `django_admin_log_user_id_c564eba6`

---

### django_content_type

**Rows:** 35

#### Columns

| # | Column | Type | Nullable | Default |
|---|--------|------|----------|---------|
| 1 | `id` 🔑 | `integer` | ✗ | - |
| 3 | `app_label` | `character varying(100)` | ✗ | - |
| 4 | `model` | `character varying(100)` | ✗ | - |

#### Indexes

- `django_content_type_pkey`
- `django_content_type_app_label_model_76bd3d3b_uniq`

---

### django_migrations

**Rows:** 57

#### Columns

| # | Column | Type | Nullable | Default |
|---|--------|------|----------|---------|
| 1 | `id` 🔑 | `bigint` | ✗ | - |
| 2 | `app` | `character varying(255)` | ✗ | - |
| 3 | `name` | `character varying(255)` | ✗ | - |
| 4 | `applied` | `timestamp with time zone` | ✗ | - |

#### Indexes

- `django_migrations_pkey`

---

### django_session

**Rows:** 12

#### Columns

| # | Column | Type | Nullable | Default |
|---|--------|------|----------|---------|
| 1 | `session_key` 🔑 | `character varying(40)` | ✗ | - |
| 2 | `session_data` | `text` | ✗ | - |
| 3 | `expire_date` | `timestamp with time zone` | ✗ | - |

#### Indexes

- `django_session_pkey`
- `django_session_session_key_c0390e0f_like`
- `django_session_expire_date_a5c62663`

---

### filemanager_mediafile

**Rows:** N/A

#### Columns

| # | Column | Type | Nullable | Default |
|---|--------|------|----------|---------|
| 1 | `id` 🔑 | `bigint` | ✗ | - |
| 2 | `name` | `character varying(255)` | ✗ | - |
| 3 | `file` | `character varying(100)` | ✗ | - |
| 4 | `folder` | `character varying(50)` | ✗ | - |
| 5 | `original_filename` | `character varying(255)` | ✗ | - |
| 6 | `file_size` | `integer` | ✗ | - |
| 7 | `mime_type` | `character varying(100)` | ✗ | - |
| 8 | `width` | `integer` | ✓ | - |
| 9 | `height` | `integer` | ✓ | - |
| 10 | `alt_text` | `character varying(255)` | ✗ | - |
| 11 | `description` | `text` | ✗ | - |
| 12 | `created_at` | `timestamp with time zone` | ✗ | - |
| 13 | `updated_at` | `timestamp with time zone` | ✗ | - |
| 14 | `uploaded_by_id` | `integer` | ✓ | - |

#### Foreign Keys

| Column | References |
|--------|------------|
| `uploaded_by_id` | `auth_user.id` |

#### Indexes

- `filemanager_mediafile_pkey`
- `filemanager_mediafile_uploaded_by_id_13a605c0`

---

### filemanager_sitelogo

**Rows:** 7

#### Columns

| # | Column | Type | Nullable | Default |
|---|--------|------|----------|---------|
| 1 | `id` 🔑 | `bigint` | ✗ | - |
| 2 | `name` | `character varying(100)` | ✗ | - |
| 3 | `logo_type` | `character varying(20)` | ✗ | - |
| 4 | `svg_code` | `text` | ✗ | - |
| 5 | `image` | `character varying(100)` | ✗ | - |
| 6 | `width` | `integer` | ✗ | - |
| 7 | `height` | `integer` | ✗ | - |
| 8 | `is_active` | `boolean` | ✗ | - |
| 9 | `created_at` | `timestamp with time zone` | ✗ | - |
| 10 | `updated_at` | `timestamp with time zone` | ✗ | - |

#### Indexes

- `filemanager_sitelogo_pkey`
- `filemanager_sitelogo_logo_type_key`
- `filemanager_sitelogo_logo_type_6117ed08_like`

---

### forum_forumbookmark

**Rows:** N/A

#### Columns

| # | Column | Type | Nullable | Default |
|---|--------|------|----------|---------|
| 1 | `id` 🔑 | `bigint` | ✗ | - |
| 2 | `created_at` | `timestamp with time zone` | ✗ | - |
| 3 | `user_id` | `integer` | ✗ | - |
| 4 | `post_id` | `bigint` | ✗ | - |

#### Foreign Keys

| Column | References |
|--------|------------|
| `user_id` | `auth_user.id` |
| `post_id` | `forum_forumpost.id` |

#### Indexes

- `forum_forumbookmark_pkey`
- `forum_forumbookmark_user_id_post_id_06cbeeb9_uniq`
- `forum_forumbookmark_user_id_2c13d80a`
- `forum_forumbookmark_post_id_8e042066`

---

### forum_forumlike

**Rows:** N/A

#### Columns

| # | Column | Type | Nullable | Default |
|---|--------|------|----------|---------|
| 1 | `id` 🔑 | `bigint` | ✗ | - |
| 2 | `created_at` | `timestamp with time zone` | ✗ | - |
| 3 | `user_id` | `integer` | ✗ | - |
| 4 | `post_id` | `bigint` | ✓ | - |
| 5 | `reply_id` | `bigint` | ✓ | - |

#### Foreign Keys

| Column | References |
|--------|------------|
| `user_id` | `auth_user.id` |
| `post_id` | `forum_forumpost.id` |
| `reply_id` | `forum_forumreply.id` |

#### Indexes

- `forum_forumlike_pkey`
- `forum_forumlike_user_id_post_id_c67e1202_uniq`
- `forum_forumlike_user_id_reply_id_d5ffc7c6_uniq`
- `forum_forumlike_user_id_9dcfdac2`
- `forum_forumlike_post_id_c7db48c8`
- `forum_forumlike_reply_id_e4e936de`

---

### forum_forumpost

**Rows:** N/A

#### Columns

| # | Column | Type | Nullable | Default |
|---|--------|------|----------|---------|
| 1 | `id` 🔑 | `bigint` | ✗ | - |
| 2 | `title` | `character varying(255)` | ✗ | - |
| 3 | `slug` | `character varying(300)` | ✗ | - |
| 4 | `content` | `text` | ✗ | - |
| 5 | `excerpt` | `character varying(300)` | ✗ | - |
| 6 | `is_pinned` | `boolean` | ✗ | - |
| 7 | `is_locked` | `boolean` | ✗ | - |
| 8 | `is_active` | `boolean` | ✗ | - |
| 9 | `views` | `integer` | ✗ | - |
| 10 | `created_at` | `timestamp with time zone` | ✗ | - |
| 11 | `updated_at` | `timestamp with time zone` | ✗ | - |
| 12 | `author_id` | `integer` | ✗ | - |
| 13 | `category` | `character varying(50)` | ✗ | - |
| 15 | `last_activity` | `timestamp with time zone` | ✗ | - |

#### Foreign Keys

| Column | References |
|--------|------------|
| `author_id` | `auth_user.id` |

#### Indexes

- `forum_forumpost_pkey`
- `forum_forumpost_slug_key`
- `forum_forumpost_slug_6e71f161_like`
- `forum_forumpost_author_id_0af5ed03`
- `forum_forumpost_category_id_9647083a`
- `forum_forumpost_last_activity_b41dd794`

---

### forum_forumreply

**Rows:** N/A

#### Columns

| # | Column | Type | Nullable | Default |
|---|--------|------|----------|---------|
| 1 | `id` 🔑 | `bigint` | ✗ | - |
| 2 | `content` | `text` | ✗ | - |
| 3 | `is_active` | `boolean` | ✗ | - |
| 4 | `is_solution` | `boolean` | ✗ | - |
| 5 | `created_at` | `timestamp with time zone` | ✗ | - |
| 6 | `updated_at` | `timestamp with time zone` | ✗ | - |
| 7 | `author_id` | `integer` | ✗ | - |
| 8 | `parent_id` | `bigint` | ✓ | - |
| 9 | `post_id` | `bigint` | ✗ | - |

#### Foreign Keys

| Column | References |
|--------|------------|
| `author_id` | `auth_user.id` |
| `parent_id` | `forum_forumreply.id` |
| `post_id` | `forum_forumpost.id` |

#### Indexes

- `forum_forumreply_pkey`
- `forum_forumreply_author_id_c1e96e44`
- `forum_forumreply_parent_id_e10463b6`
- `forum_forumreply_post_id_e11921f2`

---

### knowledge_category

**Rows:** 3

#### Columns

| # | Column | Type | Nullable | Default |
|---|--------|------|----------|---------|
| 1 | `id` 🔑 | `bigint` | ✗ | - |
| 2 | `name` | `character varying(100)` | ✗ | - |
| 3 | `slug` | `character varying(120)` | ✗ | - |
| 4 | `description` | `text` | ✗ | - |
| 5 | `icon` | `character varying(50)` | ✗ | - |
| 6 | `meta_title` | `character varying(70)` | ✗ | - |
| 7 | `meta_description` | `character varying(160)` | ✗ | - |
| 8 | `order` | `integer` | ✗ | - |
| 9 | `is_active` | `boolean` | ✗ | - |
| 10 | `created_at` | `timestamp with time zone` | ✗ | - |
| 11 | `updated_at` | `timestamp with time zone` | ✗ | - |

#### Indexes

- `knowledge_category_pkey`
- `knowledge_category_slug_key`
- `knowledge_category_slug_9e482337_like`

---

### knowledge_knowledgearticle

**Rows:** 13

#### Columns

| # | Column | Type | Nullable | Default |
|---|--------|------|----------|---------|
| 1 | `id` 🔑 | `bigint` | ✗ | - |
| 2 | `title` | `character varying(255)` | ✗ | - |
| 3 | `slug` | `character varying(280)` | ✗ | - |
| 4 | `excerpt` | `text` | ✗ | - |
| 5 | `content` | `text` | ✗ | - |
| 6 | `language` | `character varying(5)` | ✗ | - |
| 7 | `level` | `character varying(5)` | ✗ | - |
| 8 | `cover_image` | `character varying(100)` | ✗ | - |
| 9 | `thumbnail` | `character varying(100)` | ✗ | - |
| 10 | `meta_title` | `character varying(70)` | ✗ | - |
| 11 | `meta_description` | `character varying(160)` | ✗ | - |
| 12 | `meta_keywords` | `character varying(255)` | ✗ | - |
| 13 | `canonical_url` | `character varying(200)` | ✗ | - |
| 14 | `og_title` | `character varying(95)` | ✗ | - |
| 15 | `og_description` | `character varying(200)` | ✗ | - |
| 16 | `og_image` | `character varying(100)` | ✗ | - |
| 17 | `schema_type` | `character varying(20)` | ✗ | - |
| 18 | `is_published` | `boolean` | ✗ | - |
| 19 | `is_featured` | `boolean` | ✗ | - |
| 20 | `published_at` | `timestamp with time zone` | ✓ | - |
| 21 | `view_count` | `integer` | ✗ | - |
| 22 | `created_at` | `timestamp with time zone` | ✗ | - |
| 23 | `updated_at` | `timestamp with time zone` | ✗ | - |
| 24 | `author_id` | `integer` | ✓ | - |
| 25 | `category_id` | `bigint` | ✓ | - |
| 26 | `ai_model` | `character varying(50)` | ✗ | - |
| 27 | `human_reviewed` | `boolean` | ✗ | - |
| 28 | `is_ai_generated` | `boolean` | ✗ | - |
| 29 | `n8n_created_at` | `timestamp with time zone` | ✓ | - |
| 30 | `n8n_execution_id` | `character varying(100)` | ✗ | - |
| 31 | `n8n_workflow_id` | `character varying(50)` | ✗ | - |
| 32 | `reviewed_at` | `timestamp with time zone` | ✓ | - |
| 33 | `reviewed_by_id` | `integer` | ✓ | - |
| 34 | `source` | `character varying(20)` | ✗ | - |
| 35 | `source_id` | `character varying(100)` | ✗ | - |
| 36 | `source_url` | `character varying(200)` | ✗ | - |

#### Foreign Keys

| Column | References |
|--------|------------|
| `author_id` | `auth_user.id` |
| `category_id` | `knowledge_category.id` |
| `reviewed_by_id` | `auth_user.id` |

#### Indexes

- `knowledge_knowledgearticle_pkey`
- `knowledge_knowledgearticle_slug_key`
- `knowledge_knowledgearticle_slug_023d0590_like`
- `knowledge_knowledgearticle_author_id_29f5bde2`
- `knowledge_knowledgearticle_category_id_cde9c6bb`
- `knowledge_knowledgearticle_reviewed_by_id_4cf632ee`

---

### news_article

**Rows:** 10

#### Columns

| # | Column | Type | Nullable | Default |
|---|--------|------|----------|---------|
| 1 | `id` 🔑 | `bigint` | ✗ | - |
| 2 | `title` | `character varying(255)` | ✗ | - |
| 3 | `slug` | `character varying(280)` | ✗ | - |
| 4 | `excerpt` | `text` | ✗ | - |
| 5 | `content` | `text` | ✗ | - |
| 6 | `cover_image` | `character varying(100)` | ✗ | - |
| 7 | `thumbnail` | `character varying(100)` | ✗ | - |
| 8 | `meta_title` | `character varying(70)` | ✗ | - |
| 9 | `meta_description` | `character varying(160)` | ✗ | - |
| 10 | `meta_keywords` | `character varying(255)` | ✗ | - |
| 11 | `canonical_url` | `character varying(200)` | ✗ | - |
| 12 | `og_title` | `character varying(95)` | ✗ | - |
| 13 | `og_description` | `character varying(200)` | ✗ | - |
| 14 | `og_image` | `character varying(100)` | ✗ | - |
| 15 | `is_published` | `boolean` | ✗ | - |
| 16 | `is_featured` | `boolean` | ✗ | - |
| 17 | `published_at` | `timestamp with time zone` | ✓ | - |
| 18 | `view_count` | `integer` | ✗ | - |
| 19 | `created_at` | `timestamp with time zone` | ✗ | - |
| 20 | `updated_at` | `timestamp with time zone` | ✗ | - |
| 21 | `author_id` | `integer` | ✓ | - |
| 22 | `category_id` | `bigint` | ✓ | - |
| 23 | `ai_model` | `character varying(50)` | ✗ | - |
| 24 | `human_reviewed` | `boolean` | ✗ | - |
| 25 | `is_ai_generated` | `boolean` | ✗ | - |
| 26 | `n8n_created_at` | `timestamp with time zone` | ✓ | - |
| 27 | `n8n_execution_id` | `character varying(100)` | ✗ | - |
| 28 | `n8n_workflow_id` | `character varying(50)` | ✗ | - |
| 29 | `reviewed_at` | `timestamp with time zone` | ✓ | - |
| 30 | `reviewed_by_id` | `integer` | ✓ | - |
| 31 | `source` | `character varying(20)` | ✗ | - |
| 32 | `source_id` | `character varying(100)` | ✗ | - |
| 33 | `source_url` | `character varying(200)` | ✗ | - |

#### Foreign Keys

| Column | References |
|--------|------------|
| `author_id` | `auth_user.id` |
| `category_id` | `news_category.id` |
| `reviewed_by_id` | `auth_user.id` |

#### Indexes

- `news_article_pkey`
- `news_article_slug_key`
- `news_article_slug_5328fdc5_like`
- `news_article_author_id_11c60ced`
- `news_article_category_id_7ede7614`
- `news_article_reviewed_by_id_267fa2d3`

---

### news_category

**Rows:** 4

#### Columns

| # | Column | Type | Nullable | Default |
|---|--------|------|----------|---------|
| 1 | `id` 🔑 | `bigint` | ✗ | - |
| 2 | `name` | `character varying(100)` | ✗ | - |
| 3 | `slug` | `character varying(120)` | ✗ | - |
| 4 | `description` | `text` | ✗ | - |
| 5 | `icon` | `character varying(50)` | ✗ | - |
| 6 | `meta_title` | `character varying(70)` | ✗ | - |
| 7 | `meta_description` | `character varying(160)` | ✗ | - |
| 8 | `order` | `integer` | ✗ | - |
| 9 | `is_active` | `boolean` | ✗ | - |
| 10 | `created_at` | `timestamp with time zone` | ✗ | - |
| 11 | `updated_at` | `timestamp with time zone` | ✗ | - |

#### Indexes

- `news_category_pkey`
- `news_category_slug_key`
- `news_category_slug_8bf24efd_like`

---

### partners_friendrequest

**Rows:** N/A

#### Columns

| # | Column | Type | Nullable | Default |
|---|--------|------|----------|---------|
| 1 | `id` 🔑 | `bigint` | ✗ | - |
| 2 | `message` | `text` | ✗ | - |
| 3 | `status` | `character varying(20)` | ✗ | - |
| 4 | `created_at` | `timestamp with time zone` | ✗ | - |
| 5 | `updated_at` | `timestamp with time zone` | ✗ | - |
| 6 | `from_user_id` | `integer` | ✗ | - |
| 7 | `to_user_id` | `integer` | ✗ | - |

#### Foreign Keys

| Column | References |
|--------|------------|
| `from_user_id` | `auth_user.id` |
| `to_user_id` | `auth_user.id` |

#### Indexes

- `partners_friendrequest_pkey`
- `partners_friendrequest_from_user_id_to_user_id_19c723b6_uniq`
- `partners_friendrequest_from_user_id_465e55d0`
- `partners_friendrequest_to_user_id_1048c22b`

---

### partners_studyroom

**Rows:** N/A

#### Columns

| # | Column | Type | Nullable | Default |
|---|--------|------|----------|---------|
| 1 | `id` 🔑 | `bigint` | ✗ | - |
| 2 | `name` | `character varying(100)` | ✗ | - |
| 3 | `description` | `text` | ✗ | - |
| 4 | `max_members` | `integer` | ✗ | - |
| 5 | `target_language` | `character varying(10)` | ✗ | - |
| 6 | `level` | `character varying(20)` | ✗ | - |
| 7 | `house_color` | `character varying(30)` | ✗ | - |
| 8 | `is_active` | `boolean` | ✗ | - |
| 9 | `created_at` | `timestamp with time zone` | ✗ | - |
| 10 | `updated_at` | `timestamp with time zone` | ✗ | - |
| 11 | `chat_room_id` | `bigint` | ✓ | - |
| 12 | `owner_id` | `integer` | ✗ | - |
| 13 | `purpose` | `character varying(20)` | ✗ | - |
| 14 | `skill_focus` | `character varying(20)` | ✗ | - |

#### Foreign Keys

| Column | References |
|--------|------------|
| `chat_room_id` | `chat_chatroom.id` |
| `owner_id` | `auth_user.id` |

#### Indexes

- `partners_studyroom_pkey`
- `partners_studyroom_chat_room_id_key`
- `partners_studyroom_owner_id_4e96f519`

---

### partners_studyroom_members

**Rows:** N/A

#### Columns

| # | Column | Type | Nullable | Default |
|---|--------|------|----------|---------|
| 1 | `id` 🔑 | `bigint` | ✗ | - |
| 2 | `studyroom_id` | `bigint` | ✗ | - |
| 3 | `user_id` | `integer` | ✗ | - |

#### Foreign Keys

| Column | References |
|--------|------------|
| `studyroom_id` | `partners_studyroom.id` |
| `user_id` | `auth_user.id` |

#### Indexes

- `partners_studyroom_members_pkey`
- `partners_studyroom_members_studyroom_id_user_id_5ff11d63_uniq`
- `partners_studyroom_members_studyroom_id_9feb083e`
- `partners_studyroom_members_user_id_db8140eb`

---

### resources_category

**Rows:** 5

#### Columns

| # | Column | Type | Nullable | Default |
|---|--------|------|----------|---------|
| 1 | `id` 🔑 | `bigint` | ✗ | - |
| 2 | `name` | `character varying(50)` | ✗ | - |
| 3 | `slug` | `character varying(50)` | ✗ | - |
| 4 | `icon` | `character varying(50)` | ✗ | - |
| 5 | `description` | `text` | ✗ | - |

#### Indexes

- `resources_category_pkey`
- `resources_category_slug_key`
- `resources_category_slug_6b2b4140_like`

---

### resources_resource

**Rows:** 24

#### Columns

| # | Column | Type | Nullable | Default |
|---|--------|------|----------|---------|
| 1 | `id` 🔑 | `bigint` | ✗ | - |
| 2 | `title` | `character varying(200)` | ✗ | - |
| 3 | `slug` | `character varying(200)` | ✗ | - |
| 4 | `description` | `text` | ✗ | - |
| 5 | `file` | `character varying(100)` | ✓ | - |
| 6 | `youtube_url` | `character varying(200)` | ✓ | - |
| 7 | `cover_image` | `character varying(100)` | ✓ | - |
| 8 | `author` | `character varying(100)` | ✗ | - |
| 9 | `is_active` | `boolean` | ✗ | - |
| 10 | `is_featured` | `boolean` | ✗ | - |
| 11 | `view_count` | `integer` | ✗ | - |
| 12 | `download_count` | `integer` | ✗ | - |
| 13 | `created_at` | `timestamp with time zone` | ✗ | - |
| 14 | `updated_at` | `timestamp with time zone` | ✗ | - |
| 15 | `category_id` | `bigint` | ✗ | - |
| 16 | `resource_type` | `character varying(20)` | ✗ | - |
| 17 | `external_url` | `character varying(200)` | ✓ | - |
| 18 | `ai_model` | `character varying(50)` | ✗ | - |
| 19 | `human_reviewed` | `boolean` | ✗ | - |
| 20 | `is_ai_generated` | `boolean` | ✗ | - |
| 21 | `n8n_created_at` | `timestamp with time zone` | ✓ | - |
| 22 | `n8n_execution_id` | `character varying(100)` | ✗ | - |
| 23 | `n8n_workflow_id` | `character varying(50)` | ✗ | - |
| 24 | `reviewed_at` | `timestamp with time zone` | ✓ | - |
| 25 | `reviewed_by_id` | `integer` | ✓ | - |
| 26 | `source` | `character varying(20)` | ✗ | - |
| 27 | `source_id` | `character varying(100)` | ✗ | - |
| 28 | `source_url` | `character varying(200)` | ✗ | - |

#### Foreign Keys

| Column | References |
|--------|------------|
| `category_id` | `resources_category.id` |
| `reviewed_by_id` | `auth_user.id` |

#### Indexes

- `resources_resource_pkey`
- `resources_resource_slug_key`
- `resources_resource_slug_8867b959_like`
- `resources_resource_category_id_0cd2d52c`
- `resources_resource_reviewed_by_id_14080399`

---

### resources_resource_bookmarks

**Rows:** N/A

#### Columns

| # | Column | Type | Nullable | Default |
|---|--------|------|----------|---------|
| 1 | `id` 🔑 | `bigint` | ✗ | - |
| 2 | `resource_id` | `bigint` | ✗ | - |
| 3 | `user_id` | `integer` | ✗ | - |

#### Foreign Keys

| Column | References |
|--------|------------|
| `resource_id` | `resources_resource.id` |
| `user_id` | `auth_user.id` |

#### Indexes

- `resources_resource_bookmarks_pkey`
- `resources_resource_bookmarks_resource_id_user_id_e847e228_uniq`
- `resources_resource_bookmarks_resource_id_d27763af`
- `resources_resource_bookmarks_user_id_2068e4a6`

---

### resources_resource_tags

**Rows:** N/A

#### Columns

| # | Column | Type | Nullable | Default |
|---|--------|------|----------|---------|
| 1 | `id` 🔑 | `bigint` | ✗ | - |
| 2 | `resource_id` | `bigint` | ✗ | - |
| 3 | `tag_id` | `bigint` | ✗ | - |

#### Foreign Keys

| Column | References |
|--------|------------|
| `resource_id` | `resources_resource.id` |
| `tag_id` | `resources_tag.id` |

#### Indexes

- `resources_resource_tags_pkey`
- `resources_resource_tags_resource_id_tag_id_4463847d_uniq`
- `resources_resource_tags_resource_id_33e5c8e2`
- `resources_resource_tags_tag_id_7ed3b40d`

---

### resources_tag

**Rows:** 10

#### Columns

| # | Column | Type | Nullable | Default |
|---|--------|------|----------|---------|
| 1 | `id` 🔑 | `bigint` | ✗ | - |
| 2 | `name` | `character varying(50)` | ✗ | - |
| 3 | `slug` | `character varying(50)` | ✗ | - |

#### Indexes

- `resources_tag_pkey`
- `resources_tag_name_key`
- `resources_tag_slug_key`
- `resources_tag_name_0b3bfec4_like`
- `resources_tag_slug_eeaed1a6_like`

---

### tools_flashcard

**Rows:** 25

#### Columns

| # | Column | Type | Nullable | Default |
|---|--------|------|----------|---------|
| 1 | `id` 🔑 | `bigint` | ✗ | - |
| 2 | `front` | `text` | ✗ | - |
| 3 | `back` | `text` | ✗ | - |
| 4 | `example` | `text` | ✗ | - |
| 5 | `pronunciation` | `character varying(200)` | ✗ | - |
| 6 | `audio_url` | `character varying(200)` | ✗ | - |
| 7 | `image` | `character varying(100)` | ✗ | - |
| 8 | `order` | `integer` | ✗ | - |
| 9 | `created_at` | `timestamp with time zone` | ✗ | - |
| 10 | `updated_at` | `timestamp with time zone` | ✗ | - |
| 11 | `deck_id` | `bigint` | ✗ | - |

#### Foreign Keys

| Column | References |
|--------|------------|
| `deck_id` | `tools_flashcarddeck.id` |

#### Indexes

- `tools_flashcard_pkey`
- `tools_flashcard_deck_id_d8622df7`

---

### tools_flashcarddeck

**Rows:** 3

#### Columns

| # | Column | Type | Nullable | Default |
|---|--------|------|----------|---------|
| 1 | `id` 🔑 | `bigint` | ✗ | - |
| 2 | `name` | `character varying(200)` | ✗ | - |
| 3 | `slug` | `character varying(220)` | ✗ | - |
| 4 | `description` | `text` | ✗ | - |
| 5 | `language` | `character varying(5)` | ✗ | - |
| 6 | `level` | `character varying(5)` | ✗ | - |
| 7 | `is_public` | `boolean` | ✗ | - |
| 8 | `is_featured` | `boolean` | ✗ | - |
| 9 | `view_count` | `integer` | ✗ | - |
| 10 | `created_at` | `timestamp with time zone` | ✗ | - |
| 11 | `updated_at` | `timestamp with time zone` | ✗ | - |
| 12 | `author_id` | `integer` | ✓ | - |

#### Foreign Keys

| Column | References |
|--------|------------|
| `author_id` | `auth_user.id` |

#### Indexes

- `tools_flashcarddeck_pkey`
- `tools_flashcarddeck_slug_key`
- `tools_flashcarddeck_slug_f07b1a6a_like`
- `tools_flashcarddeck_author_id_1908dec7`

---

### tools_tool

**Rows:** 8

#### Columns

| # | Column | Type | Nullable | Default |
|---|--------|------|----------|---------|
| 1 | `id` 🔑 | `bigint` | ✗ | - |
| 2 | `name` | `character varying(200)` | ✗ | - |
| 3 | `slug` | `character varying(220)` | ✗ | - |
| 4 | `description` | `text` | ✗ | - |
| 5 | `tool_type` | `character varying(20)` | ✗ | - |
| 6 | `url` | `character varying(500)` | ✗ | - |
| 7 | `embed_code` | `text` | ✗ | - |
| 8 | `icon` | `character varying(50)` | ✗ | - |
| 9 | `cover_image` | `character varying(100)` | ✗ | - |
| 10 | `language` | `character varying(5)` | ✗ | - |
| 11 | `is_featured` | `boolean` | ✗ | - |
| 12 | `is_active` | `boolean` | ✗ | - |
| 13 | `order` | `integer` | ✗ | - |
| 14 | `view_count` | `integer` | ✗ | - |
| 15 | `created_at` | `timestamp with time zone` | ✗ | - |
| 16 | `updated_at` | `timestamp with time zone` | ✗ | - |
| 17 | `category_id` | `bigint` | ✓ | - |

#### Foreign Keys

| Column | References |
|--------|------------|
| `category_id` | `tools_toolcategory.id` |

#### Indexes

- `tools_tool_pkey`
- `tools_tool_slug_key`
- `tools_tool_slug_865259d9_like`
- `tools_tool_category_id_75826aee`

---

### tools_toolcategory

**Rows:** 5

#### Columns

| # | Column | Type | Nullable | Default |
|---|--------|------|----------|---------|
| 1 | `id` 🔑 | `bigint` | ✗ | - |
| 2 | `name` | `character varying(100)` | ✗ | - |
| 3 | `slug` | `character varying(120)` | ✗ | - |
| 4 | `description` | `text` | ✗ | - |
| 5 | `icon` | `character varying(50)` | ✗ | - |
| 6 | `order` | `integer` | ✗ | - |
| 7 | `is_active` | `boolean` | ✗ | - |
| 8 | `created_at` | `timestamp with time zone` | ✗ | - |
| 9 | `updated_at` | `timestamp with time zone` | ✗ | - |

#### Indexes

- `tools_toolcategory_pkey`
- `tools_toolcategory_slug_key`
- `tools_toolcategory_slug_c4baec81_like`

---
