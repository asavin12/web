/**
 * YouTube Auto-fetch — Admin helper script
 * Tự động lấy thông tin video khi nhập YouTube URL
 */
(function() {
    'use strict';

    document.addEventListener('DOMContentLoaded', function() {
        var urlInput = document.getElementById('id_youtube_url');
        if (!urlInput) return;

        var fetchBtn = document.createElement('button');
        fetchBtn.type = 'button';
        fetchBtn.textContent = '🔄 Lấy thông tin YouTube';
        fetchBtn.style.cssText = 'margin-left: 10px; padding: 6px 12px; background: #417690; color: white; border: none; border-radius: 4px; cursor: pointer;';
        fetchBtn.addEventListener('click', function() {
            var url = urlInput.value.trim();
            if (!url) {
                alert('Vui lòng nhập YouTube URL trước');
                return;
            }
            fetchBtn.textContent = '⏳ Đang lấy...';
            fetchBtn.disabled = true;

            // Extract video ID
            var videoId = '';
            var match = url.match(/(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([^&?\s]+)/);
            if (match) videoId = match[1];

            if (!videoId) {
                alert('Không tìm thấy Video ID trong URL');
                fetchBtn.textContent = '🔄 Lấy thông tin YouTube';
                fetchBtn.disabled = false;
                return;
            }

            // Set youtube_id field if exists
            var idInput = document.getElementById('id_youtube_id');
            if (idInput && !idInput.value) {
                idInput.value = videoId;
            }

            // Set thumbnail if exists
            var thumbInput = document.getElementById('id_thumbnail');
            if (thumbInput && !thumbInput.value) {
                thumbInput.value = 'https://img.youtube.com/vi/' + videoId + '/maxresdefault.jpg';
            }

            fetchBtn.textContent = '✅ Đã lấy thông tin';
            fetchBtn.disabled = false;
            setTimeout(function() {
                fetchBtn.textContent = '🔄 Lấy thông tin YouTube';
            }, 2000);
        });

        urlInput.parentNode.appendChild(fetchBtn);
    });
})();
