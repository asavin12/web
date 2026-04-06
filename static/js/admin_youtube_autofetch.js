/**
 * YouTube Auto-fetch — Admin helper script
 * Tự động lấy thông tin video khi nhập YouTube ID/URL
 * Hoạt động với field youtube_id (id_youtube_id trong DOM)
 * Dùng cho cả core.Video (legacy) và mediastream.StreamMedia
 */
(function() {
    'use strict';

    function extractYouTubeId(raw) {
        if (!raw) return '';
        raw = raw.trim();
        var match = raw.match(/(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/|youtube\.com\/v\/)([a-zA-Z0-9_-]{11})/);
        if (match) return match[1];
        if (/^[a-zA-Z0-9_-]{11}$/.test(raw)) return raw;
        return '';
    }

    document.addEventListener('DOMContentLoaded', function() {
        var idInput = document.getElementById('id_youtube_id');
        if (!idInput) return;

        // --- Create fetch button ---
        var fetchBtn = document.createElement('button');
        fetchBtn.type = 'button';
        fetchBtn.textContent = '🔄 Lấy thông tin YouTube';
        fetchBtn.style.cssText = 'margin-left: 10px; padding: 6px 12px; background: #c4302b; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 13px;';
        
        // --- Create preview container ---
        var previewDiv = document.createElement('div');
        previewDiv.id = 'yt-live-preview';
        previewDiv.style.cssText = 'margin-top: 10px; display: none;';

        function showPreview(videoId) {
            if (!videoId) {
                previewDiv.style.display = 'none';
                return;
            }
            previewDiv.innerHTML = 
                '<div style="display:flex;gap:12px;align-items:flex-start;background:#f8f9fa;padding:12px;border-radius:8px;border:1px solid #e0e0e0;">' +
                '<img src="https://img.youtube.com/vi/' + videoId + '/mqdefault.jpg" ' +
                'style="width:180px;height:auto;border-radius:6px;flex-shrink:0;" />' +
                '<div>' +
                '<div style="font-size:12px;color:#666;margin-bottom:4px;">Video ID: <code>' + videoId + '</code></div>' +
                '<a href="https://www.youtube.com/watch?v=' + videoId + '" target="_blank" ' +
                'style="color:#c4302b;font-weight:bold;text-decoration:none;">▶ Xem trên YouTube</a>' +
                '<div style="font-size:12px;color:#888;margin-top:6px;">💡 Nhấn "Lưu" để tự động lấy tiêu đề, mô tả, thời lượng</div>' +
                '</div></div>';
            previewDiv.style.display = 'block';
        }

        // Auto-set storage_type and media_type when YouTube ID is entered
        function setYouTubeMode() {
            var storageSelect = document.getElementById('id_storage_type');
            var mediaSelect = document.getElementById('id_media_type');
            if (storageSelect) storageSelect.value = 'youtube';
            if (mediaSelect) mediaSelect.value = 'video';
        }

        fetchBtn.addEventListener('click', function() {
            var rawValue = idInput.value.trim();
            if (!rawValue) {
                alert('Vui lòng nhập YouTube URL hoặc Video ID trước');
                return;
            }
            
            var videoId = extractYouTubeId(rawValue);
            if (!videoId) {
                alert('Không thể trích xuất YouTube Video ID. Kiểm tra lại URL.');
                return;
            }

            // Clean the input
            idInput.value = videoId;
            setYouTubeMode();
            showPreview(videoId);

            fetchBtn.textContent = '✅ Đã nhận ID: ' + videoId;
            setTimeout(function() {
                fetchBtn.textContent = '🔄 Lấy thông tin YouTube';
            }, 2000);
        });

        idInput.parentNode.appendChild(fetchBtn);
        // Insert preview after the field row
        var fieldRow = idInput.closest('.form-row') || idInput.parentNode;
        fieldRow.parentNode.insertBefore(previewDiv, fieldRow.nextSibling);

        // Show preview on paste/input
        idInput.addEventListener('input', function() {
            var vid = extractYouTubeId(idInput.value);
            if (vid && vid.length === 11) {
                showPreview(vid);
                setYouTubeMode();
            } else {
                previewDiv.style.display = 'none';
            }
        });

        // Show preview if already has value (edit mode)
        var existingId = extractYouTubeId(idInput.value);
        if (existingId) {
            showPreview(existingId);
        }

        // Auto-expand YouTube fieldset if youtube_id has value
        if (existingId) {
            var ytFieldset = idInput.closest('fieldset');
            if (ytFieldset && ytFieldset.classList.contains('collapsed')) {
                // Django admin collapse toggle
                var toggler = ytFieldset.querySelector('h2 a, .collapse-toggle');
                if (toggler) toggler.click();
            }
        }
    });
})();
