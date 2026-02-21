"""
Script tạo dữ liệu mẫu đầy đủ cho UnstressVN
Chạy: python manage.py shell < create_full_sample_data.py
Hoặc: python manage.py runscript create_full_sample_data
"""

import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'unstressvn_settings.settings')

from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
import random

print("=" * 60)
print("   TẠO DỮ LIỆU MẪU CHO UNSTRESSVN")
print("=" * 60)

# ============================================================
# 1. TẠO USERS VÀ PROFILES
# ============================================================
print("\n📌 1. TẠO USERS VÀ PROFILES...")

from accounts.models import UserProfile

sample_users = [
    {
        'username': 'nguyenvan',
        'email': 'nguyenvan@example.com',
        'first_name': 'Văn',
        'last_name': 'Nguyễn',
        'profile': {
            'bio': 'Mình đang học Tiếng Đức để đi du học. Rất vui được kết nối với mọi người!',
            'native_language': 'vi',
            'target_language': 'de',
            'level': 'B1',
            'is_public': True,
        }
    },
    {
        'username': 'tranlinh',
        'email': 'tranlinh@example.com',
        'first_name': 'Linh',
        'last_name': 'Trần',
        'profile': {
            'bio': 'Giáo viên Tiếng Anh với 5 năm kinh nghiệm. Sẵn sàng hỗ trợ các bạn học!',
            'native_language': 'vi',
            'target_language': 'en',
            'level': 'C1',
            'is_public': True,
        }
    },
    {
        'username': 'lehoa',
        'email': 'lehoa@example.com',
        'first_name': 'Hoa',
        'last_name': 'Lê',
        'profile': {
            'bio': 'Yêu thích văn hóa Nhật Bản, đang tự học Tiếng Nhật.',
            'native_language': 'vi',
            'target_language': 'ja',
            'level': 'A2',
            'is_public': True,
        }
    },
    {
        'username': 'phamminh',
        'email': 'phamminh@example.com',
        'first_name': 'Minh',
        'last_name': 'Phạm',
        'profile': {
            'bio': 'Sinh viên CNTT, học Tiếng Anh để đọc tài liệu chuyên ngành.',
            'native_language': 'vi',
            'target_language': 'en',
            'level': 'B2',
            'is_public': True,
        }
    },
    {
        'username': 'vuthao',
        'email': 'vuthao@example.com',
        'first_name': 'Thảo',
        'last_name': 'Vũ',
        'profile': {
            'bio': 'Đang chuẩn bị IELTS 7.0, tìm partner practice speaking!',
            'native_language': 'vi',
            'target_language': 'en',
            'level': 'B1',
            'is_public': True,
        }
    },
]

created_users = []
for user_data in sample_users:
    user, created = User.objects.get_or_create(
        username=user_data['username'],
        defaults={
            'email': user_data['email'],
            'first_name': user_data['first_name'],
            'last_name': user_data['last_name'],
        }
    )
    if created:
        user.set_password('password123')
        user.save()
    
    # Update profile
    profile = user.profile
    for key, value in user_data['profile'].items():
        setattr(profile, key, value)
    profile.save()
    
    created_users.append(user)
    status = "✓ Tạo mới" if created else "○ Đã tồn tại"
    print(f"   {status}: {user.get_full_name()} (@{user.username})")

# ============================================================
# 2. TẠO CATEGORIES (DANH MỤC NGÔN NGỮ)
# ============================================================
print("\n📌 2. TẠO DANH MỤC NGÔN NGỮ...")

from resources.models import Category

categories_data = [
    {'name': 'Tiếng Anh', 'slug': 'tieng-anh', 'description': 'Tài liệu học Tiếng Anh - English'},
    {'name': 'Tiếng Đức', 'slug': 'tieng-duc', 'description': 'Tài liệu học Tiếng Đức - Deutsch'},
    {'name': 'Tiếng Nhật', 'slug': 'tieng-nhat', 'description': 'Tài liệu học Tiếng Nhật - 日本語'},
    {'name': 'Tiếng Hàn', 'slug': 'tieng-han', 'description': 'Tài liệu học Tiếng Hàn - 한국어'},
    {'name': 'Tiếng Trung', 'slug': 'tieng-trung', 'description': 'Tài liệu học Tiếng Trung - 中文'},
    {'name': 'Tiếng Pháp', 'slug': 'tieng-phap', 'description': 'Tài liệu học Tiếng Pháp - Français'},
]

created_categories = {}
for cat_data in categories_data:
    cat, created = Category.objects.get_or_create(
        slug=cat_data['slug'],
        defaults=cat_data
    )
    created_categories[cat_data['slug']] = cat
    status = "✓ Tạo mới" if created else "○ Đã tồn tại"
    print(f"   {status}: {cat.name}")

