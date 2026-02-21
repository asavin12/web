# 📋 FORM MẪU NỘI DUNG CHUẨN SEO — UnstressVN

> **BẮT BUỘC** tuân thủ nghiêm ngặt khi tạo bài viết (thủ công hoặc tự động qua n8n).
> Tất cả nội dung trên UnstressVN phải theo đúng cấu trúc HTML bên dưới.

---

## 1. CẤU TRÚC HTML BẮT BUỘC CHO `content`

Mọi bài viết gửi qua API hoặc nhập thủ công **phải** tuân thủ cấu trúc HTML sau:

```html
<!-- ═══════════════════════════════════════════════════════════════
     FORM CHUẨN SEO — UNSTRESSVN CONTENT TEMPLATE
     Sử dụng cho: News, Knowledge, Tools
     BẮT BUỘC tuân thủ khi tạo bài viết qua n8n hoặc thủ công
     ═══════════════════════════════════════════════════════════════ -->

<!-- ▸ ĐOẠN MỞ ĐẦU (Lead Paragraph) — BẮT BUỘC
     Tóm tắt nội dung chính trong 2-3 câu.
     Chứa từ khóa chính ngay câu đầu tiên.
     Drop cap sẽ tự động áp dụng cho chữ cái đầu. -->
<p>[Từ khóa chính] là... [Mô tả ngắn gọn vấn đề/chủ đề]. Trong bài viết này, bạn sẽ tìm hiểu [lợi ích 1], [lợi ích 2] và [lợi ích 3].</p>

<!-- ▸ MỤC LỤC (Table of Contents) — KHUYẾN NGHỊ cho bài > 800 từ
     Giúp Google hiểu cấu trúc bài, tăng khả năng hiển thị sitelinks. -->
<nav>
  <h2>Nội dung bài viết</h2>
  <ul>
    <li><a href="#phan-1">1. [Tiêu đề phần 1]</a></li>
    <li><a href="#phan-2">2. [Tiêu đề phần 2]</a></li>
    <li><a href="#phan-3">3. [Tiêu đề phần 3]</a></li>
    <li><a href="#ket-luan">Kết luận</a></li>
  </ul>
</nav>

<hr>

<!-- ═══════════════════════════════════════════════════════════════
     PHẦN NỘI DUNG CHÍNH (Main Content Sections)
     Mỗi phần BẮT BUỘC có: H2 + ít nhất 1 đoạn văn
     ═══════════════════════════════════════════════════════════════ -->

<!-- ▸ PHẦN 1 -->
<h2 id="phan-1">1. [Tiêu đề phần 1 — chứa từ khóa phụ]</h2>

<p>[Nội dung giải thích chi tiết. Mỗi đoạn văn 3-5 câu. Câu đầu chứa ý chính của đoạn (topic sentence). Sử dụng ngôn ngữ tự nhiên, dễ hiểu.]</p>

<p>[Đoạn bổ sung thêm thông tin, ví dụ cụ thể, hoặc dẫn chứng.]</p>

<!-- ▸ BLOCKQUOTE — Dùng cho trích dẫn, lưu ý quan trọng, tips -->
<blockquote>
  <p><strong>💡 Mẹo:</strong> [Thông tin hữu ích, lời khuyên thực tế cho người đọc.]</p>
</blockquote>

<!-- ▸ PHẦN 2 -->
<h2 id="phan-2">2. [Tiêu đề phần 2 — chứa từ khóa phụ]</h2>

<p>[Nội dung phần 2...]</p>

<!-- ▸ DANH SÁCH (Unordered List) — Tăng Featured Snippet -->
<ul>
  <li><strong>[Điểm chính 1]:</strong> [Giải thích ngắn gọn]</li>
  <li><strong>[Điểm chính 2]:</strong> [Giải thích ngắn gọn]</li>
  <li><strong>[Điểm chính 3]:</strong> [Giải thích ngắn gọn]</li>
</ul>

<!-- ▸ PHẦN 3 — Có H3 con -->
<h2 id="phan-3">3. [Tiêu đề phần 3]</h2>

<p>[Giới thiệu nội dung phần 3...]</p>

<!-- ▸ H3 — Tiêu đề phụ trong section -->
<h3>3.1. [Tiêu đề mục con]</h3>

<p>[Chi tiết mục con...]</p>

<!-- ▸ DANH SÁCH CÓ THỨ TỰ (Ordered List) — Cho hướng dẫn từng bước -->
<ol>
  <li><strong>Bước 1:</strong> [Mô tả hành động cụ thể]</li>
  <li><strong>Bước 2:</strong> [Mô tả hành động cụ thể]</li>
  <li><strong>Bước 3:</strong> [Mô tả hành động cụ thể]</li>
</ol>

<h3>3.2. [Tiêu đề mục con 2]</h3>

<p>[Chi tiết mục con 2...]</p>

<!-- ▸ BẢNG (Table) — Dùng cho so sánh, thống kê -->
<table>
  <thead>
    <tr>
      <th>[Tiêu đề cột 1]</th>
      <th>[Tiêu đề cột 2]</th>
      <th>[Tiêu đề cột 3]</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>[Dữ liệu 1]</td>
      <td>[Dữ liệu 2]</td>
      <td>[Dữ liệu 3]</td>
    </tr>
    <tr>
      <td>[Dữ liệu 4]</td>
      <td>[Dữ liệu 5]</td>
      <td>[Dữ liệu 6]</td>
    </tr>
  </tbody>
</table>

<!-- ▸ HÌNH ẢNH TRONG BÀI — Alt text BẮT BUỘC cho SEO -->
<figure>
  <img src="[URL hình ảnh]" alt="[Mô tả hình ảnh bằng từ khóa — 5-15 từ]" loading="lazy">
  <figcaption>[Chú thích hình ảnh — mô tả ngắn gọn]</figcaption>
</figure>

<!-- ▸ VIDEO NHÚNG (nếu có) -->
<figure>
  <iframe src="https://www.youtube.com/embed/[VIDEO_ID]" title="[Tiêu đề video]" allowfullscreen></iframe>
  <figcaption>[Mô tả nội dung video]</figcaption>
</figure>

<!-- ═══════════════════════════════════════════════════════════════
     KẾT LUẬN — BẮT BUỘC, tóm tắt nội dung + CTA
     ═══════════════════════════════════════════════════════════════ -->

<h2 id="ket-luan">Kết luận</h2>

<p>[Tóm tắt lại các điểm chính trong 2-3 câu. Nhắc lại từ khóa chính một cách tự nhiên.]</p>

<p>[Lời kêu gọi hành động (CTA): Khuyến khích người đọc thực hiện hành động cụ thể — đăng ký, tải tài liệu, đọc bài liên quan...]</p>

<!-- ▸ CTA BOX — Kêu gọi hành động nổi bật -->
<blockquote>
  <p><strong>📌 Bạn thấy bài viết hữu ích?</strong> Hãy chia sẻ cho bạn bè hoặc lưu lại để đọc sau. Khám phá thêm các bài viết khác tại <a href="/tin-tuc">Tin tức</a> hoặc <a href="/kien-thuc">Kiến thức</a>.</p>
</blockquote>
```

