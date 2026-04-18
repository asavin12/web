#!/usr/bin/env python
"""Tạo dữ liệu mẫu chuẩn SEO cho local dev — gọn nhẹ, 3 bài news + 3 bài knowledge."""
import os, sys, django, secrets, string
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'unstressvn_settings.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.contrib.auth.models import User
from django.utils import timezone
from news.models import Article, Category as NewsCategory
from knowledge.models import KnowledgeArticle, Category as KnowledgeCategory

print("=" * 50)
print("  TẠO DỮ LIỆU MẪU CHUẨN SEO")
print("=" * 50)

# User
admin, _ = User.objects.get_or_create(username='admin', defaults={
    'email': 'admin@unstressvn.com', 'is_staff': True, 'is_superuser': True
})
if not admin.has_usable_password():
    password = os.environ.get('ADMIN_INITIAL_PASSWORD', '')
    if not password:
        alphabet = string.ascii_letters + string.digits + '!@#$%^&*'
        password = ''.join(secrets.choice(alphabet) for _ in range(20))
        print(f"  ⚠️  Generated admin password: {password}  (save this!)")
    admin.set_password(password)
    admin.save()

# ═══════════════════════════════════════
# NEWS CATEGORIES
# ═══════════════════════════════════════
NEWS_CATS = [
    ('Du học Đức', 'du-hoc-duc'),
    ('Đời sống Đức', 'doi-song-duc'),
    ('Kinh nghiệm', 'kinh-nghiem'),
    ('Học tiếng Đức', 'hoc-tieng-duc'),
]
news_cats = {}
for name, slug in NEWS_CATS:
    cat, _ = NewsCategory.objects.get_or_create(slug=slug, defaults={'name': name})
    if cat.name != name:
        cat.name = name
        cat.save()
    news_cats[slug] = cat
    print(f"  ✓ News category: {name}")

