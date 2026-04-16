import asyncio
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from pathlib import Path
from typing import List, Optional

from services.file_service import (
    generate_file_id, save_upload, MAX_FILE_SIZE,
    decrypt_to_temp, encrypt_output, decrypt_for_download, cleanup_temp_files,
)
from services.convert_service import (
    pdf_to_images,
    images_to_pdf,
    word_to_pdf,
    powerpoint_to_pdf,
    excel_to_pdf,
    html_to_pdf,
    url_to_pdf,
    normalize_image_format,
)
from services.pdf_service import extract_text

router = APIRouter(prefix="/api/convert", tags=["convert"])


@router.post("/pdf-to-image")
async def convert_pdf_to_image(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    fmt: str = Form("png"),
    dpi: int = Form(200),
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="File must be a PDF.")

    try:
        fmt = normalize_image_format(fmt)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File exceeds 100MB limit.")

    file_id = generate_file_id()
    enc_path = await save_upload(content, file_id, file.filename)

    try:
        dec_path = decrypt_to_temp(enc_path, file_id)
        output_path = await asyncio.to_thread(pdf_to_images, dec_path, file_id, fmt=fmt, dpi=dpi)

        stem = Path(file.filename).stem
        if output_path.suffix == ".zip":
            media_type = "application/zip"
            download_name = f"{stem}_images.zip"
        else:
            media_type = "image/jpeg" if fmt == "jpg" else "image/png"
            download_name = f"{stem}.{fmt}"

        encrypt_output(output_path, file_id)
        download_path = decrypt_for_download(output_path, file_id)

        background_tasks.add_task(cleanup_temp_files, file_id)
        return FileResponse(
            path=str(download_path),
            media_type=media_type,
            filename=download_name,
        )
    except Exception as e:
        cleanup_temp_files(file_id)
        raise HTTPException(status_code=500, detail=f"Conversion failed: {str(e)}")


@router.post("/image-to-pdf")
async def convert_images_to_pdf(
    background_tasks: BackgroundTasks,
    files: Optional[List[UploadFile]] = File(None),
    file: Optional[UploadFile] = File(None),
    page_size: str = Form("a4"),
):
    selected_files = []
    if files:
        selected_files.extend(files)
    if file:
        selected_files.append(file)

    if len(selected_files) == 0:
        raise HTTPException(status_code=400, detail="At least 1 image is required.")

    file_id = generate_file_id()
    encrypted_paths = []
    first_name = selected_files[0].filename or "image"

    allowed_exts = (".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff", ".webp")
    for f in selected_files:
        filename = f.filename or "image"
        if not filename.lower().endswith(allowed_exts):
            raise HTTPException(
                status_code=400,
                detail=f"File '{filename}' is not a supported image format.",
            )

        content = await f.read()
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail=f"File '{filename}' exceeds 100MB limit.")

        path = await save_upload(content, file_id, filename)
        encrypted_paths.append(path)

    try:
        decrypted_paths = [decrypt_to_temp(p, file_id) for p in encrypted_paths]
        output_path = await asyncio.to_thread(images_to_pdf, decrypted_paths, file_id, page_size)
        encrypt_output(output_path, file_id)
        download_path = decrypt_for_download(output_path, file_id)

        stem = Path(first_name).stem
        background_tasks.add_task(cleanup_temp_files, file_id)
        return FileResponse(
            path=str(download_path),
            media_type="application/pdf",
            filename=f"{stem}_converted.pdf",
        )
    except Exception as e:
        cleanup_temp_files(file_id)
        raise HTTPException(status_code=500, detail=f"Conversion failed: {str(e)}")


