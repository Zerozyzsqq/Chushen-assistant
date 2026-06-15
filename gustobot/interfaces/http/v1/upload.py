"""
文件上传处理API
"""
import os
import uuid
import aiofiles
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, UploadFile, File, HTTPException, status
from fastapi.responses import JSONResponse
from loguru import logger

from gustobot.config import settings
from gustobot.infrastructure.core.paths import UPLOAD_IMAGE_ROOT, UPLOAD_ROOT, ensure_upload_dirs

router = APIRouter()

ensure_upload_dirs()

# 支持的文件类型
ALLOWED_FILE_TYPES = {
    '.txt', '.md', '.json', '.csv', '.log', '.xlsx', '.xls', '.pdf', '.doc', '.docx'
}

ALLOWED_IMAGE_TYPES = {
    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'
}

# 最大文件大小 (50MB)
MAX_FILE_SIZE = 50 * 1024 * 1024


def _safe_stored_name(file_id: str, original_name: str, allowed_exts: set[str], default_ext: str) -> str:
    ext = Path(original_name or "").suffix.lower()
    if ext not in allowed_exts:
        ext = default_ext
    return f"{file_id}{ext}"


@router.post("/file")
async def upload_file(file: UploadFile = File(...)) -> JSONResponse:
    """上传文件（txt, excel, pdf等）"""

    # 检查文件类型
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_FILE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的文件类型。支持的类型: {', '.join(ALLOWED_FILE_TYPES)}"
        )

    try:
        # 生成唯一文件名
        file_id = str(uuid.uuid4())
        filename = _safe_stored_name(file_id, file.filename or "upload.txt", ALLOWED_FILE_TYPES, ".txt")
        file_path = UPLOAD_ROOT / filename

        # 保存文件
        content = await file.read()
        file_size = len(content)

        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"文件太大，最大支持 {MAX_FILE_SIZE // (1024*1024)}MB"
            )

        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(content)

        logger.info(f"文件上传成功: {filename} ({file_size} bytes)")

        return JSONResponse({
            "success": True,
            "file_id": file_id,
            "filename": filename,
            "original_name": file.filename,
            "size": file_size,
            "file_path": str(file_path.resolve()),
            "file_url": f"/api/v1/upload/files/{filename}",
            "file_type": file_ext
        })

    except Exception as e:
        logger.error(f"文件上传失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"文件上传失败: {str(e)}"
        )


@router.post("/image")
async def upload_image(image: UploadFile = File(...)) -> JSONResponse:
    """上传图片文件"""

    # 检查文件类型
    file_ext = Path(image.filename).suffix.lower()
    if file_ext not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的图片类型。支持的类型: {', '.join(ALLOWED_IMAGE_TYPES)}"
        )

    try:
        # 生成唯一文件名
        image_id = str(uuid.uuid4())
        filename = _safe_stored_name(image_id, image.filename or "upload.jpg", ALLOWED_IMAGE_TYPES, ".jpg")

        file_path = UPLOAD_IMAGE_ROOT / filename

        # 保存图片
        content = await image.read()
        file_size = len(content)

        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"图片太大，最大支持 {MAX_FILE_SIZE // (1024*1024)}MB"
            )

        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(content)

        logger.info(f"图片上传成功: {filename} ({file_size} bytes)")

        return JSONResponse({
            "success": True,
            "image_id": image_id,
            "filename": filename,
            "original_name": image.filename,
            "size": file_size,
            "file_path": str(file_path.resolve()),
            "image_url": f"/api/v1/upload/images/{filename}",
            "file_type": file_ext
        })

    except Exception as e:
        logger.error(f"图片上传失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"图片上传失败: {str(e)}"
        )


@router.get("/files/{filename}")
async def get_uploaded_file(filename: str):
    """获取上传的文件"""
    file_path = UPLOAD_ROOT / filename
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文件不存在"
        )

    from fastapi.responses import FileResponse
    return FileResponse(file_path)


@router.get("/images/{filename}")
async def get_uploaded_image(filename: str):
    """获取上传的图片"""
    file_path = UPLOAD_IMAGE_ROOT / filename
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="图片不存在"
        )

    from fastapi.responses import FileResponse
    return FileResponse(file_path)


@router.delete("/{file_id}")
async def delete_uploaded_file(file_id: str):
    """删除上传的文件"""
    # 查找文件
    for file_path in UPLOAD_ROOT.rglob(f"{file_id}_*"):
        try:
            file_path.unlink()
            logger.info(f"文件删除成功: {file_path}")
            return JSONResponse({
                "success": True,
                "message": "文件删除成功"
            })
        except Exception as e:
            logger.error(f"文件删除失败: {e}")
            break

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="文件不存在"
    )