# ═══════════════════════════════════════
# 3 BÀI NEWS MẪU CHUẨN SEO
# ═══════════════════════════════════════
NEWS_ARTICLES = [
    {
        'title': 'Học bổng DAAD 2026: Hướng dẫn đăng ký chi tiết từ A-Z',
        'slug': 'hoc-bong-daad-2026-huong-dan-dang-ky',
        'category': 'du-hoc-duc',
        'tags': 'học bổng DAAD, du học Đức miễn phí, scholarship Germany 2026',
        'excerpt': 'Hướng dẫn chi tiết cách đăng ký học bổng DAAD 2026 cho sinh viên Việt Nam, từ điều kiện đến hồ sơ.',
        'meta_title': 'Học bổng DAAD 2026 — Hướng dẫn đăng ký | UnstressVN',
        'meta_description': 'Tìm hiểu chi tiết về học bổng DAAD 2026 cho sinh viên Việt Nam. Điều kiện, hạn nộp và cách đăng ký thành công. Đọc ngay!',
        'meta_keywords': 'học bổng DAAD 2026, du học Đức miễn phí, điều kiện DAAD, cách đăng ký DAAD',
        'is_featured': True,
        'content': """<p><strong>Học bổng DAAD 2026</strong> là cơ hội tuyệt vời cho sinh viên Việt Nam muốn du học Đức miễn phí. DAAD vừa chính thức công bố chương trình học bổng dành cho sinh viên quốc tế năm 2026.</p>

<nav>
  <h2>Nội dung bài viết</h2>
  <ul>
    <li><a href="#chuong-trinh">1. Các chương trình học bổng chính</a></li>
    <li><a href="#dieu-kien">2. Điều kiện đăng ký</a></li>
    <li><a href="#ho-so">3. Chuẩn bị hồ sơ</a></li>
    <li><a href="#ket-luan">Kết luận</a></li>
  </ul>
</nav>

<hr>

<h2 id="chuong-trinh">1. Các chương trình học bổng DAAD chính</h2>

<p>DAAD cung cấp nhiều loại học bổng phù hợp với từng đối tượng sinh viên. Mỗi chương trình có yêu cầu và quyền lợi riêng biệt.</p>

<ul>
  <li><strong>Research Grants:</strong> Dành cho nghiên cứu sinh muốn thực hiện đề tài tại Đức</li>
  <li><strong>Study Scholarships:</strong> Hỗ trợ toàn phần cho chương trình Thạc sĩ tại Đức</li>
  <li><strong>PhD Scholarships:</strong> Tài trợ cho nghiên cứu sinh làm luận án Tiến sĩ</li>
</ul>

<blockquote>
  <p><strong>💡 Mẹo:</strong> Nên nghiên cứu kỹ từng loại học bổng và chọn chương trình phù hợp nhất với profile của bạn.</p>
</blockquote>

<h2 id="dieu-kien">2. Điều kiện đăng ký học bổng DAAD</h2>

<p>Để đăng ký học bổng DAAD 2026, ứng viên cần đáp ứng các yêu cầu cơ bản. Mỗi chương trình có thêm yêu cầu riêng.</p>

<table>
  <thead>
    <tr><th>Chương trình</th><th>Ngôn ngữ</th><th>Hạn nộp</th></tr>
  </thead>
  <tbody>
    <tr><td>Research Grants</td><td>Tiếng Đức B2 hoặc IELTS 6.5</td><td>15/10/2026</td></tr>
    <tr><td>Study Scholarships</td><td>Tiếng Đức B1 hoặc IELTS 6.0</td><td>15/11/2026</td></tr>
    <tr><td>PhD Scholarships</td><td>IELTS 6.5</td><td>01/10/2026</td></tr>
  </tbody>
</table>

<h2 id="ho-so">3. Chuẩn bị hồ sơ đăng ký</h2>

<p>Hồ sơ đăng ký DAAD cần được chuẩn bị kỹ lưỡng. Tất cả tài liệu phải được dịch sang tiếng Đức hoặc tiếng Anh.</p>

<ol>
  <li><strong>Bước 1:</strong> Tạo tài khoản trên DAAD Portal tại <a href="https://www.daad.de">daad.de</a></li>
  <li><strong>Bước 2:</strong> Upload đầy đủ bằng cấp, chứng chỉ ngôn ngữ</li>
  <li><strong>Bước 3:</strong> Viết kế hoạch nghiên cứu chi tiết (Research Proposal)</li>
  <li><strong>Bước 4:</strong> Xin 2 thư giới thiệu từ giáo sư</li>
</ol>

<blockquote>
  <p><strong>⚠️ Lưu ý:</strong> Hồ sơ nộp muộn sẽ không được xét. Nên nộp trước hạn ít nhất 2 tuần.</p>
</blockquote>

<h2 id="ket-luan">Kết luận</h2>

<p>Học bổng DAAD 2026 mở ra cơ hội du học Đức cho sinh viên Việt Nam. Với sự chuẩn bị kỹ, bạn hoàn toàn có thể chinh phục học bổng này.</p>

<blockquote>
  <p><strong>📌 Bạn thấy hữu ích?</strong> Chia sẻ cho bạn bè hoặc tham khảo thêm tại <a href="/kien-thuc">Kiến thức</a>.</p>
</blockquote>""",
    },
    {
        'title': 'Chi phí sinh hoạt tại Đức 2026: Bao nhiêu là đủ?',
        'slug': 'chi-phi-sinh-hoat-tai-duc-2026',
        'category': 'doi-song-duc',
        'tags': 'chi phí Đức, sinh hoạt Đức 2026, cuộc sống du học sinh',
        'excerpt': 'Tổng hợp chi phí sinh hoạt tại Đức năm 2026 — tiền thuê nhà, ăn uống, bảo hiểm và chi phí khác.',
        'meta_title': 'Chi phí sinh hoạt tại Đức 2026 | UnstressVN',
        'meta_description': 'Tổng hợp chi phí sinh hoạt tại Đức 2026 cho du học sinh. Thuê nhà, ăn uống, bảo hiểm từ 850-1200€/tháng. Xem chi tiết!',
        'meta_keywords': 'chi phí sinh hoạt Đức, cuộc sống Đức 2026, tiền thuê nhà Đức, du học sinh Đức',
        'is_featured': False,
        'content': """<p><strong>Chi phí sinh hoạt tại Đức 2026</strong> là câu hỏi hàng đầu của mọi du học sinh Việt Nam. Mức chi phí trung bình dao động từ 850€ đến 1200€/tháng tùy thành phố.</p>

<nav>
  <h2>Nội dung bài viết</h2>
  <ul>
    <li><a href="#tong-quan">1. Tổng quan chi phí</a></li>
    <li><a href="#thue-nha">2. Chi phí thuê nhà</a></li>
    <li><a href="#meo-tiet-kiem">3. Mẹo tiết kiệm</a></li>
    <li><a href="#ket-luan">Kết luận</a></li>
  </ul>
</nav>

<hr>

<h2 id="tong-quan">1. Tổng quan chi phí sinh hoạt tại Đức</h2>

<p>Theo quy định mới, du học sinh cần chứng minh tài chính tối thiểu 11.208€/năm cho tài khoản phong tỏa (Sperrkonto). Tương đương khoảng 934€/tháng.</p>

<table>
  <thead>
    <tr><th>Hạng mục</th><th>Chi phí/tháng</th><th>Ghi chú</th></tr>
  </thead>
  <tbody>
    <tr><td><strong>Thuê nhà</strong></td><td>350-700€</td><td>Tùy thành phố</td></tr>
    <tr><td><strong>Ăn uống</strong></td><td>200-300€</td><td>Nấu ở nhà tiết kiệm hơn</td></tr>
    <tr><td><strong>Bảo hiểm y tế</strong></td><td>110-120€</td><td>Bắt buộc</td></tr>
    <tr><td><strong>Giao thông</strong></td><td>49€</td><td>Deutschlandticket</td></tr>
    <tr><td><strong>Khác</strong></td><td>100-200€</td><td>Giải trí, học liệu</td></tr>
  </tbody>
</table>

<h2 id="thue-nha">2. Chi phí thuê nhà theo thành phố</h2>

<p>Thuê nhà chiếm phần lớn chi phí sinh hoạt. Mức giá khác biệt rõ rệt giữa các thành phố lớn và thành phố nhỏ.</p>

<ul>
  <li><strong>München:</strong> 600-900€ — đắt nhất nước Đức</li>
  <li><strong>Berlin:</strong> 450-700€ — đang tăng nhanh</li>
  <li><strong>Leipzig, Dresden:</strong> 300-450€ — giá phải chăng</li>
</ul>

<blockquote>
  <p><strong>💡 Mẹo:</strong> Đăng ký WG (Wohngemeinschaft — ở ghép) để tiết kiệm 30-50% tiền thuê nhà.</p>
</blockquote>

<h2 id="meo-tiet-kiem">3. Mẹo tiết kiệm chi phí</h2>

<p>Du học sinh Việt tại Đức có nhiều cách tiết kiệm hiệu quả. Dưới đây là những mẹo đã được kiểm chứng.</p>

<ol>
  <li><strong>Nấu ăn ở nhà:</strong> Tiết kiệm 100-150€/tháng so với ăn ngoài</li>
  <li><strong>Mua Deutschlandticket:</strong> 49€/tháng cho tất cả phương tiện công cộng</li>
  <li><strong>Dùng thẻ sinh viên:</strong> Giảm giá bảo tàng, rạp phim, phần mềm</li>
</ol>

<h2 id="ket-luan">Kết luận</h2>

<p>Chi phí sinh hoạt tại Đức 2026 hoàn toàn có thể kiểm soát với kế hoạch tài chính hợp lý. Hãy chuẩn bị ngân sách 900-1200€/tháng để có cuộc sống thoải mái.</p>

<blockquote>
  <p><strong>📌 Hữu ích?</strong> Xem thêm <a href="/tin-tuc/du-hoc-duc">Du học Đức</a> để cập nhật thông tin mới nhất.</p>
</blockquote>""",
    },
    {
        'title': '5 sai lầm phổ biến khi xin visa du học Đức và cách tránh',
        'slug': '5-sai-lam-xin-visa-du-hoc-duc',
        'category': 'kinh-nghiem',
        'tags': 'visa Đức, xin visa du học, lỗi visa, kinh nghiệm visa',
        'excerpt': 'Tổng hợp 5 sai lầm phổ biến nhất khi xin visa du học Đức và cách phòng tránh hiệu quả.',
        'meta_title': '5 sai lầm khi xin visa du học Đức | UnstressVN',
        'meta_description': 'Tránh 5 sai lầm phổ biến khi xin visa du học Đức. Kinh nghiệm thực tế từ du học sinh Việt Nam. Đọc ngay!',
        'meta_keywords': 'visa du học Đức, sai lầm xin visa, kinh nghiệm visa Đức, hồ sơ visa',
        'is_featured': False,
        'content': """<p><strong>Xin visa du học Đức</strong> là bước quan trọng nhất trong hành trình du học. Nhiều bạn bị từ chối visa do những sai lầm hoàn toàn có thể tránh được. Bài viết này chia sẻ 5 sai lầm phổ biến nhất.</p>

<nav>
  <h2>Nội dung bài viết</h2>
  <ul>
    <li><a href="#sai-lam-1">1. Thiếu chứng minh tài chính</a></li>
    <li><a href="#sai-lam-2">2. Không chuẩn bị phỏng vấn</a></li>
    <li><a href="#sai-lam-3">3. Hồ sơ thiếu hoặc sai format</a></li>
    <li><a href="#ket-luan">Kết luận</a></li>
  </ul>
</nav>

<hr>

<h2 id="sai-lam-1">1. Thiếu chứng minh tài chính đầy đủ</h2>

<p>Đây là lý do phổ biến nhất dẫn đến bị từ chối visa du học Đức. Đại sứ quán yêu cầu bằng chứng tài chính rõ ràng và đáng tin cậy.</p>

<ul>
  <li><strong>Sperrkonto chưa đủ số dư:</strong> Tối thiểu 11.208€ cho năm 2026</li>
  <li><strong>Không có bảo lãnh tài chính:</strong> Cần Verpflichtungserklärung nếu có người bảo lãnh</li>
  <li><strong>Sổ tiết kiệm không hợp lệ:</strong> Phải từ ngân hàng uy tín, có xác nhận</li>
</ul>

<blockquote>
  <p><strong>💡 Mẹo:</strong> Mở Sperrkonto tại Expatrio hoặc Fintiba — được đại sứ quán Đức tại Việt Nam chấp nhận.</p>
</blockquote>

<h2 id="sai-lam-2">2. Không chuẩn bị phỏng vấn kỹ lưỡng</h2>

<p>Buổi phỏng vấn visa thường chỉ kéo dài 5-10 phút, nhưng quyết định hoàn toàn số phận hồ sơ của bạn.</p>

<ol>
  <li><strong>Trả lời rõ ràng:</strong> Giải thích tại sao chọn Đức, chọn ngành, kế hoạch sau tốt nghiệp</li>
  <li><strong>Chuẩn bị tiếng Đức:</strong> Một số câu hỏi sẽ bằng tiếng Đức nếu bạn học chương trình tiếng Đức</li>
  <li><strong>Mang đầy đủ giấy tờ gốc:</strong> Bằng cấp, chứng chỉ, hợp đồng thuê nhà</li>
</ol>

<h2 id="sai-lam-3">3. Hồ sơ thiếu hoặc sai format</h2>

<p>Hồ sơ visa không được chỉnh sửa hay bổ sung sau khi nộp. Một lỗi nhỏ có thể dẫn đến bị từ chối.</p>

<table>
  <thead>
    <tr><th>Lỗi thường gặp</th><th>Cách khắc phục</th></tr>
  </thead>
  <tbody>
    <tr><td>Ảnh không đúng chuẩn</td><td>Ảnh biometric 35x45mm, nền trắng</td></tr>
    <tr><td>Thiếu bản dịch công chứng</td><td>Dịch tất cả sang tiếng Đức hoặc Anh</td></tr>
    <tr><td>Form đơn điền thiếu</td><td>Sử dụng VIDEX online, kiểm tra kỹ</td></tr>
  </tbody>
</table>

<h2 id="ket-luan">Kết luận</h2>

<p>Xin visa du học Đức không khó nếu bạn chuẩn bị kỹ lưỡng và tránh những sai lầm phổ biến trên. Hãy bắt đầu chuẩn bị hồ sơ sớm nhất có thể.</p>

<blockquote>
  <p><strong>📌 Cần thêm thông tin?</strong> Tham khảo <a href="/tin-tuc/kinh-nghiem">Kinh nghiệm</a> từ các du học sinh khác.</p>
</blockquote>""",
    },
]

