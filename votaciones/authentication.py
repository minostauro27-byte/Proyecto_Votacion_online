from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from firebase_admin import auth
import firebase_admin
from votacion.firebase_config import initialize_firebase

db = initialize_firebase()

class FirebaseAuthentication(BaseAuthentication):
    """
    Leer el token JWT del encabezado. lo va a validar con firebase y va a extraer el UID usuario
    """
    def authenticate(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION') or request.headers.get('Authorization')
        
        if not auth_header:
            return None 

        partes = auth_header.split()

        if len(partes) != 2 or partes[0].lower() != 'bearer':
            return None
        
        token = partes[1]

        try:
            decoded_token = auth.verify_id_token(token)
            
            uid = decoded_token.get('uid')
            email = decoded_token.get('email')
            

            user_profile = db.collection('perfiles').document(uid).get()
            
            rol = user_profile.to_dict().get('rol','votante') if user_profile.exists else 'votante'

            class FirebaseUser:
                def __init__(self, uid, rol, email):
                    self.uid = uid
                    self.rol = rol
                    self.email = email
                    self.is_authenticated = True

            return (FirebaseUser(uid, rol, email), decoded_token)
        
        except Exception as e:
            raise AuthenticationFailed(f"El token no es valido o esta expirado: {str(e)}")
