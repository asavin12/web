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
    """Chi tiết schema của một table"""
    columns = []
    indexes = []
    foreign_keys = []
    
    try:
        with connection.cursor() as cursor:
            # Get columns
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
                columns.append({
                    'name': row[0],
                    'type': row[1],
                    'max_length': row[2],
                    'nullable': row[3],
                    'default': row[4],
                })
            
            # Get indexes
            cursor.execute("""
                SELECT indexname, indexdef
                FROM pg_indexes
                WHERE tablename = %s;
            """, [table_name])
            
            for row in cursor.fetchall():
                indexes.append({
                    'name': row[0],
                    'definition': row[1],
                })
            
            # Get foreign keys
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
                
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    
    if request.headers.get('Accept') == 'application/json':
        return JsonResponse({
            'table': table_name,
            'columns': columns,
            'indexes': indexes,
            'foreign_keys': foreign_keys,
        })
    
    return render(request, 'admin/postgres/table_schema.html', {
        'title': f'Table: {table_name}',
        'table_name': table_name,
        'columns': columns,
        'indexes': indexes,
        'foreign_keys': foreign_keys,
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
    """Restore database từ file upload hoặc file trên server"""
    import subprocess
    import os
    import tempfile
    
    try:
        # Check if file upload (multipart form)
        if request.FILES.get('backup_file'):
            uploaded_file = request.FILES['backup_file']
            
            # Validate file extension
            if not uploaded_file.name.endswith(('.sql', '.dump')):
                return JsonResponse({
                    'status': 'error',
                    'message': 'Chỉ chấp nhận file .sql hoặc .dump',
                }, status=400)
            
            # Validate file size (max 500MB)
            if uploaded_file.size > 500 * 1024 * 1024:
                return JsonResponse({
                    'status': 'error',
                    'message': 'File quá lớn (tối đa 500MB)',
                }, status=400)
            
            # Save uploaded file to temp
            with tempfile.NamedTemporaryFile(mode='wb', suffix='.sql', delete=False) as tmp:
                for chunk in uploaded_file.chunks():
                    tmp.write(chunk)
                filepath = tmp.name
            
            filename = uploaded_file.name
            cleanup_after = True
        else:
            # Restore từ file trên server
            try:
                data = json.loads(request.body)
                filename = data.get('filename')
            except:
                filename = request.POST.get('filename')
            
            if not filename:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Thiếu file backup. Vui lòng upload file hoặc chọn file từ server.',
                }, status=400)
            
            backup_dir = os.path.join(settings.BASE_DIR, 'backups')
            filepath = os.path.join(backup_dir, filename)
            
            # Kiểm tra path traversal
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
        
        db_config = settings.DATABASES['default']
        
        # Set PGPASSWORD
        env = os.environ.copy()
        env['PGPASSWORD'] = db_config.get('PASSWORD', '')
        
        # Run psql to restore
        cmd = [
            'psql',
            '-h', db_config.get('HOST', 'localhost'),
            '-p', str(db_config.get('PORT', '5432')),
            '-U', db_config.get('USER', 'postgres'),
            '-d', db_config.get('NAME', 'unstressvn'),
            '-f', filepath,
            '--no-password',
        ]
        
        result = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=600)
        
        # Cleanup temp file if uploaded
        if cleanup_after and os.path.exists(filepath):
            os.unlink(filepath)
        
        if result.returncode == 0:
            return JsonResponse({
                'status': 'success',
                'message': f'Restore thành công từ {filename}!',
            })
        else:
            return JsonResponse({
                'status': 'error',
                'message': f'Lỗi restore: {result.stderr[:500]}',
            }, status=500)
            
    except subprocess.TimeoutExpired:
        return JsonResponse({
            'status': 'error',
            'message': 'Restore timeout (> 10 phút)',
        }, status=500)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Lỗi: {str(e)}',
        }, status=500)

