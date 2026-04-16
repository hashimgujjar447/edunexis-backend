from rest_framework.throttling import AnonRateThrottle



class RegisterThrottle(AnonRateThrottle):
    rate = '5/min'   



class VerifyThrottle(AnonRateThrottle):
    rate = '5/min'  


class ResetConfirmThrottle(AnonRateThrottle):
    rate = '5/min'