from .models import PackageCategory,Notification

def menu_categories(request):
    return{
        'menu_categories':PackageCategory.objects.all()
    }

def notifications(request):
    if request.user.is_authenticated:
        unread = request.user.notifications.filter(is_read=False)
        count = unread.count()
        print(f"DEBUG: User {request.user} has {count} unread notifications") 
        return{
            'notifications': unread[:5],
            'notification_count':unread.count()
        }
    return{}