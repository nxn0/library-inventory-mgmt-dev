"""
User authentication and session management utilities for the user-side application.
"""
import json
from datetime import timedelta
from django.utils import timezone
from django.http import HttpRequest
from .models import AnonymousUser, UserAuthentication, Member
from .encryption import PrivacyEncryption


class UserSessionManager:
    """Manage user sessions - both anonymous and authenticated"""
    
    @staticmethod
    def get_or_create_anonymous_user(request):
        """
        Get or create an anonymous user based on fingerprint.
        Returns: AnonymousUser instance
        """
        # Generate fingerprint hash from browser data
        fingerprint_data = UserSessionManager._extract_fingerprint(request)
        fingerprint_hash = PrivacyEncryption.hash_fingerprint(fingerprint_data)
        
        try:
            user = AnonymousUser.objects.get(fingerprint_hash=fingerprint_hash)
            # Update last activity
            user.last_activity = timezone.now()
            user.save(update_fields=['last_activity'])
        except AnonymousUser.DoesNotExist:
            # Create new anonymous user
            user_id = PrivacyEncryption.generate_anonymous_user_id()
            user = AnonymousUser.objects.create(
                user_id=user_id,
                fingerprint_hash=fingerprint_hash,
                session_key=request.session.session_key or '',
                ip_address=UserSessionManager._get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                is_active=True
            )
        
        return user
    
    @staticmethod
    def _extract_fingerprint(request):
        """
        Extract browser fingerprint from request.
        Returns: dict with fingerprint data
        """
        fingerprint = {
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'accept_language': request.META.get('HTTP_ACCEPT_LANGUAGE', ''),
            'accept_encoding': request.META.get('HTTP_ACCEPT_ENCODING', ''),
        }
        return fingerprint
    
    @staticmethod
    def _get_client_ip(request):
        """Get client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    @staticmethod
    def generate_unique_username(base='user'):
        """Create a unique username by adding a random suffix if needed."""
        import random, string
        username = base
        if not UserAuthentication.objects.filter(username=username).exists():
            return username

        for _ in range(20):
            suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))
            candidate = f"{base}_{suffix}"
            if not UserAuthentication.objects.filter(username=candidate).exists():
                return candidate

        # Fallback unique variant
        return f"{base}_{timezone.now().strftime('%f')}"

    @staticmethod
    def authenticate_with_library_id(library_id, username=None):
        """
        Authenticate user with library/student ID and optional username.
        Returns: UserAuthentication instance or None
        """
        encrypted_id = PrivacyEncryption.encrypt_library_id(library_id)

        if username:
            try:
                user_auth = UserAuthentication.objects.get(
                    encrypted_library_id=encrypted_id,
                    username=username,
                    is_active=True,
                    is_banned=False
                )

                if user_auth.ban and user_auth.ban.is_active:
                    return None
                return user_auth
            except UserAuthentication.DoesNotExist:
                return None

        try:
            user_auth = UserAuthentication.objects.get(
                encrypted_library_id=encrypted_id,
                is_active=True,
                is_banned=False
            )

            if user_auth.ban and user_auth.ban.is_active:
                return None
            return user_auth
        except UserAuthentication.DoesNotExist:
            # Auto-create account for first-time user
            generated = UserSessionManager.generate_unique_username(base=f"user{library_id[:3]}")
            return UserSessionManager.create_library_id_user(library_id, username=generated)

    
    @staticmethod
    def authenticate_with_credentials(name, phone, credentials):
        """
        Authenticate user with name, phone, and credentials.
        If user doesn't exist, create new UserAuthentication.
        Returns: UserAuthentication instance
        """
        encrypted_auth = PrivacyEncryption.encrypt_auth_data(name, phone, credentials)
        
        try:
            user_auth = UserAuthentication.objects.get(
                encrypted_auth_data=encrypted_auth,
                is_active=True
            )
            
            # Check if user is banned
            if user_auth.ban and user_auth.ban.is_active:
                return None
            
            return user_auth
        except UserAuthentication.DoesNotExist:
            # Create new user with credentials
            generated = UserSessionManager.generate_unique_username(base=f"user{phone[-3:] if phone else 'x'}")
            user_auth = UserAuthentication.objects.create(
                encrypted_auth_data=encrypted_auth,
                auth_method='credentials',
                username=generated,
                is_active=True
            )
            return user_auth
    
    @staticmethod
    def authenticate_with_username(username, password):
        """Authenticate user using username & password from encrypted credentials."""
        if username == 'admin' and password == '12345':
            # handled as custom admin in view layer
            return None

        try:
            user_auth = UserAuthentication.objects.get(
                username=username,
                is_active=True,
                is_banned=False
            )

            if user_auth.ban and user_auth.ban.is_active:
                return None

            if user_auth.encrypted_auth_data:
                try:
                    _, _, stored_cred = PrivacyEncryption.decrypt_auth_data(user_auth.encrypted_auth_data)
                    if stored_cred == password:
                        return user_auth
                except Exception:
                    return None

            return None
        except UserAuthentication.DoesNotExist:
            return None

    @staticmethod
    def create_library_id_user(library_id, username=None, password=None, member=None):
        """
        Create a new user authentication with library ID, optional username/password.
        """
        encrypted_id = PrivacyEncryption.encrypt_library_id(library_id)

        if not username:
            username = UserSessionManager.generate_unique_username(base=f"user{library_id[:3]}")
        else:
            if UserAuthentication.objects.filter(username=username).exists():
                username = UserSessionManager.generate_unique_username(base=username)

        encrypted_auth = None
        if password:
            # store password encrypted in the same field as raw credentials path
            encrypted_auth = PrivacyEncryption.encrypt_auth_data('', '', password)

        user_auth = UserAuthentication.objects.create(
            encrypted_library_id=encrypted_id,
            auth_method='library_id' if 'student' not in library_id.lower() else 'student_id',
            username=username,
            encrypted_auth_data=encrypted_auth,
            member=member,
            is_active=True
        )
        return user_auth
        return user_auth


class OverdueTracker:
    """Track and manage overdue books"""
    
    OVERDUE_DAYS = 15
    BLACKLIST_DAYS = 30
    
    @staticmethod
    def check_overdue_transactions():
        """
        Check for overdue transactions and move them to OverdueBook table after BLACKLIST_DAYS.
        Should be called by a periodic task (Celery).
        """
        from .models import Transaction, OverdueBook
        
        now = timezone.now().date()
        overdue_threshold = now - timedelta(days=OverdueTracker.BLACKLIST_DAYS)
        
        # Find transactions that are overdue and past blacklist threshold
        old_overdue = Transaction.objects.filter(
            status='active',
            due_date__lt=overdue_threshold
        )
        
        for transaction in old_overdue:
            # Move to OverdueBook table (unencrypted for admin)
            member = transaction.member
            user_identifier = f"{member.first_name} {member.last_name}" if member.first_name else f"ID: {member.member_id}"
            
            OverdueBook.objects.create(
                user_identifier=user_identifier,
                name=f"{member.first_name} {member.last_name}",
                phone=member.phone or '',
                book_title=transaction.resource.title,
                book_author=transaction.resource.author,
                resource_id=transaction.resource.resource_id,
                checkout_date=transaction.checkout_date.date(),
                due_date=transaction.due_date,
                days_overdue=(now - transaction.due_date).days,
                original_transaction=str(transaction.id),
            )
            
            # Update transaction status
            transaction.status = 'overdue'
            transaction.save(update_fields=['status'])
    
    @staticmethod
    def cleanup_expired_sessions():
        """
        Delete expired anonymous user sessions (inactive for 30 days).
        Should be called by a periodic task (Celery).
        """
        expiry_threshold = timezone.now() - timedelta(days=30)
        
        expired_users = AnonymousUser.objects.filter(
            last_activity__lt=expiry_threshold,
            is_active=True
        )
        
        count = 0
        for user in expired_users:
            # Delete related data if needed
            user.is_active = False
            user.save(update_fields=['is_active'])
            count += 1
        
        return count
    
    @staticmethod
    def cleanup_expired_bans():
        """
        Remove expired temporary bans.
        Should be called by a periodic task (Celery).
        """
        from .models import UserBan
        
        now = timezone.now()
        
        expired_bans = UserBan.objects.filter(
            is_permanent=False,
            ban_until__lt=now
        )
        
        count = 0
        for ban in expired_bans:
            ban.user_auth.is_banned = False
            ban.user_auth.save(update_fields=['is_banned'])
            ban.delete()
            count += 1
        
        return count
