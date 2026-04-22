
#-- Create the first 'admin' user with password admin123
#
DJANGO_SETTINGS_MODULE=config.settings python manage.py shell -c "
from django.contrib.auth.models import User
from app_traslados.models import Perfil
u = User.objects.create_superuser('admin', '', 'admin123')
Perfil.objects.filter(usuario=u).update(rol='DIRECTOR')
print('DIRECTOR created: admin / admin123')
"
