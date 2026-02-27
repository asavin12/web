"""
PostgreSQL Admin Views
Quản lý kết nối và cấu trúc database PostgreSQL
"""

from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.db import connection
from django.conf import settings
from django.views.decorators.http import require_http_methods
import json
import secrets
import string


def generate_secure_password(length=32, include_special=True):
    """Tạo password bảo mật cao"""
    if length < 16:
        length = 16
    
    lowercase = string.ascii_lowercase
    uppercase = string.ascii_uppercase
    digits = string.digits
    special = '!@#$%^&*()_+-=' if include_special else ''
    
    password = [
        secrets.choice(lowercase),
        secrets.choice(uppercase),
        secrets.choice(digits),
    ]
    
    if include_special:
        password.append(secrets.choice(special))
    
    all_chars = lowercase + uppercase + digits + special
    remaining = length - len(password)
    password.extend(secrets.choice(all_chars) for _ in range(remaining))
    
    # Shuffle using secrets for cryptographic randomness
    result = list(password)
    for i in range(len(result) - 1, 0, -1):
        j = secrets.randbelow(i + 1)
        result[i], result[j] = result[j], result[i]
    
    return ''.join(result)


@staff_member_required
def postgres_dashboard(request):
    """Dashboard quản lý PostgreSQL"""
    context = {
        'title': 'PostgreSQL Dashboard',
    }
    
    try:
        with connection.cursor() as cursor:
            # Database info
            cursor.execute("SELECT version();")
            db_version = cursor.fetchone()[0]
            
            # Database size
            cursor.execute("""
                SELECT pg_size_pretty(pg_database_size(current_database()));
            """)
            db_size = cursor.fetchone()[0]
            
            # Connection info
            cursor.execute("SELECT current_database(), current_user;")
            db_info = cursor.fetchone()
            
            # Table count
            cursor.execute("""
                SELECT COUNT(*) FROM information_schema.tables 
                WHERE table_schema = 'public';
            """)
            table_count = cursor.fetchone()[0]
            
            # Active connections
            cursor.execute("""
                SELECT COUNT(*) FROM pg_stat_activity 
                WHERE datname = current_database();
            """)
            active_connections = cursor.fetchone()[0]
            
            context.update({
                'db_version': db_version,
                'db_size': db_size,
                'db_name': db_info[0],
                'db_user': db_info[1],
                'db_host': settings.DATABASES['default'].get('HOST', 'localhost'),
                'db_port': settings.DATABASES['default'].get('PORT', '5432'),
                'table_count': table_count,
                'active_connections': active_connections,
                'connection_status': 'connected',
            })
            
    except Exception as e:
        context.update({
            'connection_status': 'error',
            'error_message': str(e),
        })
    
    return render(request, 'admin/postgres/dashboard.html', context)


@staff_member_required
def postgres_tables(request):
    """Danh sách tables và thống kê"""
    tables_info = []
    
    try:
        with connection.cursor() as cursor:
            # Get all tables with row count and size
            cursor.execute("""
                SELECT 
                    t.table_name,
                    pg_size_pretty(pg_total_relation_size(quote_ident(t.table_name)::text)) as size,
                    (SELECT COUNT(*) FROM information_schema.columns c 
                     WHERE c.table_name = t.table_name AND c.table_schema = 'public') as column_count
                FROM information_schema.tables t
                WHERE t.table_schema = 'public'
                ORDER BY t.table_name;
            """)
            
            for row in cursor.fetchall():
                table_name = row[0]
                # Get row count
                try:
                    cursor.execute(f'SELECT COUNT(*) FROM "{table_name}";')
                    row_count = cursor.fetchone()[0]
                except:
                    row_count = 'N/A'
                
                tables_info.append({
                    'name': table_name,
                    'size': row[1],
                    'columns': row[2],
                    'rows': row_count,
                })
                
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    
    if request.headers.get('Accept') == 'application/json':
        return JsonResponse({'tables': tables_info})
    
    return render(request, 'admin/postgres/tables.html', {
        'title': 'Database Tables',
        'tables': tables_info,
    })