---

## 2. QUY TẮC SEO BẮT BUỘC

### 2.1. Tiêu đề bài viết (`title`)
| Quy tắc | Chi tiết |
|---------|---------|
| Độ dài | **40-65 ký tự** (tối ưu 55-60) |
| Từ khóa | Đặt từ khóa chính **ở đầu** tiêu đề |
| Năm | Thêm năm nếu nội dung cập nhật (VD: "2026") |
| Số liệu | Ưu tiên con số (VD: "Top 10...", "5 cách...") |
| Cấu trúc | `[Từ khóa chính]: [Lợi ích/Chi tiết]` |

**Ví dụ tốt:**
- ✅ `Học bổng DAAD 2026: Cơ hội du học Đức miễn phí`
- ✅ `10 mẹo luyện nghe tiếng Đức hiệu quả cho người mới`
- ❌ `Thông tin về học bổng` (quá ngắn, không có từ khóa cụ thể)

### 2.2. SEO Meta Title (`meta_title`)
| Quy tắc | Chi tiết |
|---------|---------|
| Độ dài | **50-60 ký tự** (Google cắt ở ~60) |
| Format | `[Từ khóa chính] - [Bổ sung] | UnstressVN` |
| Khác title | Nên khác title gốc để tối ưu CTR |

### 2.3. SEO Meta Description (`meta_description`)
| Quy tắc | Chi tiết |
|---------|---------|
| Độ dài | **120-155 ký tự** (tối ưu 150) |
| Từ khóa | Chứa từ khóa chính + 1 từ khóa phụ |
| CTA | Kết thúc bằng lời kêu gọi hành động |
| Quyến rũ | Phải khiến người đọc muốn click |