@router.post("/word-to-pdf")
async def convert_word_to_pdf(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    if not file.filename.lower().endswith((".doc", ".docx")):
        raise HTTPException(status_code=400, detail="File must be a Word document (.doc or .docx).")

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File exceeds 100MB limit.")

    file_id = generate_file_id()
    enc_path = await save_upload(content, file_id, file.filename)

    try:
        dec_path = decrypt_to_temp(enc_path, file_id)
        output_path = await asyncio.to_thread(word_to_pdf, dec_path, file_id)
        encrypt_output(output_path, file_id)
        download_path = decrypt_for_download(output_path, file_id)

        stem = Path(file.filename).stem
        background_tasks.add_task(cleanup_temp_files, file_id)
        return FileResponse(
            path=str(download_path),
            media_type="application/pdf",
            filename=f"{stem}_converted.pdf",
        )
    except Exception as e:
        cleanup_temp_files(file_id)
        raise HTTPException(status_code=500, detail=f"Conversion failed: {str(e)}")


@router.post("/ppt-to-pdf")
async def convert_ppt_to_pdf(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    if not file.filename.lower().endswith((".ppt", ".pptx", ".odp")):
        raise HTTPException(status_code=400, detail="File must be a PowerPoint document (.ppt, .pptx, or .odp).")

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File exceeds 100MB limit.")

    file_id = generate_file_id()
    enc_path = await save_upload(content, file_id, file.filename)

    try:
        dec_path = decrypt_to_temp(enc_path, file_id)
        output_path = await asyncio.to_thread(powerpoint_to_pdf, dec_path, file_id)
        encrypt_output(output_path, file_id)
        download_path = decrypt_for_download(output_path, file_id)

        stem = Path(file.filename).stem
        background_tasks.add_task(cleanup_temp_files, file_id)
        return FileResponse(
            path=str(download_path),
            media_type="application/pdf",
            filename=f"{stem}_converted.pdf",
        )
    except Exception as e:
        cleanup_temp_files(file_id)
        raise HTTPException(status_code=500, detail=f"Conversion failed: {str(e)}")


@router.post("/excel-to-pdf")
async def convert_excel_to_pdf(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    if not file.filename.lower().endswith((".xls", ".xlsx", ".ods", ".csv")):
        raise HTTPException(status_code=400, detail="File must be a spreadsheet (.xls, .xlsx, .ods, or .csv).")

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File exceeds 100MB limit.")

    file_id = generate_file_id()
    enc_path = await save_upload(content, file_id, file.filename)

    try:
        dec_path = decrypt_to_temp(enc_path, file_id)
        output_path = await asyncio.to_thread(excel_to_pdf, dec_path, file_id)
        encrypt_output(output_path, file_id)
        download_path = decrypt_for_download(output_path, file_id)

        stem = Path(file.filename).stem
        background_tasks.add_task(cleanup_temp_files, file_id)
        return FileResponse(
            path=str(download_path),
            media_type="application/pdf",
            filename=f"{stem}_converted.pdf",
        )
    except Exception as e:
        cleanup_temp_files(file_id)
        raise HTTPException(status_code=500, detail=f"Conversion failed: {str(e)}")


@router.post("/html-to-pdf")
async def convert_html_to_pdf(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    if not file.filename.lower().endswith((".html", ".htm")):
        raise HTTPException(status_code=400, detail="File must be an HTML document (.html or .htm).")

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File exceeds 100MB limit.")

    file_id = generate_file_id()
    enc_path = await save_upload(content, file_id, file.filename)

    try:
        dec_path = decrypt_to_temp(enc_path, file_id)
        output_path = await asyncio.to_thread(html_to_pdf, dec_path, file_id)
        encrypt_output(output_path, file_id)
        download_path = decrypt_for_download(output_path, file_id)

        stem = Path(file.filename).stem
        background_tasks.add_task(cleanup_temp_files, file_id)
        return FileResponse(
            path=str(download_path),
            media_type="application/pdf",
            filename=f"{stem}_converted.pdf",
        )
    except Exception as e:
        cleanup_temp_files(file_id)
        raise HTTPException(status_code=500, detail=f"Conversion failed: {str(e)}")


@router.post("/url-to-pdf")
async def convert_url_to_pdf(
    background_tasks: BackgroundTasks,
    url: str = Form(...),
):
    file_id = generate_file_id()

    try:
        output_path = await asyncio.to_thread(url_to_pdf, url, file_id)
        encrypt_output(output_path, file_id)
        download_path = decrypt_for_download(output_path, file_id)

        background_tasks.add_task(cleanup_temp_files, file_id)
        return FileResponse(
            path=str(download_path),
            media_type="application/pdf",
            filename="webpage_converted.pdf",
        )
    except ValueError as e:
        cleanup_temp_files(file_id)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        cleanup_temp_files(file_id)
        raise HTTPException(status_code=500, detail=f"Conversion failed: {str(e)}")


@router.post("/extract-text")
async def extract_text_from_pdf(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="File must be a PDF.")

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File exceeds 100MB limit.")

    file_id = generate_file_id()
    enc_path = await save_upload(content, file_id, file.filename)

    try:
        dec_path = decrypt_to_temp(enc_path, file_id)
        output_path = await asyncio.to_thread(extract_text, dec_path, file_id)
        encrypt_output(output_path, file_id)
        download_path = decrypt_for_download(output_path, file_id)

        stem = Path(file.filename).stem
        background_tasks.add_task(cleanup_temp_files, file_id)
        return FileResponse(
            path=str(download_path),
            media_type="text/plain",
            filename=f"{stem}_text.txt",
        )
    except Exception as e:
        cleanup_temp_files(file_id)
        raise HTTPException(status_code=500, detail=f"Text extraction failed: {str(e)}")
