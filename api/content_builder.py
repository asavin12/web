"""
Content Builder — Chuyển đổi dữ liệu cấu trúc thành HTML chuẩn SEO

Cho phép n8n / AI gửi dữ liệu dạng JSON có cấu trúc,
tự động sinh HTML hoàn chỉnh tuân thủ SEO_CONTENT_TEMPLATE.md.

Hỗ trợ:
  - Bảng so sánh (comparison table)
  - Bảng dữ liệu (data table)
  - Bảng thông tin (info table / key-value)
  - Danh sách có thứ tự / không thứ tự
  - Blockquote / tips
  - Hình ảnh, video nhúng
  - Mục lục tự động
  - Accordion / FAQ schema
  - Đoạn code

Tham chiếu: docs/CONTENT_BUILDER_SCHEMA.md
"""

import re
from typing import Any
from core.utils import vietnamese_slugify


# ═══════════════════════════════════════════════════════════════
# BLOCK RENDERERS — mỗi hàm render 1 loại block thành HTML
# ═══════════════════════════════════════════════════════════════

def _render_paragraph(block: dict) -> str:
    """Render khối paragraph: {"type": "paragraph", "text": "..."}"""
    text = block.get('text', '')
    if not text:
        return ''
    return f'<p>{text}</p>'


def _render_heading(block: dict) -> str:
    """
    Render heading block:
    {"type": "heading", "level": 2, "text": "...", "id": "custom-id"}
    """
    level = block.get('level', 2)
    if level < 2:
        level = 2  # Never H1
    if level > 4:
        level = 4
    text = block.get('text', '')
    slug_id = block.get('id') or vietnamese_slugify(text, max_length=80)
    return f'<h{level} id="{slug_id}">{text}</h{level}>'


def _render_table(block: dict) -> str:
    """
    Render bảng dữ liệu.
    
    Format 1 — headers + rows (standard table):
    {
        "type": "table",
        "caption": "Bảng so sánh...",            # optional
        "headers": ["Tiêu chí", "A", "B"],
        "rows": [
            ["Giá", "100€", "200€"],
            ["Thời gian", "6 tháng", "12 tháng"]
        ],
        "highlight_first_col": true               # optional — bold cột đầu
    }
    
    Format 2 — key-value info table:
    {
        "type": "info_table",
        "caption": "Thông tin chương trình",
        "data": {
            "Tên chương trình": "DAAD Scholarship",
            "Hạn nộp": "15/10/2026",
            "Website": "<a href='...'>daad.de</a>"
        }
    }
    """
    table_type = block.get('type', 'table')
    caption = block.get('caption', '')
    
    if table_type == 'info_table':
        return _render_info_table(block)
    
    headers = block.get('headers', [])
    rows = block.get('rows', [])
    highlight_first = block.get('highlight_first_col', False)
    
    if not headers and not rows:
        return ''
    
    parts = ['<table>']
    
    if caption:
        parts.append(f'  <caption>{caption}</caption>')
    
    # Thead
    if headers:
        parts.append('  <thead>')
        parts.append('    <tr>')
        for h in headers:
            parts.append(f'      <th>{h}</th>')
        parts.append('    </tr>')
        parts.append('  </thead>')
    
    # Tbody
    if rows:
        parts.append('  <tbody>')
        for row in rows:
            parts.append('    <tr>')
            for i, cell in enumerate(row):
                if i == 0 and highlight_first:
                    parts.append(f'      <td><strong>{cell}</strong></td>')
                else:
                    parts.append(f'      <td>{cell}</td>')
            parts.append('    </tr>')
        parts.append('  </tbody>')
    
    parts.append('</table>')
    return '\n'.join(parts)


