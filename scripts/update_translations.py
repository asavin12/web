#!/usr/bin/env python3
"""
Script cập nhật các bản dịch cho UnstressVN
Hỗ trợ: Tiếng Việt (vi), Tiếng Anh (en), Tiếng Đức (de)
"""

import os
import re
from pathlib import Path

# Các bản dịch - Vietnamese là gốc
TRANSLATIONS = {
    # Navigation & Common
    "Kho Tri Thức": {"en": "Knowledge Hub", "de": "Wissenszentrum"},
    "Khám Phá": {"en": "Explore", "de": "Entdecken"},
    "Thư Viện": {"en": "Library", "de": "Bibliothek"},
    "Cộng Đồng": {"en": "Community", "de": "Gemeinschaft"},
    "Tìm Bạn Học": {"en": "Find Partners", "de": "Lernpartner finden"},
    "Tìm kiếm trong kho tài liệu...": {"en": "Search in library...", "de": "In der Bibliothek suchen..."},
    "Trang chủ": {"en": "Home", "de": "Startseite"},
    
    # Auth
    "Đăng Nhập": {"en": "Login", "de": "Anmelden"},
    "Đăng nhập": {"en": "Login", "de": "Anmelden"},
    "Đăng Ký": {"en": "Register", "de": "Registrieren"},
    "Đăng ký": {"en": "Register", "de": "Registrieren"},
    "Đăng xuất": {"en": "Logout", "de": "Abmelden"},
    "Chào Mừng Trở Lại": {"en": "Welcome Back", "de": "Willkommen zurück"},
    "Đăng nhập để tiếp tục hành trình học tập.": {"en": "Login to continue your learning journey.", "de": "Melden Sie sich an, um Ihre Lernreise fortzusetzen."},
    "Tên đăng nhập hoặc mật khẩu không đúng.": {"en": "Incorrect username or password.", "de": "Falscher Benutzername oder Passwort."},
    "Tên đăng nhập": {"en": "Username", "de": "Benutzername"},
    "Nhập tên đăng nhập": {"en": "Enter username", "de": "Benutzername eingeben"},
    "Mật khẩu": {"en": "Password", "de": "Passwort"},
    "Nhập mật khẩu": {"en": "Enter password", "de": "Passwort eingeben"},
    "Ghi nhớ đăng nhập": {"en": "Remember me", "de": "Angemeldet bleiben"},
    "Quên mật khẩu?": {"en": "Forgot password?", "de": "Passwort vergessen?"},
    "Hoặc tiếp tục với": {"en": "Or continue with", "de": "Oder fortfahren mit"},
    "Chưa có tài khoản?": {"en": "Don't have an account?", "de": "Noch kein Konto?"},
    "Đăng ký ngay": {"en": "Register now", "de": "Jetzt registrieren"},
    "Đã có tài khoản?": {"en": "Already have an account?", "de": "Bereits ein Konto?"},
    "Đăng nhập ngay": {"en": "Login now", "de": "Jetzt anmelden"},
    
    # Profile
    "Hồ Sơ Của Tôi": {"en": "My Profile", "de": "Mein Profil"},
    "Hồ sơ": {"en": "Profile", "de": "Profil"},
    "Chỉnh Sửa": {"en": "Edit", "de": "Bearbeiten"},
    "Chỉnh Sửa Hồ Sơ": {"en": "Edit Profile", "de": "Profil bearbeiten"},
    "Chỉnh sửa hồ sơ": {"en": "Edit profile", "de": "Profil bearbeiten"},
    "Quay lại Hồ sơ": {"en": "Back to Profile", "de": "Zurück zum Profil"},
    "Cập nhật thông tin cá nhân của bạn": {"en": "Update your personal information", "de": "Aktualisieren Sie Ihre persönlichen Daten"},
    "Thành viên từ": {"en": "Member since", "de": "Mitglied seit"},
    "Thông Tin Học Tập": {"en": "Learning Info", "de": "Lerninformationen"},
    "Thông tin học tập": {"en": "Learning Info", "de": "Lerninformationen"},
    "Thông Tin Cơ Bản": {"en": "Basic Information", "de": "Grundinformationen"},
    "Đang học": {"en": "Currently learning", "de": "Aktuell lernend"},
    "Trình độ": {"en": "Level", "de": "Niveau"},
    "Mục tiêu": {"en": "Goal", "de": "Ziel"},
    "Giới thiệu": {"en": "About", "de": "Über mich"},
    "Lưu thay đổi": {"en": "Save changes", "de": "Änderungen speichern"},
    "Lưu Thay Đổi": {"en": "Save Changes", "de": "Änderungen speichern"},
    "Hủy": {"en": "Cancel", "de": "Abbrechen"},
    "Cập nhật thành công!": {"en": "Updated successfully!", "de": "Erfolgreich aktualisiert!"},
    
    # Profile Edit specifics
    "Đổi ảnh bìa": {"en": "Change cover", "de": "Cover ändern"},
    "Định dạng JPG, PNG. Tối đa 5MB.": {"en": "JPG, PNG format. Max 5MB.", "de": "JPG, PNG Format. Max 5MB."},
    "Họ và tên": {"en": "Full name", "de": "Vollständiger Name"},
    "Nhập họ và tên của bạn": {"en": "Enter your full name", "de": "Geben Sie Ihren vollständigen Namen ein"},
    "Vị trí": {"en": "Location", "de": "Standort"},
    "Thành phố, Quốc gia": {"en": "City, Country", "de": "Stadt, Land"},
    "Ngày sinh": {"en": "Date of birth", "de": "Geburtsdatum"},
    "Viết vài dòng về bạn...": {"en": "Write a few lines about yourself...", "de": "Schreiben Sie ein paar Zeilen über sich..."},
    
    # Learning Settings
    "Cài Đặt Học Tập": {"en": "Learning Settings", "de": "Lerneinstellungen"},
    "Ngôn ngữ mẹ đẻ": {"en": "Native language", "de": "Muttersprache"},
    "Chọn ngôn ngữ": {"en": "Select language", "de": "Sprache wählen"},
    "Chọn trình độ": {"en": "Select level", "de": "Niveau wählen"},
    "Kỹ năng tập trung": {"en": "Focus skill", "de": "Fokus-Fähigkeit"},
    "Chọn kỹ năng": {"en": "Select skill", "de": "Fähigkeit wählen"},
    "Mục tiêu học hàng ngày": {"en": "Daily learning goal", "de": "Tägliches Lernziel"},
    "phút": {"en": "minutes", "de": "Minuten"},
    
    # Skills
    "Nghe": {"en": "Listening", "de": "Hören"},
    "Nói": {"en": "Speaking", "de": "Sprechen"},
    "Đọc": {"en": "Reading", "de": "Lesen"},
    "Viết": {"en": "Writing", "de": "Schreiben"},
    "Ngữ pháp": {"en": "Grammar", "de": "Grammatik"},
    "Từ vựng": {"en": "Vocabulary", "de": "Wortschatz"},
    
    # Levels
    "Bắt đầu": {"en": "Beginner", "de": "Anfänger"},
    "Sơ cấp": {"en": "Elementary", "de": "Grundstufe"},
    "Trung cấp": {"en": "Intermediate", "de": "Mittelstufe"},
    "Trung cấp cao": {"en": "Upper Intermediate", "de": "Obere Mittelstufe"},
    "Nâng cao": {"en": "Advanced", "de": "Fortgeschritten"},
    "Thành thạo": {"en": "Proficient", "de": "Kompetent"},
    
    # Social Links
    "Liên Kết Mạng Xã Hội": {"en": "Social Links", "de": "Soziale Links"},
    
    # Privacy Settings
    "Cài Đặt Quyền Riêng Tư": {"en": "Privacy Settings", "de": "Datenschutzeinstellungen"},
    "Hồ sơ công khai": {"en": "Public profile", "de": "Öffentliches Profil"},
    "Cho phép người khác xem hồ sơ của bạn": {"en": "Allow others to view your profile", "de": "Erlauben Sie anderen, Ihr Profil anzusehen"},
    "Hiển thị trạng thái online": {"en": "Show online status", "de": "Online-Status anzeigen"},
    "Cho phép người khác thấy khi bạn đang trực tuyến": {"en": "Allow others to see when you are online", "de": "Erlauben Sie anderen zu sehen, wenn Sie online sind"},
    "Cho phép tin nhắn": {"en": "Allow messages", "de": "Nachrichten erlauben"},
    "Cho phép người khác gửi tin nhắn cho bạn": {"en": "Allow others to send you messages", "de": "Erlauben Sie anderen, Ihnen Nachrichten zu senden"},
    
    # Resources
    "Tài liệu": {"en": "Resources", "de": "Materialien"},
    "Thư Viện Tài Liệu": {"en": "Resource Library", "de": "Materialbibliothek"},
    "Tất cả": {"en": "All", "de": "Alle"},
    "Sách": {"en": "Books", "de": "Bücher"},
    "Tài liệu PDF": {"en": "PDF Documents", "de": "PDF-Dokumente"},
    "Video": {"en": "Videos", "de": "Videos"},
    "Bài viết": {"en": "Articles", "de": "Artikel"},
    "Tải xuống": {"en": "Download", "de": "Herunterladen"},
    "Đăng ký để tải": {"en": "Register to download", "de": "Registrieren zum Herunterladen"},
    "Xem chi tiết": {"en": "View details", "de": "Details anzeigen"},
    "Lượt xem": {"en": "Views", "de": "Aufrufe"},
    "Lượt tải": {"en": "Downloads", "de": "Downloads"},
    "Ngày đăng": {"en": "Posted date", "de": "Veröffentlichungsdatum"},
    "Quay lại": {"en": "Go back", "de": "Zurück"},
    "Xem trên YouTube": {"en": "Watch on YouTube", "de": "Auf YouTube ansehen"},
    
    # Forum
    "Diễn Đàn": {"en": "Forum", "de": "Forum"},
    "Bài đăng": {"en": "Posts", "de": "Beiträge"},
    "Viết bài mới": {"en": "New post", "de": "Neuer Beitrag"},
    "Tạo bài viết": {"en": "Create post", "de": "Beitrag erstellen"},
    "Tiêu đề": {"en": "Title", "de": "Titel"},
    "Nội dung": {"en": "Content", "de": "Inhalt"},
    "Đăng bài": {"en": "Post", "de": "Veröffentlichen"},
    "Bình luận": {"en": "Comments", "de": "Kommentare"},
    "Viết bình luận...": {"en": "Write a comment...", "de": "Schreiben Sie einen Kommentar..."},
    "Gửi": {"en": "Send", "de": "Senden"},
    "Xóa": {"en": "Delete", "de": "Löschen"},
    "Sửa": {"en": "Edit", "de": "Bearbeiten"},
    "Xem hồ sơ": {"en": "View profile", "de": "Profil anzeigen"},
    "Nhắn tin": {"en": "Message", "de": "Nachricht"},
    "trước": {"en": "ago", "de": "vor"},
    "vừa xong": {"en": "just now", "de": "gerade eben"},
    "ngày": {"en": "days", "de": "Tage"},
    "tuần": {"en": "weeks", "de": "Wochen"},
    "tháng": {"en": "months", "de": "Monate"},
    "năm": {"en": "years", "de": "Jahre"},
    
    # Chat
    "Tin nhắn": {"en": "Messages", "de": "Nachrichten"},
    "Nhập tin nhắn...": {"en": "Type a message...", "de": "Nachricht eingeben..."},
    "Bắt đầu trò chuyện": {"en": "Start conversation", "de": "Gespräch starten"},
    "Chưa có tin nhắn": {"en": "No messages yet", "de": "Noch keine Nachrichten"},
    "Chưa có cuộc hội thoại": {"en": "No conversations yet", "de": "Noch keine Gespräche"},
    
    # Partners
    "Tìm Bạn Học Tập": {"en": "Find Study Partners", "de": "Lernpartner finden"},
    "Kết nối": {"en": "Connect", "de": "Verbinden"},
    "Đã kết nối": {"en": "Connected", "de": "Verbunden"},
    "Gửi yêu cầu": {"en": "Send request", "de": "Anfrage senden"},
    "Yêu cầu đã gửi": {"en": "Request sent", "de": "Anfrage gesendet"},
    "Chấp nhận": {"en": "Accept", "de": "Annehmen"},
    "Từ chối": {"en": "Decline", "de": "Ablehnen"},
    
    # Search
    "Tìm kiếm": {"en": "Search", "de": "Suchen"},
    "Kết quả tìm kiếm": {"en": "Search results", "de": "Suchergebnisse"},
    "Không tìm thấy kết quả": {"en": "No results found", "de": "Keine Ergebnisse gefunden"},
    "Không tìm thấy video": {"en": "No videos found", "de": "Keine Videos gefunden"},
    "Không tìm thấy thành viên": {"en": "No members found", "de": "Keine Mitglieder gefunden"},
    "Nhập từ khóa để tìm kiếm": {"en": "Enter keywords to search", "de": "Suchbegriffe eingeben"},
    "Xem tất cả kết quả": {"en": "View all results", "de": "Alle Ergebnisse anzeigen"},
    "Thành viên": {"en": "Members", "de": "Mitglieder"},
    
    # Languages
    "Tiếng Việt": {"en": "Vietnamese", "de": "Vietnamesisch"},
    "Tiếng Anh": {"en": "English", "de": "Englisch"},
    "Tiếng Đức": {"en": "German", "de": "Deutsch"},
    
    # Footer
    "Liên hệ": {"en": "Contact", "de": "Kontakt"},
    "Điều khoản": {"en": "Terms", "de": "Nutzungsbedingungen"},
    "Chính sách bảo mật": {"en": "Privacy Policy", "de": "Datenschutz"},
    "Về chúng tôi": {"en": "About us", "de": "Über uns"},
    
    # Forms
    "Email": {"en": "Email", "de": "E-Mail"},
    "Nhập email": {"en": "Enter email", "de": "E-Mail eingeben"},
    "Xác nhận mật khẩu": {"en": "Confirm password", "de": "Passwort bestätigen"},
    "Nhập lại mật khẩu": {"en": "Re-enter password", "de": "Passwort erneut eingeben"},
    "Đang xử lý...": {"en": "Processing...", "de": "Verarbeitung..."},
    
    # Misc
    "Xem thêm": {"en": "See more", "de": "Mehr anzeigen"},
    "Thu gọn": {"en": "Show less", "de": "Weniger anzeigen"},
    "Đang tải...": {"en": "Loading...", "de": "Wird geladen..."},
    "Lỗi": {"en": "Error", "de": "Fehler"},
    "Thành công": {"en": "Success", "de": "Erfolg"},
    "Cảnh báo": {"en": "Warning", "de": "Warnung"},
    "Thông tin": {"en": "Info", "de": "Information"},
    "Bạn có chắc chắn?": {"en": "Are you sure?", "de": "Sind Sie sicher?"},
    "Có": {"en": "Yes", "de": "Ja"},
    "Không": {"en": "No", "de": "Nein"},
    
    # Home page
    "Tài Liệu Mới": {"en": "New Resources", "de": "Neue Materialien"},
    "Bài Đăng Mới": {"en": "Recent Posts", "de": "Neue Beiträge"},
    "Thành Viên Nổi Bật": {"en": "Featured Members", "de": "Empfohlene Mitglieder"},
    "Xem tất cả": {"en": "View all", "de": "Alle anzeigen"},
    
    # Register page
    "Tạo Tài Khoản Mới": {"en": "Create New Account", "de": "Neues Konto erstellen"},
    "Bắt đầu hành trình học tập của bạn.": {"en": "Start your learning journey.", "de": "Starten Sie Ihre Lernreise."},
    "Tôi đồng ý với": {"en": "I agree to the", "de": "Ich stimme den"},
    "Điều khoản sử dụng": {"en": "Terms of Service", "de": "Nutzungsbedingungen"},
    "và": {"en": "and", "de": "und"},
    
    # Missing translations from templates
    "Chuỗi ngày": {"en": "Date streak", "de": "Tagesserie"},
    "Hoạt Động Gần Đây": {"en": "Recent Activity", "de": "Letzte Aktivität"},
    "Chưa có hoạt động gần đây.": {"en": "No recent activity.", "de": "Keine aktuelle Aktivität."},
    "Tài Liệu Của Tôi": {"en": "My Resources", "de": "Meine Materialien"},
    "lượt tải": {"en": "downloads", "de": "Downloads"},
    "Tải lên ngay": {"en": "Upload now", "de": "Jetzt hochladen"},
    "Not set": {"en": "Not set", "de": "Nicht festgelegt"},
    "Back to Search": {"en": "Back to Search", "de": "Zurück zur Suche"},
    "Verified": {"en": "Verified", "de": "Verifiziert"},
    "Partner": {"en": "Partner", "de": "Partner"},
    "Request Sent": {"en": "Request Sent", "de": "Anfrage gesendet"},
    "Sending...": {"en": "Sending...", "de": "Wird gesendet..."},
    "Add Partner": {"en": "Add Partner", "de": "Partner hinzufügen"},
    "Edit Profile": {"en": "Edit Profile", "de": "Profil bearbeiten"},
    "Member since": {"en": "Member since", "de": "Mitglied seit"},
    "Learning Profile": {"en": "Learning Profile", "de": "Lernprofil"},
    "Native": {"en": "Native", "de": "Muttersprache"},
    "Learning": {"en": "Learning", "de": "Lernend"},
    "Level": {"en": "Level", "de": "Niveau"},
    "Focus": {"en": "Focus", "de": "Fokus"},
    "Statistics": {"en": "Statistics", "de": "Statistiken"},
    "Resources": {"en": "Resources", "de": "Materialien"},
    "Partners": {"en": "Partners", "de": "Partner"},
    "Shared Resources": {"en": "Shared Resources", "de": "Geteilte Materialien"},
    "View more": {"en": "View more", "de": "Mehr anzeigen"},
    "No resources shared yet.": {"en": "No resources shared yet.", "de": "Noch keine Materialien geteilt."},
    
    # Register / Chat
    "Tham gia cộng đồng học ngôn ngữ ngay hôm nay!": {"en": "Join the language learning community today!", "de": "Treten Sie heute der Sprachlerngemeinschaft bei!"},
    "Ví dụ: nguyen_van_a": {"en": "Example: john_doe", "de": "Beispiel: max_mustermann"},
    "Chỉ cho phép chữ cái, số và dấu gạch dưới": {"en": "Only letters, numbers and underscores allowed", "de": "Nur Buchstaben, Zahlen und Unterstriche erlaubt"},
    "email@example.com": {"en": "email@example.com", "de": "email@beispiel.de"},
    "Ít nhất 8 ký tự": {"en": "At least 8 characters", "de": "Mindestens 8 Zeichen"},
    "Tất cả cuộc trò chuyện của bạn": {"en": "All your conversations", "de": "Alle Ihre Gespräche"},
    "Cuộc trò chuyện mới": {"en": "New conversation", "de": "Neues Gespräch"},
    "Tìm kiếm cuộc trò chuyện...": {"en": "Search conversations...", "de": "Gespräche suchen..."},
    "Bắt đầu kết nối với cộng đồng học tập!": {"en": "Start connecting with the learning community!", "de": "Verbinden Sie sich mit der Lerngemeinschaft!"},
    "Chat với": {"en": "Chat with", "de": "Chat mit"},
    "Bắt đầu cuộc trò chuyện!": {"en": "Start the conversation!", "de": "Beginnen Sie das Gespräch!"},
    
    # Home page extra
    "Khám Phá. Kết Nối. Thành Thạo.": {"en": "Explore. Connect. Master.", "de": "Entdecken. Verbinden. Meistern."},
    "Mới Cập Nhật": {"en": "Recently Updated", "de": "Kürzlich aktualisiert"},
    "Tài Liệu Đề Xuất": {"en": "Recommended Resources", "de": "Empfohlene Materialien"},
    "Kho tài liệu đang chờ bạn đóng góp.": {"en": "The library awaits your contribution.", "de": "Die Bibliothek wartet auf Ihren Beitrag."},
    "Xem Tất Cả Tài Liệu": {"en": "View All Resources", "de": "Alle Materialien anzeigen"},
    "lượt xem": {"en": "views", "de": "Aufrufe"},
    
    # Forum
    "Thảo Luận Cộng Đồng": {"en": "Community Discussion", "de": "Community-Diskussion"},
    "Tạo Bài Viết": {"en": "Create Post", "de": "Beitrag erstellen"},
    "Ghim": {"en": "Pinned", "de": "Angeheftet"},
    "Hãy là người đầu tiên bắt đầu cuộc trò chuyện!": {"en": "Be the first to start the conversation!", "de": "Seien Sie der Erste, der das Gespräch beginnt!"},
    "Tham Gia Thảo Luận": {"en": "Join Discussion", "de": "Diskussion beitreten"},
    "Cộng đồng": {"en": "Community", "de": "Gemeinschaft"},
    "Đã khóa": {"en": "Locked", "de": "Gesperrt"},
    "trả lời": {"en": "replies", "de": "Antworten"},
    "Lưu": {"en": "Save", "de": "Speichern"},
    "Trả lời": {"en": "Reply", "de": "Antworten"},
    "Chưa có trả lời nào. Hãy là người đầu tiên!": {"en": "No replies yet. Be the first!", "de": "Noch keine Antworten. Seien Sie der Erste!"},
    "Viết trả lời": {"en": "Write a reply", "de": "Eine Antwort schreiben"},
    "Chia sẻ ý kiến của bạn...": {"en": "Share your thoughts...", "de": "Teilen Sie Ihre Gedanken..."},
    "Bài viết đã bị khóa, không thể trả lời.": {"en": "This post is locked, cannot reply.", "de": "Dieser Beitrag ist gesperrt, keine Antwort möglich."},
    "để tham gia thảo luận": {"en": "to join the discussion", "de": "um an der Diskussion teilzunehmen"},
    "Đăng bài mới": {"en": "New Post", "de": "Neuer Beitrag"},
    "Quay lại cộng đồng": {"en": "Back to community", "de": "Zurück zur Gemeinschaft"},
    "Chia sẻ câu hỏi, kinh nghiệm hoặc thảo luận với cộng đồng": {"en": "Share questions, experiences or discussions with the community", "de": "Teilen Sie Fragen, Erfahrungen oder Diskussionen mit der Gemeinschaft"},
    "Nhập tiêu đề bài viết...": {"en": "Enter post title...", "de": "Beitragstitel eingeben..."},
    "Viết nội dung bài viết của bạn...": {"en": "Write your post content...", "de": "Schreiben Sie Ihren Beitragsinhalt..."},
    "Hướng dẫn đăng bài": {"en": "Posting Guidelines", "de": "Beitragsrichtlinien"},
    "Đặt tiêu đề rõ ràng, súc tích": {"en": "Use a clear, concise title", "de": "Verwenden Sie einen klaren, prägnanten Titel"},
    "Mô tả chi tiết vấn đề hoặc nội dung chia sẻ": {"en": "Describe the issue or content in detail", "de": "Beschreiben Sie das Problem oder den Inhalt im Detail"},
    "Chọn đúng danh mục để mọi người dễ tìm kiếm": {"en": "Choose the right category for easier search", "de": "Wählen Sie die richtige Kategorie für eine einfachere Suche"},
    "Tôn trọng và lịch sự với các thành viên khác": {"en": "Be respectful and polite to other members", "de": "Seien Sie respektvoll und höflich zu anderen Mitgliedern"},
    "Hãy là người đầu tiên chia sẻ trong cộng đồng!": {"en": "Be the first to share in the community!", "de": "Seien Sie der Erste, der in der Gemeinschaft teilt!"},
    "Đăng bài đầu tiên": {"en": "Create first post", "de": "Ersten Beitrag erstellen"},
    
    # Languages in selector
    "English": {"en": "English", "de": "English"},
    "Deutsch": {"en": "Deutsch", "de": "Deutsch"},
    
    # Email templates
    "UnstressVN - Lời mời kết bạn đã được chấp nhận!": {"en": "UnstressVN - Partner request accepted!", "de": "UnstressVN - Partneranfrage akzeptiert!"},
    "Xin chào": {"en": "Hello", "de": "Hallo"},
    "Hãy đăng nhập để xem và phản hồi lời mời này.": {"en": "Please log in to view and respond to this invitation.", "de": "Bitte melden Sie sich an, um diese Einladung zu sehen und zu beantworten."},
    "Email này được gửi tự động từ UnstressVN.": {"en": "This email was sent automatically from UnstressVN.", "de": "Diese E-Mail wurde automatisch von UnstressVN gesendet."},
    "Tin vui!": {"en": "Great news!", "de": "Gute Nachrichten!"},
    "Bây giờ các bạn có thể bắt đầu học tập cùng nhau!": {"en": "You can now start learning together!", "de": "Ihr könnt jetzt zusammen lernen!"},
    "Chúc bạn có những giờ học thú vị cùng bạn học mới!": {"en": "Have fun learning with your new partner!", "de": "Viel Spaß beim Lernen mit Ihrem neuen Partner!"},
    
    # Partners page
    "Danh Sách Thành Viên": {"en": "Member List", "de": "Mitgliederliste"},
    "Kết nối với những người yêu thích ngôn ngữ khác.": {"en": "Connect with other language enthusiasts.", "de": "Verbinden Sie sich mit anderen Sprachbegeisterten."},
    "Tìm theo tên, sở thích hoặc vị trí...": {"en": "Search by name, interests or location...", "de": "Suchen nach Name, Interessen oder Standort..."},
    "Bài viết:": {"en": "Posts:", "de": "Beiträge:"},
    "Hãy thử điều chỉnh tiêu chí tìm kiếm.": {"en": "Try adjusting your search criteria.", "de": "Versuchen Sie, Ihre Suchkriterien anzupassen."},
    "Đặt Lại": {"en": "Reset", "de": "Zurücksetzen"},
    "Có lỗi xảy ra. Vui lòng thử lại.": {"en": "An error occurred. Please try again.", "de": "Ein Fehler ist aufgetreten. Bitte versuchen Sie es erneut."},
    
    # Resource page
    "Thẻ tag": {"en": "Tags", "de": "Tags"},
    "Tài liệu liên quan": {"en": "Related Resources", "de": "Verwandte Materialien"},
    "Catalog Filters": {"en": "Catalog Filters", "de": "Katalogfilter"},
    "Không có tài liệu phù hợp với tiêu chí tìm kiếm.": {"en": "No resources match the search criteria.", "de": "Keine Materialien entsprechen den Suchkriterien."},
    "Reset Catalog": {"en": "Reset Catalog", "de": "Katalog zurücksetzen"},
    
    # Search
    "Tìm kiếm tài liệu học tập hoặc bạn học cùng sở thích": {"en": "Search for learning resources or study partners", "de": "Suchen Sie nach Lernmaterialien oder Lernpartnern"},
    "Nhập từ khóa tìm kiếm...": {"en": "Enter search keywords...", "de": "Suchbegriffe eingeben..."},
    "Kết quả cho": {"en": "Results for", "de": "Ergebnisse für"},
    
    # Footer
    "Kết nối tri thức qua nghệ thuật ngôn ngữ.": {"en": "Connecting knowledge through the art of language.", "de": "Wissen verbinden durch die Kunst der Sprache."},
    "Hướng Dẫn": {"en": "Guide", "de": "Anleitung"},
    "Thành Viên": {"en": "Members", "de": "Mitglieder"},
    "Đã đăng ký bản quyền.": {"en": "All rights reserved.", "de": "Alle Rechte vorbehalten."},
    "Thảo luận": {"en": "Discussions", "de": "Diskussionen"},
    
    # Chat widget
    "Tìm bạn học và bắt đầu trò chuyện!": {"en": "Find study partners and start chatting!", "de": "Finden Sie Lernpartner und chatten Sie los!"},
    
    # Admin
    "Quản trị viên": {"en": "Administrator", "de": "Administrator"},
    "Trang quản lý": {"en": "Admin Panel", "de": "Verwaltungsbereich"},
}