@staff_member_required
def postgres_table_schema(request, table_name):
    """Chi tiết schema của một table — enriched with PK/FK/UNIQUE/INDEX badges, constraints, SQL, sample data"""
    import re as _re
    columns = []
    indexes = []
    foreign_keys = []
    constraints = []
    create_sql = ''
    sample_data = []
    sample_headers = []
    row_count = 0
    table_size = '-'

    try:
        with connection.cursor() as cursor:
            # ── Row count & size ──
            try:
                cursor.execute(f'SELECT COUNT(*) FROM "{table_name}";')
                row_count = cursor.fetchone()[0]
            except Exception:
                row_count = 0

            try:
                cursor.execute("SELECT pg_size_pretty(pg_total_relation_size(quote_ident(%s)::text));", [table_name])
                table_size = cursor.fetchone()[0]
            except Exception:
                table_size = '-'

            # ── Primary key columns ──
            pk_columns = set()
            cursor.execute("""
                SELECT a.attname
                FROM pg_index i
                JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)
                WHERE i.indrelid = %s::regclass AND i.indisprimary;
            """, [table_name])
            for r in cursor.fetchall():
                pk_columns.add(r[0])

            # ── Unique columns (from unique constraints, not PK) ──
            unique_columns = set()
            cursor.execute("""
                SELECT a.attname
                FROM pg_index i
                JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)
                WHERE i.indrelid = %s::regclass AND i.indisunique AND NOT i.indisprimary;
            """, [table_name])
            for r in cursor.fetchall():
                unique_columns.add(r[0])

            # ── Indexed columns ──
            indexed_columns = set()
            cursor.execute("""
                SELECT a.attname
                FROM pg_index i
                JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)
                WHERE i.indrelid = %s::regclass AND NOT i.indisprimary AND NOT i.indisunique;
            """, [table_name])
            for r in cursor.fetchall():
                indexed_columns.add(r[0])

            # ── Foreign key map: column → ref_table.ref_column ──
            fk_map = {}
            cursor.execute("""
                SELECT
                    kcu.column_name,
                    ccu.table_name AS foreign_table,
                    ccu.column_name AS foreign_column
                FROM information_schema.table_constraints AS tc
                JOIN information_schema.key_column_usage AS kcu
                    ON tc.constraint_name = kcu.constraint_name
                JOIN information_schema.constraint_column_usage AS ccu
                    ON ccu.constraint_name = tc.constraint_name
                WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_name = %s;
            """, [table_name])
            for r in cursor.fetchall():
                fk_map[r[0]] = f'{r[1]}.{r[2]}'

            # ── Columns with badges ──
            cursor.execute("""
                SELECT
                    column_name,
                    data_type,
                    character_maximum_length,
                    is_nullable,
                    column_default
                FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = %s
                ORDER BY ordinal_position;
            """, [table_name])

            for row in cursor.fetchall():
                col_name = row[0]
                columns.append({
                    'name': col_name,
                    'type': row[1],
                    'max_length': row[2],
                    'nullable': row[3],
                    'default': row[4],
                    'is_primary': col_name in pk_columns,
                    'is_foreign_key': col_name in fk_map,
                    'fk_ref': fk_map.get(col_name, ''),
                    'is_unique': col_name in unique_columns,
                    'is_indexed': col_name in indexed_columns,
                })

            # ── Indexes (parsed) ──
            cursor.execute("""
                SELECT
                    i.relname AS index_name,
                    ix.indisprimary,
                    ix.indisunique,
                    pg_get_indexdef(ix.indexrelid) AS indexdef,
                    array_agg(a.attname ORDER BY array_position(ix.indkey, a.attnum)) AS columns
                FROM pg_class t
                JOIN pg_index ix ON t.oid = ix.indrelid
                JOIN pg_class i ON i.oid = ix.indexrelid
                JOIN pg_attribute a ON a.attrelid = t.oid AND a.attnum = ANY(ix.indkey)
                WHERE t.relname = %s AND t.relkind = 'r'
                GROUP BY i.relname, ix.indisprimary, ix.indisunique, ix.indexrelid
                ORDER BY i.relname;
            """, [table_name])

            for row in cursor.fetchall():
                indexes.append({
                    'name': row[0],
                    'is_primary': row[1],
                    'is_unique': row[2],
                    'definition': row[3],
                    'columns': row[4] if row[4] else [],
                })

            # ── Foreign keys ──
            cursor.execute("""
                SELECT
                    tc.constraint_name,
                    kcu.column_name,
                    ccu.table_name AS foreign_table,
                    ccu.column_name AS foreign_column
                FROM information_schema.table_constraints AS tc
                JOIN information_schema.key_column_usage AS kcu
                    ON tc.constraint_name = kcu.constraint_name
                JOIN information_schema.constraint_column_usage AS ccu
                    ON ccu.constraint_name = tc.constraint_name
                WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_name = %s;
            """, [table_name])

            for row in cursor.fetchall():
                foreign_keys.append({
                    'name': row[0],
                    'column': row[1],
                    'ref_table': row[2],
                    'ref_column': row[3],
                })

            # ── Constraints (CHECK, EXCLUDE, etc.) ──
            cursor.execute("""
                SELECT
                    conname,
                    contype,
                    pg_get_constraintdef(oid) AS definition
                FROM pg_constraint
                WHERE conrelid = %s::regclass
                ORDER BY contype, conname;
            """, [table_name])

            type_map = {'c': 'CHECK', 'f': 'FOREIGN KEY', 'p': 'PRIMARY KEY', 'u': 'UNIQUE', 'x': 'EXCLUDE'}
            for row in cursor.fetchall():
                constraints.append({
                    'name': row[0],
                    'type': type_map.get(row[1], row[1]),
                    'definition': row[2],
                })

            # ── CREATE TABLE SQL ──
            try:
                col_defs = []
                for c in columns:
                    parts = [f'    "{c["name"]}"', c['type'].upper()]
                    if c['max_length']:
                        parts[-1] = f'{parts[-1]}({c["max_length"]})'
                    if c['nullable'] != 'YES':
                        parts.append('NOT NULL')
                    if c['default']:
                        parts.append(f'DEFAULT {c["default"]}')
                    col_defs.append(' '.join(parts))

                if pk_columns:
                    col_defs.append(f'    PRIMARY KEY ({", ".join(sorted(pk_columns))})')

                for fk in foreign_keys:
                    col_defs.append(
                        f'    FOREIGN KEY ("{fk["column"]}") REFERENCES "{fk["ref_table"]}" ("{fk["ref_column"]}")'
                    )

                create_sql = f'CREATE TABLE "{table_name}" (\n' + ',\n'.join(col_defs) + '\n);'
            except Exception:
                create_sql = ''

            # ── Sample data (first 10 rows) ──
            try:
                cursor.execute(f'SELECT * FROM "{table_name}" LIMIT 10;')
                sample_headers = [desc[0] for desc in cursor.description]
                sample_data = cursor.fetchall()
            except Exception:
                sample_data = []
                sample_headers = []

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

    # JSON export
    if request.GET.get('format') == 'json' or request.headers.get('Accept') == 'application/json':
        import datetime
        def _json_safe(obj):
            if isinstance(obj, (datetime.datetime, datetime.date)):
                return obj.isoformat()
            if isinstance(obj, bytes):
                return obj.hex()
            return str(obj)

        data = {
            'table': table_name,
            'row_count': row_count,
            'table_size': table_size,
            'columns': columns,
            'indexes': indexes,
            'foreign_keys': foreign_keys,
            'constraints': constraints,
            'create_sql': create_sql,
            'sample_headers': sample_headers,
            'sample_data': [[_json_safe(c) for c in row] for row in sample_data],
        }
        if request.GET.get('format') == 'json':
            response = HttpResponse(
                json.dumps(data, indent=2, ensure_ascii=False, default=_json_safe),
                content_type='application/json'
            )
            response['Content-Disposition'] = f'attachment; filename="{table_name}_schema.json"'
            return response
        return JsonResponse(data, json_dumps_params={'default': _json_safe})

    return render(request, 'admin/postgres/table_schema.html', {
        'title': f'{table_name} — Schema',
        'table_name': table_name,
        'columns': columns,
        'indexes': indexes,
        'foreign_keys': foreign_keys,
        'constraints': constraints,
        'create_sql': create_sql,
        'sample_data': sample_data,
        'sample_headers': sample_headers,
        'sample_count': len(sample_data),
        'row_count': row_count,
        'table_size': table_size,
    })