print("\n📰 Tạo News articles...")
for data in NEWS_ARTICLES:
    cat = news_cats[data.pop('category')]
    art, created = Article.objects.update_or_create(
        slug=data['slug'],
        defaults={**data, 'category': cat, 'author': admin, 'is_published': True,
                  'published_at': timezone.now(), 'source': 'manual'}
    )
    status = "✓ Created" if created else "↻ Updated"
    print(f"  {status}: {art.title[:50]}")

# ═══════════════════════════════════════
# KNOWLEDGE CATEGORIES
# ═══════════════════════════════════════
KNOW_CATS = [
    ('Ngữ pháp', 'ngu-phap'),
    ('Từ vựng', 'tu-vung'),
    ('Luyện thi', 'luyen-thi'),
]
know_cats = {}
for name, slug in KNOW_CATS:
    cat, _ = KnowledgeCategory.objects.get_or_create(slug=slug, defaults={'name': name})
    know_cats[slug] = cat
    print(f"  ✓ Knowledge category: {name}")

# ═══════════════════════════════════════
# 3 BÀI KNOWLEDGE MẪU CHUẨN SEO
# ═══════════════════════════════════════
KNOWLEDGE_ARTICLES = [
    {
        'title': 'Ngữ pháp tiếng Đức A2: Nebensätze — Mệnh đề phụ đầy đủ',
        'slug': 'ngu-phap-duc-a2-nebensatze',
        'category': 'ngu-phap',
        'language': 'de',
        'level': 'A2',
        'tags': 'Nebensätze, mệnh đề phụ tiếng Đức, ngữ pháp A2, weil dass ob',
        'excerpt': 'Hướng dẫn chi tiết về Nebensätze (mệnh đề phụ) trong tiếng Đức A2 — weil, dass, ob, wenn.',
        'meta_title': 'Nebensätze tiếng Đức A2 — Mệnh đề phụ | UnstressVN',
        'meta_description': 'Học Nebensätze tiếng Đức A2: weil, dass, ob, wenn. Cấu trúc, ví dụ và bài tập. Nắm vững mệnh đề phụ ngay!',
        'meta_keywords': 'Nebensätze, mệnh đề phụ tiếng Đức, ngữ pháp A2, weil dass ob wenn',
        'content': """<p><strong>Nebensätze (mệnh đề phụ)</strong> là một trong những điểm ngữ pháp quan trọng nhất ở trình độ A2 tiếng Đức. Hiểu rõ cấu trúc này giúp bạn nói và viết tiếng Đức tự nhiên hơn.</p>

<nav>
  <h2>Nội dung bài viết</h2>
  <ul>
    <li><a href="#cau-truc">1. Cấu trúc Nebensätze</a></li>
    <li><a href="#lien-tu">2. Các liên từ phổ biến</a></li>
    <li><a href="#vi-du">3. Ví dụ thực hành</a></li>
    <li><a href="#ket-luan">Kết luận</a></li>
  </ul>
</nav>

<hr>

<h2 id="cau-truc">1. Cấu trúc cơ bản của Nebensätze</h2>

<p>Trong mệnh đề phụ tiếng Đức, <strong>động từ chia luôn đứng ở cuối câu</strong>. Đây là quy tắc bắt buộc và khác hoàn toàn với tiếng Việt.</p>

<ul>
  <li><strong>Hauptsatz (mệnh đề chính):</strong> Ich lerne Deutsch. (Tôi học tiếng Đức)</li>
  <li><strong>Nebensatz (mệnh đề phụ):</strong> ..., <em>weil</em> ich in Deutschland <em>studieren will</em>.</li>
  <li><strong>Quy tắc:</strong> Liên từ + Chủ ngữ + ... + Động từ chia (cuối câu)</li>
</ul>

<blockquote>
  <p><strong>💡 Mẹo:</strong> Nhớ công thức: Nebensatz = Konjunktion + S + O + Verb (cuối). Luyện tập hàng ngày sẽ thành thói quen!</p>
</blockquote>

<h2 id="lien-tu">2. Các liên từ phổ biến ở A2</h2>

<table>
  <thead>
    <tr><th>Liên từ</th><th>Nghĩa</th><th>Ví dụ</th></tr>
  </thead>
  <tbody>
    <tr><td><strong>weil</strong></td><td>vì</td><td>Ich bleibe zu Hause, weil ich krank <em>bin</em>.</td></tr>
    <tr><td><strong>dass</strong></td><td>rằng</td><td>Ich weiß, dass du Deutsch <em>lernst</em>.</td></tr>
    <tr><td><strong>ob</strong></td><td>liệu/có...không</td><td>Ich frage, ob du morgen <em>kommst</em>.</td></tr>
    <tr><td><strong>wenn</strong></td><td>nếu/khi</td><td>Wenn ich Zeit <em>habe</em>, lese ich.</td></tr>
  </tbody>
</table>

<h2 id="vi-du">3. Ví dụ thực hành</h2>

<p>Hãy thử chuyển các câu đơn sau thành câu có Nebensatz. Đây là cách luyện tập hiệu quả nhất.</p>

<ol>
  <li><strong>weil:</strong> Ich lerne Deutsch + Ich möchte in Deutschland arbeiten → Ich lerne Deutsch, <em>weil ich in Deutschland arbeiten möchte</em>.</li>
  <li><strong>dass:</strong> Ich glaube + Du bist intelligent → Ich glaube, <em>dass du intelligent bist</em>.</li>
  <li><strong>wenn:</strong> Das Wetter ist gut + Ich gehe spazieren → <em>Wenn das Wetter gut ist</em>, gehe ich spazieren.</li>
</ol>

<h2 id="ket-luan">Kết luận</h2>

<p>Nebensätze là nền tảng quan trọng để đạt trình độ A2 tiếng Đức. Hãy luyện tập với weil, dass, ob, wenn mỗi ngày để thành thạo.</p>

<blockquote>
  <p><strong>📌 Học thêm?</strong> Xem <a href="/kien-thuc">Kiến thức</a> để trau dồi ngữ pháp tiếng Đức.</p>
</blockquote>""",
    },
    {
        'title': 'Top 100 từ vựng tiếng Đức B1 theo chủ đề — có ví dụ',
        'slug': 'top-100-tu-vung-duc-b1-theo-chu-de',
        'category': 'tu-vung',
        'language': 'de',
        'level': 'B1',
        'tags': 'từ vựng B1, Wortschatz B1, tiếng Đức B1, học từ mới',
        'excerpt': 'Tổng hợp 100 từ vựng tiếng Đức B1 thiết yếu, phân chia theo chủ đề kèm ví dụ câu thực tế.',
        'meta_title': 'Top 100 từ vựng tiếng Đức B1 theo chủ đề | UnstressVN',
        'meta_description': '100 từ vựng tiếng Đức B1 quan trọng nhất, phân chia theo chủ đề. Có ví dụ câu và mẹo ghi nhớ. Học ngay!',
        'meta_keywords': 'từ vựng tiếng Đức B1, Wortschatz B1, học từ vựng Đức, chủ đề B1',
        'content': """<p><strong>Từ vựng tiếng Đức B1</strong> đòi hỏi khoảng 2.400 từ để giao tiếp tự tin. Bài viết này tổng hợp 100 từ quan trọng nhất theo chủ đề, giúp bạn học có hệ thống.</p>

<nav>
  <h2>Nội dung bài viết</h2>
  <ul>
    <li><a href="#arbeit">1. Chủ đề Arbeit (Công việc)</a></li>
    <li><a href="#gesundheit">2. Chủ đề Gesundheit (Sức khỏe)</a></li>
    <li><a href="#meo-hoc">3. Mẹo ghi nhớ từ vựng</a></li>
    <li><a href="#ket-luan">Kết luận</a></li>
  </ul>
</nav>

<hr>

<h2 id="arbeit">1. Chủ đề Arbeit — Công việc (25 từ)</h2>

<p>Chủ đề công việc là trọng tâm của đề thi B1. Bạn cần nắm vững từ vựng về tìm việc, phỏng vấn, và môi trường làm việc.</p>

<table>
  <thead>
    <tr><th>Từ vựng</th><th>Nghĩa</th><th>Ví dụ</th></tr>
  </thead>
  <tbody>
    <tr><td><strong>die Bewerbung</strong></td><td>Đơn xin việc</td><td>Ich schreibe eine Bewerbung.</td></tr>
    <tr><td><strong>das Vorstellungsgespräch</strong></td><td>Cuộc phỏng vấn</td><td>Morgen habe ich ein Vorstellungsgespräch.</td></tr>
    <tr><td><strong>der Lebenslauf</strong></td><td>CV/Sơ yếu lý lịch</td><td>Mein Lebenslauf ist aktuell.</td></tr>
    <tr><td><strong>die Erfahrung</strong></td><td>Kinh nghiệm</td><td>Ich habe viel Erfahrung.</td></tr>
    <tr><td><strong>kündigen</strong></td><td>Nghỉ việc</td><td>Er hat gestern gekündigt.</td></tr>
  </tbody>
</table>

<h2 id="gesundheit">2. Chủ đề Gesundheit — Sức khỏe (25 từ)</h2>

<p>Sức khỏe là chủ đề thường xuyên trong giao tiếp hàng ngày và đề thi B1. Dưới đây là từ vựng thiết yếu.</p>

<ul>
  <li><strong>der Arzt / die Ärztin:</strong> Bác sĩ — <em>Ich gehe zum Arzt.</em></li>
  <li><strong>das Rezept:</strong> Đơn thuốc — <em>Der Arzt schreibt ein Rezept.</em></li>
  <li><strong>die Apotheke:</strong> Nhà thuốc — <em>Die Apotheke ist um die Ecke.</em></li>
  <li><strong>die Versicherung:</strong> Bảo hiểm — <em>Ich brauche eine Krankenversicherung.</em></li>
</ul>

<blockquote>
  <p><strong>💡 Mẹo:</strong> Học từ vựng kèm Artikel (der/die/das) ngay từ đầu. Tạo flashcard với ví dụ câu để nhớ lâu hơn.</p>
</blockquote>

<h2 id="meo-hoc">3. Mẹo ghi nhớ từ vựng B1 hiệu quả</h2>

<ol>
  <li><strong>Spaced Repetition:</strong> Dùng Anki hoặc Quizlet, ôn lại theo chu kỳ</li>
  <li><strong>Contextual Learning:</strong> Học từ trong câu, không học từ đơn lẻ</li>
  <li><strong>Mind Map:</strong> Nhóm từ theo chủ đề, vẽ sơ đồ tư duy</li>
</ol>

<h2 id="ket-luan">Kết luận</h2>

<p>Nắm vững 100 từ vựng B1 theo chủ đề giúp bạn tự tin hơn trong giao tiếp và thi cử. Hãy luyện tập đều đặn mỗi ngày.</p>

<blockquote>
  <p><strong>📌 Tải thêm?</strong> Xem <a href="/tai-lieu">Tài liệu</a> để tải flashcard từ vựng B1 miễn phí.</p>
</blockquote>""",
    },
    {
        'title': 'Cách ôn thi Goethe B1 hiệu quả trong 3 tháng',
        'slug': 'on-thi-goethe-b1-3-thang',
        'category': 'luyen-thi',
        'language': 'de',
        'level': 'B1',
        'tags': 'Goethe B1, ôn thi B1, lịch ôn thi, luyện thi tiếng Đức',
        'excerpt': 'Kế hoạch ôn thi Goethe B1 trong 3 tháng — lịch học chi tiết theo tuần kèm tài liệu miễn phí.',
        'meta_title': 'Ôn thi Goethe B1 trong 3 tháng — Kế hoạch chi tiết | UnstressVN',
        'meta_description': 'Kế hoạch ôn thi Goethe B1 trong 3 tháng. Lịch học theo tuần, tài liệu miễn phí và mẹo thi hiệu quả. Bắt đầu ngay!',
        'meta_keywords': 'ôn thi Goethe B1, kế hoạch thi B1, luyện thi tiếng Đức, Goethe Zertifikat B1',
        'content': """<p><strong>Ôn thi Goethe B1</strong> trong 3 tháng là hoàn toàn khả thi nếu bạn có kế hoạch rõ ràng. Bài viết này chia sẻ lộ trình chi tiết từng tuần giúp bạn đạt kết quả tốt nhất.</p>

<nav>
  <h2>Nội dung bài viết</h2>
  <ul>
    <li><a href="#cau-truc-de">1. Cấu trúc đề thi Goethe B1</a></li>
    <li><a href="#lo-trinh">2. Lộ trình 3 tháng</a></li>
    <li><a href="#tai-lieu">3. Tài liệu ôn thi</a></li>
    <li><a href="#ket-luan">Kết luận</a></li>
  </ul>
</nav>

<hr>

<h2 id="cau-truc-de">1. Cấu trúc đề thi Goethe Zertifikat B1</h2>

<p>Đề thi Goethe B1 gồm 4 phần kỹ năng, mỗi phần 100 điểm. Bạn cần đạt tối thiểu 60% mỗi phần để pass.</p>

<table>
  <thead>
    <tr><th>Kỹ năng</th><th>Thời gian</th><th>Nội dung</th></tr>
  </thead>
  <tbody>
    <tr><td><strong>Lesen (Đọc)</strong></td><td>65 phút</td><td>5 phần đọc hiểu</td></tr>
    <tr><td><strong>Hören (Nghe)</strong></td><td>40 phút</td><td>4 phần nghe hiểu</td></tr>
    <tr><td><strong>Schreiben (Viết)</strong></td><td>60 phút</td><td>3 bài viết</td></tr>
    <tr><td><strong>Sprechen (Nói)</strong></td><td>15 phút</td><td>3 phần nói với đối tác</td></tr>
  </tbody>
</table>

<h2 id="lo-trinh">2. Lộ trình ôn thi 3 tháng</h2>

<p>Lộ trình chia thành 3 giai đoạn chính, mỗi giai đoạn 4 tuần với mục tiêu cụ thể.</p>

<ul>
  <li><strong>Tháng 1 — Nền tảng:</strong> Ôn lại ngữ pháp A2-B1, mở rộng từ vựng theo chủ đề</li>
  <li><strong>Tháng 2 — Luyện đề:</strong> Làm đề thi mẫu Goethe, phân tích lỗi sai</li>
  <li><strong>Tháng 3 — Sprint cuối:</strong> Thi thử, luyện Sprechen với partner, hoàn thiện</li>
</ul>

<blockquote>
  <p><strong>💡 Mẹo:</strong> Dành 2 giờ/ngày: 1 giờ ngữ pháp+từ vựng, 30 phút nghe, 30 phút đọc. Cuối tuần luyện viết + nói.</p>
</blockquote>

<h2 id="tai-lieu">3. Tài liệu ôn thi miễn phí</h2>

<ol>
  <li><strong>Goethe.de:</strong> Đề thi mẫu chính thức (miễn phí) tại <a href="https://www.goethe.de">goethe.de</a></li>
  <li><strong>Deutsche Welle:</strong> Khóa học B1 online hoàn toàn miễn phí</li>
  <li><strong>UnstressVN:</strong> Flashcard từ vựng B1 và bài giảng ngữ pháp tại <a href="/tai-lieu">Tài liệu</a></li>
</ol>

<h2 id="ket-luan">Kết luận</h2>

<p>Ôn thi Goethe B1 trong 3 tháng đòi hỏi kỷ luật và phương pháp đúng. Hãy bắt đầu với lộ trình trên và điều chỉnh cho phù hợp.</p>

<blockquote>
  <p><strong>📌 Cần thêm tài liệu?</strong> Truy cập <a href="/tai-lieu">Tài liệu</a> hoặc <a href="/kien-thuc">Kiến thức</a> trên UnstressVN.</p>
</blockquote>""",
    },
]

print("\n📚 Tạo Knowledge articles...")
for data in KNOWLEDGE_ARTICLES:
    cat = know_cats[data.pop('category')]
    lang = data.pop('language')
    level = data.pop('level')
    art, created = KnowledgeArticle.objects.update_or_create(
        slug=data['slug'],
        defaults={**data, 'category': cat, 'author': admin, 'language': lang,
                  'level': level, 'is_published': True, 'published_at': timezone.now(),
                  'source': 'manual'}
    )
    status = "✓ Created" if created else "↻ Updated"
    print(f"  {status}: {art.title[:50]}")

print("\n" + "=" * 50)
print("  ✅ HOÀN TẤT — 3 News + 3 Knowledge (chuẩn SEO)")
print("=" * 50)