def _render_info_table(block: dict) -> str:
    """Render bảng key-value (2 cột: thuộc tính — giá trị)."""
    data = block.get('data', {})
    caption = block.get('caption', '')
    
    if not data:
        return ''
    
    parts = ['<table>']
    
    if caption:
        parts.append(f'  <caption>{caption}</caption>')
    
    parts.append('  <thead>')
    parts.append('    <tr>')
    parts.append('      <th>Thông tin</th>')
    parts.append('      <th>Chi tiết</th>')
    parts.append('    </tr>')
    parts.append('  </thead>')
    parts.append('  <tbody>')
    
    for key, value in data.items():
        parts.append('    <tr>')
        parts.append(f'      <td><strong>{key}</strong></td>')
        parts.append(f'      <td>{value}</td>')
        parts.append('    </tr>')
    
    parts.append('  </tbody>')
    parts.append('</table>')
    return '\n'.join(parts)


def _render_comparison_table(block: dict) -> str:
    """
    Render bảng so sánh với ✅/❌ support.
    
    {
        "type": "comparison_table",
        "caption": "So sánh TestDaF vs Goethe",
        "subjects": ["TestDaF", "Goethe"],
        "criteria": [
            {"label": "Đối tượng", "values": ["Sinh viên ĐH", "Mọi đối tượng"]},
            {"label": "Hình thức nói", "values": ["Với máy tính", "Với giám khảo"]},
            {"label": "Quốc tế", "values": [true, true]},
            {"label": "Thi online", "values": [false, true]}
        ]
    }
    """
    subjects = block.get('subjects', [])
    criteria = block.get('criteria', [])
    caption = block.get('caption', '')
    
    if not subjects or not criteria:
        return ''
    
    parts = ['<table>']
    
    if caption:
        parts.append(f'  <caption>{caption}</caption>')
    
    # Header
    parts.append('  <thead>')
    parts.append('    <tr>')
    parts.append('      <th>Tiêu chí</th>')
    for s in subjects:
        parts.append(f'      <th>{s}</th>')
    parts.append('    </tr>')
    parts.append('  </thead>')
    
    # Body
    parts.append('  <tbody>')
    for c in criteria:
        parts.append('    <tr>')
        parts.append(f'      <td><strong>{c.get("label", "") or c.get("name", "")}</strong></td>')
        for v in c.get('values', []):
            if isinstance(v, bool):
                cell = '✅' if v else '❌'
            else:
                cell = str(v)
            parts.append(f'      <td>{cell}</td>')
        parts.append('    </tr>')
    parts.append('  </tbody>')
    
    parts.append('</table>')
    return '\n'.join(parts)


def _render_list(block: dict) -> str:
    """
    Render danh sách.
    
    {
        "type": "list",
        "ordered": false,
        "items": [
            "Item text đơn giản",
            {"title": "Tiêu đề bold", "text": "Mô tả chi tiết"},
            {"text": "Chỉ có text", "sub_items": ["a", "b", "c"]}
        ]
    }
    """
    ordered = block.get('ordered', False)
    items = block.get('items', [])
    
    if not items:
        return ''
    
    tag = 'ol' if ordered else 'ul'
    parts = [f'<{tag}>']
    
    for item in items:
        if isinstance(item, str):
            parts.append(f'  <li>{item}</li>')
        elif isinstance(item, dict):
            title = item.get('title', '')
            text = item.get('text', '')
            sub_items = item.get('sub_items', [])
            
            li_content = ''
            if title:
                li_content += f'<strong>{title}:</strong> '
            li_content += text
            
            if sub_items:
                li_content += '\n    <ul>'
                for si in sub_items:
                    li_content += f'\n      <li>{si}</li>'
                li_content += '\n    </ul>'
            
            parts.append(f'  <li>{li_content}</li>')
    
    parts.append(f'</{tag}>')
    return '\n'.join(parts)