# ============================================================
# 3. LOẠI TÀI LIỆU (ĐÃ CHUYỂN SANG CHOICES)
# ============================================================
print("\n📌 3. LOẠI TÀI LIỆU...")
print("   ℹ️ Đã chuyển sang sử dụng choices: ebook, video, audio, pdf, flashcard, document")

# ============================================================
# 4. TẠO RESOURCES (TÀI LIỆU)
# ============================================================
print("\n📌 4. TẠO TÀI LIỆU MẪU...")

from resources.models import Resource

resources_data = [
    # Tiếng Anh
    {
        'title': 'English Grammar in Use',
        'slug': 'english-grammar-in-use',
        'description': 'Cuốn sách ngữ pháp Tiếng Anh kinh điển của Raymond Murphy. Phù hợp cho người học từ trình độ sơ cấp đến trung cấp. Bao gồm các bài tập thực hành và đáp án.',
        'author': 'Raymond Murphy',
        'category': 'tieng-anh',
        'resource_type': 'ebook',
        'is_featured': True,
    },
    {
        'title': 'IELTS Academic Writing Task 2',
        'slug': 'ielts-writing-task2',
        'description': 'Tổng hợp các dạng bài Task 2 thường gặp trong IELTS Academic. Bao gồm cấu trúc bài, từ vựng và bài mẫu band 7+.',
        'author': 'IELTS Prep Team',
        'category': 'tieng-anh',
        'resource_type': 'pdf',
        'is_featured': True,
    },
    {
        'title': 'TED Talks for English Learners',
        'slug': 'ted-talks-english',
        'description': 'Tuyển tập các bài TED Talks hay nhất cho người học Tiếng Anh. Có phụ đề song ngữ và từ vựng chú thích.',
        'author': 'TED Education',
        'category': 'tieng-anh',
        'resource_type': 'video',
    },
    {
        'title': '4000 Essential English Words',
        'slug': '4000-essential-words',
        'description': 'Bộ từ vựng 4000 từ thiết yếu cho người học Tiếng Anh. Phân loại theo chủ đề, có ví dụ và audio phát âm.',
        'author': 'Paul Nation',
        'category': 'tieng-anh',
        'resource_type': 'flashcard',
    },
    
    # Tiếng Đức
    {
        'title': 'Menschen A1 - Kursbuch',
        'slug': 'menschen-a1',
        'description': 'Giáo trình Tiếng Đức Menschen trình độ A1. Được thiết kế theo chuẩn châu Âu, phù hợp cho người mới bắt đầu.',
        'author': 'Hueber Verlag',
        'category': 'tieng-duc',
        'resource_type': 'ebook',
        'is_featured': True,
    },
    {
        'title': 'Deutsche Grammatik A1-B1',
        'slug': 'deutsche-grammatik',
        'description': 'Tổng hợp ngữ pháp Tiếng Đức từ A1 đến B1. Giải thích rõ ràng bằng Tiếng Việt, có nhiều bài tập thực hành.',
        'author': 'Học Tiếng Đức Online',
        'category': 'tieng-duc',
        'resource_type': 'pdf',
    },
    {
        'title': 'Slow German Podcast',
        'slug': 'slow-german-podcast',
        'description': 'Podcast Tiếng Đức nói chậm, dễ nghe. Các chủ đề về văn hóa, lịch sử và đời sống Đức.',
        'author': 'Annik Rubens',
        'category': 'tieng-duc',
        'resource_type': 'audio',
    },
    
    # Tiếng Nhật
    {
        'title': 'Minna no Nihongo Sơ cấp 1',
        'slug': 'minna-no-nihongo-1',
        'description': 'Giáo trình Tiếng Nhật phổ biến nhất cho người mới bắt đầu. Bao gồm sách chính khóa và sách bài tập.',
        'author': '3A Corporation',
        'category': 'tieng-nhat',
        'resource_type': 'ebook',
        'is_featured': True,
    },
    {
        'title': 'Kanji N5-N4 Flashcards',
        'slug': 'kanji-n5-n4',
        'description': 'Bộ flashcard 300 Kanji cơ bản cho JLPT N5 và N4. Có cách viết, âm On/Kun và từ vựng liên quan.',
        'author': 'Japanese Pod 101',
        'category': 'tieng-nhat',
        'resource_type': 'flashcard',
    },
    
    # Tiếng Hàn
    {
        'title': 'Korean Made Simple',
        'slug': 'korean-made-simple',
        'description': 'Sách tự học Tiếng Hàn cho người mới bắt đầu. Giải thích dễ hiểu, có audio và video hỗ trợ.',
        'author': 'Billy Go',
        'category': 'tieng-han',
        'resource_type': 'ebook',
    },
    {
        'title': 'TOPIK I Vocabulary',
        'slug': 'topik-1-vocabulary',
        'description': 'Từ vựng cần thiết cho kỳ thi TOPIK I (cấp 1-2). Phân loại theo chủ đề, có ví dụ thực tế.',
        'author': 'TOPIK Guide',
        'category': 'tieng-han',
        'resource_type': 'pdf',
    },
    
    # Tiếng Trung
    {
        'title': 'HSK Standard Course 1',
        'slug': 'hsk-standard-1',
        'description': 'Giáo trình chuẩn HSK cấp 1. Bao gồm 150 từ vựng cơ bản và ngữ pháp nhập môn.',
        'author': 'Hanban',
        'category': 'tieng-trung',
        'resource_type': 'ebook',
    },
    
    # Tiếng Pháp
    {
        'title': 'Alter Ego+ A1',
        'slug': 'alter-ego-a1',
        'description': 'Giáo trình Tiếng Pháp cho người mới bắt đầu. Phương pháp giao tiếp hiện đại.',
        'author': 'Hachette FLE',
        'category': 'tieng-phap',
        'resource_type': 'ebook',
    },
]