def update_po_file(filepath: str, lang: str):
    """Cập nhật file .po với các bản dịch"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Cập nhật từng chuỗi
    for vi_text, translations in TRANSLATIONS.items():
        if lang not in translations:
            continue
        
        translation = translations[lang]
        
        # Pattern để tìm msgid và msgstr tương ứng
        # Xử lý cả trường hợp có fuzzy và không có
        pattern = rf'(#.*\n)*msgid "{re.escape(vi_text)}"\nmsgstr ""'
        replacement = f'msgid "{vi_text}"\nmsgstr "{translation}"'
        
        content = re.sub(pattern, replacement, content)
        
        # Xử lý trường hợp đã có msgstr nhưng rỗng hoặc sai
        pattern2 = rf'msgid "{re.escape(vi_text)}"\nmsgstr ".*"'
        content = re.sub(pattern2, replacement, content)
    
    # Xóa các fuzzy flags
    content = re.sub(r'#, fuzzy\n(#\| msgid "[^"]*"\n)*', '', content)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Updated {filepath}")

def main():
    base_dir = Path(__file__).resolve().parent.parent
    locale_dir = base_dir / 'locale'
    
    for lang in ['en', 'de']:
        po_file = locale_dir / lang / 'LC_MESSAGES' / 'django.po'
        if po_file.exists():
            update_po_file(str(po_file), lang)
    
    # Tiếng Việt thì msgstr = msgid (giữ nguyên)
    vi_po = locale_dir / 'vi' / 'LC_MESSAGES' / 'django.po'
    if vi_po.exists():
        with open(vi_po, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Với tiếng Việt, copy msgid vào msgstr nếu rỗng
        for vi_text in TRANSLATIONS.keys():
            pattern = rf'msgid "{re.escape(vi_text)}"\nmsgstr ""'
            replacement = f'msgid "{vi_text}"\nmsgstr "{vi_text}"'
            content = re.sub(pattern, replacement, content)
        
        # Xóa fuzzy
        content = re.sub(r'#, fuzzy\n(#\| msgid "[^"]*"\n)*', '', content)
        
        with open(vi_po, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"Updated {vi_po}")

if __name__ == '__main__':
    main()