def _render_blockquote(block: dict) -> str:
    """
    Render blockquote / tip / warning.
    
    {
        "type": "blockquote",
        "style": "tip",          # tip, warning, note, quote
        "text": "Nội dung...",
        "author": "Nguồn trích dẫn"   # optional, cho style=quote
    }
    """
    text = block.get('text', '')
    style = block.get('style', 'note')
    author = block.get('author', '')
    
    if not text:
        return ''
    
    icons = {
        'tip': '💡 Mẹo',
        'warning': '⚠️ Lưu ý quan trọng',
        'note': '📝 Ghi chú',
        'important': '🔴 Quan trọng',
        'success': '✅ Kết quả',
        'quote': '',
    }
    
    prefix = icons.get(style, '')
    
    if style == 'quote':
        inner = f'<p>{text}</p>'
        if author:
            inner += f'\n  <footer>— {author}</footer>'
        return f'<blockquote>\n  {inner}\n</blockquote>'
    
    if prefix:
        return f'<blockquote>\n  <p><strong>{prefix}:</strong> {text}</p>\n</blockquote>'
    
    return f'<blockquote>\n  <p>{text}</p>\n</blockquote>'


def _render_image(block: dict) -> str:
    """
    Render hình ảnh.
    
    {
        "type": "image",
        "src": "/media/...",
        "alt": "Mô tả hình ảnh",
        "caption": "Chú thích"
    }
    """
    src = block.get('src', '')
    alt = block.get('alt', '')
    caption = block.get('caption', '')
    
    if not src:
        return ''
    
    if caption:
        return (
            f'<figure>\n'
            f'  <img src="{src}" alt="{alt}" loading="lazy">\n'
            f'  <figcaption>{caption}</figcaption>\n'
            f'</figure>'
        )
    
    return f'<img src="{src}" alt="{alt}" loading="lazy">'


def _render_video(block: dict) -> str:
    """
    Render video nhúng.
    
    {
        "type": "video",
        "youtube_id": "dQw4w9WgXcQ",
        "title": "Tiêu đề video",
        "caption": "Mô tả"
    }
    """
    youtube_id = block.get('youtube_id', '')
    url = block.get('url', '')
    title = block.get('title', 'Video')
    caption = block.get('caption', '')
    
    if not youtube_id and not url:
        return ''
    
    if youtube_id:
        src = f'https://www.youtube.com/embed/{youtube_id}'
    else:
        src = url
    
    iframe = f'<iframe src="{src}" title="{title}" allowfullscreen></iframe>'
    
    if caption:
        return f'<figure>\n  {iframe}\n  <figcaption>{caption}</figcaption>\n</figure>'
    
    return iframe


def _render_code(block: dict) -> str:
    """
    Render code block.
    
    {
        "type": "code",
        "language": "python",
        "code": "print('hello')"
    }
    """
    language = block.get('language', '')
    code = block.get('code', '')
    
    if not code:
        return ''
    
    # Escape HTML in code
    code = code.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    
    lang_class = f' class="language-{language}"' if language else ''
    return f'<pre><code{lang_class}>{code}</code></pre>'


def _render_faq(block: dict) -> str:
    """
    Render FAQ section (schema.org FAQPage).
    
    {
        "type": "faq",
        "items": [
            {"question": "Câu hỏi 1?", "answer": "Trả lời 1"},
            {"question": "Câu hỏi 2?", "answer": "Trả lời 2"}
        ]
    }
    """
    import json as _json
    items = block.get('items', [])
    
    if not items:
        return ''
    
    # Render as details/summary accordion
    parts = ['<div class="faq-section">']
    faq_schema_items = []
    
    for item in items:
        q = item.get('question', '')
        a = item.get('answer', '')
        if q and a:
            parts.append(f'<details>')
            parts.append(f'  <summary><strong>{q}</strong></summary>')
            if '<' in a:
                parts.append(f'  <div>{a}</div>')
            else:
                parts.append(f'  <p>{a}</p>')
            parts.append(f'</details>')
            faq_schema_items.append({
                "@type": "Question",
                "name": q,
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": re.sub(r'<[^>]+>', '', a)
                }
            })
    
    parts.append('</div>')
    
    # Add JSON-LD structured data for Google
    if faq_schema_items:
        schema = {
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": faq_schema_items
        }
        parts.append(f'<script type="application/ld+json">{_json.dumps(schema, ensure_ascii=False)}</script>')
    
    return '\n'.join(parts)