**Ví dụ tốt:**
> ✅ `Tìm hiểu chi tiết về học bổng DAAD 2026 cho sinh viên Việt Nam. Điều kiện, hạn nộp và cách đăng ký thành công. Đọc ngay!`

### 2.4. Excerpt / Tóm tắt (`excerpt`)
| Quy tắc | Chi tiết |
|---------|---------|
| Độ dài | **80-200 ký tự** |
| Nội dung | Tóm tắt giá trị bài viết cho người đọc |
| Hiển thị | Dùng trong danh sách bài viết + Open Graph |

### 2.5. Từ khóa (`meta_keywords`)
| Quy tắc | Chi tiết |
|---------|---------|
| Số lượng | **3-7 từ khóa**, cách nhau bằng dấu phẩy |
| Ưu tiên | Từ khóa chính đầu tiên |
| Long-tail | Ít nhất 2 từ khóa dài (long-tail) |

**Ví dụ:** `học bổng DAAD 2026, du học Đức miễn phí, điều kiện học bổng DAAD, cách đăng ký DAAD`

### 2.6. Nội dung (`content`) — Quy tắc HTML
| Quy tắc | Chi tiết |
|---------|---------|
| Độ dài tối thiểu | **≥ 600 từ** (tối ưu 1200-2000) |
| Đoạn mở đầu | **BẮT BUỘC** — chứa từ khóa chính ngay câu đầu |
| H2 | **Tối thiểu 3 thẻ H2**, mỗi H2 chứa từ khóa phụ |
| H3 | Dùng cho mục con trong H2 |
| Đoạn văn | **3-5 câu/đoạn**, không viết đoạn quá dài |
| Danh sách | Dùng `<ul>` hoặc `<ol>` cho liệt kê |
| Bold | Dùng `<strong>` cho từ/cụm từ quan trọng |
| Link nội bộ | Ít nhất **1 liên kết nội bộ** đến bài khác |
| Hình ảnh | Alt text BẮT BUỘC, có `loading="lazy"` |
| Kết luận | **BẮT BUỘC** H2 kết luận + CTA |
| KHÔNG dùng | H1 (đã có title), inline styles, `<br>` thay paragraph |

### 2.7. Mật độ từ khóa (Keyword Density)
| Loại | Tần suất |
|------|----------|
| Từ khóa chính | 1-2% (5-15 lần / 1000 từ) |
| Từ khóa phụ | Mỗi từ khóa 2-5 lần |
| LSI keywords | Rải tự nhiên trong bài |
| Vị trí bắt buộc | Đoạn đầu, H2, đoạn kết |

---

## 3. CHECK-LIST TRƯỚC KHI ĐĂNG BÀI

