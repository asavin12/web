#!/usr/bin/env python
"""
Export Database Schema - UnstressVN
Tạo file cấu trúc database PostgreSQL

Usage:
    python scripts/export_db_schema.py                    # Export JSON
    python scripts/export_db_schema.py --format sql       # Export SQL DDL
    python scripts/export_db_schema.py --format markdown  # Export Markdown doc
"""

import os
import sys
import json
import argparse
from datetime import datetime

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'unstressvn_settings.settings')

import django
django.setup()

from django.db import connection
from django.conf import settings


def get_database_info():
    """Lấy thông tin database"""
    with connection.cursor() as cursor:
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        
        cursor.execute("SELECT current_database(), current_user;")
        db_info = cursor.fetchone()
        
        cursor.execute("SELECT pg_size_pretty(pg_database_size(current_database()));")
        size = cursor.fetchone()[0]
        
        return {
            'name': db_info[0],
            'user': db_info[1],
            'host': settings.DATABASES['default'].get('HOST', 'localhost'),
            'port': settings.DATABASES['default'].get('PORT', '5432'),
            'version': version,
            'size': size,
        }


def get_all_tables():
    """Lấy tất cả tables và schema"""
    tables = []
    
    with connection.cursor() as cursor:
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
                'primary_key': None,
            }
            
            # Get columns
            cursor.execute("""
                SELECT 
                    column_name,
                    data_type,
                    character_maximum_length,
                    is_nullable,
                    column_default,
                    ordinal_position
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
                    'position': row[5],
                })
            
            # Get primary key
            cursor.execute("""
                SELECT kcu.column_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu
                    ON tc.constraint_name = kcu.constraint_name
                WHERE tc.constraint_type = 'PRIMARY KEY' AND tc.table_name = %s;
            """, [table_name])
            pk_result = cursor.fetchone()
            if pk_result:
                table_info['primary_key'] = pk_result[0]
            
            # Get foreign keys
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
            
            # Get indexes
            cursor.execute("""
                SELECT indexname, indexdef
                FROM pg_indexes WHERE tablename = %s;
            """, [table_name])
            
            for row in cursor.fetchall():
                table_info['indexes'].append({
                    'name': row[0],
                    'definition': row[1],
                })
            
            # Get row count
            try:
                cursor.execute(f'SELECT COUNT(*) FROM "{table_name}";')
                table_info['row_count'] = cursor.fetchone()[0]
            except:
                table_info['row_count'] = None
            
            tables.append(table_info)
    
    return tables


def export_json(output_file):
    """Export schema as JSON"""
    schema = {
        'exported_at': datetime.now().isoformat(),
        'database': get_database_info(),
        'tables': get_all_tables(),
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(schema, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"✅ Exported to: {output_file}")


def export_sql(output_file):
    """Export schema as SQL DDL"""
    lines = [
        "-- UnstressVN Database Schema",
        f"-- Exported: {datetime.now().isoformat()}",
        f"-- Database: {settings.DATABASES['default'].get('NAME', 'unstressvn')}",
        "",
        "-- ================================================",
        "-- CREATE TABLES",
        "-- ================================================",
        "",
    ]
    
    tables = get_all_tables()
    
    for table in tables:
        lines.append(f"-- Table: {table['name']}")
        lines.append(f"CREATE TABLE IF NOT EXISTS \"{table['name']}\" (")
        
        col_defs = []
        for col in table['columns']:
            col_type = col['type'].upper()
            if col['max_length']:
                col_type = f"{col_type}({col['max_length']})"
            
            nullable = "" if col['nullable'] else " NOT NULL"
            default = f" DEFAULT {col['default']}" if col['default'] else ""
            pk = " PRIMARY KEY" if col['name'] == table['primary_key'] else ""
            
            col_defs.append(f"    \"{col['name']}\" {col_type}{nullable}{default}{pk}")
        
        lines.append(",\n".join(col_defs))
        lines.append(");")
        lines.append("")
        
        # Foreign keys
        for fk in table['foreign_keys']:
            lines.append(f"ALTER TABLE \"{table['name']}\" ADD CONSTRAINT \"{fk['constraint']}\"")
            lines.append(f"    FOREIGN KEY (\"{fk['column']}\")")
            lines.append(f"    REFERENCES \"{fk['references_table']}\" (\"{fk['references_column']}\");")
            lines.append("")
        
        # Indexes
        for idx in table['indexes']:
            if 'pkey' not in idx['name']:
                lines.append(f"-- {idx['definition']};")
                lines.append("")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    print(f"✅ Exported to: {output_file}")


def export_markdown(output_file):
    """Export schema as Markdown documentation"""
    db_info = get_database_info()
    tables = get_all_tables()
    
    lines = [
        "# UnstressVN Database Schema",
        "",
        f"**Exported:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## Database Info",
        "",
        f"| Property | Value |",
        f"|----------|-------|",
        f"| Database | `{db_info['name']}` |",
        f"| Host | `{db_info['host']}:{db_info['port']}` |",
        f"| Size | {db_info['size']} |",
        f"| Tables | {len(tables)} |",
        "",
        "---",
        "",
        "## Tables",
        "",
    ]
    
    # TOC
    lines.append("### Table of Contents")
    lines.append("")
    for table in tables:
        lines.append(f"- [{table['name']}](#{table['name'].replace('_', '-')})")
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # Table details
    for table in tables:
        lines.append(f"### {table['name']}")
        lines.append("")
        lines.append(f"**Rows:** {table['row_count'] or 'N/A'}")
        lines.append("")
        
        # Columns
        lines.append("#### Columns")
        lines.append("")
        lines.append("| # | Column | Type | Nullable | Default |")
        lines.append("|---|--------|------|----------|---------|")
        
        for col in table['columns']:
            col_type = col['type']
            if col['max_length']:
                col_type = f"{col_type}({col['max_length']})"
            
            pk_badge = " 🔑" if col['name'] == table['primary_key'] else ""
            nullable = "✓" if col['nullable'] else "✗"
            default = f"`{col['default'][:30]}...`" if col['default'] and len(str(col['default'])) > 30 else (f"`{col['default']}`" if col['default'] else "-")
            
            lines.append(f"| {col['position']} | `{col['name']}`{pk_badge} | `{col_type}` | {nullable} | {default} |")
        
        lines.append("")
        
        # Foreign keys
        if table['foreign_keys']:
            lines.append("#### Foreign Keys")
            lines.append("")
            lines.append("| Column | References |")
            lines.append("|--------|------------|")
            for fk in table['foreign_keys']:
                lines.append(f"| `{fk['column']}` | `{fk['references_table']}.{fk['references_column']}` |")
            lines.append("")
        
        # Indexes
        if table['indexes']:
            lines.append("#### Indexes")
            lines.append("")
            for idx in table['indexes']:
                lines.append(f"- `{idx['name']}`")
            lines.append("")
        
        lines.append("---")
        lines.append("")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    print(f"✅ Exported to: {output_file}")


def main():
    parser = argparse.ArgumentParser(description='Export Database Schema')
    parser.add_argument('--format', choices=['json', 'sql', 'markdown'], default='json',
                        help='Output format (default: json)')
    parser.add_argument('-o', '--output', help='Output file path')
    
    args = parser.parse_args()
    
    # Default output file
    if not args.output:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        ext = {'json': 'json', 'sql': 'sql', 'markdown': 'md'}[args.format]
        args.output = f'docs/database_schema_{timestamp}.{ext}'
    
    # Ensure docs directory exists
    os.makedirs(os.path.dirname(args.output) or '.', exist_ok=True)
    
    print(f"\n📊 Exporting database schema...")
    print(f"   Format: {args.format}")
    print(f"   Output: {args.output}")
    print()
    
    if args.format == 'json':
        export_json(args.output)
    elif args.format == 'sql':
        export_sql(args.output)
    elif args.format == 'markdown':
        export_markdown(args.output)
    
    print()


if __name__ == '__main__':
    main()
