import pytest
import os
from aioresponses import aioresponses
from fastapi_mail import MessageSchema, MessageType
from starlette.responses import JSONResponse
from src.utils.send_mail import send_verification_code, send_reset_password_code

@pytest.mark.asyncio
async def test_send_verification_code():
    email = "test@example.com"
    code = 123456
    is_unb = True
    DEPLOY_URL = os.getenv("DEPLOY_URL", "http://localhost:8000")

    with aioresponses() as mock:
        mock.post(f"{os.getenv('MAIL_SERVER')}/send", status=200, payload={"status": "success"})
        
        response = await send_verification_code(email, code, is_unb)
        
        assert response.status_code == 200
        assert response.body.decode('utf-8') == '{"status":"success"}'

@pytest.mark.asyncio
async def test_send_reset_password_code():
    email = "test@example.com"
    code = 654321

    with aioresponses() as mock:
        mock.post(f"{os.getenv('MAIL_SERVER')}/send", status=200, payload={"status": "success"})
        
        response = await send_reset_password_code(email, code)
        
        assert response.status_code == 200
        assert response.body.decode('utf-8') == '{"status":"success"}'