```
☐ title: 40-65 ký tự, chứa từ khóa chính ở đầu
☐ meta_title: 50-60 ký tự, format chuẩn
☐ meta_description: 120-155 ký tự, có CTA
☐ excerpt: 80-200 ký tự, tóm tắt giá trị
☐ meta_keywords: 3-7 từ khóa, từ khóa chính đầu tiên
☐ content: ≥ 600 từ
☐ content: Đoạn mở đầu có từ khóa chính
☐ content: ≥ 3 thẻ H2 (không dùng H1)
☐ content: Mỗi H2 có id="" để anchor link
☐ content: ≥ 1 danh sách (ul/ol)
☐ content: ≥ 1 blockquote (tips/lưu ý)
☐ content: ≥ 1 liên kết nội bộ
☐ content: Kết luận + CTA ở cuối
☐ content: Hình ảnh có alt text (nếu có ảnh)
☐ content: Không có H1, inline styles, hoặc <br> thay paragraph
☐ Slug: đúng format tiếng Việt không dấu
```

---

## 4. JSON MẪU ĐẦY ĐỦ CHO N8N API

### 4.1. Tin tức (News) — Mẫu hoàn chỉnh

```json
{
  "title": "Học bổng DAAD 2026: Cơ hội du học Đức miễn phí",
  "excerpt": "DAAD vừa công bố chương trình học bổng 2026 cho sinh viên quốc tế. Cùng tìm hiểu điều kiện và cách đăng ký.",
  "content": "<p>Học bổng DAAD 2026 là cơ hội tuyệt vời cho sinh viên Việt Nam muốn du học Đức miễn phí. Cơ quan Trao đổi Hàn lâm Đức (DAAD) vừa chính thức công bố chương trình học bổng năm 2026 dành cho sinh viên quốc tế.</p>\n\n<nav>\n  <h2>Nội dung bài viết</h2>\n  <ul>\n    <li><a href=\"#chuong-trinh-hoc-bong\">1. Các chương trình học bổng chính</a></li>\n    <li><a href=\"#dieu-kien-dang-ky\">2. Điều kiện đăng ký</a></li>\n    <li><a href=\"#cach-nop-ho-so\">3. Cách nộp hồ sơ thành công</a></li>\n    <li><a href=\"#ket-luan\">Kết luận</a></li>\n  </ul>\n</nav>\n\n<hr>\n\n<h2 id=\"chuong-trinh-hoc-bong\">1. Các chương trình học bổng DAAD chính</h2>\n\n<p>DAAD cung cấp nhiều loại học bổng phù hợp với từng đối tượng sinh viên. Mỗi chương trình có yêu cầu và quyền lợi riêng biệt, giúp bạn lựa chọn phù hợp nhất với mục tiêu học tập.</p>\n\n<ul>\n  <li><strong>Học bổng nghiên cứu (Research Grants):</strong> Dành cho nghiên cứu sinh và học viên cao học muốn thực hiện đề tài tại Đức</li>\n  <li><strong>Học bổng Thạc sĩ (Study Scholarships):</strong> Hỗ trợ toàn phần cho chương trình Thạc sĩ tại các trường đại học Đức</li>\n  <li><strong>Học bổng Tiến sĩ (PhD Scholarships):</strong> Tài trợ cho nghiên cứu sinh làm luận án Tiến sĩ tại Đức</li>\n</ul>\n\n<blockquote>\n  <p><strong>💡 Mẹo:</strong> Nên nghiên cứu kỹ từng loại học bổng và chọn chương trình phù hợp nhất với profile của bạn trước khi nộp hồ sơ.</p>\n</blockquote>\n\n<h2 id=\"dieu-kien-dang-ky\">2. Điều kiện đăng ký học bổng DAAD</h2>\n\n<p>Để đăng ký học bổng DAAD 2026, ứng viên cần đáp ứng các yêu cầu cơ bản sau đây. Lưu ý rằng mỗi chương trình có thể có thêm yêu cầu riêng.</p>\n\n<ol>\n  <li><strong>Bằng cấp:</strong> Có bằng cử nhân hoặc tương đương từ trường đại học được công nhận</li>\n  <li><strong>Ngôn ngữ:</strong> Trình độ tiếng Đức B2 hoặc tiếng Anh IELTS 6.5 trở lên</li>\n  <li><strong>Thư giới thiệu:</strong> Ít nhất 2 thư giới thiệu từ giáo sư hoặc người hướng dẫn</li>\n  <li><strong>Kế hoạch nghiên cứu:</strong> Bản mô tả chi tiết mục tiêu học tập/nghiên cứu tại Đức</li>\n</ol>\n\n<table>\n  <thead>\n    <tr>\n      <th>Chương trình</th>\n      <th>Yêu cầu ngôn ngữ</th>\n      <th>Hạn nộp hồ sơ</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td>Research Grants</td>\n      <td>Tiếng Đức B2 hoặc IELTS 6.5</td>\n      <td>15/10/2026</td>\n    </tr>\n    <tr>\n      <td>Study Scholarships</td>\n      <td>Tiếng Đức B1 hoặc IELTS 6.0</td>\n      <td>15/11/2026</td>\n    </tr>\n    <tr>\n      <td>PhD Scholarships</td>\n      <td>Tiếng Anh IELTS 6.5</td>\n      <td>01/10/2026</td>\n    </tr>\n  </tbody>\n</table>\n\n<h2 id=\"cach-nop-ho-so\">3. Cách nộp hồ sơ thành công</h2>\n\n<p>Quy trình nộp hồ sơ học bổng DAAD được thực hiện hoàn toàn trực tuyến. Dưới đây là hướng dẫn chi tiết từng bước để bạn chuẩn bị hồ sơ tốt nhất.</p>\n\n<h3>3.1. Chuẩn bị tài liệu</h3>\n\n<p>Trước khi bắt đầu nộp hồ sơ, hãy chuẩn bị đầy đủ các giấy tờ cần thiết. Tất cả tài liệu phải được dịch sang tiếng Đức hoặc tiếng Anh và có công chứng.</p>\n\n<h3>3.2. Nộp hồ sơ trực tuyến</h3>\n\n<p>Truy cập cổng DAAD Portal tại <a href=\"https://www.daad.de\">daad.de</a> để tạo tài khoản và nộp hồ sơ. Hãy hoàn thành hồ sơ sớm, không nên đợi đến ngày cuối cùng.</p>\n\n<blockquote>\n  <p><strong>⚠️ Lưu ý quan trọng:</strong> Hồ sơ nộp muộn sẽ không được xét duyệt. Nên nộp trước hạn ít nhất 2 tuần để có thời gian xử lý vấn đề phát sinh.</p>\n</blockquote>\n\n<h2 id=\"ket-luan\">Kết luận</h2>\n\n<p>Học bổng DAAD 2026 mở ra cơ hội du học Đức miễn phí cho sinh viên Việt Nam ở nhiều cấp độ. Với sự chuẩn bị kỹ lưỡng và hồ sơ chất lượng, bạn hoàn toàn có thể chinh phục học bổng danh giá này.</p>\n\n<p>Hãy bắt đầu chuẩn bị hồ sơ ngay từ bây giờ và tham khảo thêm kinh nghiệm từ các bài viết khác trên <a href=\"/tin-tuc/hoc-tieng-duc\">chuyên mục Học tiếng Đức</a> của UnstressVN.</p>\n\n<blockquote>\n  <p><strong>📌 Bạn thấy bài viết hữu ích?</strong> Hãy chia sẻ cho bạn bè hoặc lưu lại để đọc sau. Khám phá thêm tại <a href=\"/kien-thuc\">Kiến thức</a> để chuẩn bị tốt nhất cho hành trình du học Đức.</p>\n</blockquote>",
  "category": "hoc-tieng-duc",
  "is_featured": true,
  "is_published": true,
  "meta_title": "Học bổng DAAD 2026 — Du học Đức miễn phí | UnstressVN",
  "meta_description": "Tìm hiểu chi tiết về học bổng DAAD 2026 cho sinh viên Việt Nam. Điều kiện, hạn nộp và cách đăng ký thành công. Đọc ngay!",
  "meta_keywords": "học bổng DAAD 2026, du học Đức miễn phí, điều kiện học bổng DAAD, cách đăng ký DAAD, scholarship Germany",
  "is_ai_generated": true,
  "ai_model": "gpt-4o",
  "workflow_id": "workflow_news_auto",
  "source_url": "https://www.daad.de/en/study-and-research-in-germany/scholarships/"
}
```

