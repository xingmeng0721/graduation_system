# Graduation System (Unified Auth)

一个最小可运行的毕业系统后端骨架，采用统一用户模型（AUTH_USER_MODEL=accounts.User），通过 SimpleJWT 发放 Token，支持三类角色：管理员（admin）、教师（teacher）、学生（student）。

## 特性
- 自定义用户模型 `accounts.User`，字段包含 `role`（admin/teacher/student）、`display_name`
- 三类档案 Profile：`AdminProfile`、`TeacherProfile`、`StudentProfile`（分别包含原有业务字段）
- 统一登录接口：`POST /api/auth/login`
- 获取当前用户信息：`GET /api/auth/me`
- 基于角色的权限控制：`IsAdmin`、`IsTeacher`、`IsStudent`
- CORS + DRF + SimpleJWT 已配置
- 附带管理命令一键创建示例账号：`python manage.py create_demo_users`

## 环境要求
- Python 3.10+
- pip / venv

## 安装与运行（SQLite）
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

pip install -r requirements.txt

python manage.py makemigrations accounts
python manage.py migrate
python manage.py create_demo_users  # 创建示例账号
python manage.py runserver 0.0.0.0:8000
```

示例账号（均为密码 `123456`）：
- 管理员：username=admin001，role=admin，对应 AdminProfile.admin_id=admin001
- 教师：username=t001，role=teacher，对应 TeacherProfile.teacher_id=t001
- 学生：username=s001，role=student，对应 StudentProfile.student_number=s001

## API

### 1) 登录
POST /api/auth/login

请求体：
```json
{
  "role": "admin|teacher|student",
  "identifier": "admin_id|teacher_id|student_number",
  "password": "123456"
}
```

说明：
- identifier 需要等于用户的 username；约定如下：
  - 管理员 username = admin_id
  - 教师 username = teacher_id
  - 学生 username = student_number

响应示例：
```json
{
  "code": 200,
  "success": true,
  "message": "登录成功",
  "data": {
    "access_token": "<access>",
    "refresh_token": "<refresh>",
    "user": {
      "id": 1,
      "username": "admin001",
      "display_name": "系统管理员",
      "role": "admin"
    },
    "profile": {
      "admin_id": "admin001",
      "name": "系统管理员",
      "phone": ""
    }
  }
}
```

### 2) 当前用户信息
GET /api/auth/me

请求头：
```
Authorization: Bearer <access_token>
```

返回当前用户及其 Profile。

## 切换到 MySQL（可选）
1. 安装驱动：
```bash
pip install PyMySQL
```
2. 修改 `graduation_system/settings.py`，将 `DATABASES` 改为：
```python
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": "graduation_system",
        "USER": "gs",
        "PASSWORD": "123456",
        "HOST": "127.0.0.1",
        "PORT": "3306",
        "OPTIONS": { "init_command": "SET sql_mode='STRICT_TRANS_TABLES'" },
    }
}
import pymysql
pymysql.install_as_MySQLdb()
```
3. 重新迁移：
```bash
python manage.py migrate
python manage.py create_demo_users
```

## 前端对接建议
- 登录成功后保存 `access_token` 到 `sessionStorage` 或 `localStorage`。
- 所有接口通过 `Authorization: Bearer <access_token>` 访问。
- 根据响应中的 `user.role` 控制不同角色的路由与界面.