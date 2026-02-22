from rest_framework.throttling import AnonRateThrottle

class PlanThrottle(AnonRateThrottle):
    rate = "200/min"



class CreateInvoiceThrottle(AnonRateThrottle):
    rate = "30/min"