### 4.2. Kiến thức (Knowledge) — Mẫu hoàn chỉnh

```json
{
  "title": "10 cách luyện nghe tiếng Đức hiệu quả cho trình độ A2-B1",
  "excerpt": "Hướng dẫn chi tiết 10 phương pháp luyện nghe tiếng Đức giúp cải thiện kỹ năng nhanh chóng, phù hợp trình độ A2-B1.",
  "content": "<p>Luyện nghe tiếng Đức hiệu quả là kỹ năng quan trọng nhất để giao tiếp tự tin. Nhiều người học tiếng Đức gặp khó khăn với việc nghe hiểu, đặc biệt ở giai đoạn chuyển từ A2 lên B1. Bài viết này chia sẻ 10 phương pháp đã được chứng minh hiệu quả.</p>\n\n<nav>\n  <h2>Nội dung bài viết</h2>\n  <ul>\n    <li><a href=\"#nguyen-tac-co-ban\">1. Nguyên tắc cơ bản khi luyện nghe</a></li>\n    <li><a href=\"#phuong-phap\">2. 10 phương pháp luyện nghe hiệu quả</a></li>\n    <li><a href=\"#tai-nguyen\">3. Tài nguyên luyện nghe miễn phí</a></li>\n    <li><a href=\"#ket-luan\">Kết luận</a></li>\n  </ul>\n</nav>\n\n<hr>\n\n<h2 id=\"nguyen-tac-co-ban\">1. Nguyên tắc cơ bản khi luyện nghe tiếng Đức</h2>\n\n<p>Trước khi đi vào các phương pháp cụ thể, bạn cần hiểu rõ 3 nguyên tắc nền tảng để luyện nghe đạt hiệu quả cao nhất.</p>\n\n<ul>\n  <li><strong>Nghe chủ động (Aktives Hören):</strong> Tập trung vào nội dung, không chỉ để tiếng Đức chạy nền</li>\n  <li><strong>Lặp lại có chủ đích:</strong> Nghe đi nghe lại cùng đoạn, mỗi lần tập trung vào khía cạnh khác nhau</li>\n  <li><strong>Nghe đúng trình độ:</strong> Chọn tài liệu phù hợp level, hiểu được 70-80% nội dung</li>\n</ul>\n\n<blockquote>\n  <p><strong>💡 Mẹo:</strong> Dành 15-20 phút mỗi ngày luyện nghe đều đặn sẽ hiệu quả hơn nghe 2 tiếng vào cuối tuần.</p>\n</blockquote>\n\n<h2 id=\"phuong-phap\">2. 10 phương pháp luyện nghe tiếng Đức hiệu quả</h2>\n\n<p>Dưới đây là 10 phương pháp được sắp xếp từ cơ bản đến nâng cao, phù hợp cho người học ở trình độ A2-B1.</p>\n\n<ol>\n  <li><strong>Shadowing (Nói theo):</strong> Nghe và lặp lại ngay lập tức từng câu. Giúp cải thiện cả phát âm lẫn nghe hiểu.</li>\n  <li><strong>Dictation (Nghe chép):</strong> Nghe và viết lại nội dung. Phương pháp hiệu quả nhất để tăng độ chính xác.</li>\n  <li><strong>Podcast tiếng Đức:</strong> Nghe các podcast như \"Slow German\" hoặc \"Easy German\" hàng ngày.</li>\n</ol>\n\n<h2 id=\"tai-nguyen\">3. Tài nguyên luyện nghe miễn phí</h2>\n\n<p>UnstressVN đã tổng hợp danh sách tài nguyên luyện nghe tiếng Đức miễn phí tốt nhất. Tất cả đều phù hợp cho trình độ A2-B1.</p>\n\n<table>\n  <thead>\n    <tr>\n      <th>Tài nguyên</th>\n      <th>Trình độ</th>\n      <th>Miễn phí</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td>Deutsche Welle</td>\n      <td>A1-C1</td>\n      <td>✅ Hoàn toàn</td>\n    </tr>\n    <tr>\n      <td>Slow German</td>\n      <td>A2-B2</td>\n      <td>✅ Có phần free</td>\n    </tr>\n  </tbody>\n</table>\n\n<h2 id=\"ket-luan\">Kết luận</h2>\n\n<p>Luyện nghe tiếng Đức hiệu quả đòi hỏi sự kiên trì và phương pháp đúng. Hãy bắt đầu với 1-2 phương pháp phù hợp và tăng dần theo thời gian.</p>\n\n<blockquote>\n  <p><strong>📌 Bạn thấy bài viết hữu ích?</strong> Khám phá thêm tại <a href=\"/kien-thuc\">Kiến thức</a> để nâng cao trình độ tiếng Đức mỗi ngày.</p>\n</blockquote>",
  "category": "ky-nang-nghe",
  "language": "de",
  "level": "B1",
  "is_published": true,
  "meta_title": "10 cách luyện nghe tiếng Đức A2-B1 | UnstressVN",
  "meta_description": "Hướng dẫn 10 phương pháp luyện nghe tiếng Đức hiệu quả cho trình độ A2-B1. Podcast, shadowing, dictation và tài nguyên miễn phí. Đọc ngay!",
  "meta_keywords": "luyện nghe tiếng Đức, nghe tiếng Đức A2, nghe tiếng Đức B1, cách luyện nghe, podcast tiếng Đức",
  "is_ai_generated": true,
  "ai_model": "gpt-4o",
  "workflow_id": "workflow_knowledge_auto"
}
```

