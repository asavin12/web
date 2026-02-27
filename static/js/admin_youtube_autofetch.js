/**
 * YouTube Auto-fetch — Admin helper script
 * Tự động lấy thông tin video khi nhập YouTube ID/URL
 * Hoạt động với field youtube_id (id_youtube_id trong DOM)
 */
(function() {
    'use strict';

    document.addEventListener('DOMContentLoaded', function() {
        var idInput = document.getElementById('id_youtube_id');
        if (!idInput) return;

        var fetchBtn = document.createElement('button');
        fetchBtn.type = 'button';
        fetchBtn.textContent = '🔄 Lấy thông tin YouTube';
        fetchBtn.style.cssText = 'margin-left: 10px; padding: 6px 12px; background: #417690; color: white; border: none; border-radius: 4px; cursor: pointer;';
        fetchBtn.addEventListener('click', function() {
            var rawValue = idInput.value.trim();
            if (!rawValue) {
                alert('Vui lòng nhập YouTube URL hoặc Video ID trước');
                return;
            }
            fetchBtn.textContent = '⏳ Đang xử lý...';
            fetchBtn.disabled = true;

            // Extract video ID from URL or use raw value as ID
            var videoId = rawValue;
            var match = rawValue.match(/(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([^&?\s]+)/);
            if (match) {
                videoId = match[1];
                // Update the field with clean ID
                idInput.value = videoId;
            }

            if (!videoId || videoId.length < 5) {
                alert('Video ID không hợp lệ');
                fetchBtn.textContent = '🔄 Lấy thông tin YouTube';
                fetchBtn.disabled = false;
                return;
            }

            // Set thumbnail if exists and empty
            var thumbInput = document.getElementById('id_thumbnail');
            if (thumbInput && !thumbInput.value) {
                thumbInput.value = 'https://img.youtube.com/vi/' + videoId + '/maxresdefault.jpg';
            }

            fetchBtn.textContent = '✅ Đã xử lý ID';
            fetchBtn.disabled = false;
            setTimeout(function() {
                fetchBtn.textContent = '🔄 Lấy thông tin YouTube';
            }, 2000);
        });

        idInput.parentNode.appendChild(fetchBtn);
    });
})();
