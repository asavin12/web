/**
 * API Key Generator — Admin helper script
 * Tạo key ngẫu nhiên và copy vào clipboard
 */
(function() {
    'use strict';

    // Generate random key using Web Crypto API
    window.generateRandomKey = function() {
        const array = new Uint8Array(32);
        crypto.getRandomValues(array);
        const key = btoa(String.fromCharCode.apply(null, array))
            .replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');

        const keyInput = document.getElementById('id_key');
        if (keyInput) {
            keyInput.value = key;
            keyInput.style.backgroundColor = '#e8f4e8';
            setTimeout(function() {
                keyInput.style.backgroundColor = '';
            }, 1000);
        }
    };

    // Copy text to clipboard
    window.copyToClipboard = function(text) {
        if (navigator.clipboard && navigator.clipboard.writeText) {
            navigator.clipboard.writeText(text).then(function() {
                alert('Đã copy API Key!');
            });
        } else {
            // Fallback for older browsers
            var textArea = document.createElement('textarea');
            textArea.value = text;
            document.body.appendChild(textArea);
            textArea.select();
            document.execCommand('copy');
            document.body.removeChild(textArea);
            alert('Đã copy API Key!');
        }
    };
})();