for res_data in resources_data:
    category = created_categories.get(res_data.pop('category'))
    resource_type = res_data.pop('resource_type')
    
    resource, created = Resource.objects.get_or_create(
        slug=res_data['slug'],
        defaults={
            **res_data,
            'category': category,
            'resource_type': resource_type,
            'is_active': True,
            'view_count': random.randint(50, 500),
            'download_count': random.randint(10, 100),
        }
    )
    status = "✓ Tạo mới" if created else "○ Đã tồn tại"
    print(f"   {status}: {resource.title}")

# ============================================================
# 5. TẠO FORUM CATEGORIES VÀ POSTS
# ============================================================
print("\n📌 5. TẠO DIỄN ĐÀN MẪU...")

try:
    from forum.models import ForumCategory, ForumPost
    
    forum_categories_data = [
        {'name': 'Chia sẻ kinh nghiệm', 'slug': 'chia-se-kinh-nghiem', 'description': 'Chia sẻ kinh nghiệm học ngoại ngữ'},
        {'name': 'Hỏi đáp', 'slug': 'hoi-dap', 'description': 'Đặt câu hỏi và nhận giải đáp từ cộng đồng'},
        {'name': 'Tìm partner học', 'slug': 'tim-partner', 'description': 'Tìm bạn học cùng'},
        {'name': 'Giới thiệu tài liệu', 'slug': 'gioi-thieu-tai-lieu', 'description': 'Giới thiệu sách, video, khóa học hay'},
    ]
    
    forum_cats = {}
    for cat_data in forum_categories_data:
        cat, created = ForumCategory.objects.get_or_create(
            slug=cat_data['slug'],
            defaults=cat_data
        )
        forum_cats[cat_data['slug']] = cat
        status = "✓ Tạo mới" if created else "○ Đã tồn tại"
        print(f"   {status}: {cat.name}")
    
    # Forum Posts
    posts_data = [
        {
            'title': 'Kinh nghiệm thi IELTS 7.5 sau 3 tháng ôn',
            'content': '''Mình vừa nhận kết quả IELTS 7.5 overall và muốn chia sẻ kinh nghiệm:

1. **Listening (8.0)**: Nghe TED Talks và BBC mỗi ngày, làm Cambridge Practice Tests
2. **Reading (7.5)**: Đọc The Economist, làm bài từ IELTS Trainer
3. **Writing (7.0)**: Học cấu trúc từ IELTS Simon, viết mỗi ngày và nhờ người sửa
4. **Speaking (7.0)**: Nói chuyện với bạn nước ngoài qua HelloTalk, tự thu âm và nghe lại

Chúc các bạn học tốt! Có gì cứ hỏi mình nhé.''',
            'category': 'chia-se-kinh-nghiem',
            'author': 'tranlinh',
            'is_pinned': True,
        },
        {
            'title': 'Hỏi về cách học ngữ pháp Tiếng Đức hiệu quả',
            'content': '''Chào mọi người,

Mình đang học Tiếng Đức được 2 tháng nhưng thấy ngữ pháp rất khó, đặc biệt là:
- Der/Die/Das (giống của danh từ)
- Cách chia động từ
- Các giới từ + cách

Mọi người có tips gì không ạ? Cảm ơn nhiều!''',
            'category': 'hoi-dap',
            'author': 'nguyenvan',
        },
        {
            'title': 'Tìm partner practice speaking Tiếng Anh online',
            'content': '''Hi everyone!

Mình đang chuẩn bị thi IELTS và cần partner để practice speaking. 

**Thông tin về mình:**
- Level: B1-B2
- Mục tiêu: IELTS 6.5
- Thời gian rảnh: Tối 8-10h

Ai có nhu cầu tương tự thì liên hệ mình nhé!''',
            'category': 'tim-partner',
            'author': 'vuthao',
        },
        {
            'title': 'Review sách "English Grammar in Use" - Raymond Murphy',
            'content': '''Xin giới thiệu đến các bạn cuốn sách ngữ pháp kinh điển!

**Ưu điểm:**
- Giải thích rõ ràng, dễ hiểu
- Mỗi unit có bài tập kèm đáp án
- Phù hợp tự học

**Nhược điểm:**
- Hoàn toàn bằng Tiếng Anh (có thể khó với beginner)
- Không có audio

**Đánh giá:** 9/10 - Must have cho ai học Tiếng Anh!''',
            'category': 'gioi-thieu-tai-lieu',
            'author': 'phamminh',
        },
    ]
    
    for post_data in posts_data:
        category = forum_cats.get(post_data.pop('category'))
        author = User.objects.get(username=post_data.pop('author'))
        
        post, created = ForumPost.objects.get_or_create(
            title=post_data['title'],
            defaults={
                **post_data,
                'category': category,
                'author': author,
                'is_active': True,
                'view_count': random.randint(20, 200),
            }
        )
        status = "✓ Tạo mới" if created else "○ Đã tồn tại"
        print(f"   {status}: {post.title[:40]}...")

