from django.db import models

# Create your models here.
class AdminUser(models.Model):
    #主键
    admin_id = models.AutoField(primary_key=True)
    admin_name = models.CharField(max_length=150, unique=True)
    admin_username = models.CharField(max_length=150, unique=True)
    admin_password = models.CharField(max_length=128)

    def __str__(self):
        return self.admin_username