@staff_member_required
@require_http_methods(["GET", "POST"])
def generate_password(request):
    """API để tạo password bảo mật"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            length = int(data.get('length', 32))
            include_special = data.get('include_special', True)
        except:
            length = 32
            include_special = True
    else:
        length = int(request.GET.get('length', 32))
        include_special = request.GET.get('include_special', 'true').lower() == 'true'
    
    password = generate_secure_password(length, include_special)
    
    return JsonResponse({
        'password': password,
        'length': len(password),
        'has_special': include_special,
    })


@staff_member_required
def export_schema(request):
    """Export toàn bộ database schema"""
    schema_data = {
        'database': {},
        'tables': [],
    }
    
    try:
        with connection.cursor() as cursor:
            # Database info
            cursor.execute("SELECT version();")
            schema_data['database']['version'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT current_database();")
            schema_data['database']['name'] = cursor.fetchone()[0]
            
            cursor.execute("""
                SELECT pg_size_pretty(pg_database_size(current_database()));
            """)
            schema_data['database']['size'] = cursor.fetchone()[0]
            
            # Get all tables
            cursor.execute("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public' ORDER BY table_name;
            """)
            
            for (table_name,) in cursor.fetchall():
                table_info = {
                    'name': table_name,
                    'columns': [],
                    'indexes': [],
                    'foreign_keys': [],
                }
                
                # Columns
                cursor.execute("""
                    SELECT 
                        column_name,
                        data_type,
                        character_maximum_length,
                        is_nullable,
                        column_default
                    FROM information_schema.columns
                    WHERE table_schema = 'public' AND table_name = %s
                    ORDER BY ordinal_position;
                """, [table_name])
                
                for row in cursor.fetchall():
                    table_info['columns'].append({
                        'name': row[0],
                        'type': row[1],
                        'max_length': row[2],
                        'nullable': row[3] == 'YES',
                        'default': row[4],
                    })
                
                # Indexes
                cursor.execute("""
                    SELECT indexname, indexdef
                    FROM pg_indexes WHERE tablename = %s;
                """, [table_name])
                
                for row in cursor.fetchall():
                    table_info['indexes'].append({
                        'name': row[0],
                        'definition': row[1],
                    })
                
                # Foreign keys
                cursor.execute("""
                    SELECT
                        tc.constraint_name,
                        kcu.column_name,
                        ccu.table_name,
                        ccu.column_name
                    FROM information_schema.table_constraints tc
                    JOIN information_schema.key_column_usage kcu
                        ON tc.constraint_name = kcu.constraint_name
                    JOIN information_schema.constraint_column_usage ccu
                        ON ccu.constraint_name = tc.constraint_name
                    WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_name = %s;
                """, [table_name])
                
                for row in cursor.fetchall():
                    table_info['foreign_keys'].append({
                        'constraint': row[0],
                        'column': row[1],
                        'references_table': row[2],
                        'references_column': row[3],
                    })
                
                # Row count
                try:
                    cursor.execute(f'SELECT COUNT(*) FROM "{table_name}";')
                    table_info['row_count'] = cursor.fetchone()[0]
                except:
                    table_info['row_count'] = None
                
                schema_data['tables'].append(table_info)
                
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    
    # Return as JSON download
    if request.GET.get('format') == 'json':
        response = HttpResponse(
            json.dumps(schema_data, indent=2, ensure_ascii=False),
            content_type='application/json'
        )
        response['Content-Disposition'] = 'attachment; filename="database_schema.json"'
        return response
    
    return JsonResponse(schema_data)