def _render_divider(block: dict) -> str:
    """Render horizontal rule."""
    return '<hr>'


def _render_callout(block: dict) -> str:
    """
    Render a styled callout box (renders as blockquote with icon).
    
    {
        "type": "callout",
        "style": "tip",
        "title": "Tiêu đề callout",
        "text": "Nội dung chi tiết."
    }
    """
    style = block.get('style', 'info')
    icons = {'tip': '💡', 'warning': '⚠️', 'info': '📌', 'important': '❗'}
    icon = icons.get(style, block.get('icon', '📌'))
    title = block.get('title', '')
    text = block.get('text', '')
    
    if title:
        inner = f'<strong>{icon} {title}</strong> {text}'
    else:
        inner = f'{icon} {text}'
    
    return f'<blockquote class="callout callout-{style}">\n  <p>{inner}</p>\n</blockquote>'


# ═══════════════════════════════════════════════════════════════
# BLOCK REGISTRY
# ═══════════════════════════════════════════════════════════════

BLOCK_RENDERERS = {
    'paragraph': _render_paragraph,
    'heading': _render_heading,
    'table': _render_table,
    'info_table': _render_info_table,
    'comparison_table': _render_comparison_table,
    'list': _render_list,
    'blockquote': _render_blockquote,
    'image': _render_image,
    'video': _render_video,
    'code': _render_code,
    'faq': _render_faq,
    'divider': _render_divider,
    'callout': _render_callout,
    'html': lambda b: b.get('html', ''),  # Raw HTML passthrough
}


# ═══════════════════════════════════════════════════════════════
# TOC GENERATOR — Tự động tạo mục lục từ headings
# ═══════════════════════════════════════════════════════════════

def _generate_toc(blocks: list[dict]) -> str:
    """Tạo nav mục lục tự động từ danh sách blocks."""
    headings = []
    for b in blocks:
        if b.get('type') == 'heading' and b.get('level', 2) == 2:
            text = b.get('text', '')
            slug_id = b.get('id') or vietnamese_slugify(text, max_length=80)
            headings.append((slug_id, text))
    
    if len(headings) < 2:
        return ''
    
    parts = ['<nav>', '  <h2>Nội dung bài viết</h2>', '  <ul>']
    for slug_id, text in headings:
        parts.append(f'    <li><a href="#{slug_id}">{text}</a></li>')
    parts.append('  </ul>')
    parts.append('</nav>')
    parts.append('<hr>')
    
    return '\n'.join(parts)


# ═══════════════════════════════════════════════════════════════
# MAIN BUILDER — Xử lý toàn bộ structured content → HTML
# ═══════════════════════════════════════════════════════════════

