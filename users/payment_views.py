# import stripe
# import json
# import paypalrestsdk

# from django.conf import settings
# from django.shortcuts import render
# from django.db.models import Sum
# from django.contrib.auth.models import User
# from django.contrib.auth import authenticate, login
# from django.shortcuts import HttpResponse
# from django.http import FileResponse

# from django.db.models import Sum
# from django.db.models.functions import TruncDate

# from rest_framework import generics, status
# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework.permissions import AllowAny, IsAuthenticated
# from rest_framework_simplejwt.tokens import RefreshToken

# from users.models import Tenant, UserProfile, Invoice, Client, Expense
# from users.serializers import (InvoiceSerializer, ClientSerializer, ExpenseSerializer,
#     SummarySerializer, RecentExpenseSerializer, RecentInvoiceSerializer, InvoiceExpenseTrendSerializer, 
#     ExpenseDistributionSerializer, TenantSerializer)
# from users.utils import generate_invoice_pdf, send_invoice_reminder

# from django.http import JsonResponse
# from django.views.decorators.csrf import csrf_exempt

# from datetime import datetime, timedelta
# from django.utils.timezone import now

# from .serializers import TenantSerializer
# from rest_framework.permissions import IsAuthenticated
# from rest_framework_simplejwt.authentication import JWTAuthentication
    
# # Payment Intent

# class StripePaymentView(APIView):
#     '''Creates a Stripe payment session for an invoice.'''
#     permission_classes = [IsAuthenticated]

#     def post(self, request, invoice_id):
#         invoice = Invoice.objects.get(id=invoice_id, tenant=request.user.userprofile.tenant)
        
#         stripe.api_key = settings.STRIPE_SECRET_KEY
#         payment_intent = stripe.PaymentIntent.create(
#             amount=int(invoice.amount * 100),  # Convert to cents
#             currency="usd",
#             metadata={"invoice_id": invoice.id},
#         )
        
#         return Response({"client_secret": payment_intent.client_secret})



# @csrf_exempt
# def stripe_webhook(request):
#     '''Automatically marks invoice as "paid" when Stripe confirms payment.'''
#     payload = request.body
#     event = None

#     try:
#         event = stripe.Event.construct_from(json.loads(payload), settings.STRIPE_SECRET_KEY)
#     except ValueError:
#         return JsonResponse({"error": "Invalid payload"}, status=400)

#     if event["type"] == "payment_intent.succeeded":
#         invoice_id = event["data"]["object"]["metadata"]["invoice_id"]
#         Invoice.objects.filter(id=invoice_id).update(status="paid")

#     return JsonResponse({"message": "Webhook received"})



# # Create PayPal Payment API

# paypalrestsdk.configure({
#     "mode": "sandbox",  # Change to "live" for production
#     "client_id": settings.PAYPAL_CLIENT_ID,
#     "client_secret": settings.PAYPAL_SECRET_KEY,
# })

# class PayPalPaymentView(APIView):
    
#     permission_classes = [IsAuthenticated]

#     def post(self, request, invoice_id):
#         invoice = Invoice.objects.get(id=invoice_id, tenant=request.user.userprofile.tenant)

#         payment = paypalrestsdk.Payment({
#             "intent": "sale",
#             "payer": {"payment_method": "paypal"},
#             "redirect_urls": {
#                 "return_url": f"http://yourdomain.com/paypal/success/{invoice.id}/",
#                 "cancel_url": f"http://yourdomain.com/paypal/cancel/{invoice.id}/",
#             },
#             "transactions": [{
#                 "amount": {"total": str(invoice.amount), "currency": "USD"},
#                 "description": f"Payment for Invoice {invoice.invoice_number}",
#             }]
#         })

#         if payment.create():
#             return Response({"approval_url": payment.links[1].href})
#         else:
#             return Response({"error": "Payment creation failed"}, status=400)


# @csrf_exempt
# def paypal_webhook(request):
#     '''Automatically updates invoice status when payment is completed.'''
#     data = json.loads(request.body)
    
#     if data["event_type"] == "PAYMENT.SALE.COMPLETED":
#         invoice_id = data["resource"]["transactions"][0]["description"].split()[-1]
#         Invoice.objects.filter(invoice_number=invoice_id).update(status="paid")

#     return JsonResponse({"message": "Webhook received"})



# # Payment Intent

