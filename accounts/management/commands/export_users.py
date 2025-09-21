import csv
import json
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from accounts.models import StudentProfile, TeacherProfile

User = get_user_model()


class Command(BaseCommand):
    help = '导出用户数据（支持CSV和JSON格式）'
    
    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str, help='导出文件路径')
        parser.add_argument(
            '--format',
            type=str,
            choices=['csv', 'json'],
            default='csv',
            help='文件格式 (默认: csv)'
        )
        parser.add_argument(
            '--role',
            type=str,
            choices=['student', 'teacher', 'admin'],
            help='只导出指定角色的用户'
        )
        parser.add_argument(
            '--department',
            type=str,
            help='只导出指定院系的用户'
        )
    
    def handle(self, *args, **options):
        file_path = options['file_path']
        file_format = options['format']
        role_filter = options.get('role')
        department_filter = options.get('department')
        
        try:
            # 构建查询
            queryset = User.objects.all().select_related('student_profile', 'teacher_profile')
            
            if role_filter:
                queryset = queryset.filter(role=role_filter)
            
            if department_filter:
                queryset = queryset.filter(department__icontains=department_filter)
            
            users = list(queryset.order_by('department', 'role', 'real_name'))
            
            if file_format == 'csv':
                self.export_to_csv(file_path, users)
            else:
                self.export_to_json(file_path, users)
            
            self.stdout.write(
                self.style.SUCCESS(f'成功导出 {len(users)} 个用户到 {file_path}')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'导出失败: {str(e)}')
            )
    
    def export_to_csv(self, file_path, users):
        """导出到CSV文件"""
        with open(file_path, 'w', newline='', encoding='utf-8') as file:
            # CSV字段
            fieldnames = [
                'username', 'email', 'real_name', 'student_id', 'phone_number',
                'department', 'major', 'grade', 'role', 'is_active',
                'date_joined', 'last_login'
            ]
            
            # 添加学生特有字段
            student_fields = ['gpa', 'research_interests', 'skills', 'introduction']
            
            # 添加教师特有字段
            teacher_fields = [
                'title', 'research_areas', 'max_students', 'current_students',
                'teacher_introduction', 'requirements', 'is_accepting'
            ]
            
            fieldnames.extend(student_fields)
            fieldnames.extend(teacher_fields)
            
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            
            for user in users:
                row = {
                    'username': user.username,
                    'email': user.email,
                    'real_name': user.real_name,
                    'student_id': user.student_id,
                    'phone_number': user.phone_number,
                    'department': user.department,
                    'major': user.major,
                    'grade': user.grade,
                    'role': user.role,
                    'is_active': user.is_active,
                    'date_joined': user.date_joined.isoformat() if user.date_joined else '',
                    'last_login': user.last_login.isoformat() if user.last_login else '',
                }
                
                # 添加学生档案信息
                if hasattr(user, 'student_profile') and user.student_profile:
                    profile = user.student_profile
                    row.update({
                        'gpa': profile.gpa or '',
                        'research_interests': profile.research_interests,
                        'skills': profile.skills,
                        'introduction': profile.introduction,
                    })
                
                # 添加教师档案信息
                if hasattr(user, 'teacher_profile') and user.teacher_profile:
                    profile = user.teacher_profile
                    row.update({
                        'title': profile.title,
                        'research_areas': profile.research_areas,
                        'max_students': profile.max_students,
                        'current_students': profile.current_students,
                        'teacher_introduction': profile.introduction,
                        'requirements': profile.requirements,
                        'is_accepting': profile.is_accepting,
                    })
                
                writer.writerow(row)
    
    def export_to_json(self, file_path, users):
        """导出到JSON文件"""
        users_data = []
        
        for user in users:
            user_data = {
                'username': user.username,
                'email': user.email,
                'real_name': user.real_name,
                'student_id': user.student_id,
                'phone_number': user.phone_number,
                'department': user.department,
                'major': user.major,
                'grade': user.grade,
                'role': user.role,
                'is_active': user.is_active,
                'date_joined': user.date_joined.isoformat() if user.date_joined else None,
                'last_login': user.last_login.isoformat() if user.last_login else None,
            }
            
            # 添加学生档案信息
            if hasattr(user, 'student_profile') and user.student_profile:
                profile = user.student_profile
                user_data['student_profile'] = {
                    'gpa': profile.gpa,
                    'research_interests': profile.research_interests,
                    'skills': profile.skills,
                    'introduction': profile.introduction,
                }
            
            # 添加教师档案信息
            if hasattr(user, 'teacher_profile') and user.teacher_profile:
                profile = user.teacher_profile
                user_data['teacher_profile'] = {
                    'title': profile.title,
                    'research_areas': profile.research_areas,
                    'max_students': profile.max_students,
                    'current_students': profile.current_students,
                    'introduction': profile.introduction,
                    'requirements': profile.requirements,
                    'is_accepting': profile.is_accepting,
                }
            
            users_data.append(user_data)
        
        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(users_data, file, ensure_ascii=False, indent=2)