def build_article_content(data: dict) -> dict:
    """
    Chuyển đổi dữ liệu cấu trúc thành HTML chuẩn SEO.
    
    Input:
    {
        "lead": "Đoạn mở đầu chứa từ khóa...",
        "toc": true,                              # auto-generate TOC
        "blocks": [
            {"type": "heading", "level": 2, "text": "Phần 1"},
            {"type": "paragraph", "text": "Nội dung..."},
            {"type": "table", "headers": [...], "rows": [...]},
            {"type": "list", "ordered": true, "items": [...]},
            {"type": "blockquote", "style": "tip", "text": "..."},
            {"type": "comparison_table", "subjects": [...], "criteria": [...]},
            {"type": "info_table", "data": {...}},
            {"type": "image", "src": "...", "alt": "..."},
            ...
        ],
        "conclusion": {
            "text": "Tóm tắt...",
            "cta": "Lời kêu gọi hành động..."
        }
    }
    
    Output:
    {
        "success": true,
        "html": "<p>.....</p><nav>...</nav>...<h2 id='ket-luan'>Kết luận</h2>...",
        "word_count": 1234,
        "heading_count": 5,
        "table_count": 2,
        "list_count": 3,
        "has_toc": true,
        "has_conclusion": true,
        "block_summary": ["paragraph", "heading", "table", ...]
    }
    """
    lead = data.get('lead', '')
    auto_toc = data.get('toc', True)
    blocks = data.get('blocks', [])
    conclusion = data.get('conclusion', {})
    
    errors = []
    
    if not blocks and not lead:
        errors.append('Cần ít nhất "lead" hoặc "blocks"')
    
    if errors:
        return {'success': False, 'errors': errors}
    
    html_parts = []
    block_summary = []
    stats = {
        'heading_count': 0,
        'table_count': 0,
        'list_count': 0,
        'image_count': 0,
        'blockquote_count': 0,
    }
    
    # 1. Lead paragraph
    if lead:
        if '<' in lead:
            html_parts.append(lead)
        else:
            html_parts.append(f'<p>{lead}</p>')
        block_summary.append('lead')
    
    # 2. TOC (auto-generated from blocks)
    if auto_toc:
        toc_html = _generate_toc(blocks)
        if toc_html:
            html_parts.append('')
            html_parts.append(toc_html)
            block_summary.append('toc')
    
    # 3. Render each block
    for block in blocks:
        block_type = block.get('type', 'paragraph')
        renderer = BLOCK_RENDERERS.get(block_type)
        
        if not renderer:
            errors.append(f'Block type không hợp lệ: "{block_type}"')
            continue
        
        html = renderer(block)
        if html:
            html_parts.append('')
            html_parts.append(html)
            block_summary.append(block_type)
            
            # Track stats
            if block_type == 'heading':
                stats['heading_count'] += 1
            elif block_type in ('table', 'info_table', 'comparison_table'):
                stats['table_count'] += 1
            elif block_type == 'list':
                stats['list_count'] += 1
            elif block_type == 'image':
                stats['image_count'] += 1
            elif block_type in ('blockquote', 'callout'):
                stats['blockquote_count'] += 1
    
    # 4. Conclusion
    if conclusion:
        # Support both string and dict formats
        if isinstance(conclusion, str):
            conclusion_text = conclusion
            conclusion_cta = ''
        else:
            conclusion_text = conclusion.get('text', '')
            conclusion_cta = conclusion.get('cta', '')
        
        html_parts.append('')
        html_parts.append('<h2 id="ket-luan">Kết luận</h2>')
        stats['heading_count'] += 1
        block_summary.append('conclusion')
        
        if conclusion_text:
            html_parts.append('')
            # If it already contains HTML tags, use as-is; otherwise wrap in <p>
            if '<' in conclusion_text:
                html_parts.append(conclusion_text)
            else:
                html_parts.append(f'<p>{conclusion_text}</p>')
        
        if conclusion_cta:
            html_parts.append('')
            html_parts.append(
                f'<blockquote>\n'
                f'  <p><strong>📌 Bạn thấy bài viết hữu ích?</strong> {conclusion_cta}</p>\n'
                f'</blockquote>'
            )
    
    # Assemble
    full_html = '\n'.join(html_parts).strip()
    
    # Calculate word count
    text_only = re.sub(r'<[^>]+>', ' ', full_html)
    word_count = len(text_only.split())
    
    return {
        'success': True,
        'html': full_html,
        'word_count': word_count,
        'has_toc': auto_toc and bool(_generate_toc(blocks)),
        'has_conclusion': bool(conclusion),
        'block_summary': block_summary,
        **stats,
    }


