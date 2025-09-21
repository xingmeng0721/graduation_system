import csv
import json
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from accounts.models import StudentProfile, TeacherProfile
from django.db import transaction

User = get_user_model()


class Command(BaseCommand):
    help = '导入用户数据（支持CSV和JSON格式）'
    
    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str, help='数据文件路径')
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
            choices=['student', 'teacher'],
            help='用户角色（当文件中没有指定时使用）'
        )
    
    def handle(self, *args, **options):
        file_path = options['file_path']
        file_format = options['format']
        default_role = options.get('role')
        
        try:
            if file_format == 'csv':
                self.import_from_csv(file_path, default_role)
            else:
                self.import_from_json(file_path)
        except FileNotFoundError:
            self.stdout.write(
                self.style.ERROR(f'文件不存在: {file_path}')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'导入失败: {str(e)}')
            )
    
    def import_from_csv(self, file_path, default_role):
        """从CSV文件导入数据"""
        with open(file_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            created_count = 0
            updated_count = 0
            error_count = 0
            
            for row in reader:
                try:
                    with transaction.atomic():
                        username = row.get('username')
                        email = row.get('email', '')
                        real_name = row.get('real_name', '')
                        student_id = row.get('student_id', '')
                        phone_number = row.get('phone_number', '')
                        department = row.get('department', '')
                        major = row.get('major', '')
                        grade = row.get('grade', '')
                        role = row.get('role', default_role)
                        password = row.get('password', '123456')  # 默认密码
                        
                        if not username:
                            self.stdout.write(
                                self.style.WARNING(f'跳过无用户名的行: {row}')
                            )
                            continue
                        
                        # 创建或更新用户
                        user, created = User.objects.get_or_create(
                            username=username,
                            defaults={
                                'email': email,
                                'real_name': real_name,
                                'student_id': student_id,
                                'phone_number': phone_number,
                                'department': department,
                                'major': major,
                                'grade': grade,
                                'role': role,
                            }
                        )
                        
                        if created:
                            user.set_password(password)
                            user.save()
                            created_count += 1
                            
                            # 创建相应的档案
                            if role == 'student':
                                StudentProfile.objects.create(
                                    user=user,
                                    gpa=row.get('gpa'),
                                    research_interests=row.get('research_interests', ''),
                                    skills=row.get('skills', ''),
                                    introduction=row.get('introduction', '')
                                )
                            elif role == 'teacher':
                                TeacherProfile.objects.create(
                                    user=user,
                                    title=row.get('title', ''),
                                    research_areas=row.get('research_areas', ''),
                                    max_students=int(row.get('max_students', 5)),
                                    introduction=row.get('introduction', ''),
                                    requirements=row.get('requirements', ''),
                                    is_accepting=row.get('is_accepting', 'true').lower() == 'true'
                                )
                        else:
                            # 更新现有用户信息
                            user.email = email or user.email
                            user.real_name = real_name or user.real_name
                            user.student_id = student_id or user.student_id
                            user.phone_number = phone_number or user.phone_number
                            user.department = department or user.department
                            user.major = major or user.major
                            user.grade = grade or user.grade
                            user.save()
                            updated_count += 1
                            
                            # 更新档案
                            if role == 'student' and hasattr(user, 'student_profile'):
                                profile = user.student_profile
                                if row.get('gpa'):
                                    profile.gpa = float(row['gpa'])
                                profile.research_interests = row.get('research_interests', profile.research_interests)
                                profile.skills = row.get('skills', profile.skills)
                                profile.introduction = row.get('introduction', profile.introduction)
                                profile.save()
                            elif role == 'teacher' and hasattr(user, 'teacher_profile'):
                                profile = user.teacher_profile
                                profile.title = row.get('title', profile.title)
                                profile.research_areas = row.get('research_areas', profile.research_areas)
                                if row.get('max_students'):
                                    profile.max_students = int(row['max_students'])
                                profile.introduction = row.get('introduction', profile.introduction)
                                profile.requirements = row.get('requirements', profile.requirements)
                                if row.get('is_accepting'):
                                    profile.is_accepting = row['is_accepting'].lower() == 'true'
                                profile.save()
                        
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'{"创建" if created else "更新"} 用户: {username}'
                            )
                        )
                        
                except Exception as e:
                    error_count += 1
                    self.stdout.write(
                        self.style.ERROR(f'处理用户 {row.get("username", "未知")} 时出错: {str(e)}')
                    )
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n导入完成！'
                    f'\n创建用户: {created_count}'
                    f'\n更新用户: {updated_count}'
                    f'\n错误数量: {error_count}'
                )
            )
    
    def import_from_json(self, file_path):
        """从JSON文件导入数据"""
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
            
            if not isinstance(data, list):
                raise ValueError('JSON文件必须包含用户数组')
            
            created_count = 0
            updated_count = 0
            error_count = 0
            
            for user_data in data:
                try:
                    with transaction.atomic():
                        username = user_data.get('username')
                        
                        if not username:
                            self.stdout.write(
                                self.style.WARNING(f'跳过无用户名的记录: {user_data}')
                            )
                            continue
                        
                        # 提取用户基本信息
                        user_fields = {
                            'email': user_data.get('email', ''),
                            'real_name': user_data.get('real_name', ''),
                            'student_id': user_data.get('student_id', ''),
                            'phone_number': user_data.get('phone_number', ''),
                            'department': user_data.get('department', ''),
                            'major': user_data.get('major', ''),
                            'grade': user_data.get('grade', ''),
                            'role': user_data.get('role', 'student'),
                        }
                        
                        user, created = User.objects.get_or_create(
                            username=username,
                            defaults=user_fields
                        )
                        
                        if created:
                            password = user_data.get('password', '123456')
                            user.set_password(password)
                            user.save()
                            created_count += 1
                        else:
                            for field, value in user_fields.items():
                                if value:
                                    setattr(user, field, value)
                            user.save()
                            updated_count += 1
                        
                        # 处理档案信息
                        if user.role == 'student':
                            profile, _ = StudentProfile.objects.get_or_create(user=user)
                            if 'student_profile' in user_data:
                                profile_data = user_data['student_profile']
                                for field in ['gpa', 'research_interests', 'skills', 'introduction']:
                                    if field in profile_data:
                                        setattr(profile, field, profile_data[field])
                                profile.save()
                        
                        elif user.role == 'teacher':
                            profile, _ = TeacherProfile.objects.get_or_create(user=user)
                            if 'teacher_profile' in user_data:
                                profile_data = user_data['teacher_profile']
                                for field in ['title', 'research_areas', 'max_students', 
                                            'introduction', 'requirements', 'is_accepting']:
                                    if field in profile_data:
                                        setattr(profile, field, profile_data[field])
                                profile.save()
                        
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'{"创建" if created else "更新"} 用户: {username}'
                            )
                        )
                        
                except Exception as e:
                    error_count += 1
                    self.stdout.write(
                        self.style.ERROR(
                            f'处理用户 {user_data.get("username", "未知")} 时出错: {str(e)}'
                        )
                    )
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n导入完成！'
                    f'\n创建用户: {created_count}'
                    f'\n更新用户: {updated_count}'
                    f'\n错误数量: {error_count}'
                )
            )