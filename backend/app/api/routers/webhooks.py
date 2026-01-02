from typing import Optional
from fastapi import APIRouter, File, Form, HTTPException, FastAPI, Response, UploadFile,status, Request
from fastapi.params import Depends
from app.schemas.general import StandardResponse as resp
from app.utils.logging import logger
from typing import Optional
from app.models import vehicle_category_rate
from ..services.stripe_services.webhooks import WebhookServices, get_ebhook_services

router = APIRouter(
    prefix = "/api/v1/webhooks",
    tags = ["Webhooks"]
)


@router.post("/tenant/connect", status_code=201)
async def tenant_connect_service(request: Request,
                                webhook_service: WebhookServices = Depends(get_ebhook_services),
                           ):
 
    webhook =await webhook_service.tenant_connect_webhooks(request=request)
    return webhook

@router.post("/", status_code=status.HTTP_201_CREATED)
async def stripe_webooks(request: Request, stripe_service: WebhookServices = Depends(get_ebhook_services)):
    webhooks = await stripe_service.webhook(request)
    return webhooks