def get_available_block_types() -> dict:
    """Trả về danh sách các block types có sẵn với schema mẫu."""
    return {
        'paragraph': {
            'description': 'Đoạn văn bản',
            'schema': {'type': 'paragraph', 'text': 'Nội dung đoạn văn...'},
        },
        'heading': {
            'description': 'Tiêu đề (H2, H3, H4)',
            'schema': {'type': 'heading', 'level': 2, 'text': 'Tiêu đề phần', 'id': 'tieu-de-phan'},
        },
        'table': {
            'description': 'Bảng dữ liệu chuẩn',
            'schema': {
                'type': 'table',
                'caption': 'Mô tả bảng (tùy chọn)',
                'headers': ['Cột 1', 'Cột 2', 'Cột 3'],
                'rows': [
                    ['Dữ liệu 1a', 'Dữ liệu 1b', 'Dữ liệu 1c'],
                    ['Dữ liệu 2a', 'Dữ liệu 2b', 'Dữ liệu 2c'],
                ],
                'highlight_first_col': True,
            },
        },
        'info_table': {
            'description': 'Bảng thông tin key-value (2 cột)',
            'schema': {
                'type': 'info_table',
                'caption': 'Thông tin chương trình',
                'data': {
                    'Tên': 'Giá trị',
                    'Hạn nộp': '15/10/2026',
                    'Website': '<a href="https://example.com">example.com</a>',
                },
            },
        },
        'comparison_table': {
            'description': 'Bảng so sánh với ✅/❌',
            'schema': {
                'type': 'comparison_table',
                'caption': 'So sánh A vs B',
                'subjects': ['Lựa chọn A', 'Lựa chọn B'],
                'criteria': [
                    {'label': 'Tiêu chí 1', 'values': ['Giá trị A', 'Giá trị B']},
                    {'label': 'Hỗ trợ X', 'values': [True, False]},
                ],
            },
        },
        'list': {
            'description': 'Danh sách có/không thứ tự',
            'schema': {
                'type': 'list',
                'ordered': False,
                'items': [
                    'Item đơn giản',
                    {'title': 'Tiêu đề bold', 'text': 'Mô tả chi tiết'},
                    {'text': 'Có danh sách con', 'sub_items': ['a', 'b']},
                ],
            },
        },
        'blockquote': {
            'description': 'Trích dẫn / mẹo / lưu ý',
            'schema': {
                'type': 'blockquote',
                'style': 'tip',  # tip, warning, note, important, success, quote
                'text': 'Nội dung mẹo hoặc lưu ý...',
            },
        },
        'callout': {
            'description': 'Hộp nổi bật với icon',
            'schema': {
                'type': 'callout',
                'icon': '📌',
                'title': 'Tiêu đề',
                'text': 'Nội dung chi tiết',
            },
        },
        'image': {
            'description': 'Hình ảnh với alt text và caption',
            'schema': {
                'type': 'image',
                'src': '/media/...',
                'alt': 'Mô tả hình ảnh (5-15 từ)',
                'caption': 'Chú thích hiển thị dưới ảnh',
            },
        },
        'video': {
            'description': 'Video nhúng YouTube',
            'schema': {
                'type': 'video',
                'youtube_id': 'VIDEO_ID',
                'title': 'Tiêu đề video',
                'caption': 'Mô tả video (tùy chọn)',
            },
        },
        'faq': {
            'description': 'Câu hỏi thường gặp (FAQ schema)',
            'schema': {
                'type': 'faq',
                'items': [
                    {'question': 'Câu hỏi 1?', 'answer': 'Trả lời 1'},
                    {'question': 'Câu hỏi 2?', 'answer': 'Trả lời 2'},
                ],
            },
        },
        'code': {
            'description': 'Khối code',
            'schema': {
                'type': 'code',
                'language': 'python',
                'code': 'print("Hello")',
            },
        },
        'divider': {
            'description': 'Đường kẻ phân cách',
            'schema': {'type': 'divider'},
        },
        'html': {
            'description': 'HTML tùy chỉnh (passthrough)',
            'schema': {'type': 'html', 'html': '<div>Custom HTML</div>'},
        },
    }