except ImportError:
    print("   ⚠ Forum app chưa được cài đặt")

# ============================================================
# 6. TẠO FRIEND REQUESTS (LỜI MỜI KẾT BẠN)
# ============================================================
print("\n📌 6. TẠO LỜI MỜI KẾT BẠN MẪU...")

try:
    from partners.models import FriendRequest
    
    # Tạo một số lời mời kết bạn
    pairs = [
        ('nguyenvan', 'tranlinh', 'accepted'),
        ('vuthao', 'phamminh', 'accepted'),
        ('lehoa', 'nguyenvan', 'pending'),
    ]
    
    for from_user, to_user, status in pairs:
        from_u = User.objects.get(username=from_user)
        to_u = User.objects.get(username=to_user)
        
        fr, created = FriendRequest.objects.get_or_create(
            from_user=from_u,
            to_user=to_u,
            defaults={'status': status}
        )
        if not created:
            fr.status = status
            fr.save()
        
        print(f"   ✓ {from_u.username} → {to_u.username}: {status}")

except ImportError:
    print("   ⚠ Partners app chưa được cài đặt")

# ============================================================
# 7. TẠO CHAT ROOMS VÀ MESSAGES
# ============================================================
print("\n📌 7. TẠO TIN NHẮN MẪU...")

try:
    from chat.models import ChatRoom, Message
    
    # Tạo chat room giữa các cặp bạn
    user1 = User.objects.get(username='nguyenvan')
    user2 = User.objects.get(username='tranlinh')
    
    room, created = ChatRoom.objects.get_or_create(
        name=f"chat_{user1.id}_{user2.id}"
    )
    room.participants.add(user1, user2)
    
    messages_data = [
        (user1, "Chào chị Linh! Em đang học Tiếng Đức, chị có tips gì không ạ?"),
        (user2, "Chào em! Em học được bao lâu rồi?"),
        (user1, "Em mới học được 2 tháng thôi ạ, đang loay hoay với ngữ pháp"),
        (user2, "Ngữ pháp Đức khó thiệt! Chị recommend em dùng app Duolingo kết hợp với sách Menschen nhé"),
        (user1, "Dạ em cảm ơn chị! Em sẽ thử ngay 😊"),
    ]
    
    for i, (sender, content) in enumerate(messages_data):
        msg, created = Message.objects.get_or_create(
            room=room,
            sender=sender,
            content=content,
            defaults={
                'created_at': timezone.now() - timedelta(hours=len(messages_data)-i)
            }
        )
        if created:
            print(f"   ✓ {sender.username}: {content[:30]}...")

except ImportError:
    print("   ⚠ Chat app chưa được cài đặt")

# ============================================================
# HOÀN THÀNH
# ============================================================
print("\n" + "=" * 60)
print("   ✅ HOÀN THÀNH TẠO DỮ LIỆU MẪU!")
print("=" * 60)
print("""
📋 Tài khoản mẫu (password: password123):
   - nguyenvan / tranlinh / lehoa / phamminh / vuthao

🔗 Truy cập:
   - Trang chủ: http://localhost:8000/
   - Tài liệu: http://localhost:8000/tai-lieu/
   - Cộng đồng: http://localhost:8000/tim-ban-hoc/
   - Admin: http://localhost:8000/admin/
""")
