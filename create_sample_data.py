#!/usr/bin/env python
"""
Sample data for UnstressVN
Creates users, resources, videos, news, knowledge articles
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'unstressvn_settings.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.text import slugify
from datetime import timedelta
import random

User = get_user_model()

print("=" * 50)
print("Creating sample data for UnstressVN...")
print("=" * 50)

# ============================================
# 1. Create Users
# ============================================
print("\n📝 Creating users...")

users_data = [
    {'username': 'admin', 'email': 'admin@unstressvn.com', 'is_staff': True, 'is_superuser': True},
    {'username': 'nguyenvan', 'email': 'nguyen@example.com', 'first_name': 'Văn', 'last_name': 'Nguyễn'},
    {'username': 'tranlinh', 'email': 'linh@example.com', 'first_name': 'Linh', 'last_name': 'Trần'},
    {'username': 'lehoa', 'email': 'hoa@example.com', 'first_name': 'Hòa', 'last_name': 'Lê'},
    {'username': 'phamminh', 'email': 'minh@example.com', 'first_name': 'Minh', 'last_name': 'Phạm'},
    {'username': 'vuthao', 'email': 'thao@example.com', 'first_name': 'Thảo', 'last_name': 'Vũ'},
]

created_users = []
for user_data in users_data:
    user, created = User.objects.get_or_create(
        username=user_data['username'],
        defaults=user_data
    )
    if created:
        password = 'admin123' if user_data.get('is_superuser') else 'password123'
        user.set_password(password)
        user.save()
        print(f"  ✓ Created user: {user.username}")
    else:
        print(f"  - User exists: {user.username}")
    created_users.append(user)

admin_user = User.objects.get(username='admin')

# ============================================
# 2. Create Resources
# ============================================
print("\n📚 Creating resources...")

try:
    from resources.models import Resource, Category, Tag
    
    # Categories (Language categories)
    categories_data = [
        {'name': 'Tiếng Anh', 'slug': 'tieng-anh', 'icon': 'bi-translate', 'description': 'Tài liệu học tiếng Anh'},
        {'name': 'Tiếng Đức', 'slug': 'tieng-duc', 'icon': 'bi-flag', 'description': 'Tài liệu học tiếng Đức'},
        {'name': 'IELTS', 'slug': 'ielts', 'icon': 'bi-award', 'description': 'Tài liệu luyện thi IELTS'},
        {'name': 'Goethe', 'slug': 'goethe', 'icon': 'bi-trophy', 'description': 'Tài liệu luyện thi Goethe'},
        {'name': 'Tổng hợp', 'slug': 'tong-hop', 'icon': 'bi-collection', 'description': 'Tài liệu tổng hợp'},
    ]
    
    for cat_data in categories_data:
        cat, created = Category.objects.get_or_create(
            slug=cat_data['slug'],
            defaults=cat_data
        )
        if created:
            print(f"  ✓ Created category: {cat.name}")
    
    # Tags
    tags_data = ['A1', 'A2', 'B1', 'B2', 'C1', 'grammar', 'vocabulary', 'speaking', 'listening', 'writing']
    for tag_name in tags_data:
        Tag.objects.get_or_create(name=tag_name)
    
    # Resources
    resources_data = [
        {
            'title': 'IELTS Cambridge 18 - Test Book',
            'slug': 'ielts-cambridge-18',
            'description': 'Sách luyện thi IELTS Cambridge 18 với đầy đủ 4 kỹ năng.',
            'category_slug': 'ielts',
            'resource_type': 'ebook',
            'author': 'Cambridge University Press',
        },
        {
            'title': 'Từ vựng tiếng Đức A1-B1',
            'slug': 'tu-vung-tieng-duc-a1-b1',
            'description': 'Bộ từ vựng tiếng Đức từ cơ bản đến trung cấp.',
            'category_slug': 'tieng-duc',
            'resource_type': 'pdf',
            'author': 'UnstressVN',
        },
        {
            'title': 'English Grammar in Use',
            'slug': 'english-grammar-in-use',
            'description': 'Giáo trình ngữ pháp tiếng Anh kinh điển của Raymond Murphy.',
            'category_slug': 'tieng-anh',
            'resource_type': 'ebook',
            'author': 'Raymond Murphy',
        },
        {
            'title': 'Goethe B1 Exam Practice',
            'slug': 'goethe-b1-exam-practice',
            'description': 'Bộ đề luyện thi Goethe B1 với hướng dẫn chi tiết.',
            'category_slug': 'goethe',
            'resource_type': 'pdf',
            'author': 'Goethe Institut',
        },
        {
            'title': 'Podcast tiếng Anh cho người Việt',
            'slug': 'podcast-tieng-anh-nguoi-viet',
            'description': 'Tổng hợp các podcast học tiếng Anh dành riêng cho người Việt.',
            'category_slug': 'tieng-anh',
            'resource_type': 'audio',
            'author': 'UnstressVN',
        },
        {
            'title': 'Deutsch Welle Audio Lessons',
            'slug': 'deutsch-welle-audio',
            'description': 'Bài học audio tiếng Đức từ Deutsch Welle.',
            'category_slug': 'tieng-duc',
            'resource_type': 'audio',
            'author': 'Deutsche Welle',
        },
        {
            'title': 'Flashcards Từ vựng IELTS',
            'slug': 'flashcards-ielts',
            'description': 'Bộ flashcards 3000 từ vựng IELTS thường gặp nhất.',
            'category_slug': 'ielts',
            'resource_type': 'flashcard',
            'author': 'UnstressVN',
        },
        {
            'title': 'Tài liệu ôn thi Goethe A2',
            'slug': 'tai-lieu-goethe-a2',
            'description': 'Tổng hợp tài liệu ôn thi Goethe A2 đầy đủ 4 kỹ năng.',
            'category_slug': 'goethe',
            'resource_type': 'document',
            'author': 'Goethe Institut',
        },
        {
            'title': 'Video hướng dẫn phát âm tiếng Đức',
            'slug': 'video-phat-am-tieng-duc',
            'description': 'Series video hướng dẫn phát âm chuẩn tiếng Đức.',
            'category_slug': 'tieng-duc',
            'resource_type': 'video',
            'youtube_url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
            'author': 'UnstressVN',
        },
        {
            'title': 'Tổng hợp tài liệu học ngoại ngữ 2024',
            'slug': 'tong-hop-tai-lieu-2024',
            'description': 'Bộ tài liệu học ngoại ngữ đầy đủ nhất 2024 cho người Việt.',
            'category_slug': 'tong-hop',
            'resource_type': 'document',
            'author': 'UnstressVN Team',
        },
    ]
    
    for res_data in resources_data:
        category_slug = res_data.pop('category_slug')
        category = Category.objects.get(slug=category_slug)
        
        resource, created = Resource.objects.get_or_create(
            slug=res_data['slug'],
            defaults={
                **res_data,
                'category': category,
                'view_count': random.randint(100, 1000),
                'download_count': random.randint(50, 500),
            }
        )
        if created:
            print(f"  ✓ Created resource: {resource.title}")
            
except Exception as e:
    print(f"  ⚠ Error creating resources: {e}")

# ============================================
# 3. Create Videos
# ============================================
print("\n🎬 Creating videos...")

try:
    from core.models import Video
    
    videos_data = [
        {
            'title': 'Học tiếng Đức A1 - Bài 1: Giới thiệu bản thân',
            'youtube_id': 'dQw4w9WgXcQ',
            'language': 'de',
            'level': 'A1',
            'description': 'Bài học đầu tiên về cách giới thiệu bản thân bằng tiếng Đức'
        },
        {
            'title': 'Học tiếng Đức A1 - Bài 2: Số đếm',
            'youtube_id': 'jNQXAC9IVRw',
            'language': 'de',
            'level': 'A1',
            'description': 'Học cách đếm số từ 1 đến 100 trong tiếng Đức'
        },
        {
            'title': 'Ngữ pháp tiếng Đức B1 - Konjunktiv II',
            'youtube_id': '9bZkp7q19f0',
            'language': 'de',
            'level': 'B1',
            'description': 'Giải thích chi tiết về thức giả định trong tiếng Đức'
        },
        {
            'title': 'English Pronunciation - Vowel Sounds',
            'youtube_id': 'FzQ5vEtT2-Q',
            'language': 'en',
            'level': 'A2',
            'description': 'Learn English vowel sounds with clear examples'
        },
        {
            'title': 'IELTS Speaking Tips - Band 7+',
            'youtube_id': 'kJQP7kiw5Fk',
            'language': 'en',
            'level': 'B2',
            'description': 'Tips and strategies for IELTS Speaking test'
        },
    ]
    
    for video_data in videos_data:
        slug = slugify(video_data['title'])
        video, created = Video.objects.get_or_create(
            slug=slug,
            defaults={
                **video_data,
                'view_count': random.randint(100, 5000),
                'is_active': True,
            }
        )
        if created:
            print(f"  ✓ Created video: {video.title}")
            
except Exception as e:
    print(f"  ⚠ Error creating videos: {e}")

# ============================================
# 4. Create News Articles
# ============================================
print("\n📰 Creating news articles...")

try:
    # Model names: Category and Article (not NewsCategory, NewsArticle)
    from news.models import Article, Category as NewsCategory
    
    # Categories
    news_cats_data = [
        {'name': 'Học tiếng Đức', 'slug': 'hoc-tieng-duc', 'description': 'Tin tức về học tiếng Đức'},
        {'name': 'Học tiếng Anh', 'slug': 'hoc-tieng-anh', 'description': 'Tin tức về học tiếng Anh'},
        {'name': 'Du học', 'slug': 'du-hoc', 'description': 'Tin tức du học'},
        {'name': 'Thi cử', 'slug': 'thi-cu', 'description': 'Thông tin thi cử'},
    ]
    
    for cat_data in news_cats_data:
        cat, created = NewsCategory.objects.get_or_create(
            slug=cat_data['slug'],
            defaults=cat_data
        )
        if created:
            print(f"  ✓ Created news category: {cat.name}")
    
    # Articles - Using correct field names: excerpt (not summary), is_published (not status)
    news_articles_data = [
        {
            'title': 'Lộ trình học tiếng Đức từ A1 đến B2 trong 12 tháng',
            'slug': 'lo-trinh-hoc-tieng-duc-a1-b2',
            'excerpt': 'Hướng dẫn chi tiết lộ trình học tiếng Đức hiệu quả từ con số 0.',
            'content': '''<h2>Lộ trình học tiếng Đức hiệu quả</h2>
<p>Học tiếng Đức không khó nếu bạn có phương pháp đúng đắn. Dưới đây là lộ trình chi tiết:</p>
<h3>Giai đoạn 1: A1 (2-3 tháng)</h3>
<p>Học cơ bản về phát âm, bảng chữ cái, và các câu giao tiếp đơn giản.</p>
<h3>Giai đoạn 2: A2 (2-3 tháng)</h3>
<p>Mở rộng từ vựng, học ngữ pháp cơ bản như chia động từ, giống từ.</p>
<h3>Giai đoạn 3: B1 (3-4 tháng)</h3>
<p>Học ngữ pháp phức tạp hơn, luyện nghe và nói nhiều hơn.</p>
<h3>Giai đoạn 4: B2 (3-4 tháng)</h3>
<p>Hoàn thiện ngữ pháp, luyện viết học thuật, chuẩn bị thi Goethe B2.</p>''',
            'category_slug': 'hoc-tieng-duc',
            'is_featured': True,
        },
        {
            'title': 'Top 10 ứng dụng học tiếng Đức miễn phí tốt nhất 2024',
            'slug': 'top-10-ung-dung-hoc-tieng-duc-2024',
            'excerpt': 'Tổng hợp các ứng dụng học tiếng Đức miễn phí được đánh giá cao nhất.',
            'content': '''<h2>Top 10 App học tiếng Đức miễn phí</h2>
<ol>
<li><strong>Duolingo</strong> - Ứng dụng học ngoại ngữ phổ biến nhất thế giới</li>
<li><strong>Babbel</strong> - Thiết kế bài học theo chủ đề thực tế</li>
<li><strong>Deutsche Welle</strong> - Tài liệu chính thức từ Đức</li>
<li><strong>Anki</strong> - Flashcard thông minh cho từ vựng</li>
<li><strong>Memrise</strong> - Học qua video người bản xứ</li>
</ol>''',
            'category_slug': 'hoc-tieng-duc',
        },
        {
            'title': 'Lịch thi Goethe 2026 - Cập nhật mới nhất',
            'slug': 'lich-thi-goethe-2026',
            'excerpt': 'Lịch thi các kỳ thi Goethe tại Việt Nam năm 2026.',
            'content': '''<h2>Lịch thi Goethe 2026</h2>
<p>Goethe Institut Việt Nam vừa công bố lịch thi chính thức năm 2026.</p>
<h3>Kỳ thi A1-A2</h3>
<p>Tháng 1, 3, 5, 7, 9, 11</p>
<h3>Kỳ thi B1</h3>
<p>Tháng 2, 4, 6, 8, 10, 12</p>
<h3>Kỳ thi B2</h3>
<p>Tháng 3, 6, 9, 12</p>''',
            'category_slug': 'thi-cu',
        },
        {
            'title': 'Du học Đức 2026: Chi phí và điều kiện mới nhất',
            'slug': 'du-hoc-duc-2026-chi-phi-dieu-kien',
            'excerpt': 'Cập nhật chi phí sinh hoạt, học phí và điều kiện du học Đức mới nhất.',
            'content': '''<h2>Du học Đức 2026</h2>
<p>Đức vẫn là điểm đến du học hấp dẫn nhất châu Âu với chi phí thấp.</p>
<h3>Chi phí</h3>
<ul>
<li>Học phí: Miễn phí (trừ một số trường)</li>
<li>Sinh hoạt: 900-1200 EUR/tháng</li>
<li>Bảo hiểm: 120 EUR/tháng</li>
</ul>
<h3>Điều kiện</h3>
<ul>
<li>Tiếng Đức B1-B2 hoặc IELTS 6.0+</li>
<li>Tài chính: 11.208 EUR/năm</li>
</ul>''',
            'category_slug': 'du-hoc',
            'is_featured': True,
        },
        {
            'title': 'IELTS vs Goethe: Nên thi chứng chỉ nào?',
            'slug': 'ielts-vs-goethe-nen-thi-chung-chi-nao',
            'excerpt': 'So sánh chi tiết giữa IELTS và Goethe để bạn chọn đúng chứng chỉ.',
            'content': '''<h2>So sánh IELTS và Goethe</h2>
<table>
<tr><th>Tiêu chí</th><th>IELTS</th><th>Goethe</th></tr>
<tr><td>Ngôn ngữ</td><td>Tiếng Anh</td><td>Tiếng Đức</td></tr>
<tr><td>Độ phổ biến</td><td>Toàn cầu</td><td>Châu Âu, Đức</td></tr>
<tr><td>Chi phí</td><td>4-5 triệu VND</td><td>2-4 triệu VND</td></tr>
<tr><td>Thời hạn</td><td>2 năm</td><td>Vô thời hạn</td></tr>
</table>''',
            'category_slug': 'thi-cu',
        },
    ]
    
    for article_data in news_articles_data:
        category_slug = article_data.pop('category_slug')
        is_featured = article_data.pop('is_featured', False)
        category = NewsCategory.objects.get(slug=category_slug)
        
        article, created = Article.objects.get_or_create(
            slug=article_data['slug'],
            defaults={
                **article_data,
                'category': category,
                'author': admin_user,
                'is_published': True,
                'is_featured': is_featured,
                'published_at': timezone.now(),
                'view_count': random.randint(100, 2000),
            }
        )
        if created:
            print(f"  ✓ Created article: {article.title[:45]}...")
            
except Exception as e:
    print(f"  ⚠ Error creating news: {e}")

# ============================================
# 5. Create Knowledge Articles
# ============================================
print("\n📖 Creating knowledge articles...")

try:
    # Model names: Category and KnowledgeArticle (not KnowledgeCategory)
    from knowledge.models import KnowledgeArticle, Category as KnowledgeCategory
    
    # Categories
    know_cats_data = [
        {'name': 'Ngữ pháp', 'slug': 'ngu-phap', 'description': 'Kiến thức ngữ pháp'},
        {'name': 'Từ vựng', 'slug': 'tu-vung', 'description': 'Kiến thức từ vựng'},
        {'name': 'Phát âm', 'slug': 'phat-am', 'description': 'Kiến thức phát âm'},
    ]
    
    for cat_data in know_cats_data:
        cat, created = KnowledgeCategory.objects.get_or_create(
            slug=cat_data['slug'],
            defaults=cat_data
        )
        if created:
            print(f"  ✓ Created knowledge category: {cat.name}")
    
    # Articles - Using correct field names: excerpt (not summary), is_published (not status)
    knowledge_articles_data = [
        {
            'title': 'Tổng quan về hệ thống giống trong tiếng Đức',
            'slug': 'he-thong-giong-tieng-duc',
            'excerpt': 'Hiểu về Der, Die, Das trong tiếng Đức',
            'content': '''<h2>Giống trong tiếng Đức (Artikel)</h2>
<p>Tiếng Đức có 3 giống: Nam (Der), Nữ (Die), Trung (Das).</p>
<h3>Quy tắc nhận biết</h3>
<ul>
<li><strong>Nam (Der)</strong>: Ngày trong tuần, tháng, mùa</li>
<li><strong>Nữ (Die)</strong>: Từ kết thúc bằng -ung, -heit, -keit</li>
<li><strong>Trung (Das)</strong>: Từ kết thúc bằng -chen, -lein</li>
</ul>''',
            'category_slug': 'ngu-phap',
            'language': 'de',
            'level': 'A1',
        },
        {
            'title': 'Cách chia động từ tiếng Đức ở thì hiện tại',
            'slug': 'chia-dong-tu-tieng-duc-hien-tai',
            'excerpt': 'Hướng dẫn chia động từ cơ bản trong tiếng Đức',
            'content': '''<h2>Chia động từ tiếng Đức - Präsens</h2>
<p>Động từ tiếng Đức chia theo ngôi và số.</p>
<h3>Ví dụ với động từ "machen" (làm)</h3>
<ul>
<li>ich mache (tôi làm)</li>
<li>du machst (bạn làm)</li>
<li>er/sie/es macht (anh ấy/cô ấy/nó làm)</li>
<li>wir machen (chúng tôi làm)</li>
<li>ihr macht (các bạn làm)</li>
<li>sie/Sie machen (họ/Quý vị làm)</li>
</ul>''',
            'category_slug': 'ngu-phap',
            'language': 'de',
            'level': 'A1',
        },
        {
            'title': '500 từ vựng tiếng Đức A1 thông dụng nhất',
            'slug': '500-tu-vung-tieng-duc-a1',
            'excerpt': 'Danh sách 500 từ vựng cần thiết cho trình độ A1',
            'content': '''<h2>500 từ vựng tiếng Đức A1</h2>
<h3>Chào hỏi</h3>
<ul>
<li>Hallo - Xin chào</li>
<li>Guten Morgen - Chào buổi sáng</li>
<li>Guten Tag - Chào buổi trưa</li>
<li>Auf Wiedersehen - Tạm biệt</li>
</ul>
<h3>Số đếm</h3>
<ul>
<li>eins - một</li>
<li>zwei - hai</li>
<li>drei - ba</li>
</ul>''',
            'category_slug': 'tu-vung',
            'language': 'de',
            'level': 'A1',
        },
        {
            'title': 'English Tenses - Present Simple vs Present Continuous',
            'slug': 'english-present-simple-continuous',
            'excerpt': 'Understanding the difference between Present Simple and Continuous',
            'content': '''<h2>Present Simple vs Present Continuous</h2>
<h3>Present Simple</h3>
<p>Used for habits, facts, and general truths.</p>
<ul>
<li>I work every day.</li>
<li>She lives in Hanoi.</li>
</ul>
<h3>Present Continuous</h3>
<p>Used for actions happening now or temporary situations.</p>
<ul>
<li>I am working right now.</li>
<li>She is living in Hanoi (temporarily).</li>
</ul>''',
            'category_slug': 'ngu-phap',
            'language': 'en',
            'level': 'A2',
        },
        {
            'title': 'Phát âm tiếng Đức: Các nguyên âm đặc biệt ä, ö, ü',
            'slug': 'phat-am-nguyen-am-dac-biet-tieng-duc',
            'excerpt': 'Hướng dẫn phát âm các nguyên âm Umlaut trong tiếng Đức',
            'content': '''<h2>Nguyên âm Umlaut trong tiếng Đức</h2>
<h3>ä (a-Umlaut)</h3>
<p>Phát âm gần giống "e" trong tiếng Việt. Ví dụ: Mädchen (cô gái)</p>
<h3>ö (o-Umlaut)</h3>
<p>Phát âm tròn môi như "ơ". Ví dụ: schön (đẹp)</p>
<h3>ü (u-Umlaut)</h3>
<p>Phát âm tròn môi như "uy". Ví dụ: für (cho)</p>''',
            'category_slug': 'phat-am',
            'language': 'de',
            'level': 'A1',
        },
        {
            'title': 'Ngữ pháp B1: Konjunktiv II và cách sử dụng',
            'slug': 'ngu-phap-b1-konjunktiv-ii',
            'excerpt': 'Học về thức giả định Konjunktiv II trong tiếng Đức',
            'content': '''<h2>Konjunktiv II - Thức giả định</h2>
<p>Konjunktiv II được dùng để diễn đạt điều không có thật, lịch sự, hoặc ước muốn.</p>
<h3>Cách tạo</h3>
<p>Từ thể Präteritum + đuôi chia + Umlaut (nếu có)</p>
<h3>Ví dụ với "haben"</h3>
<ul>
<li>ich hätte (tôi sẽ có)</li>
<li>du hättest</li>
<li>er/sie/es hätte</li>
</ul>
<h3>Sử dụng</h3>
<ul>
<li>Lịch sự: Könnten Sie mir helfen? (Ông/Bà có thể giúp tôi được không?)</li>
<li>Ước muốn: Ich hätte gern einen Kaffee. (Tôi muốn một cốc cà phê)</li>
</ul>''',
            'category_slug': 'ngu-phap',
            'language': 'de',
            'level': 'B1',
        },
    ]
    
    for article_data in knowledge_articles_data:
        category_slug = article_data.pop('category_slug')
        category = KnowledgeCategory.objects.get(slug=category_slug)
        
        article, created = KnowledgeArticle.objects.get_or_create(
            slug=article_data['slug'],
            defaults={
                **article_data,
                'category': category,
                'author': admin_user,
                'is_published': True,
                'view_count': random.randint(50, 1000),
            }
        )
        if created:
            print(f"  ✓ Created knowledge: {article.title[:45]}...")
            
except Exception as e:
    print(f"  ⚠ Error creating knowledge: {e}")

# ============================================
# Summary
# ============================================
print("\n" + "=" * 50)
print("✅ Sample data creation completed!")
print("=" * 50)

# Stats
try:
    from resources.models import Resource
    from core.models import Video
    from news.models import Article
    from knowledge.models import KnowledgeArticle
    
    print(f"\n📊 Statistics:")
    print(f"   Users: {User.objects.count()}")
    print(f"   Resources: {Resource.objects.count()}")
    print(f"   Videos: {Video.objects.count()}")
    print(f"   News Articles: {Article.objects.count()}")
    print(f"   Knowledge Articles: {KnowledgeArticle.objects.count()}")
except Exception as e:
    print(f"   Error getting stats: {e}")

print(f"\n🔑 Login credentials:")
print(f"   Admin: admin / admin123")
print(f"   Users: nguyenvan, tranlinh, lehoa, phamminh, vuthao / password123")