# class StripePaymentView(APIView):
#     '''Creates a Stripe payment session for an invoice.'''
#     permission_classes = [IsAuthenticated]

#     def post(self, request, invoice_id):
#         invoice = Invoice.objects.get(id=invoice_id, tenant=request.user.userprofile.tenant)
        
#         stripe.api_key = settings.STRIPE_SECRET_KEY
#         payment_intent = stripe.PaymentIntent.create(
#             amount=int(invoice.amount * 100),  # Convert to cents
#             currency="usd",
#             metadata={"invoice_id": invoice.id},
#         )
        
#         return Response({"client_secret": payment_intent.client_secret})



# @csrf_exempt
# def stripe_webhook(request):
#     '''Automatically marks invoice as "paid" when Stripe confirms payment.'''
#     payload = request.body
#     event = None

#     try:
#         event = stripe.Event.construct_from(json.loads(payload), settings.STRIPE_SECRET_KEY)
#     except ValueError:
#         return JsonResponse({"error": "Invalid payload"}, status=400)

#     if event["type"] == "payment_intent.succeeded":
#         invoice_id = event["data"]["object"]["metadata"]["invoice_id"]
#         Invoice.objects.filter(id=invoice_id).update(status="paid")

#     return JsonResponse({"message": "Webhook received"})



# # Create PayPal Payment API

# paypalrestsdk.configure({
#     "mode": "sandbox",  # Change to "live" for production
#     "client_id": settings.PAYPAL_CLIENT_ID,
#     "client_secret": settings.PAYPAL_SECRET_KEY,
# })

# class PayPalPaymentView(APIView):
    
#     permission_classes = [IsAuthenticated]

#     def post(self, request, invoice_id):
#         invoice = Invoice.objects.get(id=invoice_id, tenant=request.user.userprofile.tenant)

#         payment = paypalrestsdk.Payment({
#             "intent": "sale",
#             "payer": {"payment_method": "paypal"},
#             "redirect_urls": {
#                 "return_url": f"http://yourdomain.com/paypal/success/{invoice.id}/",
#                 "cancel_url": f"http://yourdomain.com/paypal/cancel/{invoice.id}/",
#             },
#             "transactions": [{
#                 "amount": {"total": str(invoice.amount), "currency": "USD"},
#                 "description": f"Payment for Invoice {invoice.invoice_number}",
#             }]
#         })

#         if payment.create():
#             return Response({"approval_url": payment.links[1].href})
#         else:
#             return Response({"error": "Payment creation failed"}, status=400)


# @csrf_exempt
# def paypal_webhook(request):
#     '''Automatically updates invoice status when payment is completed.'''
#     data = json.loads(request.body)
    
#     if data["event_type"] == "PAYMENT.SALE.COMPLETED":
#         invoice_id = data["resource"]["transactions"][0]["description"].split()[-1]
#         Invoice.objects.filter(invoice_number=invoice_id).update(status="paid")

#     return JsonResponse({"message": "Webhook received"})

# class ClientPayInvoiceView(APIView):
#     '''Clients choose Stripe or PayPal to pay invoices.'''
#     permission_classes = [IsAuthenticated]

#     def post(self, request, invoice_id):
#         invoice = request.user.client.invoices.get(id=invoice_id)

#         if request.data.get("method") == "stripe":
#             stripe.api_key = settings.STRIPE_SECRET_KEY
#             payment_intent = stripe.PaymentIntent.create(
#                 amount=int(invoice.amount * 100),
#                 currency="usd",
#                 metadata={"invoice_id": invoice.id},
#             )
#             return Response({"client_secret": payment_intent.client_secret})

#         elif request.data.get("method") == "paypal":
#             payment = paypalrestsdk.Payment({
#                 "intent": "sale",
#                 "payer": {"payment_method": "paypal"},
#                 "redirect_urls": {
#                     "return_url": f"http://yourdomain.com/paypal/success/{invoice.id}/",
#                     "cancel_url": f"http://yourdomain.com/paypal/cancel/{invoice.id}/",
#                 },
#                 "transactions": [{
#                     "amount": {"total": str(invoice.amount), "currency": "USD"},
#                     "description": f"Payment for Invoice {invoice.invoice_number}",
#                 }]
#             })

#             if payment.create():
#                 return Response({"approval_url": payment.links[1].href})
#             else:
#                 return Response({"error": "Payment failed"}, status=400)

#         return Response({"error": "Invalid payment method"}, status=400)