---

## 5. CÁC PHẦN TỬ HTML ĐƯỢC PHÉP TRONG `content`

| Thẻ HTML | Mục đích | Ghi chú |
|----------|----------|---------|
| `<p>` | Đoạn văn | BẮT BUỘC cho mọi đoạn text |
| `<h2 id="">` | Tiêu đề chính | BẮT BUỘC có `id` cho anchor |
| `<h3>` | Tiêu đề phụ | Dùng trong section H2 |
| `<h4>` | Tiêu đề cấp 3 | Dùng giới hạn |
| `<ul>`, `<ol>`, `<li>` | Danh sách | Tăng cơ hội Featured Snippet |
| `<strong>` | In đậm | Cho từ khóa, cụm từ quan trọng |
| `<em>` | In nghiêng | Cho thuật ngữ, từ ngoại ngữ |
| `<a href="">` | Liên kết | Liên kết nội bộ BẮT BUỘC |
| `<blockquote>` | Trích dẫn / Tips | Nổi bật thông tin quan trọng |
| `<table>` | Bảng | So sánh, thống kê |
| `<figure>`, `<figcaption>` | Hình ảnh | Bao bọc img + chú thích |
| `<img>` | Hình ảnh | BẮT BUỘC có `alt`, `loading="lazy"` |
| `<iframe>` | Video nhúng | Chỉ cho YouTube |
| `<nav>` | Mục lục | Đầu bài viết |
| `<hr>` | Phân cách | Giữa các section lớn |
| `<code>`, `<pre>` | Code | Cho nội dung kỹ thuật |

### KHÔNG ĐƯỢC DÙNG:
- ❌ `<h1>` — Đã có title
- ❌ `<div>` với inline styles
- ❌ `<br>` thay cho `<p>` mới
- ❌ `<span style="">` — Styling bất kỳ
- ❌ `<font>`, `<center>`, `<b>`, `<i>` — Thẻ lỗi thời
- ❌ Inline CSS (`style="..."`)
- ❌ JavaScript trong content