@staff_member_required  
def test_connection(request):
    """Test kết nối PostgreSQL"""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1;")
            result = cursor.fetchone()
            
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            
            cursor.execute("SELECT current_database(), current_user;")
            db_info = cursor.fetchone()
            
            return JsonResponse({
                'status': 'success',
                'message': 'Kết nối PostgreSQL thành công!',
                'database': db_info[0],
                'user': db_info[1],
                'version': version.split(',')[0],
            })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Lỗi kết nối: {str(e)}',
        }, status=500)


@staff_member_required
@require_http_methods(["GET", "POST"])
def backup_database(request):
    """Backup database PostgreSQL - Tải về máy người dùng"""
    import subprocess
    import os
    import tempfile
    from datetime import datetime
    
    backup_dir = os.path.join(settings.BASE_DIR, 'backups')
    os.makedirs(backup_dir, exist_ok=True)
    
    if request.method == 'GET':
        # Nếu có download param, tải file từ server
        download_file = request.GET.get('download')
        if download_file:
            filepath = os.path.join(backup_dir, download_file)
            
            # Kiểm tra path traversal
            if not os.path.abspath(filepath).startswith(os.path.abspath(backup_dir)):
                return JsonResponse({'status': 'error', 'message': 'Invalid file path'}, status=400)
            
            if os.path.exists(filepath):
                with open(filepath, 'rb') as f:
                    response = HttpResponse(f.read(), content_type='application/sql')
                    response['Content-Disposition'] = f'attachment; filename="{download_file}"'
                    return response
            return JsonResponse({'status': 'error', 'message': 'File not found'}, status=404)
        
        # Lấy danh sách backups trên server
        backups = []
        for f in os.listdir(backup_dir):
            if f.endswith('.sql') or f.endswith('.dump'):
                filepath = os.path.join(backup_dir, f)
                stat = os.stat(filepath)
                backups.append({
                    'filename': f,
                    'size': f"{stat.st_size / 1024 / 1024:.2f} MB",
                    'size_bytes': stat.st_size,
                    'created': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                })
        
        backups.sort(key=lambda x: x['created'], reverse=True)
        
        # Get database info
        db_config = settings.DATABASES['default']
        db_name = db_config.get('NAME', 'unstressvn')
        
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_size_pretty(pg_database_size(current_database()));")
                db_size = cursor.fetchone()[0]
        except Exception:
            db_size = 'Unknown'
        
        context = {
            'title': 'Database Backup',
            'backups': backups,
            'backup_dir': backup_dir,
            'db_name': db_name,
            'db_size': db_size,
        }
        
        return render(request, 'admin/postgres/backup.html', context)
    
    # POST - Tạo backup và trả về để download
    try:
        db_config = settings.DATABASES['default']
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"unstressvn_backup_{timestamp}.sql"
        
        # Tạo temp file để pg_dump
        with tempfile.NamedTemporaryFile(mode='w+b', suffix='.sql', delete=False) as tmp:
            temp_path = tmp.name
        
        # Set PGPASSWORD environment variable
        env = os.environ.copy()
        env['PGPASSWORD'] = db_config.get('PASSWORD', '')
        
        # Run pg_dump
        cmd = [
            'pg_dump',
            '-h', db_config.get('HOST', 'localhost'),
            '-p', str(db_config.get('PORT', '5432')),
            '-U', db_config.get('USER', 'postgres'),
            '-d', db_config.get('NAME', 'unstressvn'),
            '-f', temp_path,
            '--no-password',
        ]
        
        result = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            # Cũng lưu vào thư mục backups trên server
            backup_dir = os.path.join(settings.BASE_DIR, 'backups')
            os.makedirs(backup_dir, exist_ok=True)
            server_path = os.path.join(backup_dir, filename)
            
            # Copy to server backups
            import shutil
            shutil.copy2(temp_path, server_path)
            
            # Đọc file và trả về cho người dùng download
            with open(temp_path, 'rb') as f:
                content = f.read()
            
            # Cleanup temp file
            os.unlink(temp_path)
            
            response = HttpResponse(content, content_type='application/sql')
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            response['X-Backup-Size'] = str(len(content))
            response['X-Backup-Filename'] = filename
            return response
        else:
            # Cleanup temp file on error
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            return JsonResponse({
                'status': 'error',
                'message': f'Lỗi backup: {result.stderr}',
            }, status=500)
            
    except subprocess.TimeoutExpired:
        return JsonResponse({
            'status': 'error',
            'message': 'Backup timeout (> 5 phút)',
        }, status=500)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Lỗi: {str(e)}',
        }, status=500)


@staff_member_required
@require_http_methods(["POST"])
def delete_backup(request):
    """Xóa file backup trên server"""
    import os
    import json
    
    try:
        data = json.loads(request.body)
        filename = data.get('filename')
        
        if not filename:
            return JsonResponse({'status': 'error', 'message': 'Thiếu tên file'}, status=400)
        
        backup_dir = os.path.join(settings.BASE_DIR, 'backups')
        filepath = os.path.join(backup_dir, filename)
        
        # Kiểm tra path traversal
        if not os.path.abspath(filepath).startswith(os.path.abspath(backup_dir)):
            return JsonResponse({'status': 'error', 'message': 'Invalid file path'}, status=400)
        
        if os.path.exists(filepath):
            os.remove(filepath)
            return JsonResponse({'status': 'success', 'message': f'Đã xóa {filename}'})
        
        return JsonResponse({'status': 'error', 'message': 'File không tồn tại'}, status=404)
        
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': f'Lỗi: {str(e)}'}, status=500)


@staff_member_required
@require_http_methods(["POST"])
def restore_database(request):
    """Restore database từ file SQL upload hoặc file trên server.
    Sử dụng Django database connection (psycopg2) — không cần psql/pg_restore binary.
    Hỗ trợ file .sql (plain text SQL dump, data-only hoặc full).
    """
    import os
    import io
    import tempfile
    from django.db import connection
    
    try:
        # ── 1. Đọc file ──────────────────────────────────────────────
        if request.FILES.get('backup_file'):
            uploaded_file = request.FILES['backup_file']
            
            if not uploaded_file.name.endswith('.sql'):
                return JsonResponse({
                    'status': 'error',
                    'message': 'Chỉ chấp nhận file .sql (plain text SQL dump)',
                }, status=400)
            
            if uploaded_file.size > 500 * 1024 * 1024:
                return JsonResponse({
                    'status': 'error',
                    'message': 'File quá lớn (tối đa 500MB)',
                }, status=400)
            
            # Save to temp then read
            with tempfile.NamedTemporaryFile(mode='wb', suffix='.sql', delete=False) as tmp:
                for chunk in uploaded_file.chunks():
                    tmp.write(chunk)
                filepath = tmp.name
            
            filename = uploaded_file.name
            cleanup_after = True
        else:
            try:
                data = json.loads(request.body)
                filename = data.get('filename')
            except Exception:
                filename = request.POST.get('filename')
            
            if not filename:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Thiếu file backup. Vui lòng upload file hoặc chọn file từ server.',
                }, status=400)
            
            if not filename.endswith('.sql'):
                return JsonResponse({
                    'status': 'error',
                    'message': 'Chỉ chấp nhận file .sql (plain text SQL dump)',
                }, status=400)
            
            backup_dir = os.path.join(settings.BASE_DIR, 'backups')
            filepath = os.path.join(backup_dir, filename)
            
            if not os.path.abspath(filepath).startswith(os.path.abspath(backup_dir)):
                return JsonResponse({
                    'status': 'error',
                    'message': 'Invalid file path',
                }, status=400)
            
            if not os.path.exists(filepath):
                return JsonResponse({
                    'status': 'error',
                    'message': f'File backup không tồn tại: {filename}',
                }, status=404)
            
            cleanup_after = False
        
        # ── 2. Đọc nội dung SQL ──────────────────────────────────────
        with open(filepath, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        if cleanup_after and os.path.exists(filepath):
            os.unlink(filepath)
        
        # ── 3. Thực thi SQL qua Django connection (psycopg2) ─────────
        lines = sql_content.split('\n')
        errors = []
        warnings = []
        success_count = 0
        copy_count = 0
        skipped_count = 0
        
        # Các lệnh DDL cần bỏ qua (khi restore data-only vào DB đã có schema từ migrations)
        skip_prefixes = (
            'CREATE TABLE ', 'CREATE INDEX ', 'CREATE UNIQUE INDEX ',
            'CREATE SEQUENCE ', 'ALTER TABLE ', 'ALTER SEQUENCE ',
            'DROP TABLE ', 'DROP INDEX ', 'DROP SEQUENCE ',
            'CREATE TRIGGER ', 'CREATE EXTENSION ', 'CREATE TYPE ',
            'SELECT pg_catalog.', 'REVOKE ', 'GRANT ',
        )
        
        # psql meta-commands cần bỏ qua
        meta_commands = ('\\connect', '\\restrict', '\\.')
        
        with connection.cursor() as cursor:
            # Tắt triggers/FK constraints trong quá trình import
            cursor.execute("SET session_replication_role = 'replica';")
            
            i = 0
            while i < len(lines):
                line = lines[i]
                stripped = line.strip()
                
                # Bỏ qua dòng trống, comment, meta-commands
                if not stripped or stripped.startswith('--') or stripped.startswith('\\'):
                    i += 1
                    continue
                
                # Bỏ qua các lệnh DDL
                upper = stripped.upper()
                if any(upper.startswith(prefix) for prefix in skip_prefixes):
                    # Đọc hết lệnh multi-line (kết thúc bằng ;)
                    while i < len(lines) and not lines[i].rstrip().endswith(';'):
                        i += 1
                    i += 1
                    skipped_count += 1
                    continue
                
                # ── Xử lý COPY block ──
                if upper.startswith('COPY ') and 'FROM stdin' in stripped:
                    copy_header = stripped
                    i += 1
                    
                    # Thu thập data lines cho đến \.
                    data_lines = []
                    while i < len(lines):
                        if lines[i].strip() == '\\.':
                            i += 1
                            break
                        data_lines.append(lines[i])
                        i += 1
                    
                    if data_lines:
                        data_text = '\n'.join(data_lines) + '\n'
                        try:
                            cursor.copy_expert(copy_header, io.StringIO(data_text))
                            copy_count += 1
                            success_count += len(data_lines)
                        except Exception as e:
                            err_msg = str(e)
                            # Nếu lỗi duplicate key → bỏ qua, thêm warning
                            if 'duplicate key' in err_msg.lower():
                                # Reset connection state after error
                                connection.connection.rollback()
                                cursor.execute("SET session_replication_role = 'replica';")
                                table_name = copy_header.split('(')[0].replace('COPY ', '').strip()
                                warnings.append(f'Bảng {table_name}: dữ liệu đã tồn tại, bỏ qua')
                            else:
                                connection.connection.rollback()
                                cursor.execute("SET session_replication_role = 'replica';")
                                errors.append(f'COPY error: {err_msg[:200]}')
                    continue
                
                # ── Xử lý SET, SELECT setval, và các lệnh thông thường ──
                if upper.startswith('SET ') or upper.startswith('SELECT '):
                    # Gom lệnh multi-line
                    stmt = stripped
                    while not stmt.rstrip().endswith(';') and i + 1 < len(lines):
                        i += 1
                        stmt += ' ' + lines[i].strip()
                    
                    try:
                        cursor.execute(stmt)
                        success_count += 1
                    except Exception as e:
                        err_msg = str(e)
                        if 'does not exist' not in err_msg:
                            warnings.append(f'SQL warning: {err_msg[:150]}')
                        connection.connection.rollback()
                        cursor.execute("SET session_replication_role = 'replica';")
                    i += 1
                    continue
                
                # Các lệnh khác → bỏ qua
                i += 1
                skipped_count += 1
            
            # Bật lại triggers/FK
            try:
                cursor.execute("SET session_replication_role = 'origin';")
            except Exception:
                pass
            
            # Update sequences cho tất cả bảng có id
            try:
                cursor.execute("""
                    DO $$
                    DECLARE r RECORD;
                    BEGIN
                        FOR r IN (
                            SELECT c.relname AS table_name, a.attname AS column_name
                            FROM pg_class c
                            JOIN pg_attribute a ON a.attrelid = c.oid
                            JOIN pg_attrdef d ON d.adrelid = c.oid AND d.adnum = a.attnum
                            WHERE c.relkind = 'r'
                              AND pg_get_expr(d.adbin, d.adrelid) LIKE 'nextval%%'
                              AND c.relnamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'public')
                        ) LOOP
                            EXECUTE format(
                                'SELECT setval(pg_get_serial_sequence(%%L, %%L), COALESCE(MAX(%I), 1)) FROM %I',
                                r.table_name, r.column_name, r.column_name, r.table_name
                            );
                        END LOOP;
                    END $$;
                """)
            except Exception as e:
                warnings.append(f'Sequence update warning: {str(e)[:150]}')
        
        # ── 4. Kết quả ───────────────────────────────────────────────
        summary_parts = []
        if copy_count:
            summary_parts.append(f'{copy_count} bảng')
        if success_count:
            summary_parts.append(f'{success_count} dòng dữ liệu')
        if skipped_count:
            summary_parts.append(f'{skipped_count} lệnh DDL bỏ qua')
        
        summary = ', '.join(summary_parts) if summary_parts else 'không có dữ liệu'
        
        if errors:
            return JsonResponse({
                'status': 'error',
                'message': f'Restore có lỗi ({summary}): {"; ".join(errors[:5])}',
            }, status=500)
        
        warning_text = ''
        if warnings:
            warning_text = f' Warnings: {"; ".join(warnings[:5])}'
        
        return JsonResponse({
            'status': 'success',
            'message': f'Restore thành công từ {filename}! ({summary}){warning_text} Hãy restart container để load lại cấu hình.',
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Lỗi: {str(e)}',
        }, status=500)


@staff_member_required
@require_http_methods(["GET"])
def download_media(request):
    """Tải xuống toàn bộ media dưới dạng tar.gz"""
    import tarfile
    import io
    import os
    
    media_root = settings.MEDIA_ROOT
    if not os.path.exists(media_root):
        return JsonResponse({'status': 'error', 'message': 'MEDIA_ROOT không tồn tại'}, status=404)
    
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode='w:gz') as tar:
        for root, dirs, files in os.walk(media_root):
            for f in files:
                full_path = os.path.join(root, f)
                arcname = os.path.relpath(full_path, media_root)
                tar.add(full_path, arcname=arcname)
    
    buf.seek(0)
    response = HttpResponse(buf.read(), content_type='application/gzip')
    response['Content-Disposition'] = 'attachment; filename="media_backup.tar.gz"'
    return response


@staff_member_required
@require_http_methods(["POST"])
def upload_media(request):
    """Upload media tar.gz/zip và giải nén vào MEDIA_ROOT"""
    import tarfile
    import zipfile
    import io
    import os
    import tempfile
    
    uploaded_file = request.FILES.get('media_file')
    if not uploaded_file:
        return JsonResponse({'status': 'error', 'message': 'Thiếu file media'}, status=400)
    
    if uploaded_file.size > 500 * 1024 * 1024:
        return JsonResponse({'status': 'error', 'message': 'File quá lớn (tối đa 500MB)'}, status=400)
    
    media_root = settings.MEDIA_ROOT
    os.makedirs(media_root, exist_ok=True)
    
    file_count = 0
    name = uploaded_file.name.lower()
    
    try:
        if name.endswith('.tar.gz') or name.endswith('.tgz'):
            data = io.BytesIO(uploaded_file.read())
            with tarfile.open(fileobj=data, mode='r:gz') as tar:
                # Kiểm tra path traversal
                for member in tar.getmembers():
                    target = os.path.join(media_root, member.name)
                    if not os.path.abspath(target).startswith(os.path.abspath(media_root)):
                        return JsonResponse({'status': 'error', 'message': f'Path traversal detected: {member.name}'}, status=400)
                tar.extractall(path=media_root)
                file_count = sum(1 for m in tar.getmembers() if m.isfile())
        elif name.endswith('.zip'):
            data = io.BytesIO(uploaded_file.read())
            with zipfile.ZipFile(data) as zf:
                for zi in zf.infolist():
                    target = os.path.join(media_root, zi.filename)
                    if not os.path.abspath(target).startswith(os.path.abspath(media_root)):
                        return JsonResponse({'status': 'error', 'message': f'Path traversal detected: {zi.filename}'}, status=400)
                zf.extractall(path=media_root)
                file_count = sum(1 for zi in zf.infolist() if not zi.is_dir())
        else:
            return JsonResponse({'status': 'error', 'message': 'Chỉ chấp nhận file .tar.gz, .tgz hoặc .zip'}, status=400)
        
        return JsonResponse({
            'status': 'success',
            'message': f'Upload media thành công! {file_count} files đã được giải nén vào {media_root}',
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': f'Lỗi giải nén: {str(e)}'}, status=500)

